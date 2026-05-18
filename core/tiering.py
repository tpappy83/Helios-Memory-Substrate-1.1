"""core/tiering.py — Helios v0.2 NEXT: temperature/drift/reranker tiering.

Formulas ported verbatim from Helios v4.1 spec
(see attached_assets/helios_core_(faiss_ivf_&_zero_copy)_*.py
 lines 54, 173-186, 193-197, 217).

Design constraints honored (per Helios wedges):
- No vector DB dependency (preserves wedge #2: no vector DB)
- No new heavy deps beyond stdlib (preserves wedge #3: dev-loop simplicity)
- Reads memory_records via core.db.connect() (preserves single-SoT)
- 2-tier collapse (hot/cold) from v4.1's 4-tier HBM4/NVMe/SSD/Archive
  — quantization deferred until row count justifies it
- Single canonical schema in schema.sql — this module reads existing columns
  via the v2 migration in migrations/002_tiering_namespace_audit.sql

Public API:
- compute_drift, compute_recency, compute_final_score, update_temperature_ema
  → pure functions, no I/O, testable in isolation
- record_access, update_temperature, apply_tiering_decision
  → DB-backed, single-row operations
- rerank_candidates
  → high-level entrypoint called from core.llm.llm_rerank or similar
- decay_inactive_records
  → background-worker scaffold (call from a periodic task)
"""
from __future__ import annotations

import math
import time
from typing import Iterable, Optional

from core.db import connect

# ─── Constants (verbatim from v4.1 spec) ──────────────────────────────

ALPHA = 0.3                  # Temperature EMA decay coefficient — v4.1 line 173
PROMOTE_THRESHOLD = 0.65     # v4.1 line 174
DEMOTE_THRESHOLD = 0.35      # v4.1 line 174

W_SIMILARITY = 0.55          # v4.1 line 193
W_VALUE      = 0.20
W_RECENCY    = 0.10
W_TIER       = 0.10
W_DRIFT      = 0.05

TIER_HOT = "hot"
TIER_COLD = "cold"
TIER_BONUS = {TIER_HOT: 1.0, TIER_COLD: 0.3}    # collapsed from v4.1's {0:1.0, 1:0.6, 2:0.3, 3:0.0}

RECENCY_TAU_SEC = 600.0      # v4.1 line 194

DEFAULT_TEMPERATURE = 0.5    # New rows start neutral
RERANK_FEEDBACK_TOP_K = 20   # v4.1 line 217 — apply tiering only on the top-K


# ─── Pure functions (no I/O) ──────────────────────────────────────────

def compute_drift(compression_cycles: int, read_count: int) -> float:
    """Drift score: increases with re-tiering and reads.

    Verbatim from v4.1 line 54.

    >>> compute_drift(0, 0)
    0.02
    >>> round(compute_drift(2, 10), 4)
    0.05
    """
    return 0.02 + 0.01 * compression_cycles + 0.001 * read_count


def compute_recency(ts_epoch: float, now: Optional[float] = None) -> float:
    """Exponential decay; ~600-second time constant.

    Verbatim from v4.1 line 194.

    Returns ~1.0 for fresh records, decays toward 0.0 as records age.
    """
    delta = (now or time.time()) - ts_epoch
    return math.exp(-delta / RECENCY_TAU_SEC)


def compute_final_score(
    sim: float,
    value: float,
    recency: float,
    tier_bonus: float,
    drift: float,
) -> float:
    """Linear reranker formula. Weights and form from v4.1 lines 193, 197.

    In current Helios the `sim` slot is fed by either FTS5 BM25
    or the existing LLM-rerank score from core.llm.llm_rerank().
    """
    return (W_SIMILARITY * sim
            + W_VALUE * value
            + W_RECENCY * recency
            + W_TIER * tier_bonus
            - W_DRIFT * drift)


def update_temperature_ema(current_temp: float, new_score: float, alpha: float = ALPHA) -> float:
    """EMA update: temp = α·score + (1-α)·prev.

    Verbatim from v4.1 line 178.

    >>> round(update_temperature_ema(0.5, 1.0), 4)
    0.65
    >>> round(update_temperature_ema(0.5, 0.0), 4)
    0.35
    """
    return alpha * new_score + (1 - alpha) * current_temp


# ─── DB-backed single-row operations ──────────────────────────────────

def record_access(record_id: str) -> None:
    """Bump read_count + last_accessed. Call on each retrieval hit."""
    with connect() as cx:
        cx.execute(
            "UPDATE memory_records SET read_count = read_count + 1, "
            "last_accessed = ? WHERE id = ?",
            (time.time(), record_id),
        )


def update_temperature(record_id: str, new_score: float) -> float:
    """Apply EMA + persist. Returns the new temperature.

    Returns DEFAULT_TEMPERATURE if record_id is unknown (caller may have
    raced with a delete; degrade gracefully rather than raising).
    """
    with connect() as cx:
        row = cx.execute(
            "SELECT temperature FROM memory_records WHERE id = ?",
            (record_id,),
        ).fetchone()
        if row is None:
            return DEFAULT_TEMPERATURE

        new = update_temperature_ema(row[0], new_score)
        cx.execute(
            "UPDATE memory_records SET temperature = ? WHERE id = ?",
            (new, record_id),
        )
        return new


