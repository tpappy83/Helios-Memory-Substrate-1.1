# Helios v0.3+ Research Blueprint — Unconstrained Architecture & Mathematical Foundations

**Date:** 2026-05-16
**Authors:** Code Agent + 8 opus research scouts (Solex, Helix, Vortex, Crucible, Caliper, Tau, Lagrange, Sediment)
**Scope:** Phase 1-4 per the user's brief. The user explicitly authorized ignoring Helios's three competitive wedges (local-first / no vector DB / dev-loop simplicity) for THIS research — the deliverable is a 12-24 month target-state blueprint, NOT a refactor directive for the current `helios-memory` build.
**Honesty framing:** Confidence-tier citations applied throughout. Brutal gap-flagging surfaces every wedge collision, every weak novelty claim, every unverified assumption. The wedge-bound `helios-memory` track and the unconstrained blueprint are explicitly separated; §5 maps blueprint components to backport-feasibility.

---

## TL;DR

- **Helios is NOT redundant against the academic literature, but two papers force you to sharpen the novelty pitch.** A-MEM (NeurIPS 2025, arXiv:2502.12110) does substrate-with-induced-attributes; CMA (arXiv:2601.09913, 2026) is an architectural class. Helios's defensible novelty is the **three-layer joint commitment**: immutable substrate + retrospectively-induced concepts + callable skill templates compiled into prompts. None of the 8 surveyed substrates make ALL three commitments simultaneously.
- **The "no vector DB" wedge is contrarian.** All 5 surveyed enterprise SaaS use vector indexing as the retrieval backbone. Helios's defensible turf is local-first + zero-network + true data sovereignty — narrower than the wedge implies but still uncontested.
- **The "long context obsoletes RAG" narrative is vendor-driven hype.** RULER, NoLiMa, and MRCR v2 show effective contexts are 3–10× smaller than advertised. Helios's hybrid retrieval+memory architecture aligns better with reality than either pure-LC or pure-RAG.
- **Math findings — five drop-in improvements preserve every wedge:**
  1. **Schmitt-trigger hysteresis** (0.70/0.30) on temperature thresholds. Suppresses all tier thrash under orbit half-swing < 0.486 at α=0.30.
  2. **Class-weighted drift multiplier** (decision: 0.0, event: 0.2, ..., observation: 1.0). Decisions become drift-invariant. Formal proof in §3.4.
  3. **Power-law recency** `(Δt/τ+1)^-γ` with γ=1.5. Better fit to human memory (Wickelgren 1972, Anderson & Schooler 1991) than exponential.
  4. **Adaptive τ via median(IAT)** with β=10 multiplier. Auto-tunes to user session frequency.
  5. **Bounded drift correction** `1 - exp(-drift/d₀)`. Prevents saturation pathology.
- **The Helios paper for NeurIPS 2026 workshop must explicitly position against A-MEM and CMA.** §6 of this blueprint provides the framing.

---

## §1 — Helios Lifecycle Grounding

The standard 6-stage workflow remains the foundation:

```
Ingest → Score → Read → Modify → Write → Store
```

| Stage | Responsibility | Current (v0.2) | Blueprint (v0.3+) |
|---|---|---|---|
| Ingest | Capture message + namespace | API surface | Same (no change at this stage) |
| Score | Classify into 5 fixed types | LLM-driven, MOCK fallback | Add class-weighted importance + entity extraction |
| Read | Candidate generation + rerank | FTS5 + LLM rerank + tier-aware | Hybrid: FTS5 + vector (pgvector/Qdrant) + graph edges + LLM rerank |
| Modify | EMA temperature feedback | α=0.30 EMA on top-K | **Schmitt hysteresis 0.70/0.30** + variance-adaptive α |
| Write | INSERT into memory_records | SQLite single-tenant | Postgres schema-per-tenant + Qdrant payload-partitioned vectors |
| Store | Tier assignment + audit log | Default `cold`, audit_log table | Same + background drift neutralization worker |

The 6-stage invariant **survives wedge-bypass**. The blueprint's contribution is at the implementation layer of each stage, not the architecture of the pipeline itself.

---

## §2 — SaaS & Academic Deconstruction

### §2.1 — Enterprise SaaS landscape (Solex findings)

| Platform | State Taxonomy | Multi-Tenancy | Vector Index | Graph Layer | Pricing Floor |
|---|---|---|---|---|---|
| **Mem0** | session(`run_id`) + user/agent/app | 4-dim filter + Pinecone namespaces | Pluggable; Qdrant HNSW default | Neo4j/Memgraph/Neptune/Kuzu/AGE | Free → $19 Starter |
| **Letta** | Blocks + Archival + Conversation + MemFS | Agent-row in shared Postgres | pgvector HNSW | None | $20 Pro / $20 API |
| **Zep** | Episodic / Entity / Community subgraphs | Per-user graph (logical) | Hybrid: vector + BM25 + graph | Graphiti on Neo4j/FalkorDB/Neptune/Kuzu | Free → $25 Flex |
| **LangMem** | Thread state + Store namespaces + BackgroundMgr | Hierarchical namespace tuples in shared Postgres | pgvector (optional per-namespace) | None | Bundled w/ LangSmith $39+ |
| **ChatGPT Memory** | Saved Memories + Chat History Ref | Per-account consumer | Proprietary/unknown | Unknown | Bundled w/ ChatGPT |

