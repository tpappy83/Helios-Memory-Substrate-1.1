# Helios v0.3+ — Backports Falsifiability Appendix

**Status:** Splice-in deliverable for the NeurIPS workshop paper (likely §5 Experiments / Pilot Design) and for `helios-memory` engineering planning.

**Framing per user instruction:** the five wedge-preserving math backports from the research blueprint are **claimed, falsifiable, and pilot-proposed** — not empirically verified. Each is a design proposal grounded in cited theory + simulation, with a concrete pilot that could disconfirm it. Treat this appendix as the honest weight-bearing structure for the paper's pilot section and for any investor-facing claim.

---

## Format

For each backport:

1. **Claim** — what the change is alleged to accomplish.
2. **Theoretical warrant** — the derivation, citation, or simulation result that supports the claim.
3. **Falsifiability condition** — the specific empirical observation that would falsify the claim. If we cannot articulate a falsifier, the claim is not science.
4. **Proposed pilot** — the smallest experiment that exercises the falsifier.
5. **Success / failure criteria** — pre-registered numerical thresholds.
6. **Timeline & cost** — ballpark, honest.
7. **What we will say if the pilot disconfirms** — pre-committed response to a negative result. (This is the most important section and the one most often skipped.)

---

## Backport 1 — Schmitt-Trigger Hysteresis on Temperature Thresholds

### Claim
Replacing the current symmetric thresholds `(0.65 promote, 0.35 demote)` with hysteretic thresholds `(0.70 promote, 0.30 demote, stay-in-tier between)` reduces spurious tier transitions by ≥ 50% on bursty access workloads without sacrificing legitimate transition recall.

### Theoretical warrant
- Caliper §4a [FORMAL-PROOF]: with α=0.30 EMA and alternating-sign score sequence of amplitude $A$, the steady-state orbit half-swing is $A \cdot (1-\alpha)/(2-\alpha) = 0.412A$. Schmitt deadband of width $0.40$ around the midpoint suppresses all orbits with $A < 0.486$.
- Numerical simulation [NUMERICAL-VERIFIED]: 100 random orderings of 20-read bursts (12 high + 8 low) yielded baseline EMA 3.14 spurious promotes/run, Schmitt 2.17 — a 31% reduction at the **single** improvement axis. Larger reductions expected on more bursty real workloads (≥ 50% target).
- Foundational citation: Roberts (1959) EWMA control-chart literature; Lucas & Saccucci (1990, Technometrics) on EWMA design parameters.

### Falsifiability condition
On replayed production retrieval traffic (1 week, all classes), Schmitt produces **fewer than 30% reduction** in tier-transition rate AND/OR Schmitt's tier-transition decisions correlate at < 0.85 Spearman ρ with a held-out gold-label "true tier" derived from 30-day forward access frequency.

### Proposed pilot
- **Setup**: replay 1 week of production `query_memories()` calls through three estimators in parallel — (a) baseline EMA α=0.30, (b) Schmitt (0.70/0.30), (c) Schmitt + variance-adaptive α as secondary.
- **Data**: ≥ 10,000 retrieval events across ≥ 100 distinct records.
- **Gold label**: each record's "true tier" derived from forward access pattern over the next 30 days (records accessed ≥ 5× in 30 days post-event = hot; < 5× = cold).
- **Metric 1 (primary)**: tier-transition rate per record per day for each estimator.
- **Metric 2 (primary)**: false-transition rate = `|estimator transitions - gold transitions| / total events`.
- **Metric 3 (guardrail)**: legitimate-transition recall — fraction of gold transitions that the estimator also produced (within ±1 day).

### Success / failure criteria (pre-registered)
- **PASS**: Schmitt false-transition rate ≤ 50% of baseline AND legitimate-transition recall ≥ 90% of baseline.
- **PARTIAL PASS**: Schmitt false-transition rate 50–80% of baseline AND recall ≥ 90%.
- **FAIL**: Schmitt false-transition rate > 80% of baseline OR recall < 90%.

### Timeline & cost
- Sandbox replay harness: 1 day engineering.
- Pilot run on a single production replay log (if available; otherwise synthetic 1-week workload): 2 hours compute.
- Total: ~2 days.

### What we will say if disconfirmed
- "Schmitt hysteresis on temperature thresholds did not produce the predicted reduction in spurious transitions on real production traffic. The orbit-amplitude assumption from Caliper §4a — namely that real workloads exhibit alternating-sign score sequences with the amplitude regime where Schmitt dominates — does not hold. Real workloads are blocky rather than oscillatory, and hysteresis is less helpful than median pre-filtering. We pivot to variance-adaptive α as the primary stabilization mechanism."

---

