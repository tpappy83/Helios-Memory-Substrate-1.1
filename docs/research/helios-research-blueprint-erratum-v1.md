# Helios Research Blueprint — Erratum v1

**Date:** 2026-05-17
**Status:** Active correction to `reports/helios-research-blueprint.md` and the published webpage.
**Source of the corrections:** user audit (tpapenb@iu.edu) flagged two mathematical errors during the IP-claimability research pass. Both errors are confirmed via independent derivation below.

---

## Erratum 1 — Caliper §3.1 EMA Half-Swing Coefficient (INVALID DERIVATION)

### What the blueprint claimed

Quoting `reports/helios-research-blueprint.md` §3.1 verbatim:

> At α=0.30, half-swing = 0.4118·A. **Spurious thrash condition around μ=0.5**: any amplitude `A > 0.364` crosses both thresholds every cycle.

The cited formula was `(1-α)/(2-α)` with α=0.30 evaluating to 0.4118.

### Why it's wrong

The recurrence is `t_n = α·s_n + (1-α)·t_{n-1}` under alternating input `s_n ∈ {μ+A, μ-A, μ+A, μ-A, ...}`. Let `t_high` denote the steady-state value AFTER processing a high sample, `t_low` AFTER a low sample.

```
t_high = α·(μ+A) + (1-α)·t_low
t_low  = α·(μ-A) + (1-α)·t_high
```

Substituting:

```
t_high = α·(μ+A) + (1-α)·[α·(μ-A) + (1-α)·t_high]
       = α·(μ+A) + α·(1-α)·(μ-A) + (1-α)²·t_high
```

Solve for `t_high`:

```
t_high · [1 - (1-α)²] = α·(μ+A) + α·(1-α)·(μ-A)
                      = α·μ·[1 + (1-α)] + α·A·[1 - (1-α)]
                      = α·μ·(2-α) + α²·A
```

Using `1 - (1-α)² = α·(2-α)`:

```
t_high · α·(2-α) = α·μ·(2-α) + α²·A
t_high = μ + α·A/(2-α)
```

**Correct half-swing coefficient: `α/(2-α)`**, not `(1-α)/(2-α)`.

| α | Blueprint (WRONG): (1-α)/(2-α) | Correct: α/(2-α) |
|---|---|---|
| 0.10 | 0.474 | 0.0526 |
| **0.30** | **0.412 (wrong)** | **0.1765 (correct)** |
| 0.50 | 0.333 | 0.333 |
| 0.70 | 0.176 | 0.412 |

### Numerical verification

At α=0.30 with maximum theoretical alternating amplitude A=0.5 (signal swings between 0.0 and 1.0):

- **Correct half-swing** = 0.5 × 0.1765 = **±0.0882 around μ=0.5**
- Steady-state orbit: [0.4118, 0.5882]
- Does this cross baseline thresholds (0.65, 0.35)? **NO** — orbit is bounded entirely within [0.4118, 0.5882].
- Does it cross Schmitt deadband (0.70, 0.30)? **NO** — even further from threshold.

**Pure alternation cannot trigger tier thrash at α=0.30.** The blueprint's analytical proof that "amplitude A > 0.364 crosses both thresholds every cycle" is invalid.

### What thrash IS observed in the simulation

The 100-trial burst simulation in Caliper §4 (3.14 spurious promotes per run) is real, but the mechanism is NOT alternating orbits — it's **consecutive same-sign clustering**. When the burst happens to feed 4-5 high scores in a row before any low scores, the EMA climbs above 0.65 (promote) and then a subsequent cluster of low scores drops it below 0.35 (demote). This is a *runs-of-same-sign* phenomenon, not an alternating-orbit phenomenon.

### What survives and what doesn't

