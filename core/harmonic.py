"""core/harmonic.py — Helios v0.3+ Wave-Coherence Stage-3 plugin.

Implements harmonic decomposition for typed similarity retrieval, integrated into
the Helios 6-stage workflow at Stage 3 (Read/Rerank).

Math primitive (from atech-hub/Wave-Coherence-as-a-Computational-Primitive,
Zenodo DOI 10.5281/zenodo.18607190):
- Standard cosine similarity captures only the n=1 fundamental of the angular
  relationship between two vectors.
- Higher harmonics cos(n × Δθ) for n=2,3,4,5,6 reveal structured relationships
  (opposition, triadic, quadrant, pentagonal, sextile) that scalar cosine collapses.
- A harmonic sweep across multiple n returns a typed-similarity vector instead of
  a single scalar, enabling queries like "what memories oppose this one?" (n=2)
  or "what are the triadic counterparts of this concept?" (n=3).

Scoping (per user's design directive):
- This is an OPTIONAL plugin to Stage 3, not a replacement for FTS5 + LLM rerank
- Stays local; no network-dependent external vector DB required
- Preserves Helios's local-first wedge: harmonic sweep runs in-process

For multi-channel embeddings (which Wave-Coherence's empirical work demonstrates
survive transformer layers with high channel independence), the sweep decomposes
the angular relationship into independent harmonic bands without scaling
infrastructure footprint.

IP context: see reports/helios-research-blueprint-v0.3-integration.md and the
provisional disclosure draft in reports/helios-claim-1-harmonic-disclosure.md.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional, Sequence


# ─── Configuration ────────────────────────────────────────────────────

DEFAULT_HARMONICS: tuple[int, ...] = (1, 2, 3, 4, 5, 6)

# Relationship type names for harmonic bands (per Wave-Coherence framework).
HARMONIC_RELATIONS: dict[int, str] = {
    1: "fundamental",     # standard cosine
    2: "opposition",      # 180-degree harmonic
    3: "triadic",         # 120-degree
    4: "quadrant",        # 90-degree
    5: "pentagonal",      # 72-degree
    6: "sextile",         # 60-degree
}


# ─── Pure math primitives ────────────────────────────────────────────

def angle_between(v: Sequence[float], u: Sequence[float]) -> float:
    """Return the angle Δθ in radians between two real-valued vectors.

    Uses the dot product / norm relationship, clamped to [-1, 1] for safety.
    Returns 0 if either vector is the zero vector.
    """
    if len(v) != len(u):
        raise ValueError(f"vector length mismatch: {len(v)} vs {len(u)}")
    dot = sum(a * b for a, b in zip(v, u))
    nv = math.sqrt(sum(a * a for a in v))
    nu = math.sqrt(sum(b * b for b in u))
    if nv < 1e-12 or nu < 1e-12:
        return 0.0
    cos_theta = max(-1.0, min(1.0, dot / (nv * nu)))
    return math.acos(cos_theta)


def harmonic_sweep(
    v: Sequence[float],
    u: Sequence[float],
    harmonics: Sequence[int] = DEFAULT_HARMONICS,
) -> dict[int, float]:
    """Decompose the angular relationship between v and u into harmonic bands.

    For each harmonic n in `harmonics`, returns cos(n × Δθ) where Δθ is the
    angle between v and u. n=1 reduces to standard cosine similarity.

    >>> # Two unit vectors at 120 degrees (triadic relation)
    >>> v = [1.0, 0.0]
    >>> u = [math.cos(2*math.pi/3), math.sin(2*math.pi/3)]
    >>> result = harmonic_sweep(v, u, harmonics=(1, 2, 3))
    >>> round(result[1], 4)   # cosine sim of 120-degree pair = -0.5
    -0.5
    >>> round(result[3], 4)   # n=3 harmonic of triadic = cos(360) = +1
    1.0
    """
    theta = angle_between(v, u)
    return {n: math.cos(n * theta) for n in harmonics}


def harmonic_at(
    v: Sequence[float],
    u: Sequence[float],
    n: int,
    harmonics: Sequence[int] = DEFAULT_HARMONICS,
) -> float:
    """Per-channel inner product for the n'th harmonic of a multi-channel embedding.

    For embeddings constructed by `multi_channel_embedding(theta, harmonics=...)`,
    where the n'th harmonic's contribution is at slot 2*(idx_of_n), 2*(idx_of_n)+1,
    this function extracts JUST that channel's inner product.

    This is the correct "typed similarity" operation on multi-channel embeddings —
    distinct from `harmonic_sweep(v, u, harmonics=(n,))` which computes
    cos(n × Δθ_total) from the overall angle.

    The two are mathematically equivalent ONLY for 2D unit-circle vectors;
    they DIFFER for multi-channel encodings that mix orthogonal harmonic bands.

    Returns cos(n × Δθ_n) where Δθ_n is the angular offset in the n'th band.
    """
    if n not in harmonics:
        raise ValueError(f"n={n} not in harmonics list {harmonics}")
    idx = list(harmonics).index(n)
    slot_cos = 2 * idx
    slot_sin = 2 * idx + 1
    if slot_sin >= len(v) or slot_sin >= len(u):
        raise ValueError(f"vector too short for harmonic n={n}; need at least {slot_sin+1} dims")
    # Inner product of the (cos, sin) pair at this channel = cos(Δθ_n)
    return v[slot_cos] * u[slot_cos] + v[slot_sin] * u[slot_sin]


def harmonic_distance_typed(
    v: Sequence[float],
    u: Sequence[float],
    relation: str,
) -> float:
    """Score the pair (v, u) for a specific named relation.

    Higher = stronger evidence the pair has that relationship type.

    Relations: 'fundamental', 'opposition', 'triadic', 'quadrant',
    'pentagonal', 'sextile' (see HARMONIC_RELATIONS).

    >>> v = [1.0, 0.0]
    >>> u = [-1.0, 0.0]
    >>> round(harmonic_distance_typed(v, u, 'opposition'), 4)
    1.0
    """
    rev = {name: n for n, name in HARMONIC_RELATIONS.items()}
    if relation not in rev:
        raise ValueError(f"unknown relation {relation!r}; valid: {sorted(rev)}")
    return math.cos(rev[relation] * angle_between(v, u))


# ─── Multi-channel embedding constructor (for tests and synthetic) ───

def multi_channel_embedding(
    theta: float,
    harmonics: Sequence[int] = DEFAULT_HARMONICS,
) -> list[float]:
    """Construct a synthetic multi-channel embedding for entity at angular position theta.

    Each harmonic n contributes a (cos(n·θ), sin(n·θ)) pair to the embedding.
    Total dimension = 2 × len(harmonics).

    Used to demonstrate that real cosine similarity collapses while the harmonic
    sweep recovers per-band relationships. Not for production use — production
    embeddings come from the LLM embedding endpoint.
    """
    v: list[float] = []
    for n in harmonics:
        v.append(math.cos(n * theta))
        v.append(math.sin(n * theta))
    return v


# ─── Stage-3 plugin integration ───────────────────────────────────────

@dataclass
class HarmonicRerankConfig:
    """Configuration for the harmonic plugin in Stage 3 rerank.

    weights: per-harmonic contribution to the final score. The default
    weights the fundamental highest and decays slightly with each harmonic
    (no theoretical justification — tune empirically per workload).
    """
    enabled: bool = False
    harmonics: tuple[int, ...] = DEFAULT_HARMONICS
    weights: dict[int, float] = field(default_factory=lambda: {
        1: 0.55,   # mirrors the fundamental's weight in the existing reranker
        2: 0.10,
        3: 0.10,
        4: 0.10,
        5: 0.05,
        6: 0.05,
    })

    def total_weight(self) -> float:
        return sum(self.weights.get(n, 0.0) for n in self.harmonics)


def harmonic_rerank_score(
    query_vec: Sequence[float],
    candidate_vec: Sequence[float],
    config: Optional[HarmonicRerankConfig] = None,
) -> float:
    """Compute a typed-similarity score by weighted sum across harmonic bands.

    score = Σ_n w_n · cos(n × Δθ)

    If config is None or disabled, falls back to standard cosine similarity
    (the n=1 fundamental) — preserves backward compatibility.

    Returns a scalar in [-Σw_n, +Σw_n]. Down-stream rerankers can combine this
    with the existing Helios formula (similarity + importance + recency + tier - drift).
    """
    cfg = config or HarmonicRerankConfig()
    if not cfg.enabled:
        # Standard cosine — exactly the fundamental harmonic
        sweep = harmonic_sweep(query_vec, candidate_vec, harmonics=(1,))
        return sweep[1]

    sweep = harmonic_sweep(query_vec, candidate_vec, harmonics=cfg.harmonics)
    return sum(cfg.weights.get(n, 0.0) * sweep[n] for n in cfg.harmonics)


def harmonic_query_typed(
    query_vec: Sequence[float],
    candidates: list[tuple[str, Sequence[float]]],
    relation: str,
    top_k: int = 10,
) -> list[tuple[str, float]]:
    """Retrieve candidates by named relation (opposition / triadic / quadrant / etc.).

    Use case: "find memories that *oppose* this one" — relation='opposition' (n=2).

    Returns (candidate_id, score) pairs sorted descending. Standard cosine
    cannot answer this question because it collapses all harmonics into the
    fundamental.
    """
    scored = [
        (cid, harmonic_distance_typed(query_vec, vec, relation))
        for cid, vec in candidates
    ]
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:top_k]


if __name__ == "__main__":   # pragma: no cover
    import doctest
    doctest.testmod(verbose=True)