## Backport 2 — Class-Weighted Drift Multiplier

### Claim
A class-weighted drift multiplier with weights `{decision: 0.0, event: 0.2, state: 0.5, summary: 0.8, observation: 1.0}` preserves decision-class recall under arbitrary access patterns and bounds observation-class drift influence.

### Theoretical warrant
- Sediment §2.2 [FORMAL-PROOF]: with `w_τ = 0` for decision class, `d_eff(c, r, decision) = 0` for any access pattern `(c, r) ∈ ℕ²`. The reranker penalty `-0.05·d_eff` is identically zero on decisions.
- Sediment §4 [NUMERICAL-VERIFIED]: on a 5-record sim across all classes with 1000 reads + 5 compression cycles, the class-weighted variant produces decision drift = 0 (penalty 0), observation drift = 1.07 (penalty -0.054) — preserved relative ordering as predicted.
- Class weights themselves are a **product decision** flagged as [HEURISTIC] — they encode the assumption "decisions matter most, observations matter least." A different product framing would require different weights.

### Falsifiability condition
On a replay of production retrieval logs filtered to "user reached for an important past decision" queries (heuristic: queries containing "I decided", "we chose", "the decision was", or labeled by an annotator as decision-recall queries), class-weighted drift produces **lower than baseline** recall@5 on decision-class records. OR: observation-class user-perceived freshness degrades by > 10% (measured via thumbs-up/down on observation-class results).

### Proposed pilot
- **Setup**: A/B/C deploy on 5% of production traffic for 2 weeks: (a) baseline drift, (b) class-weighted drift, (c) class-weighted + background neutralization.
- **Decision-recall queries**: filter via the heuristic above; expect ~5% of queries.
- **Metric 1 (primary)**: recall@5 on decision-class records for decision-recall queries.
- **Metric 2 (guardrail)**: recall@5 on observation-class records for general queries — must not regress by > 10%.
- **Metric 3 (operational)**: tier distribution stability — observation class should not accumulate runaway drift.

### Success / failure criteria
- **PASS**: decision recall@5 ↑ by ≥ 5pp AND observation recall@5 within ±5pp of baseline.
- **PARTIAL PASS**: decision recall@5 ↑ by 2–5pp AND no guardrail violation.
- **FAIL**: decision recall@5 unchanged OR observation regresses by > 10%.

### Timeline & cost
- Engineering: 1 day (weights are constants in `core/tiering.py`).
- A/B/C deploy: 2 weeks.
- Total: ~2 weeks + 1 day eng.

### What we will say if disconfirmed
- "The class-weighted multiplier did not produce the expected decision-recall improvement, or did so at unacceptable cost to observation freshness. The product assumption that 'decisions > events > state > summary > observation' may not match user behavior — perhaps users care more about recent observations than old decisions. We pivot to a single user-tunable `decision_boost` parameter rather than a fixed class hierarchy."

---

## Backport 3 — Power-Law Recency Decay

### Claim
Replacing exponential decay `r = exp(-Δt/τ)` with power-law `r = (Δt/τ + 1)^(-γ)` at `γ = 1.5` improves recall on retrospective queries ("what did I say about X last week?") by ≥ 3 percentage points without regressing recency-emphasis queries.

### Theoretical warrant
- Tau §2 [VERIFIED-COGSCI]: Wickelgren (1972) shows human memory follows power-law decay; Wixted & Ebbesen (1997) replicate at individual-subject level; Anderson & Schooler (1991) show environmental access patterns are power-law. Evidence ratio (Stevens et al. 2016) ≈ 10^10 in favor of power vs exponential on real-world data.
- Tau §1 [FORMAL-PROOF]: exponential half-life at τ=600 is 416 seconds; power-law (γ=1.5) half-life is 3·τ ≈ 1800 seconds. Power-law preserves weight on items 30 minutes – 2 hours old, where exponential has crushed them.
- Tau §6 [BRUTAL FLAG]: at γ ≤ 1, the integral $\int_0^\infty r\,dt$ diverges, meaning recency scores for distant memories don't shrink fast enough relative to nearby ones. **Must use γ ≥ 1.5 OR apply in-pool normalization.**

### Falsifiability condition
On a held-out set of retrospective queries (queries containing "earlier", "last week", "previously", "yesterday", or annotator-labeled retrospective), power-law @ γ=1.5 produces **lower** recall@5 than exponential @ τ=600. OR: recency-emphasis queries (containing "just now", "today", "most recent") regress in recall@5 by > 3 percentage points.