| Claim in §3.1 | Status |
|---|---|
| EMA at α=0.30 has half-life ≈ 1.94 reads, effective memory ≈ 2.33 reads | ✅ CORRECT — unaffected |
| Pure alternation at A > 0.364 thrashes | ❌ INVALID — derivation error confirmed |
| 100-trial burst sim: 3.14 spurious promotes/run | ✅ CORRECT — but mechanism is clustering, not alternation |
| Schmitt hysteresis (0.70/0.30) suppresses thrash | ✅ CORRECT — but for different mathematical reason than stated (handles clusters/regime-shifts, not orbits) |
| "Schmitt suppresses all orbits with A < 0.486" | ❌ INVALID derivation — but Schmitt does still help via cluster-rejection |
| Backport recommendation: apply Schmitt hysteresis | ✅ STILL VALID as a stabilization technique, justified by cluster-handling, not orbit-suppression |

### Impact on the rest of the blueprint

- The §3.1 "spurious thrash condition" claim and the "Schmitt suppresses orbits with A < 0.486" claim are wrong.
- The §8 roadmap recommendation to backport Schmitt remains valid because the simulation observation (false transitions during bursts) is real, just caused by a different mechanism.
- The falsifiability appendix Backport #1 (Schmitt hysteresis) needs its theoretical-warrant section rewritten to point to cluster-rejection theory (Roberts EWMA charts + cluster sensitivity literature) rather than alternating-orbit analysis.

### Corrected recommendation language

> "Schmitt hysteresis (promote 0.70, demote 0.30) is recommended not because it suppresses pure-alternation orbits (which at α=0.30 are bounded within [0.41, 0.59] regardless of input amplitude) but because real workloads exhibit *runs-of-same-sign clustering* where 4-5 consecutive high or low scores can push the EMA across baseline thresholds. The deadband between 0.30 and 0.70 absorbs short cluster events without triggering spurious tier transitions, allowing transitions only when the EMA crosses the wider deadband — which requires sustained signal change rather than transient clustering."

---

## Erratum 2 — Sediment §3.4 Order Preservation Theorem (FALSIFIED)

### What the blueprint claimed

Quoting `reports/helios-research-blueprint.md` §3.4 verbatim:

> **Order preservation theorem** [FORMAL-PROOF]: Strategy A preserves relative ordering across same-type records. The affine map `d ↦ (d - 0.02)/2 + 0.02` is order-preserving.

The accompanying pseudocode:
```python
record.cycles //= 2
record.reads //= 2
```

### Why it's wrong

The "proof" treats neutralization as if it were applied directly to the composite drift value `d`. But the implementation applies integer floor division SEPARATELY to the two counters `c` and `r`, then recomputes `d` from the floor-divided counters. **These are not the same operation.**

### User's counter-example (verified)

Drift formula: `d = 0.02 + 0.01·c + 0.001·r` (so composite is `10c + r` up to the 0.001 scale, or equivalently `c·10 + r` weighted-units).

Two same-type records:
- **Record A**: c=3, r=0 → effective `10c + r = 30`, drift = 0.02 + 0.03 + 0 = **0.050**
- **Record B**: c=2, r=9 → effective `10c + r = 29`, drift = 0.02 + 0.02 + 0.009 = **0.049**

Pre-neutralization: **A > B** in drift (correct).

After floor halving:
- **A'**: c=3//2=1, r=0//2=0 → effective = 10, drift = 0.02 + 0.01 + 0 = **0.030**
- **B'**: c=2//2=1, r=9//2=4 → effective = 14, drift = 0.02 + 0.01 + 0.004 = **0.034**

Post-neutralization: **A' < B'** in drift. **Order flipped.**

This violates the theorem as stated. The "proof" was sloppy.

### Why the proof failed

The blueprint's claimed affine map `d ↦ (d - 0.02)/2 + 0.02` would only apply if the implementation literally executed `d_new = (d_old - 0.02)/2 + 0.02`. Instead, the implementation floor-divides the underlying integer counters, which introduces **truncation that scales differently on c vs r** (c-coefficient is 10× the r-coefficient in the drift formula, so floor-dropping a c-unit costs 10× more in drift than floor-dropping an r-unit).

### Fix options

