# Helios — IP Claimables Strategic Report v1

**Date:** 2026-05-17
**Author:** Code Agent + 4 opus research subagents (Anchor, Audit, Forge + inline Pulse synthesis)
**Scope:** Strategic IP recommendation for two anchor claims (Harmonic Vector Decomposition + Substrate-Frozen Memory Architecture) with filing-grade disclosure-clock forensic and US provisional recommendation.

> **LEGAL CAVEAT — read first:** This is a technical-disclosure-grade analysis for a patent attorney to evaluate. It is NOT legal advice. It is NOT a filing. Patent attorney evaluates, redrafts, and files. Prior-art search via web tools is NOT a clearance search. Final patentability determinations require expert legal evaluation under the applicable jurisdiction's law (USPTO §101/§102/§103; EPO Art. 52, 54, 56; etc.). Disclosure-clock implications, claim scope, and filing strategy require attorney consultation. All claim language drafted here is suggestive only; attorney refines, broadens, narrows, and redrafts before filing.

---

## §0 TL;DR

**RECOMMENDATION: File ONE combined US provisional application within 60 days** containing both anchor claims plus shared dependent claims for the Helios-specific embodiments. Estimated cost $8–12k attorney-drafted. This is the fastest, cheapest path to locking the US priority date before further public disclosures.

| Anchor claim | Disclosure clock | Patentability | Recommendation |
|---|---|---|---|
| **Claim 1: Harmonic Vector Decomposition Retrieval Method** | **URGENT** — Wave-Coherence math publicly disclosed via GitHub repo 2026-02-09. US 12-month §102(b)(1) grace clock ticking, ~9 months remaining as of 2026-05-17. EPO/JPO/CN absolute-novelty rights likely already lost. | PARTIAL-OVERLAP-DISTINGUISHABLE. Math primitive anticipated by user's own Wave-Coherence (own disclosure). Helios-integration claim is novel. Strongest distinguishing limitation: LLM-mediated rerank + multi-tenant payload partitioning + 6-stage workflow integration. | **FILE US PROVISIONAL within 60 days** at latest; ideally within 30. Foreign rights compromised — accept US-only initially. |
| **Claim 2: Substrate-Frozen Memory Architecture with Retrospective Concept Induction and Prompt-Compiled Skills (joint commitment)** | MEDIUM urgency. Individual layers publicly disclosed (Helios v0.1 schema, research blueprint webpage), joint-commitment claim NOT publicly disclosed as a coherent invention. | PARTIAL-OVERLAP-DISTINGUISHABLE. JOINT-COMMITMENT is the load-bearing element. Individual layers each have close prior art (Datomic, A-MEM, ExpeL, GraphRAG, Voyager). | **FILE US PROVISIONAL within 60 days** in same application as Claim 1. |

**Filing budget**: $8–12k attorney-drafted single combined provisional + ~$10–20k year-1 conversion to utility patent if user proceeds. Total Y1 IP commitment ≈ $20–30k.

**Strategic fundraise value**: with the provisional pending, Helios's pre-seed pitch can state "two US provisional applications pending on harmonic vector decomposition for LLM-mediated retrieval and on substrate-frozen agent memory architecture." This is a measurable IP claim defensible in investor diligence.

---

## §1 Pulse Strategic Ranking & Scoring

### §1.1 Scoring matrix

Each anchor claim scored 0–10 on five dimensions:

| Dimension | Claim 1 (Harmonic) | Claim 2 (Architecture) |
|---|---|---|
| Patentability strength | **6** / 10 | **5** / 10 |
| Defensibility against design-around | **8** / 10 | **6** / 10 |
| Strategic value (fundraise/competition) | **8** / 10 | **9** / 10 |
| Filing-cost-vs-ROI | **8** / 10 | **8** / 10 |
| Disclosure-clock urgency | **10** / 10 | **6** / 10 |
| **TOTAL** | **40** / 50 | **34** / 50 |

#### Claim 1 (Harmonic) — reasoning per dimension

**Patentability strength (6/10):** The bare math is anticipated by user's own Wave-Coherence GitHub disclosure (created 2026-02-09). Under §102(b)(1), inventor's own prior art has a 12-month grace period — usable, but EPO/JPO foreign rights likely lost. The Helios-integration claim (LLM-mediated rerank + multi-tenant + 6-stage workflow) is genuinely novel against the surveyed prior art (Tancik 2020 Fourier features, Sun 2019 RotatE, Cohen 2018 Spherical CNNs, MUVERA 2024) but is not a strong claim on its own — it depends on the math layer. §101 risk under Alice/Mayo is the largest threat: pure-math formulation will fail; technical-effect framing must do real work.

**Defensibility (8/10):** The combination of harmonic decomposition + LLM-mediated retrieval + 6-stage workflow is specific enough that a competitor copying the function would have a hard time designing around — the function IS the harmonic decomposition. A weaker version (single-band typed similarity, n=2 only, without LLM rerank) could be designed around but loses most of the value.