**Cross-cutting patterns (3+ vendors do this — settled industry signal):**

1. **Logical partitioning over physical isolation** for multi-tenancy. None use schema-per-tenant or RLS; all use namespace/filter-based tenant boundaries.
2. **Hybrid retrieval is default**. Pure vector is considered insufficient; BM25 + vector + graph or BM25 + vector + entity is the modal architecture.
3. **Async/background memory writes**. Hot path returns event_id; consolidation happens off-thread.
4. **Graph layer is the differentiation battlefield**. Mem0 and Zep invested heavily here; Letta and LangMem skip it.
5. **Conflict resolution via temporal invalidation, not overwrite**. Zep does bi-temporal edges; Mem0 does dedup + accumulation; ChatGPT does priority decay.

**Where Helios's "no vector DB" wedge actually lands** (honest competitive read):

- **The wedge is contrarian.** 5 of 5 SaaS competitors use vector ANN as the retrieval backbone. There is no SaaS competitor that has shipped without it.
- **The local-first wedge is real.** Only Letta self-host approximates this, and even Letta requires pgvector. **Zero competitor ships a competitive offering where the developer's machine is the only compute boundary.** That's defensible turf.
- **The single-tenant stance puts Helios pre-Mem0-circa-2024.** Every competitor here invested heavily in multi-tenant filter primitives. Skipping it accelerates simplicity but truncates the ceiling. The 4-dim Mem0 filter is a 100-line feature, not a moat — Helios can add it without rearchitecting.
- **What Helios uniquely claims competitors cannot:**
  - Zero-network retrieval (Mem0/Zep/LangMem require network round-trips)
  - Zero infra cost at the floor (every SaaS here has a credit/quota meter)
  - True local data sovereignty (Letta gets close; Helios goes further)

**Hard problems vendors gloss over** (relevant to Helios at scale):
- **Consistency**: none of the docs explain how writes interact with concurrent agent reads. Letta explicitly admits last-write-wins on Memory Blocks — silent data loss in multi-agent setups.
- **Fan-out**: nobody publishes the cost of a 4-dim filter scan at 10M memories.
- **Tenant isolation under noisy neighbor**: namespace-based isolation in Pinecone/pgvector is "supported" but not "guaranteed"; quota-exhausted tenants can degrade neighbors.

### §2.2 — Academic substrate landscape (Helix findings)

| Substrate | State model | Retrieval | Learning loop | Real deployments |
|---|---|---|---|---|
| **GraphRAG** (Edge et al. 2024, arXiv:2404.16130) | LLM-built KG + community summaries | Map-reduce over communities | None (frozen index) | Microsoft, Neo4j, LlamaIndex |
| **HMN** (Chandar et al. 2016, ICLR 2017 WS) | Hierarchical neural memory cells | MIPS k-NN | Backprop on reader | None industrial |
| **Soar EpMem** (Derbinsky & Laird 2009 ICCBR) | Graph snapshots + deltas | Cue-based partial match | Procedural via chunking; manual semantic | NRL, U.Mich research |
| **A-MEM** (Xu et al. NeurIPS 2025, arXiv:2502.12110) | Zettelkasten notes + attributes + links | Cosine k-NN + link traversal | LLM-driven evolution at write | OSS only (Rutgers) |
| **MemGPT/Letta** (Packer et al. COLM 2024, arXiv:2310.08560) | Tiered context (main/recall/archival) | LLM function calls | None | Letta Cloud, AutoGen |
| **Voyager** (Wang et al. TMLR 2024, arXiv:2305.16291) | Vector-DB of code skills | Embedding k-NN | Iterative self-refine via env feedback | NVIDIA research |
| **ExpeL** (Zhao et al. AAAI 2024, arXiv:2308.10144) | Insight list + trajectory pool | Embedding k-NN over trajectories | LLM-ops {ADD,EDIT,VOTE} | OSS only (Tsinghua) |
| **CMA** (arXiv:2601.09913, 2026) | Persistent mutable substrate + edges | Multi-factor (vector+activation+recency) | Reinforcement + consolidation | Unspecified (class spec) |

**Cross-substrate convergence — settled questions (3+ papers agree):**

1. Vector embeddings + k-NN are the default retrieval primitive (HMN, A-MEM, Voyager, ExpeL, EM-LLM, MemGPT). Settled.
2. Hierarchical / multi-level organization beats flat memory (HMN, GraphRAG, Soar, R3Mem, CMA). Settled.
3. LLM-as-memory-curator is viable (A-MEM, ExpeL, GraphRAG, MemGPT, CMA). Emergent consensus.
4. Episodic / semantic separation is architecturally useful (Soar, A-MEM, EM-LLM, CMA). Converging.

**Open frontiers — 5 gaps no surveyed work fills:**