### Proposed pilot
- **Setup**: A/B test on 10% of production traffic for 2 weeks. Arm A: exponential @ τ=600 (control). Arm B: power-law @ γ=1.5 with adaptive τ from Backport 4.
- **Query stratification**: retrospective vs recency-emphasis vs neutral; stratify analysis.
- **Metric 1 (primary)**: recall@5 on retrospective queries.
- **Metric 2 (guardrail)**: recall@5 on recency-emphasis queries — must not regress by > 3pp.
- **Metric 3 (operational)**: distribution of recency feature values across candidate pools — should NOT be near-uniform (would indicate γ too low).

### Success / failure criteria
- **PASS**: retrospective recall@5 ↑ ≥ 3pp AND recency-emphasis recall@5 within ±3pp.
- **PARTIAL PASS**: retrospective recall@5 ↑ 1–3pp.
- **FAIL**: retrospective recall@5 unchanged OR recency-emphasis regresses > 3pp OR recency-feature distribution degenerate.

### Timeline & cost
- Engineering: 1 day (function swap + γ as constant).
- A/B run: 2 weeks.
- Total: ~2 weeks.

### What we will say if disconfirmed
- "Power-law decay did not produce the expected improvement on retrospective queries on this user's workload. The cognitive-science fit (Wickelgren 1972 et al.) may not transfer to LLM-mediated memory retrieval, possibly because the LLM reranker already captures temporal relevance through other features. We retain exponential decay as default but expose γ as a tunable parameter for users with strongly retrospective workloads."

---

## Backport 4 — Adaptive τ via median(IAT)

### Claim
Setting `τ_n = β · median(IAT_{n-k+1..n})` with `β = 10, k = 5` auto-tunes recency timescale to the user's session frequency, reducing the need for hand-tuned τ defaults and improving recall on users with non-default session cadence (very fast or very slow IATs).

### Theoretical warrant
- Tau §3 [FORMAL-PROOF]: median is the robust order statistic; rejects up to ⌊k/2⌋ IAT outliers. With β = 10, recency at one-IAT-old content is `r ≈ 0.905` for exponential, providing strong but not overwhelming weight on the immediately prior message.
- Tau §4.1 [NUMERICAL-VERIFIED]: simulated IAT sequence `[30, 25, 35, 28, 32, 600, 28, 30, 31]` — arithmetic mean would jump to ~137 at the spike; median holds firm at 32. Robust to bursty IATs.
- Tau §4.3 [HEURISTIC, FLAGGED]: cold-start trajectory has the first `k` turns operating on default τ = 600s. For typical 6–12-turn sessions, that's 40–80% of the session at the unjustified default. Linear warm-up blend mitigates but does not eliminate.

### Falsifiability condition
For users whose session IAT distribution has median significantly different from the implicit default (say, |median(IAT) - 60s| > 30s), adaptive τ produces **no improvement** in recall@5 versus the fixed-τ baseline. OR: cold-start performance (first 5 turns of each session) regresses by > 5pp.

### Proposed pilot
- **Setup**: A/B test on 10% of production traffic for 2 weeks.
- **User stratification**: bucket users by their long-run median IAT — fast (< 30s), normal (30–120s), slow (> 120s). Analyze each bucket separately.
- **Metric 1 (primary)**: recall@5 by IAT bucket.
- **Metric 2 (guardrail)**: first-5-turn recall (cold-start) — must not regress by > 5pp in any bucket.
- **Metric 3 (operational)**: distribution of computed `τ_n` values — should span the bucketed IAT regime; if all users converge to τ ≈ τ_default, the adaptive mechanism is not actually adapting.

### Success / failure criteria
- **PASS**: recall@5 improves ≥ 2pp in BOTH fast and slow buckets, no regression in normal bucket, cold-start within ±5pp.
- **PARTIAL PASS**: improvement in fast OR slow bucket only.
- **FAIL**: no recall improvement in any bucket OR cold-start regresses > 5pp.

### Timeline & cost
- Engineering: 2 days (IAT tracking + median computation + warm-up logic + cold-start handler).
- A/B run: 2 weeks.
- Total: ~2 weeks + 2 days eng.

### What we will say if disconfirmed
- "Adaptive τ did not produce the expected per-user-bucket improvement, indicating that either (a) the IAT signal is too noisy to drive τ updates at the per-record granularity needed, or (b) the LLM reranker's other features (similarity, importance) dominate recency such that τ-tuning is in the noise floor. We retain fixed τ = 600s as default but expose τ as a per-tenant configuration override."

---

## Backport 5 — Bounded Drift Correction

### Claim
Replacing linear drift `-w_drift · drift` with bounded smooth correction `-w_drift · (1 - exp(-drift/d_0))` at `d_0 = 1.0` prevents reranker saturation pathology in long-running deployments where drift can grow unbounded.