| Option | Description | Trade-off |
|---|---|---|
| **A. Float counters with multiplicative decay** | Convert c, r to floats; apply `c *= 0.5; r *= 0.5` | Preserves order; introduces non-integer counters (UI display annoyance, audit-trail change) |
| **B. Store derived drift column with float halving** | Add `drift_value REAL` column; apply `drift = (drift - 0.02) * 0.5 + 0.02` directly | Preserves order; adds a column; counters become advisory |
| **C. Timestamp-based decay** | Replace counter-based drift with `drift = f(age)` where age = `now - last_compression_timestamp` | Order-preserving; removes the counter system entirely; bigger refactor |
| **D. Class-weighted multiplier as multiplicative attenuator** | Replace floor division with multiplicative `c = round(c * 0.5)` keeping the existing recipe in §2 | Partial fix — round() instead of // — still produces flips at small counter values |

**Recommended:** Option B. Persisted drift column, multiplicative attenuation, preserves order rigorously, and matches the actual semantic intent of "background neutralization halves drift."

### What survives in §3.4

| Claim | Status |
|---|---|
| Class-weighted multiplier (decision: 0.0, ..., observation: 1.0) | ✅ CORRECT — decision-invariance proof holds independently |
| Decision invariance theorem | ✅ CORRECT — `w_τ = 0` ⟹ d_eff = 0 regardless of (c, r) |
| Background neutralization is desirable | ✅ CORRECT — but pseudocode needs Option B fix |
| **Order Preservation Theorem (as stated)** | ❌ **FALSIFIED** by user counter-example |
| Convergence proof (drift bounded under steady access rate) | ⚠️ PARTIALLY CORRECT — bound holds but the analysis was for the **wrong** halving operation |

### Impact on the synthetic helios-memory

I checked. The synthetic implementation in `core/tiering.py` (the `decay_inactive_records` function) does NOT use floor division on c/r. It uses `update_temperature_ema(temp, 0.0)` which is a *temperature*-based multiplicative attenuation — semantically correct and order-preserving in the temperature space.

**The synthetic code is safe.** The bug exists only in the research-blueprint pseudocode and the published webpage. If you adopt Option B above, the synthetic `decay_inactive_records` can be extended to also persist a separate `drift_value` column with multiplicative attenuation, but the current temperature-EMA approach already avoids the order-flipping pathology.

---

## Where the corrections need to land

1. **`reports/helios-research-blueprint.md`** (~5500 word document) — update §3.1 and §3.4 with corrected derivations. Will be re-saved.
2. **`reports/helios-backports-falsifiability-appendix.md`** — Backport #1 (Schmitt hysteresis) theoretical-warrant section needs updating to point to cluster-rejection rather than orbit-suppression. Backport #2 (class-weighted drift) appendix mentions Order Preservation — add note that pseudocode uses Option B going forward.
3. **Published webpage** (`[[ARTIFACT_2edsott3]]`) — re-publish with corrected text.
4. **`reports/helios-paper-section-2-revision.md`** — no changes needed; §2 is Related Work, not the math derivations.

## Honesty note

This is a real correction, not a cosmetic one. Both errors were introduced by the opus subagents (Caliper and Sediment) during the first dispatch. The user audit caught them. My synthesis pass should have caught them — I propagated subagent claims without re-deriving them. That's a process failure I'll surface in the IP-research synthesis as a meta-finding: when claims are mathematical, the synthesis pass needs to re-derive at least the key formulas, not just consolidate.

**Both math errors strengthen the case for Pulse's "this is technical disclosure, not legal opinion" framing in the IP work — derivations carry weight only when verified, and the Caliper/Sediment math is exactly the kind of thing a patent attorney would re-check against the implementation.**

## Subagent dispatch context

The 6 IP-research subagents dispatched in this same turn have been briefed on both math errors. This ensures Anchor/Lattice/Audit/Forge/Quill/Pulse don't propagate the false claims into their patentability analyses. Specifically:
- Audit must not list the Schmitt-suppresses-orbits derivation as a Helios invention worth claiming
- Audit may still list "class-weighted drift with decision invariance" as a candidate, but with the floor-division pseudocode replaced by Option B
- Pulse must include this erratum as a check on the synthesis pass's reliability