def apply_tiering_decision(record_id: str) -> Optional[str]:
    """Move record between hot/cold based on its temperature.

    Returns "promote", "demote", or None.
    Increments compression_cycles on every transition (v4.1 semantics —
    each tier change consumes a re-compression cycle, contributes to drift).
    """
    with connect() as cx:
        row = cx.execute(
            "SELECT tier, temperature, compression_cycles "
            "FROM memory_records WHERE id = ?",
            (record_id,),
        ).fetchone()
        if row is None:
            return None

        tier, temp, cycles = row

        if temp > PROMOTE_THRESHOLD and tier != TIER_HOT:
            cx.execute(
                "UPDATE memory_records SET tier = ?, compression_cycles = ? "
                "WHERE id = ?",
                (TIER_HOT, cycles + 1, record_id),
            )
            return "promote"

        if temp < DEMOTE_THRESHOLD and tier != TIER_COLD:
            cx.execute(
                "UPDATE memory_records SET tier = ?, compression_cycles = ? "
                "WHERE id = ?",
                (TIER_COLD, cycles + 1, record_id),
            )
            return "demote"

        return None


# ─── High-level rerank entrypoint ─────────────────────────────────────

def rerank_candidates(
    candidates: Iterable[tuple[str, float]],
) -> list[tuple[str, float]]:
    """Given (record_id, similarity_or_llm_score) pairs, rerank using full formula.

    Side effects on top-K (per v4.1 line 217 feedback loop):
    - Updates temperature via EMA on each top-K record
    - Applies tier promote/demote decisions on each top-K record

    Returns: list of (record_id, final_score) sorted descending.

    Typical wiring in core.llm.query_memories:
        candidates = keyword_candidates(query, k=25)
        scored     = llm_rerank(query, candidates)        # → (id, score) pairs
        reranked   = rerank_candidates(scored)            # tier-aware reweight
        return reranked[:top_k]
    """
    out: list[tuple[str, float]] = []
    now = time.time()

    with connect() as cx:
        for rid, sim in candidates:
            row = cx.execute(
                "SELECT importance, timestamp, tier, read_count, "
                "compression_cycles FROM memory_records WHERE id = ?",
                (rid,),
            ).fetchone()
            if row is None:
                continue

            value, ts, tier, reads, cycles = row
            final = compute_final_score(
                sim,
                value if value is not None else DEFAULT_TEMPERATURE,
                compute_recency(ts, now),
                TIER_BONUS.get(tier, TIER_BONUS[TIER_COLD]),
                compute_drift(cycles, reads),
            )
            out.append((rid, final))

    out.sort(key=lambda x: x[1], reverse=True)

    # v4.1 line 217: feedback loop on top-K only (cheap, focuses adaptation
    # on records actually being used).
    for rid, score in out[:RERANK_FEEDBACK_TOP_K]:
        update_temperature(rid, score)
        apply_tiering_decision(rid)

    return out


# ─── Background decay worker scaffold ─────────────────────────────────

def decay_inactive_records(stale_seconds: float = 86400.0) -> int:
    """Bump temperature downward on records with no recent access.

    Designed to be called from a periodic background worker
    (e.g., apscheduler or a simple threading.Timer in core.bg).

    Returns count of records demoted by this pass.

    Algorithm:
    - Find records last accessed > stale_seconds ago that are still HOT
      with temperature above the demote threshold.
    - Apply one EMA decay step with new_score=0 (pure decay).
    - Run apply_tiering_decision on each; count demotions.
    """
    cutoff = time.time() - stale_seconds
    demoted = 0

    with connect() as cx:
        rows = cx.execute(
            "SELECT id, temperature FROM memory_records "
            "WHERE (last_accessed IS NULL OR last_accessed < ?) "
            "AND tier = ? AND temperature > ?",
            (cutoff, TIER_HOT, DEMOTE_THRESHOLD),
        ).fetchall()

        for rid, temp in rows:
            new_temp = update_temperature_ema(temp, 0.0)
            cx.execute(
                "UPDATE memory_records SET temperature = ? WHERE id = ?",
                (new_temp, rid),
            )

    # Apply tiering decisions OUTSIDE the SELECT cursor to avoid lock churn.
    for rid, _ in rows:
        if apply_tiering_decision(rid) == "demote":
            demoted += 1

    return demoted


# ─── Diagnostics ──────────────────────────────────────────────────────

def tier_distribution() -> dict[str, int]:
    """Return {tier: count} for /stats endpoint."""
    with connect() as cx:
        rows = cx.execute(
            "SELECT tier, COUNT(*) FROM memory_records GROUP BY tier"
        ).fetchall()
    return {tier: count for tier, count in rows}


def reranker_weights() -> dict[str, float]:
    """Return current weights for /config/retrieval inspection."""
    return {
        "similarity": W_SIMILARITY,
        "value":      W_VALUE,
        "recency":    W_RECENCY,
        "tier":       W_TIER,
        "drift":      W_DRIFT,
    }


if __name__ == "__main__":   # pragma: no cover
    import doctest
    doctest.testmod(verbose=True)