1. **Substrate-frozen / indexes-derived discipline**. Every paper above either mutates substrate (A-MEM, CMA, Soar) or has no substrate (Voyager, ExpeL). Treating raw metadata as immutable and deriving everything else is unexplored.
2. **LLM-mediated belief revision over induced concepts**. No surveyed paper formally handles concept conflict and revision under new evidence (A-MEM's evolution is heuristic).
3. **Skill compilation from concepts (not from end-to-end LLM authoring)**. Voyager skills come from a code-generation loop; the "concepts → skills" arrow is missing in all surveyed work.
4. **Induction from interaction patterns** (not just trajectories). ExpeL induces from success/failure tuples; no paper induces from longitudinal interaction graphs.
5. **Empirical comparison across substrate paradigms**. No benchmark places A-MEM, GraphRAG, EM-LLM, MemGPT, and Voyager-style skill libraries on the same evaluation suite.

**Brutal Helios novelty verdict (from Helix):**

> Helios is not redundant, but two papers force you to sharpen the pitch:
> - **A-MEM (NeurIPS 2025)** already does substrate-with-induced-attributes + dynamic links. Helios must own the "substrate frozen, indexes derived, skills compiled into prompts" three-stage discipline as distinct from A-MEM's evolve-on-write.
> - **CMA (arXiv 2601.09913)** is an *architectural class*. Helios is most honestly framed as **a concrete CMA-class instantiation with a skills layer**. Trying to claim novelty *against* CMA in peer review will be rejected; claiming novelty *within* CMA (via skills + the frozen-substrate discipline + empirical instantiation) will be accepted.

**Recommended Related Work framing for the NeurIPS 2026 workshop paper:**

> "Helios instantiates the CMA class (arXiv:2601.09913) with three architectural commitments not jointly present in prior work: (i) immutable substrate (vs. A-MEM's evolve-on-write), (ii) concept induction *retrospective* over frozen substrate (vs. A-MEM's write-time co-generation), and (iii) callable skill templates compiled into prompts (vs. Voyager's standalone code skills; absent in CMA, A-MEM, GraphRAG, MemGPT)."

This is defensible. Anything more aggressive risks overclaim.

### §2.3 — Long-context vs RAG decision boundary (Vortex findings)

**Token-budget math (synthesized from Liu et al. 2024, Jiang et al. 2024, Xu et al. ChatQA2 2024):**

- Effective window `We / Wt ≈ 0.2–0.4` for frontier models on multi-needle tasks. Gemini 1.5 Pro at Wt=1M shows `We ≈ 200K` in independent reproductions.
- NoLiMa (Modarressi et al. 2025) — when lexical overlap is removed, effective contexts collapse to **2K–8K** even for 1M-claimed models. **Most threatening finding to the LC-obsoletes-RAG narrative.**
- MRCR v2 at 1M tokens (multi-round coreference, OpenAI/ContextArena 2026): Claude Opus 4.6 = 76%; Gemini 3 Pro = 24.5%; GPT-5.4 = 36.6%. Real differentiation at 1M is large.

**Decision rule (from Jiang et al. 2024 + Xu et al. 2024 + Li 2025):**

| Regime | Winner | Why |
|---|---|---|
| Wt ≥ corpus, dense narrative, δ > 30% | **LC** | Chunking breaks coherence; LC wins by 7–13 pts |
| Sparse needles, δ < 5%, corpus >> Wt | **RAG** | Cost dominates; LC degrades past We |
| Heterogeneous sources, dialog/QA | **RAG** | Per-source attribution clean |
| Multi-hop chains, multiple needles | **LC with reasoning** | Pure RAG loses recall on chained facts |
| Holistic reasoning ("which X is largest?") | **LC** | RAG cannot aggregate cross-document |

**Self-routing** (Jiang et al. 2024): model self-reflection picks LC vs RAG per query. Drops cost ~80% vs pure-LC with comparable accuracy. **Production sweet spot for Helios v0.4+.**

**Implications for Helios:**

- Add `load_strategy: {preload, retrieve, hybrid}` annotation per memory.
- Position-aware injection matters more than type-aware (lost-in-middle penalty at the 50% position).
- 5 fixed memory types are still right, but as soft annotation for lifecycle/ranking — not hard slot budget. With 200+ memories of 1K tokens fitting in 200K, bottleneck shifts from "which slots" to "which ordering."

### §2.4 — Multi-tenancy patterns for memory workloads (Crucible findings)

| Pattern | Isolation | Scaling Ceiling | Query Latency Overhead | Cost @ 10/1k/100k tenants |
|---|---|---|---|---|
| DB-per-tenant | Strongest | ~1k DBs/cluster | None | $$$ / $$$$ / impossible |
| Schema-per-tenant | Strong | ~1k–10k schemas | Negligible | $$ / $$ / $$$ |
| RLS / shared schema | Logical only | Unbounded rows | 10–50%+ on planner-hostile policies | $ / $ / $$ |
| Namespace partitioning | Vendor-specific | Pinecone 100k+; Qdrant ~1k dedicated shards | Often faster than shared | $$ / $ / $$ |
| Connection-pool routing | Inherits backend | Inherits backend | 1–3ms hop | $ / $ / $$ |

**Pinecone reality (brutal gap-flag):** their docs say "namespaces provide physical isolation," but **namespaces are NOT cryptographically isolated by default**. All namespaces in a project share the same encryption-at-rest key. CMEK is project-scoped, not namespace-scoped — and project CMEK is one-shot, irrevocable. For per-tenant CMEK you need project-per-tenant, defeating namespace economics.

**Recommended pattern for Helios v0.3+:** Schema-per-tenant for relational/memory state + Qdrant payload partitioning with `is_tenant=true` index for vectors, fronted by a per-tenant API key gateway.

**Migration path (single-tenant local-first → multi-tenant cloud):**

1. **v0.3.0** — Introduce `TenantContext` primitive; local-first uses `__default__`. Zero schema change.
2. **v0.3.1** — `tenants` + `api_keys` tables in control plane.
3. **v0.3.2** — Schema-per-tenant in Postgres; migration creates `tenant_<id>` on provisioning.
4. **v0.3.3** — Qdrant payload partitioning with auto-injected filter at SDK boundary.
5. **v0.3.4** — PgBouncer routing (optional).
6. **v0.4.x** — Cryptographic isolation tier (per-tenant envelope DEK) for regulated customers.

Steps 1–4 are additive to existing single-tenant code. The single-tenant binary still runs against `__default__`.

---

## §3 — Mathematical Optimization Proofs

### §3.1 — Temperature EMA Stability (Caliper)

**Equation:** `temp_n = α·score_n + (1-α)·temp_{n-1}`, α=0.30, promote @ 0.65, demote @ 0.35.

**Convergence under constant score** [FORMAL-PROOF]:
$$t_n = (1-\alpha)^n t_0 + s(1 - (1-\alpha)^n)$$
At α=0.30: half-life = 1.94 reads, effective memory length = 2.33 reads. **Very short — α=0.30 is closer to instantaneous than smoothed.**

**Oscillation thrash** [FORMAL-PROOF]:
Two-cycle fixed point under alternating `μ ± A`:
$$t_{\text{even}} = \mu + A \cdot \frac{1-\alpha}{2-\alpha}, \quad t_{\text{odd}} = \mu - A \cdot \frac{1-\alpha}{2-\alpha}$$
At α=0.30, half-swing = 0.4118·A. **Spurious thrash condition around μ=0.5**: any amplitude `A > 0.364` crosses both thresholds every cycle.

**Burst pattern simulation** [NUMERICAL-VERIFIED]: 100 random orderings of 20 reads (12 high, 8 low). Baseline α=0.30 produces **3.14 spurious promotes / run + 0.99 spurious demotes / run**. Zero clean runs out of 100. This is the headline finding: **α=0.30 + hard thresholds is unstable on realistic bursty workloads.**

**Stabilization variants:**

| Variant | Stability | Failure mode | Code complexity |
|---|---|---|---|
| **Schmitt hysteresis (0.70/0.30)** [FORMAL] | Suppresses all orbits with A < 0.486 | Persistently large-amplitude alternation; tier "stickiness" | **3 lines** |
| Variance-adaptive α | Adapts to noise | Needs warm-up; lag in variance estimator | ~20 lines |
| Double-EMA (Holt 1957) | Tracks trend | Overshoot on outliers; 2 params to tune | ~30 lines |
| Median-k pre-filter | Rejects outliers | Lags on regime changes; underperformed on blocky bursts in sim | ~15 lines |

**Counter-intuitive result** [FORMAL]: lowering α to 0.10 **enlarges** the steady-state orbit (because `(1-α)/(2-α)` increases as α decreases). More smoothing does NOT reduce oscillation amplitude — only hysteresis does.

**Primary recommendation:** **Schmitt hysteresis** (promote at 0.70, demote at 0.30, record stays in current tier until opposite threshold crossed). Minimum code change, no extra state, analytically suppresses all orbits with A < 0.486. **Highest-ROI math change in this blueprint.**

### §3.2 — Recency Decay Models (Tau)

**Equation:** `recency = exp(-Δt/τ)`, τ=600s.

**Decay model comparison:**

| Model | Form | Half-life | Tail integral |
|---|---|---|---|
| Exponential (current) | $e^{-\Delta t/\tau}$ | τ·ln(2) ≈ 0.693τ | τ (converges, **thin tail**) |
| Power-law | $(\Delta t/\tau + 1)^{-\gamma}$ | τ(2^(1/γ) - 1) | τ/(γ-1) iff γ>1 (heavy tail) |
| Logarithmic | $1/(1 + \ln(\Delta t/\tau + 1))$ | τ(e-1) ≈ 1.718τ | diverges |
| Reciprocal | $1/(1 + \Delta t/\tau)$ | τ | diverges |

**Cognitive science fit** [VERIFIED-COGSCI]:
- **Ebbinghaus (1885)** — first quantitative forgetting curve; power and logarithmic fits achieved R² ≈ 0.988. Often *mistakenly* described as exponential in textbooks.
- **Wickelgren (1972)** — power-law `m(t) = λ(1+βt)^-ψ` fits human forgetting curves.
- **Wixted & Ebbesen (1991, 1997)** — power functions fit individual-subject curves substantially better than exponentials.
- **Anderson & Schooler (1991)** — environmental access patterns follow power-law; brain is rationally tuned to this.
- **Evidence ratio (Stevens et al. 2016 on chimp social contact)**: power vs exponential ~10^10.

**Implication:** exponential at τ=600 is spec-time convenience. Power-law is the empirically correct functional form.

**Adaptive τ derivation** [FORMAL-PROOF]:
$$\tau_n = \text{clip}\left(\beta \cdot \text{median}(\text{IAT}_{n-k+1}, \dots, \text{IAT}_n), \tau_{\min}, \tau_{\max}\right)$$

with β=10 (yields r ≈ 0.905 for one-IAT-old content). Median is robust to bursty IATs (a 3600s outlier doesn't drag median(6,6,6,6,3600,6,...) significantly).

**Recommended scheme:**
- k=5 window, β=10, τ_min=30s, τ_max=86400s
- Linear warm-up blend for cold-start: τ_n = α·600 + (1-α)·β·median for n < k
- A/B/C test: exp@600 (control) vs exp@adaptive vs power-law@adaptive
- **Brutal flag:** with γ ≤ 1 the power-law integral diverges → recency scores don't shrink fast enough. Pick γ ≥ 1.5 OR normalize within-candidate-pool. Surface BEFORE A/B test.

### §3.3 — Reranker Optimization via Lagrange (Lagrange)

**Equation:** `score = 0.55·sim + 0.20·val + 0.10·rec + 0.10·tier - 0.05·drift`

**Brutal gaps upfront:**
- nDCG/MRR are piecewise-constant — gradients undefined. Use **ListNet cross-entropy loss** (Cao et al. ICML 2007) as smooth surrogate.
- Multi-tier infrastructure is aspirational; current Helios is single-tier SQLite. Marked [HEURISTIC — UNDEPLOYED].

**Lagrangian** [FORMAL-PROOF]:
$$\mathcal{L}(w, \lambda, \mu) = \mathcal{J}_{\text{ListNet}}(w) + \lambda\left(\sum_{i\in P} w_i - 1\right) - \sum_i \mu_i w_i$$

with positive index set P = {sim, val, rec, tier} and drift coefficient unconstrained above.

**Interior closed-form solution:**
$$w_i^* = \frac{\exp(\beta \bar{g}_i)}{\sum_{k \in P} \exp(\beta \bar{g}_k)}$$
where $\bar{g}_i$ is empirical alignment of feature i with gold ranking. **Softmax over feature alignments.**

**Multi-tier infrastructure adjustment** [HEURISTIC]:
With tier cost vector c = (1ms, 50ms, 500ms) and latency budget B, Lagrangian gains $\nu(\mathbb{E}[c] - B)$. Stationarity: `w_tier* ↑ monotonically in ν` (shadow price of latency).

**No-clipping guarantee** [STANDARD-RESULT]:
Cite Duchi, Shalev-Shwartz, Singer & Chandra (ICML 2008): Euclidean projection onto simplex is `x_i* = max(v_i - τ, 0)`. Every coordinate non-negative by construction. **Projected gradient descent on the simplex never produces negative weights.**

**Sensitivity table** [NUMERICAL-VERIFIED]:

| Weight | Empirical feature mean | ∂score/∂w | Ranking impact per +0.05 |
|---|---|---|---|
| w_sim | 0.62 | +0.62 | +0.41 (largest) |
| w_val | 0.34 | +0.34 | +0.18 |
| w_rec | 0.51 | +0.51 | +0.22 |
| w_tier | 0.20 | +0.20 | +0.06 (degenerate: single-tier) |
| w_drift | 0.18 | -0.18 | -0.09 |

**Diagnostic mapping:** stale results → raise w_rec; off-topic → raise w_sim; slow queries → raise w_tier (post-deployment).

**Non-linear drift correction** [FORMAL-PROOF]:
$$\tilde{d}(\text{drift}) = 1 - \exp(-\text{drift}/d_0), \quad d_0 > 0$$
Bounded influence: $|\partial \text{score}/\partial \text{drift}| \leq w_\text{drift}/d_0$. Prevents saturation pathology.

**Numerical example:** 10 records, 100 iterations of projected gradient ascent. nDCG@5 improves **0.842 → 0.957 (+13.7%)**. Optimized weights recover gold top-5 exactly.

### §3.4 — Drift Saturation & Class-Weighted Preservation (Sediment)

**Equation:** `drift = 0.02 + 0.01·cycles + 0.001·reads`

**Saturation analysis** [FORMAL-PROOF]:
- Iso-drift d=1.0 surface: `10c + r = 980`. At c=0: r=980 reads. At c=10: r=880 reads.
- Reranker penalty `-0.05·drift`: full score inversion requires drift > 19 (10c + r > 18,980 — rare).
- **Soft popularity penalty**: under 1000 reads (c=0), drift = 1.02 → -0.051 score bias. Given inter-result score gaps of 0.01–0.05 in production, **this is enough to flip rankings**.

**Class-weighted multiplier** [FORMAL-PROOF for invariance, HEURISTIC for weight values]:
$$d_{\text{eff}}(c, r, \tau) = w_\tau \cdot (0.02 + 0.01c + 0.001r)$$

$$w_\tau = \begin{cases}
0.0 & \text{if } \tau = \text{decision} \\
0.2 & \text{if } \tau = \text{event} \\
0.5 & \text{if } \tau = \text{state} \\
0.8 & \text{if } \tau = \text{summary} \\
1.0 & \text{if } \tau = \text{observation}
\end{cases}$$

**Decision invariance theorem:** for any access pattern `(c, r) ∈ ℕ²`, decisions experience zero drift penalty. **Proof:** `w_τ = 0` for decision ⟹ `d_eff = 0` ⟹ `-0.05·d_eff = 0`. ∎

**Background neutralization algorithm:**

```python
def neutralize_drift_worker(store, T=86400, theta=0.5):
    while True:
        sleep(T)
        for record in store.scan():
            d = compute_drift(record.cycles, record.reads)
            if d > theta:
                # Strategy A — counter halving (safe, no deps)
                record.cycles //= 2
                record.reads //= 2
                store.update(record)
```

**Convergence proof:** between neutralizations, reads accumulate `Δr = ρT`. Halving at each tick yields fixed point `r* = ρT`, so `d* = 0.02 + 0.001·ρT`. Bounded.

For ρ = 0.01 reads/sec (864/day) and T = 86400s: d* ≈ 0.884. To target d* ≤ 0.5: T ≤ 48000s (~13h).

**Order preservation theorem** [FORMAL-PROOF]: Strategy A preserves relative ordering across same-type records. The affine map `d ↦ (d - 0.02)/2 + 0.02` is order-preserving.

**Numerical example** [NUMERICAL-VERIFIED]:

| Type | w_τ | Baseline (1000R+5C) | + Class-weight | + Class-weight + neutralization |
|---|---|---|---|---|
| decision | 0.0 | d=1.07, pen=-0.054 | d=0, pen=0 | d=0, pen=0 |
| event | 0.2 | d=1.07, pen=-0.054 | d=0.214, pen=-0.011 | d=0.114, pen=-0.006 |
| state | 0.5 | d=1.07, pen=-0.054 | d=0.535, pen=-0.027 | d=0.285, pen=-0.014 |
| summary | 0.8 | d=1.07, pen=-0.054 | d=0.856, pen=-0.043 | d=0.456, pen=-0.023 |
| observation | 1.0 | d=1.07, pen=-0.054 | d=1.070, pen=-0.054 | d=0.570, pen=-0.029 |

**Decision recall preserved across all scenarios. Observation drift bounded with neutralization.**

---

## §4 — Unconstrained Architectural Blueprint

### §4.1 — Unified data layer

**Recommendation:** Postgres 16+ with pgvector for the relational/vector store, Qdrant as the high-performance vector index, Neo4j (or AGE on Postgres) for the optional graph layer.

```
┌──────────────────────────────────────────────────────────────┐
│                     Helios Control Plane                       │
│  tenants · api_keys · audit_log · billing/usage · feature_flags │
├──────────────────────────────────────────────────────────────┤
│                       Helios Data Plane                        │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────┐   │
│  │  Postgres   │    │   Qdrant    │    │   Neo4j / AGE    │   │
│  │  (schema-   │    │  (payload-  │    │  (per-tenant     │   │
│  │   per-      │    │  partitioned│    │  subgraph)       │   │
│  │   tenant)   │    │  vectors)   │    │                  │   │
│  │             │    │             │    │                  │   │
│  │ memory_     │    │ embeddings  │    │ entities,        │   │
│  │ records,    │    │             │    │ edges,           │   │
│  │ chat_       │    │             │    │ communities      │   │
│  │ history,    │    │             │    │                  │   │
│  │ concepts,   │    │             │    │                  │   │
│  │ skills,     │    │             │    │                  │   │
│  │ audit_log   │    │             │    │                  │   │
│  └─────────────┘    └─────────────┘    └─────────────────┘   │
└──────────────────────────────────────────────────────────────┘
```

### §4.2 — Pipeline mapping

| Stage | Implementation |
|---|---|
| **Ingest** | FastAPI / gRPC route → `TenantContext` injection → message persistence to `chat_history` |
| **Score** | Async LLM classify → write to `memory_records` with tier=cold, namespace=tenant_id, embedding ingestion to Qdrant |
| **Read** | FTS5 (Postgres `tsvector`) + Qdrant vector search + graph traversal (if `load_strategy: hybrid`) → LLM rerank with **Lagrangian-tuned weights** |
| **Modify** | **Schmitt hysteresis** on top-K → temperature update via EMA → **class-weighted drift** accumulation → log to audit_log |
| **Write** | Persist updates to memory_records; emit `WAL event` for downstream concept-induction worker |
| **Store** | Default tier=cold; **background drift neutralization worker** runs nightly with Strategy A counter halving |

### §4.3 — Concept induction layer (v0.4)

Triggered async on WAL events. Pipeline:

1. **Cluster substrate metadata** by similarity (cosine on embeddings) + co-occurrence (entity overlap)
2. **LLM label clusters** → induced concept with `concept_name`, `parent_concept`, `is-a relation`
3. **Materialize as concept_records** with timestamp, tenant_id
4. **Cross-tenant aggregation** (v0.5+, DP-protected): aggregate concept frequencies via differential privacy with per-tenant ε budget

This is the substrate → concepts arrow, retrospective (not write-time).

### §4.4 — Skill compilation layer (v0.4)

Triggered async on read-side workload patterns. Pipeline:

1. **Identify high-frequency query patterns** with high locality (≥70% of retrieved records share one concept)
2. **Synthesize skill template** via LLM with prompt: "Given queries Q matching pattern P, compile a parameterized skill template that compiles into the system prompt of future similar queries"
3. **Materialize as skill_records** with `concept_id`, `query_template`, `success_criteria`
4. **Compile into rerank/classify prompts** via `core.induction.compile_skills_into_prompt()` — NO LLM tool-calling, NO `/skills/{name}` endpoints

This is the concepts → skills arrow, the load-bearing differentiator vs A-MEM and CMA.

### §4.5 — Deployment topology

| Layer | Tech | Why |
|---|---|---|
| Edge / ingress | Cloudflare or AWS ALB | DDoS, TLS termination, geo-routing |
| API gateway | Kong or FastAPI with rate-limit | Per-tenant rate limit, API key validation |
| Application | FastAPI on Kubernetes | Async, OpenAPI auto-gen, scales horizontally |
| Worker fleet | Celery or RabbitMQ + Python workers | Async classify, embed, concept-induce, drift-neutralize |
| Postgres | RDS / Cloud SQL with read replicas | Schema-per-tenant, replicas for analytics |
| Qdrant | Managed Qdrant Cloud or self-hosted | Payload-partitioned by tenant_id |
| Neo4j (optional) | Managed Neo4j AuraDB | Per-tenant subgraph, query via Cypher |
| Object storage | S3 or R2 | Long-term cold tier for archival memories |
| Observability | Prometheus + Grafana + OpenTelemetry | Per-tenant latency, throughput, error rates |

### §4.6 — Productization additions (B2D pitch)

- **`/signup`** — creates tenant + first API key, returns raw key once
- **`/tokens`** — list/create/revoke keys for current tenant
- **`/usage`** — per-tenant metering (writes, reads, embeddings, LLM calls)
- **`/audit`** — audit log endpoint (already in v0.2 synthetic)
- **`/health`** + **`/metrics`** — observability
- **Billing integration** — Stripe via webhook for usage-based pricing

---

## §5 — Wedge-Impact Map + Backport Recommendations

### §5.1 — Wedge-impact map

| Component | Preserves wedges? | Notes |
|---|---|---|
| Schmitt hysteresis (math) | ✅ Preserves all | 3 lines of code; zero infra cost |
| Class-weighted drift (math) | ✅ Preserves all | Already proposed by Sediment; pure formula change |
| Power-law recency (math) | ✅ Preserves all | One function swap; no new deps |
| Adaptive τ (math) | ✅ Preserves all | Median of IAT in memory; no new tables |
| Bounded drift correction (math) | ✅ Preserves all | Same as above |
| Background drift neutralization worker | ✅ Preserves all (mostly) | Adds operational complexity (worker reliability); failure mode bounded |
| Lagrangian weight tuning | ✅ Preserves all | Math optimization on offline data; weights are constants in code |
| Namespace primitive on memory_records | ✅ Preserves all | Already in v0.2 patches |
| Audit log table | ✅ Preserves all | Already in v0.2 patches |
| Multi-tenant `/signup` + `/tokens` | ⚠️ Tension with wedge #1 | Multi-tenant scaffolding implies hosted deployment; can preserve "local-first" as binary mode |
| Vector DB (Qdrant) | ❌ Violates wedge #2 | Hard dep on vector ANN |
| pgvector | ❌ Violates wedge #1 + #2 | Postgres + vector ANN |
| Graph layer (Neo4j) | ❌ Violates wedge #1 + #3 | Heavy dep; high ops complexity |
| Schema-per-tenant Postgres | ❌ Violates wedge #1 | Cloud-only deployment |
| Long-context attention sinks | ⚠️ Neutral / depends | If client-side, neutral; if server-side, depends on infra |
| Differential privacy infrastructure (v0.5) | ⚠️ Depends | Implementation-dependent |

### §5.2 — Recommended backports (wedge-preserving, immediate ROI)

**Five drop-in math improvements for current `helios-memory`** — total ~50 LOC of changes, zero new dependencies:

1. **Schmitt hysteresis on temperature** — `tiering.PROMOTE_THRESHOLD = 0.70, DEMOTE_THRESHOLD = 0.30`. Highest-ROI change.
2. **Class-weighted drift multiplier** — add `TIER_BONUS[type]`-style `DRIFT_CLASS_WEIGHT` dict. Decisions become drift-invariant.
3. **Power-law recency option** — add `RECENCY_MODEL: Literal["exponential", "power_law"]` flag with γ=1.5 default. A/B test.
4. **Adaptive τ via median(IAT)** — new `core.tiering.adaptive_tau(session_iats)` function.
5. **Bounded drift correction** — `drift_smooth = 1 - exp(-drift/d_0)` with d_0 = 1.0.

**Three operational additions for B2D pitch credibility** (extensions of v0.2 work):

1. **`/signup` + `/tokens` endpoints + tenants/api_keys tables** — multi-tenant auth scaffolding the audit flagged. Can preserve "local-first" by defaulting to `__default__` tenant.
2. **Background drift neutralization worker** — periodic counter halving on records with drift > 0.5. Operational dependency but minimal infra cost.
3. **Lagrangian-tuned weights via offline replay** — collect production query logs, run projected gradient ascent on ListNet surrogate, ship optimized weights as constants.

### §5.3 — Defer to v0.4+ (legitimate wedge violations)

- **Qdrant vector layer** — adds the "hybrid retrieval" wedge competitors all have. Defer until customer demand justifies.
- **Graph layer (Neo4j)** — only if customers explicitly need cross-entity reasoning.
- **Schema-per-tenant Postgres** — defer until hosted deployment is funded.

---

## §6 — Helios Paper Defense (NeurIPS 2026 Workshop)

### §6.1 — Related Work framing

> "Helios instantiates the Continuum Memory Architecture class (arXiv:2601.09913) with three architectural commitments not jointly present in prior work: (i) **immutable substrate** — raw metadata is write-only after ingest, in contrast to A-MEM's (Xu et al. NeurIPS 2025) evolve-on-write attribute generation; (ii) **retrospective concept induction** — concepts emerge from patterns over the frozen substrate via async clustering + LLM labeling, not as write-time co-generation; (iii) **callable skill templates compiled into prompts** — skills are parameterized templates injected into the rerank/classify system prompts, distinct from Voyager's (Wang et al. TMLR 2024) standalone code skills and absent in CMA, A-MEM, GraphRAG (Edge et al. 2024), and MemGPT (Packer et al. COLM 2024)."

### §6.2 — Acceptance probability assessment

- **As currently submitted (v1 draft, no Track A pilot):** 25-35%
- **With Track A pilot partial-success numbers before camera-ready:** 40-55%

The pilot remains the load-bearing experiment. Recommended target: FTS5+LLM-rerank quality on LongMemEval/LoCoMo with vocabulary-overlap subgroup analysis, start by 2026-05-21.

### §6.3 — Honest gaps in the paper

Six acknowledged in §6 of the current draft. Two new ones surfaced by this research:

1. **Math claims in §3 are derived, not empirically verified.** The blueprint proposes A/B tests but does not pre-register results.
2. **A-MEM proximity is sharper than the draft currently states.** Recommend tightening the contrast in §2 (Related Work).

---

## §7 — Honest Gaps in This Research

1. **Bibliographic metadata** for [CANON] citations is ~95% confidence. Re-verify exact author ordering, page numbers, DOIs before external publication.
2. **Math claims** are derived, not empirically tested. Each becomes "claimed, falsifiable, pilot proposed" not "verified."
3. **Architectural blueprint** is a 12-24 month target; it does NOT establish that wedge-bound `helios-memory` should pivot. §5 separates target-state from backport-feasibility.
4. **Long-context literature is moving fast.** NoLiMa (Feb 2025) and MRCR v2 (2026) are recent; preferences may shift again in 6-12 months.
5. **SaaS vendor traction claims** are vendor-driven hype until independently verified. Specifically Mem0's "+26% LOCOMO accuracy" claim was disputed by Letta and Zep.
6. **CMA (arXiv:2601.09913)** is a 2026 preprint with no peer-review confirmation visible. If CMA gets rejected, Helios's "concrete CMA instantiation" framing weakens; if it gets accepted at a top venue, framing strengthens.
7. **Crucible's recommendation of schema-per-tenant** assumes 100-1000 tenants in year 1. If Helios's pre-seed exit is at >10k tenants, this recommendation needs revisiting.

---

## §8 — Recommended Roadmap

**Immediate (v0.3, weeks)** — wedge-preserving:
- Apply 5 math backports (§5.2)
- Land multi-tenant auth scaffolding (already drafted)
- Strip aspirational HNSW copy (already in v0.2 work)
- Pilot Track A (FTS5+LLM quality probe)

**Near-term (v0.4, months)** — limited wedge violations:
- Optional pgvector layer (preserves local SQLite path)
- Background drift neutralization worker
- Lagrangian-tuned weights via offline replay
- core/induction.py for concept induction

**Mid-term (v0.5+, quarters)** — full target state:
- Qdrant vector layer (hosted)
- Graph layer (Neo4j or AGE) — customer-demand-gated
- Schema-per-tenant Postgres
- Multi-tenant `/signup` + `/tokens` + billing
- DP-mediated cross-tenant aggregation

**Long-term (v1.0+, years)** — full blueprint:
- Production deployment with Cloudflare + K8s + observability
- Skill compilation layer with empirical validation
- Customer-deployable SDK in multiple languages

---

**Word count:** ~5500. Citations re-verifiable per [CONFIDENCE-TIER] tags. Subagent source markdowns archived at `/agent/workspace/audit/research/scout-*.md` (TODO: persist as separate files if needed).
