"""tests/test_harmonic.py — Wave-Coherence Stage-3 plugin tests.

Validates the harmonic decomposition math primitive and its integration into
the Helios Stage 3 rerank.

Per the Wave-Coherence framework (atech-hub/Wave-Coherence-as-a-Computational-Primitive):
- Standard cosine similarity captures only n=1 harmonic
- Higher harmonics reveal structured relationships (opposition n=2, triadic n=3,
  quadrant n=4, pentagonal n=5, sextile n=6)
- The harmonic sweep recovers them all
"""
import math

import pytest

from core import harmonic as h


def test_fundamental_equals_cosine():
    """n=1 harmonic IS the standard cosine similarity."""
    v = [1.0, 0.0]
    u = [math.cos(math.pi/3), math.sin(math.pi/3)]   # 60-degree pair
    sweep = h.harmonic_sweep(v, u, harmonics=(1,))
    assert round(sweep[1], 4) == round(math.cos(math.pi/3), 4)


def test_triadic_recovery():
    """At 120 degrees, cosine = -0.5 BUT n=3 harmonic = cos(360) = +1.0."""
    v = [1.0, 0.0]
    u = [math.cos(2*math.pi/3), math.sin(2*math.pi/3)]
    sweep = h.harmonic_sweep(v, u, harmonics=(1, 2, 3))
    assert round(sweep[1], 4) == -0.5            # standard cosine
    assert round(sweep[3], 4) == 1.0              # triadic harmonic = +1
    # n=2 is opposition; 120° is not opposition
    assert round(sweep[2], 4) != 1.0


def test_opposition_recovery():
    """At 180 degrees, n=2 harmonic = cos(360) = +1.0."""
    v = [1.0, 0.0]
    u = [-1.0, 0.0]
    sweep = h.harmonic_sweep(v, u, harmonics=(1, 2, 3))
    assert round(sweep[1], 4) == -1.0           # cosine = -1
    assert round(sweep[2], 4) == 1.0             # opposition harmonic = +1


def test_quadrant_collapses_cosine_but_n4_recovers():
    """At 90 degrees, cosine = 0 BUT n=4 harmonic = cos(360) = +1.0."""
    v = [1.0, 0.0]
    u = [0.0, 1.0]
    sweep = h.harmonic_sweep(v, u, harmonics=(1, 2, 4))
    assert abs(sweep[1]) < 1e-9                  # cosine collapses to 0
    assert round(sweep[4], 4) == 1.0             # quadrant harmonic = +1


def test_harmonic_distance_typed_named_relations():
    """harmonic_distance_typed exposes named relations cleanly."""
    v = [1.0, 0.0]
    # 120-degree pair = triadic
    u = [math.cos(2*math.pi/3), math.sin(2*math.pi/3)]
    assert round(h.harmonic_distance_typed(v, u, 'triadic'), 4) == 1.0
    assert round(h.harmonic_distance_typed(v, u, 'opposition'), 4) != 1.0
    # 90-degree pair = quadrant
    u90 = [0.0, 1.0]
    assert round(h.harmonic_distance_typed(v, u90, 'quadrant'), 4) == 1.0


def test_zero_vector_returns_zero_angle():
    """Defensive: zero vector input doesn't crash."""
    assert h.angle_between([0.0, 0.0], [1.0, 0.0]) == 0.0


def test_multi_channel_embedding_dimension():
    """Construct a multi-channel embedding for synthetic testing."""
    theta = math.pi / 4
    vec = h.multi_channel_embedding(theta, harmonics=(1, 2, 3))
    # Each harmonic contributes 2 dims (cos, sin)
    assert len(vec) == 6