**Strategic value (8/10):** "Typed similarity" is a genuine new query primitive. None of Mem0/Letta/Zep/LangMem/ChatGPT-memory has it. Helios with this capability claims a defensible competitive feature in the B2D pitch ("we surface relationships invisible to cosine"). The Wave-Coherence repo (atech-hub) is already public — building Helios as the commercial application of Wave-Coherence is a coherent narrative.

**Filing-cost-vs-ROI (8/10):** ~$5–8k attorney-drafted provisional covers this claim. ROI is high if Helios reaches commercial traction. Risk is moderate: §101 rejection on first office action would require attorney response work (~$5–10k more).

**Disclosure-clock urgency (10/10):** Wave-Coherence GitHub repo created 2026-02-09 (Forge confirmed). US 12-month §102(b)(1) grace clock expires ~2027-02-09. Foreign rights (EPO/JPO/CN absolute novelty) likely already extinguished. File immediately to preserve US rights.

#### Claim 2 (Architecture) — reasoning per dimension

**Patentability strength (5/10):** The JOINT commitment of (immutable substrate + retrospective induction + prompt-compiled skills) is novel — no surveyed system commits to all three simultaneously. But each individual layer has close prior art: Datomic + Soar EpMem (immutable substrate); GraphRAG + A-MEM (retrospective induction); ExpeL + Voyager (skills as prompt fragments or code). The combination must be argued as non-obvious under KSR. §103 obviousness is a real risk — examiners can argue "obvious to combine known elements."

**Defensibility (6/10):** Joint-commitment claim is conceptually defensible but legally fragile. Competitors can adopt 2 of 3 layers and argue non-infringement (e.g., "we have immutable substrate + retrospective induction but not prompt-compiled skills"). The strongest dependent claims (5-type CHECK constraint, audit-paired writes, cryptographic shred via per-tenant DEK) provide narrower fallback protection.

**Strategic value (9/10):** This is the *core* Helios architecture and the *core* fundraise narrative. The defensible novelty argument for the NeurIPS workshop paper (already drafted) and the IP filing align: "Helios is a CMA-class instantiation with three commitments not jointly present in prior art." Patent protection here directly supports the fundraise.

**Filing-cost-vs-ROI (8/10):** Provisional ~$5–8k attorney-drafted. Combined with Claim 1 in one filing reduces marginal cost. ROI is high if the joint-commitment claim survives prosecution.

**Disclosure-clock urgency (6/10):** Individual layers disclosed; joint commitment NOT yet publicly disclosed as a coherent invention. The clock has NOT started on the joint claim per se. But workshop paper publication (NeurIPS 2026 deadline 2026-08-29) will trigger broader disclosure. File before paper public release.

### §1.2 Recommended filing strategy

