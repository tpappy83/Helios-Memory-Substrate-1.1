"""tests/test_tiering.py — 6 tests for core/tiering.py (v0.2 NEXT).

Covers:
1. Pure function: compute_drift formula
2. Pure function: compute_recency exponential decay
3. Pure function: update_temperature_ema EMA math
4. Pure function: compute_final_score linear reranker
5. DB-backed: apply_tiering_decision promote/demote round-trip
6. DB-backed: rerank_candidates feedback loop on top-K
"""
import math
import time

from core import tiering
from core.memory import write_memory
from core.db import connect


# ─── 1. compute_drift formula ─────────────────────────────────────

def test_compute_drift_formula():
    """drift = 0.02 + 0.01·cycles + 0.001·reads (v4.1 line 54)."""
    assert tiering.compute_drift(0, 0) == 0.02
    assert tiering.compute_drift(2, 0) == 0.04
    assert tiering.compute_drift(0, 10) == 0.03
    assert round(tiering.compute_drift(2, 10), 4) == 0.05


# ─── 2. compute_recency exponential decay ─────────────────────────

def test_compute_recency_exponential():
    """recency = exp(-Δt / 600) (v4.1 line 194)."""
    now = 10000.0
    # Δt = 0 → recency = 1.0
    assert tiering.compute_recency(now, now) == 1.0
    # Δt = 600 → recency = exp(-1) ≈ 0.3679
    assert round(tiering.compute_recency(now - 600.0, now), 4) == round(math.exp(-1.0), 4)
    # Older records decay further
    assert tiering.compute_recency(now - 1200.0, now) < tiering.compute_recency(now - 600.0, now)


# ─── 3. update_temperature_ema ────────────────────────────────────

def test_update_temperature_ema_math():
    """EMA: temp = α·score + (1-α)·prev, α=0.3 (v4.1 line 178)."""
    # Score 1.0 nudges 0.5 → 0.65
    assert round(tiering.update_temperature_ema(0.5, 1.0), 4) == 0.65
    # Score 0.0 nudges 0.5 → 0.35
    assert round(tiering.update_temperature_ema(0.5, 0.0), 4) == 0.35
    # Identity check
    assert round(tiering.update_temperature_ema(0.7, 0.7), 4) == 0.7


# ─── 4. compute_final_score reranker formula ───────────────────────

def test_compute_final_score_weights():
    """score = 0.55·sim + 0.20·val + 0.10·rec + 0.10·tier - 0.05·drift (v4.1 line 197)."""
    # All-1 inputs minus drift = 0.55 + 0.20 + 0.10 + 0.10 - 0 = 0.95
    assert round(tiering.compute_final_score(1.0, 1.0, 1.0, 1.0, 0.0), 4) == 0.95
    # All-0 except drift=1 → -0.05
    assert round(tiering.compute_final_score(0.0, 0.0, 0.0, 0.0, 1.0), 4) == -0.05
    # Similarity dominates: 1.0 sim alone → 0.55
    assert round(tiering.compute_final_score(1.0, 0.0, 0.0, 0.0, 0.0), 4) == 0.55


# ─── 5. apply_tiering_decision round-trip ─────────────────────────

def test_apply_tiering_decision_round_trip():
    """High temperature → promote to hot; low temperature → demote to cold."""
    rid = write_memory(content="hot data", type="observation")

    # Force temperature above promote threshold
    with connect() as cx:
        cx.execute(
            "UPDATE memory_records SET temperature = 0.9, tier = 'cold' WHERE id = ?",
            (rid,),
        )
    action = tiering.apply_tiering_decision(rid)
    assert action == "promote"
    with connect() as cx:
        row = cx.execute(
            "SELECT tier, compression_cycles FROM memory_records WHERE id = ?", (rid,)
        ).fetchone()
    assert row["tier"] == "hot"
    assert row["compression_cycles"] == 1

    # Force temperature below demote threshold
    with connect() as cx:
        cx.execute(
            "UPDATE memory_records SET temperature = 0.1 WHERE id = ?", (rid,)
        )
    action = tiering.apply_tiering_decision(rid)
    assert action == "demote"
    with connect() as cx:
        row = cx.execute(
            "SELECT tier, compression_cycles FROM memory_records WHERE id = ?", (rid,)
        ).fetchone()
    assert row["tier"] == "cold"
    assert row["compression_cycles"] == 2

    # Mid-temperature: no change
    with connect() as cx:
        cx.execute(
            "UPDATE memory_records SET temperature = 0.5 WHERE id = ?", (rid,)
        )
    action = tiering.apply_tiering_decision(rid)
    assert action is None


# ─── 6. rerank_candidates feedback loop ────────────────────────────

def test_rerank_candidates_top_k_feedback():
    """rerank_candidates updates temperature on top-K and returns sorted final scores."""
    r1 = write_memory(content="alpha quick brown")
    r2 = write_memory(content="beta lazy dog")
    r3 = write_memory(content="gamma jumps over")

    # Feed in fake similarity scores
    inputs = [(r1, 0.9), (r2, 0.5), (r3, 0.7)]
    out = tiering.rerank_candidates(inputs)

    assert len(out) == 3
    # Top scorer first
    assert out[0][0] == r1
    # Output is sorted descending by final score
    assert out[0][1] >= out[1][1] >= out[2][1]

    # Top-K feedback: r1's temperature should have moved (was 0.5, EMA toward final score)
    with connect() as cx:
        row = cx.execute(
            "SELECT temperature FROM memory_records WHERE id = ?", (r1,)
        ).fetchone()
    assert row["temperature"] != 0.5, "EMA should have updated temperature"


# ─── Bonus: tier_distribution + reranker_weights diagnostics ──────

def test_tier_distribution_and_weights():
    """The /stats endpoint exposes tier_distribution + reranker_weights."""
    write_memory(content="x")
    dist = tiering.tier_distribution()
    assert sum(dist.values()) == 1
    assert "cold" in dist   # default tier on new rows

    weights = tiering.reranker_weights()
    assert weights["similarity"] == tiering.W_SIMILARITY
    assert sum([weights["similarity"], weights["value"],
                weights["recency"], weights["tier"]]) <= 1.0 + 0.01
