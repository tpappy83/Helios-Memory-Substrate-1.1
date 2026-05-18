[![Build Status](https://github.com/tpappy83/Helios-Memory-Substrate-1.1/actions/workflows/main.yml/badge.svg)](https://github.com/tpappy83/Helios-Memory-Substrate-1.1/actions/workflows/main.yml) [![License](https://img.shields.io/github/license/tpappy83/Helios-Memory-Substrate-1.1.svg)](LICENSE) [![Issues](https://img.shields.io/github/issues/tpappy83/Helios-Memory-Substrate-1.1.svg)](https://github.com/tpappy83/Helios-Memory-Substrate-1.1/issues) [![Stars](https://img.shields.io/github/stars/tpappy83/Helios-Memory-Substrate-1.1.svg)](https://github.com/tpappy83/Helios-Memory-Substrate-1.1/stargazers)

# Helios CRM — Cognitive Resource Manager for LLM Memory

> **Patent Pending.** This repository implements inventions on which patent
> applications are being prepared. See [PATENTS.md](PATENTS.md) and
> [INVENTORSHIP_AND_PRIOR_ART.md](INVENTORSHIP_AND_PRIOR_ART.md). Source code
> is licensed under PolyForm Noncommercial 1.0.0 with Commons Clause; patent
> rights are reserved independently. Commercial licensing: `tpapenb@iu.edu`.

**Helios CRM** is a Cognitive Resource Manager for Large Language Model
memory: a disciplined three-layer architecture that manages raw memory
records, retrospectively-induced concepts, and prompt-compiled skill templates
for LLM-mediated agentic systems. The acronym "CRM" is repurposed for the
AI/cognitive layer to give the product positioning recognition value while
clearly distinguishing it from the legacy customer-relationship-management
category.

## What Helios Solves

LLMs need memory systems that behave like cognition, not storage.

Existing AI memory backends (Mem0, Letta, Zep, LangMem, MemGPT, A-MEM)
collapse cognitive abstractions into mutable in-place edits, lose audit
trails, and use single-scalar cosine similarity that discards structured
relationships between memories. Helios is built around three architectural
commitments not jointly present in any surveyed prior system:

1. **Immutable substrate.** Raw memory records are append-only post-commit.
   No evolve-on-write. Logical revisions create new versioned records linked
   by `prior_record_id`; the original is never overwritten. Provides bit-exact
   replay reproducibility and complete audit trail.

2. **Retrospective concept induction.** An asynchronous worker reads the
   frozen substrate, clusters records by content similarity + entity overlap
   + temporal proximity, calls an LLM to label each cluster, and persists
   the induced concept to a separate `concept_records` table. Induction
   happens AFTER, never concurrent with, substrate write. Concept revisions
   create new concept rows; prior concepts remain queryable for reproducibility.

3. **Prompt-compiled skills.** A skill is a parameterized text fragment
   bound to an induced concept. At rerank or classify time, applicable
   skills are compiled directly into the LLM system prompt — not executed
   as code, not invoked as tool calls. The skill IS the prompt fragment.
   Enables single-call rerank with concept-specific relevance biasing.

Additional technical contributions disclosed in this repository include
**harmonic vector decomposition** for typed-similarity retrieval
(`core/harmonic.py`) and **per-tenant cryptographic shred via DEK
destruction** for GDPR Article 17 compliance by construction.

## Architecture Overview

### Stage 1 — Ingest
Capture incoming message, payload metadata, and namespace scope. See
`api.py` `_resolve_namespace` / `_require_tenant` dependencies.

### Stage 2 — Score
LLM classification into one of five fixed memory types (`event`, `state`,
`summary`, `decision`, `observation`) enforced via SQL CHECK constraint.
See `core/llm.py` `llm_classify`.

### Stage 3 — Read
Candidate generation (FTS5 keyword + LLM rerank) optionally augmented by
the **harmonic decomposition plugin** (`core/harmonic.py`) for typed-
similarity queries. Tier-aware reranker formula combines similarity,
importance, recency, tier bonus, and (negated) drift.

### Stage 4 — Modify
Temperature EMA feedback loop over Top-K retrieval results. Uses Schmitt-
hysteresis thresholds (0.70 promote / 0.30 demote) for cluster-rejection
stability. Class-weighted drift multiplier preserves decision-class recall
invariantly.

### Stage 5 — Write
Database serialization and state insertion into the immutable substrate
`memory_records` table. See `core/memory.py` `write_memory`.

### Stage 6 — Store
Placement execution, default tiering assignment, audit log generation via
`core/audit.py`. Background workers (drift neutralization, concept induction)
coordinate via git-native task board (see `experimental/gnap/`).

## Key Files

| Path | Purpose |
|---|---|
| `schema.sql` | Canonical schema v3 with substrate + audit + tenants + apikeys |
| `core/memory.py` | Memory record CRUD with immutability discipline |
| `core/llm.py` | LLM client + classify + rerank + chat streaming |
| `core/tiering.py` | Temperature EMA + class-weighted drift + adaptive recency |
| `core/harmonic.py` | Harmonic vector decomposition Stage-3 plugin |
| `core/audit.py` | Audit log with actor + namespace + timestamp + content |
| `core/tenants.py` | Multi-tenant control plane with API key auth |
| `core/qdrant_client.py` | Vector store SDK with tenant payload partitioning |
| `api.py` | FastAPI routes with auth, tenants, streaming chat |
| `app.py` | Streamlit UI |
| `frontend/` | Browser-direct pipeline demo with localStorage persistence |
| `experimental/gnap/` | Git-native task board for background workers |
| `migrations/` | Schema migrations (v1→v2→v3) |
| `tests/` | 79+ pytest tests covering all layers |
| `docs/research/` | IP-claimables report, paper revisions, blueprint, errata |

## Installation

```bash
git clone https://github.com/tpappy83/Helios-Memory-Substrate-1.1
cd Helios-Memory-Substrate-1.1
pip install -r requirements.txt
cp .env.example .env
# Edit .env to set OPENROUTER_API_KEY (free tier at openrouter.ai/keys)
python init_db.py
uvicorn api:app --port 8000
```

Open `http://localhost:8000/docs` for the OpenAPI surface, or
`http://localhost:8000/ui/` for the bundled static chat UI.

## Testing

Helios uses pytest:

```bash
pip install -r requirements.txt
python -m pytest -v
```

Current suite: 79 tests covering core, API, tenants, tiering, harmonic
decomposition, Qdrant payload partitioning, and database schema migrations.

## License

This project is licensed under the **PolyForm Noncommercial License 1.0.0**
with the **Commons Clause** condition.

- **Non-commercial use** (research, personal projects, education, open-source)
  is freely permitted.
- **Commercial use** — including selling, hosting as a service, or
  incorporating into a commercial product — is **prohibited** without a
  separate commercial license from Travis Papenbrock.

**Patent rights are reserved independently of the source code license.** Use
of source code under PolyForm Noncommercial does NOT convey any patent
license on the asserted inventions. See [PATENTS.md](PATENTS.md) and
[INVENTORSHIP_AND_PRIOR_ART.md](INVENTORSHIP_AND_PRIOR_ART.md).

See [LICENSE](LICENSE) for the full source-code license terms. To inquire
about a commercial license or patent license, contact: `tpapenb@iu.edu`.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines. Contributors must
acknowledge that all contributions are subject to PolyForm Noncommercial
license terms and that patent rights on novel inventive contributions remain
with the original inventor or are subject to a written assignment agreement.

## Security

See [SECURITY.md](SECURITY.md) for vulnerability reporting instructions.

## Roadmap

See [ROADMAP.md](ROADMAP.md) for planned milestones.

## Communication

For questions or collaboration proposals: `tpapenb@iu.edu`