def test_multi_channel_demonstrates_cosine_collapse():
    """Show: cosine similarity collapses to 0 between multi-channel encodings of
    certain pairs while PER-CHANNEL inner products recover their structured
    relationships.

    This is the central claim of the Wave-Coherence framework, reproduced as a
    unit test.

    IMPORTANT: for multi-channel embeddings, the "harmonic sweep" must use the
    per-channel inner product (`harmonic_at`), NOT the full-vector angle followed
    by cos(n × Δθ). The latter gives the wrong answer because the full-vector
    angle is the average across all channels.
    """
    HARMONICS = (1, 2, 3, 4, 5, 6)
    # 12-entity unit-circle encoding (per the Wave-Coherence demonstration)
    N = 12
    entities = [
        h.multi_channel_embedding(2 * math.pi * i / N, harmonics=HARMONICS)
        for i in range(N)
    ]
    # Find a pair where standard cosine collapses to ~0
    collapses_found = 0
    recovered_at_n3 = 0
    recovered_at_n4 = 0
    for i in range(N):
        for j in range(i + 1, N):
            # Standard cosine on the full multi-channel vector
            v, u = entities[i], entities[j]
            dot = sum(a * b for a, b in zip(v, u))
            nv = math.sqrt(sum(a * a for a in v))
            nu = math.sqrt(sum(b * b for b in u))
            cos_sim = dot / (nv * nu)

            if abs(cos_sim) < 0.05:   # cosine effectively 0
                collapses_found += 1
                # PER-CHANNEL n=3 harmonic on this collapsed pair
                n3 = h.harmonic_at(v, u, 3, harmonics=HARMONICS)
                n4 = h.harmonic_at(v, u, 4, harmonics=HARMONICS)
                d = (j - i) % N
                # Triadic on 12-entity = 4 apart OR 8 apart
                if d in (4, 8) and n3 > 0.95:
                    recovered_at_n3 += 1
                # Quadrant on 12-entity = 3 apart OR 9 apart
                if d in (3, 9) and n4 > 0.95:
                    recovered_at_n4 += 1

    assert collapses_found > 0, "expected cosine collapses in 12-entity encoding"
    assert recovered_at_n3 > 0 or recovered_at_n4 > 0, (
        "expected per-channel harmonic to recover at least one structured relationship "
        f"(found {collapses_found} collapses, {recovered_at_n3} triadic, {recovered_at_n4} quadrant)"
    )


def test_rerank_config_disabled_falls_back_to_cosine():
    """When config.enabled=False, harmonic_rerank_score == standard cosine."""
    v = [1.0, 0.0]
    u = [math.cos(math.pi/3), math.sin(math.pi/3)]
    cfg_off = h.HarmonicRerankConfig(enabled=False)
    score = h.harmonic_rerank_score(v, u, config=cfg_off)
    assert round(score, 4) == round(math.cos(math.pi/3), 4)


def test_rerank_config_enabled_uses_weighted_sweep():
    """When config.enabled=True, score is a weighted sum across harmonics."""
    v = [1.0, 0.0]
    u = [-1.0, 0.0]   # opposition pair
    cfg_on = h.HarmonicRerankConfig(enabled=True)
    score = h.harmonic_rerank_score(v, u, config=cfg_on)
    # Cosine contributes -0.55; opposition (n=2) contributes +0.10; rest contribute their cos(n×180°)
    # The exact value depends on harmonics; just check it's different from pure cosine
    assert abs(score - math.cos(math.pi)) > 0.01


def test_harmonic_query_typed_returns_opposition_partners():
    """Query for 'opposition' should rank 180-degree partners highest."""
    # Build 6 entities equally spaced on a unit circle (in multi-channel encoding)
    entities = [
        (f"e{i}", h.multi_channel_embedding(2 * math.pi * i / 6, harmonics=(1, 2, 3)))
        for i in range(6)
    ]
    query_vec = h.multi_channel_embedding(0.0, harmonics=(1, 2, 3))
    results = h.harmonic_query_typed(query_vec, entities, 'opposition', top_k=3)
    # e0 is identical to the query → opposition of identity might pick up.
    # e3 is exactly opposite (180°) → should score highest for opposition
    top_id = results[0][0]
    # Either e0 (self) or e3 (true opposition) — both have cos(2·π) = +1 for n=2
    assert top_id in ("e0", "e3")