### Theoretical warrant
- Sediment §1 [FORMAL-PROOF]: under 1000 reads (c=0), drift = 1.02, linear penalty = -0.051. Inter-result score gaps in production rerankers are 0.01–0.05; a -0.051 bias can flip rankings.
- Lagrange §5 [FORMAL-PROOF]: bounded correction has `|∂score/∂drift| ≤ w_drift/d_0`, so drift influence is uniformly bounded. Linear correction has unbounded gradient.
- Lagrange §5.3 [FORMAL-PROOF]: the modified Lagrangian remains valid under KKT, and the gradient saturation at high drift prevents the multiplier from blowing up.

### Falsifiability condition
On records with drift > 2.0 (heavy access regime), bounded correction produces **the same** ranking as linear correction — i.e., the bound never activates. This would indicate the saturation pathology is hypothetical, not real. OR: bounded correction degrades ranking quality on low-drift records (drift < 0.5) where the two formulas should agree.

### Proposed pilot
- **Setup**: A/B on 5% of production traffic. Arm A: linear drift. Arm B: bounded drift.
- **Stratification**: records by drift level — low (< 0.5), medium (0.5–1.5), high (> 1.5).
- **Metric 1 (primary)**: rank correlation (Spearman ρ) between arms within each stratum. Low and medium strata should produce ρ ≈ 1.0; high stratum should diverge.
- **Metric 2 (operational)**: fraction of records in high-drift stratum. If this is < 1%, the pathology is rare and the fix is over-engineering.
- **Metric 3 (guardrail)**: user-perceived rank quality (CTR on top-3 results) — must not regress in any stratum.

### Success / failure criteria
- **PASS**: high-drift stratum exists (> 1% of records), bounded variant maintains rank quality where linear does not (Spearman ρ_bounded > ρ_linear with statistical significance).
- **PARTIAL PASS**: high-drift stratum exists but bounded variant is statistically indistinguishable from linear.
- **FAIL**: high-drift stratum < 1% of records (pathology not real) OR bounded variant regresses on any stratum.

### Timeline & cost
- Engineering: 1 day.
- A/B run: 2 weeks.
- Total: ~2 weeks.

### What we will say if disconfirmed
- "The bounded drift correction did not improve ranking on real production traffic, indicating either (a) drift never grows large enough to saturate the linear formula in actual use, or (b) the saturation pathology is real but Helios deployments don't run long enough to hit it. We retain linear drift as default but expose the correction as a configuration flag for long-running deployments (multi-year continuous usage)."

---

## Aggregate Pilot Design

Run all five A/B tests **in parallel** on disjoint 5–10% traffic slices over the same 2-week window. Total traffic budget: 30–50% of production for 2 weeks. Statistical power: with baseline recall@5 ≈ 0.65 and minimum detectable effect of 3pp, each arm needs ~4,500 events; with production traffic at >1k events/day across 100+ tenants, the budget is comfortable.

**Pre-registration:** before deploy, commit the following file to the `helios-memory` repo as `experiments/2026-v0.3-backports-preregistration.md`:

1. The five claims and falsifiers above, copied verbatim.
2. The pre-registered success/failure thresholds, copied verbatim.
3. The analysis plan: which metrics, which stratifications, which statistical tests.
4. The pre-committed responses to negative results.

**Rationale:** pre-registration is the difference between empirical science and post-hoc rationalization. Without it, the 5 backports remain "claimed and pilot-proposed" indefinitely. With it, they become "tested and either verified or refuted." The paper's §5 Experiments section should reproduce the pre-registration verbatim.

---

## Honest Gaps in This Appendix

1. **No real production traffic is available to Helios at the time of this writing.** The pilots above presuppose deployed users; if Helios remains pre-launch through 2026, these pilots will need synthetic-workload proxies. The Helix subagent's Track A pilot (FTS5+LLM-rerank quality probe on LongMemEval/LoCoMo) is the closest currently-available analogue.
2. **The class-weighted drift weights are a product decision, not a derived result.** If product framing changes — e.g., "events matter as much as decisions" — the weights must change and the pilot results don't transfer.
3. **The CMA preprint (arXiv:2601.09913) is unverified at peer review.** If CMA gets rejected, the framing of these pilots as "instantiating the CMA class with specific commitments" weakens.
4. **Multi-arm A/B testing on a small user base risks underpowered comparisons.** If Helios has < 100 users at pilot time, switch from per-event statistical comparison to per-user paired analysis (each user is their own control across arms over different days).
5. **All five backports together change the reranker's behavior simultaneously.** A 4th arm with all five enabled tests the joint effect; analyzing per-backport contribution requires factorial design or sequential dose-response runs, both of which exceed the proposed timeline.
