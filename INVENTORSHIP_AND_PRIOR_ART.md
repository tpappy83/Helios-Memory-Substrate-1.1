# Inventorship and Prior Art Anchor

> **THIS COMMIT IS A TIMESTAMPED PUBLIC PRIOR-ART RECORD.**
> The public timestamp on this commit, signed by GitHub on the date of merge,
> serves as evidence that the inventor named below had reduced to practice the
> inventions enumerated in §3 by that date. Combined with the source code
> changes shipped in this commit, it constitutes prior-art evidence sufficient
> to anchor priority claims for any subsequent patent filings on the named
> inventions.

---

## §1 — Sole Inventor

**Travis Papenbrock**
GitHub: [`@tpappy83`](https://github.com/tpappy83) · Email: `tpapenb@iu.edu`
Affiliation: independent inventor; founder of the Helios CRM project.

No co-inventors. AI tools (including but not limited to Anthropic's Claude
models) were used as drafting and analysis assistance. Per USPTO 2024
guidance (89 Fed. Reg. 10,043, Feb. 13, 2024), AI tools are NOT co-inventors;
significant human contribution to conception establishes sole human inventorship.
Inventor retains contemporaneous notes and conversation records demonstrating
human conception of each invention.

---

## §2 — What Helios Is

**Helios CRM — Cognitive Resource Manager for LLM Memory.**

A memory backend architecture for large-language-model agentic systems that
manages cognitive resources (raw memory records, induced concepts, callable
skill templates) across a disciplined three-layer architecture. The "CRM"
acronym is repurposed for the AI/cognitive layer to give the product positioning
recognition value while clearly distinguishing it from the legacy customer-
relationship-management category.

---

## §3 — Inventions Asserted in This Commit

### Claim 1 — Harmonic Vector Decomposition Retrieval Method

**One-sentence summary:** A method for retrieving vectors from a database by
computing harmonic-band similarity scores `cos(n × Δθ)` for multiple
frequencies n in place of single-scalar cosine similarity, returning typed-
similarity output (opposition, triadic, quadrant, pentagonal, sextile) that
scalar cosine collapses.

**Conception date:** February 9, 2026 (date of first public commit to
`github.com/atech-hub/Wave-Coherence-as-a-Computational-Primitive`).

**Reduction to practice in this repository:** see `core/harmonic.py` — the
Stage-3 plugin integration of the harmonic decomposition primitive into the
Helios 6-stage workflow. Verified by `tests/test_harmonic.py` (11 tests passing
including the central 12-entity multi-channel cosine-collapse demonstration).

**Closest prior art and how this invention distinguishes:** see
`docs/research/helios-ip-claimables-v1.md` §2.5 and §4 for full landscape.
The bare math operator `cos(n × Δθ)` is the inventor's own pre-existing
public disclosure (Wave-Coherence repo) and is the §102(b)(1) starting point
for the US 12-month grace clock. The patentable element claimed here is the
integration into the LLM-mediated retrieval pipeline: harmonic-band scoring
as Stage-3 plugin, multi-tenant payload partitioning, browser-direct
embodiment, and the typed-similarity query pattern.

**Disclosure clock:** US 35 U.S.C. § 102(b)(1) one-year grace running from
2026-02-09. Filing deadline to preserve US rights: 2027-02-09. Foreign
absolute-novelty rights (EPO, JPO, CNIPA) likely already extinguished for the
bare math; integration claim may survive subject to attorney evaluation.

### Claim 2 — Substrate-Frozen Memory Architecture with Retrospective Concept Induction and Prompt-Compiled Skills

**One-sentence summary:** A memory backend architecture for LLM-mediated
agentic systems comprising three architecturally-disciplined layers — (a) an
immutable substrate of memory records frozen post-commit, (b) retrospective
asynchronous concept induction via clustering plus LLM labeling over the
frozen substrate, and (c) callable skill templates compiled as parameterized
text fragments directly into LLM rerank or classify system prompts — wherein
the joint commitment to all three disciplines provides reproducibility, audit
trail, skill template stability under concept evolution, and cryptographic
shred-ability by per-tenant DEK destruction.

**Conception date:** May 9, 2026 (Helios workshop paper draft v1 conception
of the substrate→concepts→indexes→skills thesis).

**Reduction to practice in this repository:**
- Immutable substrate layer — `schema.sql` (memory_records with CHECK on five
  fixed types), `core/memory.py` (append-only write path), `core/audit.py`
  (paired audit log).
- Retrospective concept induction — proposed in `docs/research/helios-research-blueprint.md`
  §4.3 and §4.4; scaffold in `experimental/gnap/README.md` (worker
  coordination via git-native task board).
- Prompt-compiled skills — proposed in research blueprint §4.4; integration
  hook points in `core/llm.py` (`_build_chat_messages` would compose skill
  template fragments at rerank/classify time in production).
- Tenant isolation — `core/tenants.py`, `migrations/003_tenants_apikeys_v3.sql`,
  `api.py` `_require_tenant` dependency forcing `namespace = tenant_id`.

**Joint-commitment novelty:** the three layers individually have prior art
(Datomic and Soar EpMem for immutable substrate; GraphRAG and A-MEM for
retrospective induction; ExpeL and Voyager for prompt-compiled skills);
no surveyed system commits to all three jointly. The joint commitment is
the load-bearing claim element.

**Disclosure clock:** Individual layers publicly disclosed via the
`Helios-Memory-Substrate-1.1` README and the v0.1 substrate code on this
repository; joint commitment NOT yet publicly disclosed as a coherent
invention prior to this commit. Filing deadline: before NeurIPS 2026
workshop paper publication (deadline 2026-08-29).

---

## §4 — Supporting Public Disclosures (Inventor's Own Prior Art)

| Disclosure | URL | Date | Affects |
|---|---|---|---|
| Wave-Coherence as Computational Primitive | `github.com/atech-hub/Wave-Coherence-as-a-Computational-Primitive` | 2026-02-09 | Claim 1 math primitive |
| Wave-Coherence Zenodo preprint | DOI `10.5281/zenodo.18607190` | (verify metadata) | Claim 1 math primitive |
| Helios-Memory-Substrate-1.1 initial scaffold | this repository | (existing commit history) | Claim 2 substrate concept |
| Helios workshop paper draft v1 | private | 2026-05-09 | Claim 2 architecture (not yet public) |
| Helios research blueprint webpage | published artifact | 2026-05-16 | Both claims (conceptual disclosure) |
| THIS COMMIT | this commit | (commit timestamp) | Anchor for joint commitment & integration claims |

---

## §5 — Supporting Documents in This Repository

- `docs/research/helios-ip-claimables-v1.md` — strategic IP filing report with
  prior-art landscape, claim drafts, disclosure-clock forensic, and filing-cost
  estimates. Combines outputs of four parallel opus research subagents
  (Anchor, Audit, Forge, plus inline Pulse synthesis).
- `docs/research/helios-paper-section-2-revision.md` — revised Related Work
  section for the NeurIPS 2026 workshop paper, distinguishing Helios's joint
  commitment against A-MEM, Voyager, CMA, MemGPT, GraphRAG.
- `docs/research/helios-backports-falsifiability-appendix.md` — five
  wedge-preserving math backports framed as claimed, falsifiable, pilot-
  proposed (per published-science discipline).
- `docs/research/helios-research-blueprint.md` — the unconstrained v0.3+
  architectural blueprint with embedded prior-art map.
- `docs/research/helios-research-blueprint-erratum-v1.md` — corrections to
  two math errors in the original blueprint (EMA half-swing coefficient;
  drift floor-truncation order flip). Surfaced and corrected during the IP
  research pass.
- `docs/research/helios-audit-applied.md` — application notes for the v0.3
  multi-tenant + Wave-Coherence + GNAP integration work.

---

## §6 — Legal Caveat

This document is technical-disclosure-grade evidence prepared by the inventor
for use by a patent attorney. It is NOT legal advice, NOT a filed patent
application, and does NOT establish patent rights on its own. Patent rights
arise only from filed applications evaluated and granted under applicable
jurisdiction's law. The inventor will engage a registered patent attorney to
evaluate, redraft, and prosecute claims arising from the inventions disclosed
here. Public timestamping via this GitHub commit serves only as evidence of
the date of reduction to practice; it does not constitute filing.

---

## §7 — Commit Provenance

This INVENTORSHIP_AND_PRIOR_ART.md document, together with the substantive
code shipped in the same commit, establishes the date on which the inventor
asserts reduction to practice for the inventions in §3. The commit SHA
serves as the canonical timestamp.

For verification:
```
git log --format='%H %ci %s' INVENTORSHIP_AND_PRIOR_ART.md
git show <SHA>:INVENTORSHIP_AND_PRIOR_ART.md
```

For any subsequent patent prosecution, attorneys may rely on the GitHub-signed
timestamp of this commit as a primary documentary record under 35 U.S.C. § 102(b)(1).