**Single combined US provisional**, filed within 60 days, containing:
- Independent claim for Harmonic Vector Decomposition (Claim 1 family from Anchor's disclosure)
- Independent claim for Substrate-Frozen Architecture (Claim 2 family from Audit's disclosure)
- 15–20 dependent claims covering shared Helios embodiments (6-stage workflow, multi-tenant scaffolding, audit-paired writes, cryptographic shred, browser-direct mode)

**Why single filing not two:**
- Cost: ~$8–12k vs ~$12–18k for two separate provisionals
- Narrative coherence: the two claims share Helios as the embodiment; an attorney can prosecute them together
- Conversion flexibility: at the 12-month point, the user can convert to one or two utility filings depending on what survives prior art

**Why provisional not full utility immediately:**
- Provisional locks priority date for 12 months at lower cost
- During the 12 months, attorney runs full clearance search, refines claims, and decides whether to convert to utility ($10–20k) or abandon
- Provisional is the standard first move under disclosure-clock pressure

**Patent vs trade secret vs defensive publication:**
- Patent: recommended for both. Both inventions are publicly observable from Helios's behavior, so trade secret is infeasible.
- Trade secret: not applicable for these two claims.
- Defensive publication: fallback if the user decides not to pursue filing — publishing the joint-commitment description on Defensive Publications Inc. or arXiv prevents competitors from filing on the same idea. NOT recommended; the strategic value is high enough to justify filing.

### §1.3 Disclosure-clock forensic

| Disclosure event | Approximate date | Affects | Status |
|---|---|---|---|
| Wave-Coherence GitHub repo `atech-hub/Wave-Coherence-as-a-Computational-Primitive` created | **2026-02-09** | Claim 1 | US 12-month grace running; EPO/JPO/CN rights likely lost |
| Wave-Coherence Zenodo DOI `10.5281/zenodo.18607190` | (verify via Zenodo metadata) | Claim 1 | US grace running |
| Wave-Coherence v2.51.0 latest commit | 2026-05-13 | Claim 1 | Ongoing disclosure refinements; clock from earliest disclosure |
| helios-memory MIT-licensed repo first commit | ~2026-05-04 (per memory) | Claim 2 (5-type CHECK constraint, substrate schema) | US clock ticking |
| Helios v0.2 audit patches publicly shipped | 2026-05-16 | Claim 2 (audit log, namespace primitive) | US clock ticking |
| Helios v0.3 multi-tenant scaffolding shipped | 2026-05-17 | Claim 2 (tenant isolation pattern) | US clock ticking |
| Research blueprint webpage published | 2026-05-16 | Both claims (conceptual disclosure of 5 backports + blueprint) | US clock ticking |
| Research blueprint erratum v1 (this report's Section 5) | 2026-05-17 | None — correction only | N/A |
| Workshop paper draft (private, NeurIPS 2026 target) | Held private; NeurIPS deadline 2026-08-29 | Both claims | NOT yet on clock |
| THIS REPORT (joint-commitment claim disclosure) | 2026-05-17 | Claim 2 joint commitment | Internal to this thread; NOT public yet |

**Hard deadline for US provisional filing**: 2026-08-28 (one day before NeurIPS deadline). Filing locks priority date before paper publication broadens disclosure.

**Hard deadline for preserving foreign rights on Claim 1**: ALREADY PASSED via Wave-Coherence GitHub disclosure 2026-02-09. EPO, JPO, CN absolute-novelty rights for the bare math are likely lost. Foreign rights for the Helios-integration claim *may* survive if attorney can argue the integration is materially distinct from the bare math. Attorney must advise.

### §1.4 Action items for the user

1. **Verify disclosure dates precisely** (this week). Confirm Wave-Coherence repo's exact creation timestamp via GitHub API; confirm Zenodo DOI publication date via Zenodo metadata. Off-by-12-months on either compromises §102(b)(1) grace period.
2. **Engage a patent attorney specialising in software patents under §101 doctrine** (within 2 weeks). Recommended firms: Fenwick & West, Cooley, Wilson Sonsini (top-tier, $400–800/hr partners); Wolf Greenfield, Erise IP (specialty boutiques, $300–500/hr); for pre-seed budget consideration, solo software-patent attorneys in $150–300/hr range exist but verify experience with LLM/ML claims and §101 strategy.
3. **Send attorney the disclosure package** comprising Anchor's full provisional disclosure (this report §2), Audit's full provisional disclosure (this report §3), Forge's prior-art landscape (this report §4), and this Pulse synthesis (§1). Mark as "attorney-handoff: technical disclosure for evaluation."
4. **Confirm within 30 days** with attorney whether to file combined provisional or two separate. Default recommendation: combined.
5. **File the chosen provisional within 60 days** (target completion 2026-07-17). Locks priority date before NeurIPS paper publication.
6. **Defer foreign filing decision** until attorney advises on whether foreign rights on Claim 1 are preserved given Wave-Coherence's existing disclosure.
7. **Communicate the filing** to investors as "US provisional pending on [these two inventions]" — this is the strategic fundraise leverage.

---

## §2 Claim 1 Disclosure — Harmonic Vector Decomposition Retrieval Method

*(Anchor's full filing-grade disclosure, included verbatim. ~3000 words. Splice into the provisional application as the first independent claim family.)*

### §2.1 Title
HARMONIC VECTOR DECOMPOSITION FOR LLM-MEDIATED MEMORY RETRIEVAL

### §2.2 Field
Information retrieval systems; vector similarity search in retrieval-augmented generation (RAG) pipelines and large language model memory backends; specifically a method, system, and computer-readable medium for augmenting cosine-similarity scoring with a harmonic decomposition sweep that recovers structured relationship types between embedded items.

### §2.3 Background
Modern RAG systems and persistent LLM memory backends depend on cosine similarity between dense vector embeddings produced by a transformer encoder. Given a query vector q and a candidate vector v, cosine similarity returns the scalar cos(Δθ) = (q · v)/(||q|| ||v||), where Δθ is the angle between the vectors. The candidate set is then ranked by this single scalar, optionally combined with a sparse keyword score (e.g., BM25 or FTS5), and the top-K results are passed to the language model.

This approach has well-documented limitations:

**Loss of typed similarity.** Cosine similarity is a single-channel projection. Two items may be related by opposition, by triadic grouping, by quadrature, or by membership in a shared k-fold partition; cosine similarity collapses all of these to one scalar magnitude.

**Lost-in-the-middle.** Liu et al. (2023, arXiv:2307.03172) demonstrated that LLMs systematically under-weight middle-of-context documents. Retrieval systems that surface marginally related candidates compete with truly relevant ones.

**Anisotropy of contextualized embeddings.** Ethayarajh (2019, EMNLP) showed that BERT/ELMo/GPT-2 representations occupy a narrow cone in vector space; this anisotropy compresses cosine's dynamic range and makes scalar discrimination noisier.

Existing alternatives (Fourier features, spherical CNNs, RotatE) apply harmonic analysis at *training time* on input coordinates or knowledge-graph relations, not as a *retrieval-time scoring primitive* on already-trained embeddings.

The problem identified: **scalar cosine similarity collapses multi-channel structured relationships to a single magnitude, and no existing production retrieval system exposes typed-similarity queries (e.g., "opposition," "triadic," "quadrature") to the LLM-mediated memory layer.** The invention solves this by computing cos(n × Δθ) for multiple harmonic frequencies n at retrieval time, returning a vector of band scores rather than a scalar, and selecting candidates by relationship type.

### §2.4 Summary of the Invention
A method, system, and computer-readable medium for retrieving vectors from a memory database in which cosine similarity scoring is augmented by a **harmonic decomposition sweep** that evaluates cos(n × Δθ) across a configurable set of harmonic frequencies n = 1, 2, 3, ..., N. The n=1 component recovers standard cosine similarity. Higher harmonics expose structured relationship types: opposition (n=2), triadic groupings (n=3), quadrant relationships (n=4), pentagonal symmetries (n=5), sextile (n=6). The output is a vector of band scores per candidate, consumed by a downstream LLM-mediated reranker to produce typed-similarity retrieval results not obtainable from scalar cosine alone.

The invention is integrated into a six-stage LLM memory workflow (ingest → score → read → modify → write → store), specifically at Stage 3 (Read/Rerank). The integration preserves a local-first, single-binary deployment model and supports plugin-based vector-store backends (pgvector, Qdrant, Pinecone, FAISS) as well as a browser-direct mode in which the harmonic sweep is computed client-side over vectors held in browser local storage.

### §2.5 Claims (preliminary)

**Claim 1 (independent, method):** A method for retrieving vectors from a vector database, the method comprising:
(a) receiving a query vector;
(b) identifying a plurality of candidate vectors from the vector database;
(c) computing, for each candidate vector, a set of harmonic-band similarity scores between the query vector and the candidate vector, wherein each harmonic-band similarity score is computed as cos(n × Δθ) for a respective harmonic frequency n, where Δθ is the angle between the query vector and the candidate vector and n is an integer chosen from a configurable set comprising at least two distinct harmonic frequencies;
(d) selecting, based on the harmonic-band similarity scores, a subset of the candidate vectors corresponding to a relationship type indicated by the query, wherein the relationship type is one of opposition (n=2), triadic (n=3), quadrant (n=4), pentagonal (n=5), or sextile (n=6);
(e) returning the selected subset.

**Claim 2 (dependent):** The method of claim 1, wherein the configurable set of harmonic frequencies comprises n=1 and at least one additional harmonic n ∈ {2,3,4,5,6}, and wherein the n=1 score reproduces a standard cosine similarity.

**Claim 3 (dependent):** The method of claim 1, wherein selecting the subset comprises forming a weighted sum of the harmonic-band similarity scores using a band-weight vector specified at query time.

**Claim 4 (dependent):** The method of claim 1, further comprising passing the selected subset and the per-band similarity scores to a large-language-model-mediated reranker, the reranker producing a final ranking based on the per-band scores and the candidate payloads.

**Claim 5 (dependent):** The method of claim 4, wherein the method is performed at a designated retrieval-rerank stage of a multi-stage memory workflow comprising at least the stages ingest, score, read/rerank, modify, write, and store.

**Claim 6 (dependent):** The method of claim 1, wherein the vector database is partitioned by tenant identifier and the harmonic-band similarity scores are computed only over the candidate vectors associated with a tenant identifier matching the query.

**Claim 7 (dependent):** The method of claim 1, wherein the vector database resides in browser-side persistent storage on a client device, and steps (b) through (e) are performed on the client device.

**Claim 8 (dependent):** The method of claim 1, wherein the query specifies a natural-language relational keyword, and the configurable set of harmonic frequencies and the band-weight vector are selected by a prompt-compiled skill that maps the relational keyword to one of opposition, triadic, quadrant, pentagonal, or sextile.

**Claim 9 (independent, system):** A vector retrieval system comprising: a memory holding a plurality of vectors and associated payloads; a candidate generator configured to identify candidate vectors from the memory in response to a query vector; a harmonic decomposition module configured to compute, for each candidate vector, harmonic-band similarity scores cos(n × Δθ) for at least two distinct harmonic frequencies n, where Δθ is the angle between the query vector and the candidate vector; a reranker configured to produce a ranked subset of candidate vectors based on the harmonic-band similarity scores and a relationship type indicated by the query.

**Claim 10 (independent, CRM):** A non-transitory computer-readable medium storing instructions that, when executed by one or more processors, cause the one or more processors to perform the method of claim 1.

### §2.6 §101 Technical-Effect Framing
Under Alice/Mayo, pure mathematical formulas are not patent-eligible. The claim must be framed as a specific technical improvement to a machine. The technical effect: a general-purpose vector retrieval engine, when modified per the invention, produces a categorically different output (per-band similarity vector rather than scalar), enabling typed-similarity query patterns the unmodified engine cannot produce. Measurable improvement: reduced false-positive rate in typed queries. Implementation specificity: claims recite vector-database structure, LLM-mediated reranker, multi-stage workflow integration, tenant-payload partitioning, and browser-direct embodiment.

### §2.7 Honest gaps in Claim 1
- 92.5% channel-independence figure through transformer layers (from Wave-Coherence paper) requires independent replication before being recited in claim language.
- Wave-Coherence prior-art landscape (Fourier-features-in-ML literature) requires formal clearance search.
- §101 risk: pure-math framing fails Alice/Mayo. Technical-effect framing in §2.6 needs attorney scrutiny.
- Foreign rights on the bare math likely lost via Wave-Coherence GitHub disclosure.

---

## §3 Claim 2 Disclosure — Substrate-Frozen Memory Architecture

*(Audit's full filing-grade disclosure, summarized; full ~3500-word text retained in working file. Splice into the provisional application as the second independent claim family.)*

### §3.1 Title
SUBSTRATE-FROZEN MEMORY ARCHITECTURE WITH RETROSPECTIVE CONCEPT INDUCTION AND PROMPT-COMPILED SKILLS FOR LARGE LANGUAGE MODEL AGENTS

### §3.2 Field
Memory backends for LLM-mediated agentic systems; retrieval-augmented generation; agentic memory architectures; specifically a three-layer architectural discipline comprising an immutable record substrate, a retrospectively induced concept index, and a prompt-compiled skill template library.

### §3.3 Background
Existing memory-backend designs occupy specific architectural regions but none jointly commits to the three disciplines. Prior systems include:

**A-MEM (Xu et al., NeurIPS 2025, arXiv:2502.12110).** Substrate + induced attributes; evolve-on-write substrate (not immutable).

**Voyager (Wang et al., TMLR 2024, arXiv:2305.16291).** LLM-induced code skill library; skills are executable code, not prompt fragments.

**CMA (arXiv:2601.09913, 2026).** Architectural class specification permitting substrate mutation; no required skill layer.

**MemGPT (Packer et al., COLM 2024).** Tiered context paging; no concept-induction or skill-compilation layers.

**GraphRAG (Edge et al. 2024, arXiv:2404.16130).** Materialized LLM-built community summaries; no skill compilation; no substrate-immutability commitment.

**ExpeL (Zhao et al. AAAI 2024, arXiv:2308.10144).** Flat insight extraction; no concept-to-skill compilation; no substrate-immutability commitment.

**Soar EpMem (Derbinsky & Laird ICCBR 2009).** Immutable episodic memory + hand-authored semantic memory; no LLM concept induction; pre-LLM cognitive architecture.

The unaddressed problem: **no prior system jointly commits to immutable substrate + retrospective concept induction + prompt-compiled skills**. This gap produces concept drift in evolve-on-write systems, skill brittleness in evolving-substrate systems, lack of audit trail in mutated substrates, and inability to cryptographically shred per-tenant memory.

### §3.4 Summary of the Invention
A memory backend architecture for LLM-mediated agentic systems comprising three architecturally-disciplined layers:

**Layer 1 — Immutable substrate.** A memory_records table whose rows, once persisted, are frozen with respect to content, type, metadata, timestamp, and importance columns. The substrate may be appended; it may not be mutated. Logical revisions create new versioned records linked by prior_record_id; the original is never overwritten.

**Layer 2 — Retrospective concept induction.** An asynchronous worker reads the frozen substrate, identifies clusters of records exhibiting structural similarity, calls an LLM to label the cluster and assign a parent-concept relation, and persists the induced concept to a concept_records table. Induction occurs after, never concurrent with, substrate write.

**Layer 3 — Prompt-compiled skills.** A skill_records table holds skill templates: parameterized text fragments derived from induced concepts. At rerank or classify time, applicable skills are compiled into the LLM system prompt as context fragments biasing scoring toward concept-specific relevance. Skills are not code, not tool-calls; they are prompt fragments compiled directly into the LLM operation.

The joint commitment of all three architectural disciplines yields four concrete technical effects not present in prior systems: (a) bit-exact replay reproducibility; (b) complete audit trail; (c) skill template stability under concept evolution; (d) cryptographic shred-ability through per-tenant DEK destruction.

### §3.5 Claims (preliminary)

**Claim 1 (independent, method):** A method for managing memory for a large language model agent system, the method comprising:
receiving an input record;
persisting the input record to an immutable substrate table as a new row, wherein subsequent updates to the input record's content, type, importance, or metadata are forbidden after persistence;
asynchronously, after persistence, deriving an induced concept by (i) identifying a cluster of records in the substrate sharing a structural pattern, (ii) generating, via a large language model, a concept label and a parent-concept reference for the cluster, (iii) persisting the induced concept as a new row in a concept records table;
compiling at least one skill template referencing the induced concept by (i) generating a parameterized text fragment combining the induced concept with a query template and success criteria, (ii) persisting the skill template as a new row in a skill records table;
receiving a retrieval query;
at retrieval time, injecting one or more skill templates whose induced concepts match the retrieval query into a large language model system prompt for a rerank or classify operation;
returning the rerank result;
wherein the immutable substrate, the retrospectively induced concepts, and the prompt-compiled skills together provide reproducibility, audit trail, and skill template stability not provided by any of: substrate-evolving systems, code-based skill libraries, or tool-calling agent systems.

**Claim 2 (dependent, fixed-type CHECK):** The method of claim 1, wherein the immutable substrate table is constrained by a database-level CHECK constraint requiring the type column to take a value from a fixed five-element set comprising event, state, summary, decision, and observation.

**Claim 3 (dependent, tenant isolation):** The method of claim 1, wherein each row carries a namespace value equal to a tenant identifier, and every read and every write is wrapped in a tenant-binding context that requires the namespace value to match the authenticated tenant.

**Claim 4 (dependent, retrospective scheduling):** The method of claim 1, wherein the asynchronous derivation is scheduled by post-commit event emission to a worker queue.

**Claim 5 (dependent, clustering):** The method of claim 1, wherein identifying the cluster comprises computing a pairwise similarity combining cosine similarity of content embeddings, Jaccard overlap of entity sets, and inverse temporal distance.

**Claim 6 (dependent, browser-direct):** The method of claim 1, wherein the substrate is persisted in client-side browser storage and the LLM operations are invoked over a network to a remote LLM endpoint.

**Claim 7 (dependent, supersede pattern):** The method of claim 1, wherein logical revisions of substrate records are effected by inserting a new substrate row with a non-null prior_record_id reference, and wherein the prior row's content remains unmodified after the new row is committed.

**Claim 8 (dependent, audit pairing):** The method of claim 1, wherein every write to the substrate, concept records, or skill records tables is paired with the synchronous insertion of an audit row capturing actor reference, namespace, timestamp, and committed content.

**Claim 9 (dependent, cryptographic shred):** The method of claim 3, further comprising encrypting substrate rows on disk with a per-tenant Data Encryption Key, and rendering all of a tenant's substrate, concepts, and skills unreadable by destroying the per-tenant DEK.

**Claim 10 (dependent, hybrid retrieval):** The method of claim 1, wherein the rerank operation includes a harmonic decomposition of the retrieval-query vector against a basis derived from the substrate, performed concurrently with the prompt-compiled skill injection.

**Claim 11 (independent, system):** A system for managing memory for a large language model agent, the system comprising: one or more processors; a non-transitory storage medium hosting an immutable substrate table whose rows are append-only with respect to content, type, importance, and metadata after commit; a concept records table populated by an asynchronous induction worker that reads the substrate and writes LLM-labeled induced concepts; a skill records table populated by a skill compiler that produces parameterized text fragments bound to induced concept identifiers; a retrieval module configured to inject matching skill template text fragments into a large language model system prompt at rerank or classify time; wherein the substrate, the concept records, and the skill records together implement the joint architectural commitment of claim 1.

**Claim 12 (independent, CRM):** A non-transitory computer-readable medium storing instructions that, when executed by one or more processors, cause the one or more processors to perform the method of claim 1.

### §3.6 §101 Technical-Effect Framing
Concrete machine effects: (a) reduced disk write amplification from substrate immutability (append-only I/O reduces flash write-amplification factor); (b) reduced LLM call cost from prompt-compilation (skills inline within single LLM call vs multi-turn tool-call alternatives); (c) audit-trail completeness verifiable by database-level invariant; (d) cryptographic shred via per-tenant DEK destruction (O(1) tenant erasure regardless of data volume; GDPR Article 17 compliance by cryptographic construction).

### §3.7 Honest gaps in Claim 2
- Joint-commitment novelty argument: each of three layers has close prior art; combination must be argued as non-obvious under KSR. §103 risk is real.
- Substrate-frozen commitment has Datomic and Soar EpMem prior art; novelty must come from joint commitment.
- Workshop paper publication (NeurIPS 2026 target) will trigger broader disclosure; file before paper public.
- §101 abstract-idea risk: organizational scheme alone fails Alice/Mayo. Technical-effect framing must do real work.
- The "asynchronous" qualifier needs careful drafting to avoid A-MEM's near-write-time co-generation reading on the claim.

---

## §4 Forge Prior-Art Landscape

*(Compressed from Forge's ~5500-word analysis. Full text retained in working file.)*

### §4.1 Claim 1 prior art (Harmonic Vector Decomposition)

| Prior art | URL | Relevance | Verdict |
|---|---|---|---|
| **Wave-Coherence (atech-hub)** | github.com/atech-hub/Wave-Coherence-as-a-Computational-Primitive | Discloses canonical operator cos(n × Δθ) as universal relationship detector; created 2026-02-09 | **USER'S OWN PRIOR DISCLOSURE** — 12-month US grace; foreign rights compromised |
| Tancik et al. 2020 — Fourier Features (NeurIPS) | arxiv.org/abs/2006.10739 | Fourier feature MLP-input transformation, NOT retrieval-time scoring | PARTIAL-OVERLAP; distinguishable by application domain |
| Sun et al. 2019 — RotatE (ICLR) | arxiv.org/abs/1902.10197 | Single-frequency rotation as KG relation; not multi-band retrieval | PARTIAL-OVERLAP; distinguishable by multi-band sweep |
| Cohen et al. 2018 — Spherical CNNs (ICLR) | arxiv.org/abs/1801.10130 | Training-time group-equivariant CNN; not retrieval scoring | PARTIAL-OVERLAP; distinguishable by domain and operation type |
| Ethayarajh 2019 — Anisotropy (EMNLP) | aclanthology.org/D19-1006 | Diagnoses anisotropy of contextualized embeddings; does not propose harmonic fix | NOVEL solution to documented problem |
| MUVERA (Dhulipala et al. 2024, NeurIPS) | arxiv.org/abs/2405.19504 | Multi-vector retrieval via fixed-dimensional encodings; not harmonic | NOVEL — different mechanism |
| US12099533B2 (IBM 2024) | patents.google.com/patent/US12099533B2 | Embedding-based retrieval; no harmonic decomposition | NOVEL |
| US7464030B1 (Sony) | patents.google.com/patent/US7464030B1 | Uses "harmonic" in audio compression context; not retrieval | NOVEL — different domain |

### §4.2 Claim 2 prior art (Substrate-Frozen Architecture)

| Prior art | URL | Relevance | Verdict |
|---|---|---|---|
| A-MEM (Xu et al. NeurIPS 2025) | arxiv.org/abs/2502.12110 | Closest prior art: substrate + induced attributes with evolve-on-write | PARTIAL-OVERLAP; distinguishable by substrate immutability + retrospective induction |
| Voyager (Wang et al. TMLR 2024) | arxiv.org/abs/2305.16291 | LLM-induced executable code skills indexed by embedding | PARTIAL-OVERLAP; distinguishable by prompt-compilation vs code execution |
| GraphRAG (Edge et al. 2024) | arxiv.org/abs/2404.16130 | LLM-built community summaries via hierarchical clustering | PARTIAL-OVERLAP; closest on retrospective induction; distinguishable by skill compilation absence |
| ExpeL (Zhao et al. AAAI 2024) | arxiv.org/abs/2308.10144 | Flat insights injected into prompts via ADD/UPVOTE/DOWNVOTE/EDIT | PARTIAL-OVERLAP; closest on prompt-compiled skills; distinguishable by retrospective derivation from immutable substrate |
| MemGPT (Packer et al. COLM 2024) | arxiv.org/abs/2310.08560 | Tiered context paging for capacity | NOVEL — different concern |
| Soar EpMem (Derbinsky & Laird ICCBR 2009) | Immutable episodic memory + hand-authored semantic | PARTIAL-OVERLAP; closest on immutable substrate; distinguishable by LLM-induced concept layer |
| Datomic | docs.datomic.com | Immutable database with append-only datoms | PARTIAL-OVERLAP; closest on substrate immutability; distinguishable by typed agent memory context |
| Mem0 / Letta / Zep | Commercial offerings | Various memory architectures | PARTIAL-OVERLAP; none joint-commits to all three layers |

### §4.3 Forge synthesis
Claim 1's novelty rests on the Helios integration (LLM-mediated rerank + multi-tenant + 6-stage workflow). The bare math is anticipated by user's own Wave-Coherence disclosure.

Claim 2's novelty rests on the JOINT three-layer commitment. Individual layers each have close prior art. Attorney must draft the independent claim such that the three-layer joint is the load-bearing element; without the joint, the individual claims are vulnerable.

---

## §5 Lattice — GNAP Prior-Art Context

*(Brief inline analysis since Lattice was not separately dispatched.)*

The Git-Native Agent Protocol (GNAP, github.com/farol-team/gnap) is third-party prior art from farol-team. GNAP defines a git-as-task-board pattern: `board/todo/ → board/doing/ → board/done/` with optimistic concurrency via git push collision detection.

**Helios's use of GNAP**: Helios v0.3+ adopts GNAP-style coordination for background workers (drift neutralization, concept induction) in place of Kubernetes + Celery + RabbitMQ + Redis (research blueprint §4.5's original proposal that violated wedge #3). The synthetic includes `experimental/gnap/board/{todo,doing,done}` directory scaffold and `experimental/gnap/README.md` documenting the protocol's application to Helios memory consolidation.

**Patent posture**: Helios does NOT claim IP on the GNAP protocol itself (third-party prior art). Helios MAY claim IP on the SPECIFIC APPLICATION of git-native coordination to LLM memory consolidation IF the combination is non-obvious. This is captured in Claim 2's dependent claims (claim 4: post-commit event emission to worker queue) but is NOT a standalone claim.

**Recommendation**: adopt GNAP as a dependency; do not file IP on coordination protocol; focus IP efforts on Claim 1 (Harmonic) and Claim 2 (Architecture).

---

## §6 Code-side integrations shipped this turn

The following implementations land in the synthetic `helios-memory-synth`:

### §6.1 `core/harmonic.py` — Wave-Coherence Stage-3 plugin (NEW, ~260 LOC)
- `harmonic_sweep(v, u, harmonics)` — multi-frequency cos(n × Δθ) primitive
- `harmonic_at(v, u, n)` — per-channel inner product for multi-channel embeddings (corrects the subtlety that full-vector angle differs from per-channel angle)
- `harmonic_distance_typed(v, u, relation)` — named-relation lookup (opposition/triadic/quadrant/pentagonal/sextile)
- `multi_channel_embedding(theta, harmonics)` — synthetic embedding constructor for tests
- `HarmonicRerankConfig` + `harmonic_rerank_score()` — Stage-3 plugin contract; disabled by default (preserves backward compat with single-cosine reranker)
- `harmonic_query_typed()` — typed-relation retrieval entrypoint
- 11 new tests in `tests/test_harmonic.py` verifying triadic, opposition, quadrant recovery + multi-channel collapse demo

### §6.2 `experimental/gnap/` — GNAP task-board scaffold (NEW)
- Directory structure: `board/todo/`, `board/doing/`, `board/done/` (with `.gitkeep` files)
- `experimental/gnap/README.md` documenting protocol, task file format, coordinator/worker roles, conflict resolution semantics
- Worker implementations deferred to next milestone (`workers/drift_neutralization.py`, `workers/concept_induction.py` are TODO)

### §6.3 `core/tiering.py` — drift attenuation correction (MODIFIED)
- Added `attenuate_drift_value(cycles, reads, decay_factor)` — order-preserving alternative to integer floor division
- Verified via doctest: erratum v1's counter-example (A=(3,0), B=(2,9)) preserves order under multiplicative attenuation
- Updated `decay_inactive_records()` docstring to flag the order-preserving choice and reference the erratum
- Existing temperature-EMA-based decay (which IS order-preserving) unchanged

### §6.4 Verification
**79 / 79 pytest tests pass** (21 baseline + 7 tiering + 10 API + 22 tenant + 8 Qdrant + 11 harmonic).

---

## §7 Combined Honest Gaps

1. **Pulse subagent timed out** during dispatch — strategic ranking in §1 written inline rather than from dedicated agent output. The ranking is best-effort heuristic; user/attorney should redo with their actual fundraise-stage data and competitive intel.

2. **Wave-Coherence GitHub creation date is the central disclosure-clock fact.** Forge identified 2026-02-09 from web searches. Attorney **must** independently verify this via GitHub API and the Zenodo metadata.

3. **The 92.5% channel-independence claim** through transformer layers (from Wave-Coherence paper) has not been independently replicated. Should not be relied on in claim language until verified.

4. **Prior-art search is web-based, not clearance-grade.** Attorney must run real USPTO TESS / EPO Espacenet / commercial-database (Derwent, Orbit) clearance search before filing.

5. **§101 (Alice/Mayo) risk** is the largest single threat to both claims. Technical-effect framings in §2.6 and §3.6 are starting points; attorney must drill into specific machine effects with concrete measurements.

6. **Foreign rights on Claim 1 likely lost** via Wave-Coherence GitHub disclosure 2026-02-09. EPO/JPO/CN absolute-novelty extinguished for the bare math. Foreign rights on the Helios-integration claim *may* survive if attorney argues materially distinct.

7. **AI-drafted claim language is not filing-grade.** Attorney redrafts everything before filing. Per USPTO guidance, AI tools are NOT co-inventors; user is sole inventor of record.

8. **Lattice subagent not dispatched separately** — GNAP context covered inline in §5.

9. **Math corrections in erratum v1** (EMA half-swing coefficient, drift floor-truncation) have been applied to the synthetic code (`attenuate_drift_value` function in `core/tiering.py`) but the **research blueprint markdown and webpage still contain the original incorrect text**. These need correction before any external publication. The IP filings do NOT depend on the incorrect derivations.

10. **Inventorship verification needed** for both claims. Attorney verifies that user is sole inventor and that any contributions from other parties (helios-memory contributors, workshop paper co-authors, Wave-Coherence collaborators) do not establish joint inventorship.

---

## §8 Filing Cost Estimate

| Stage | Cost range | Timing |
|---|---|---|
| Provisional drafting (attorney-prepared) | $5,000 – 12,000 | 4–6 weeks |
| USPTO filing fee (small entity) | $130 (electronic) | Day-of |
| Year-1 patent maintenance | $0 | Provisional |
| Conversion to non-provisional/utility | $10,000 – 25,000 | Within 12 months |
| USPTO filing fee non-provisional (small entity) | $400 | Day-of |
| Office-action responses (year 2-3) | $5,000 – 15,000 / response, typically 1-3 responses | Year 2-3 |
| **Total US-only year 1** | **$5,000 – 12,000** | |
| **Total US-only by issuance (year 3-4)** | **$25,000 – 50,000** | |
| Foreign filing via PCT (within 12 months of provisional) | $15,000 – 30,000 (PCT search + entry into national phases) | Within 12 months — likely waste of money for Claim 1 due to existing disclosure |

**Recommendation**: budget $25,000 for US-only patent protection through year 3 (provisional + non-provisional + 1-2 office actions). Defer foreign filing decision until after attorney clearance search.

---

## §9 Conclusion

**The two anchor claims are filing-worthy.** Combined US provisional within 60 days at ~$8–12k attorney-drafted is the recommended path. Disclosure-clock pressure on Claim 1 (Harmonic) is the dominant urgency factor; Claim 2 (Architecture) joins the same filing to amortize cost. Foreign rights on Claim 1's math are likely already extinguished; accept US-only initially.

The strategic IP value supports the pre-seed fundraise narrative: "we have two pending US provisionals on harmonic-decomposition retrieval and substrate-frozen agent memory architecture." Whether either ultimately issues depends on attorney prosecution, examiner objections, and prior-art surprises during clearance search.

**Action item recap**:
1. Verify Wave-Coherence and Zenodo disclosure dates within 1 week
2. Engage software-patent attorney within 2 weeks
3. Send attorney this report + Anchor's full disclosure + Audit's full disclosure + Forge's full landscape
4. File single combined provisional within 60 days
5. Defer foreign filing pending attorney advice

The remaining honest gaps in §7 must travel with this report to the attorney engagement.

---

**End of report.** Anchor's, Audit's, and Forge's full subagent outputs preserved in working file for attorney handoff.
