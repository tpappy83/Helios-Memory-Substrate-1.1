# Helios — Code Audit & Evolution Report

**Date:** 2026-05-16
**Auditor:** Code Agent (Hyperagent) + six opus subagents (Volt, Whirl, Spin, Forge, Quill, Glyph)
**Scope:** Two uploaded bundles representing earlier Helios lineages, evaluated against the current Python `helios-memory` repo and its locked architectural invariants.
**Mode:** Read-only audit. No file in `helios-memory` was modified.

---

## TL;DR

The uploaded files are not a competing Python implementation — they are **earlier Helios lineages** the user previously built:

1. **Helios v4.1 spec (original Python)** — at `attached_assets/helios_core_(faiss_ivf_&_zero_copy)_*.py`, 3219 lines, dataclass-based. Contains explicit formulas the current Python `helios-memory` is about to need for the v0.2 NEXT `core/tiering.py` work.
2. **Helios Core Node/TS port** — bulk of `helios-core.tar.gz`. Stack: Express + React + Drizzle + Postgres. Distributed as Windows `SETUP.EXE` (which explains `autorun.inf` + the two bundled DLLs).
3. **Helios Control Plane SDK** — the TS bundle. Orval-generated React SDK for a SEPARATE server (`@workspace/api-client-react`) with admin/governance domain types Shards/Policies/Alerts/AuditLog/DashboardStats.

The audit's verdict is **harvest the formulas and the multi-tenant primitive, reject everything that violates the three competitive wedges** (no vector DB, local-first single-binary EXE, dev-loop simplicity).

**Eight concrete patch files** were generated in `/agent/workspace/audit/patches/`. The headline ones (BLOCKING for v0.2 NEXT):

- `01_core_tiering.py` — Volt's Python module with the v4.1 formulas ported verbatim (temperature EMA, drift, reranker weights, promote/demote thresholds), collapsed from 4 tiers (HBM4/NVMe/SSD/Archive) to 2 (hot/cold).
- `02_schema_migration_v2.sql` — Quill's ALTER TABLE additions: tier, temperature, compression_cycles, read_count, last_accessed, namespace on `memory_records` + namespace on `chat_history` + an `audit_log` table.
- `03_db_migration_runner.py` — `PRAGMA user_version`-based migration plumbing for `core/db.py`.

**Three Windows binaries from the first batch are PARKED** — `autorun.inf` references a `SETUP.EXE` (previous Windows-installer distribution attempt), `concrt140.dll` is MSVC concurrency runtime, `clang_rt.asan_dynamic-i386.dll` is an AddressSanitizer DLL accidentally shipped from a debug build. No Helios architectural artifacts.

---

## What was actually in the upload

### First batch (helios-core.tar.gz, 411 KB)

A Node/TypeScript port of Helios v4.1, with the v4.1 Python source preserved alongside:

| Path | Purpose | Lines |
|---|---|---|
| `attached_assets/helios_core_(faiss_ivf_&_zero_copy)_*.py` | **Original Python v4.1 spec** (Colab-generated) | 3219 |
| `server/helios.ts` | TS port of the engine: StorageHierarchy, FAISS IVF, TieringEngine, RerankingEngine, QueryEngine, SemanticMemory | ~600 (22 KB) |
| `server/simulation.ts` | ML-powered tiering simulation | ~700 (22 KB) |
| `server/routes.ts` | ~20 REST endpoints under `/api/helios/*` and `/api/simulation/*` | ~500 (17 KB) |
| `server/storage.ts` | Drizzle DatabaseStorage class | ~150 |
| `shared/schema.ts` | 4 Drizzle tables (`simulationRuns`, `heliosObjects`, `semanticThreads`, `heliosQueryLog`) + zod schemas + TIER_CONSTANTS | 8 KB |
| `client/src/...` | React + Vite + TanStack Query + shadcn/ui + Tailwind dashboard with IVF heatmap, tier visualizer, reranker tuner | ~3 MB of node_modules-worth of UI |
| `replit.md` | Self-described as "real, dynamic AI-powered storage and memory architecture ported from the Python Helios v4.1 specification" | — |
| `autorun.inf` + DLLs | Windows installer media bundle | — |

Confirmed sandbox-clean: `python3 -m py_compile` on the v4.1 Python spec returned 0. Brace/paren balance is correct on all TypeScript files.

### Second batch (TS bundle — separate lineage)

An Orval v8.5.3-generated React SDK for "Helios Control Plane API" (OpenAPI 0.1.0):

| File | Role |
|---|---|
| `api.ts` (30 KB) | Auto-generated client functions: getShards, getShard, pinShard, getPolicies, createPolicy, alerts, audit log, stats, healthz |
| `api.schemas.ts` | Domain types: `Shard {tier, isPinned, status, tenant, cluster}`, `Policy {vectorWeight, recencyWeight, valueWeight}`, `Alert {severity, autonomousFix, primaryAction}`, `AuditLogEntry {shardId, action, reason}`, `DashboardStats {p95LatencyMs, baselineRecallPct, tcoSavingsPct}` |
| `custom-fetch.ts` | Bearer-token HTTP wrapper with `ApiError`/`ResponseParseError` typed errors and RFC 7807 problem+json support |
| `shard-preview.ts` | Hand-written extension: shards wrap tabular files (`filename`, `columns`, `previewRows`, `mediaCategory`) — a DuckDB-style preview |
| `package.json` | `@workspace/api-client-react`, peerDeps on `@tanstack/react-query` >= 5 and `react` >= 18 — monorepo workspace package |
| `scripts/post-merge.sh` | `pnpm --filter db push` — confirms a monorepo with a `db` workspace using Drizzle or Prisma |

Domain model implies this Helios was an **autonomous storage-tiering governance plane** sitting on top of the v4.1 engine: operators view shards, configure scoring policies, approve/dismiss autonomous-fix alerts, view audit log of pin/unpin actions. Notably absent: `/auth/login`, `/users`, `/api-keys`, `/tenants` — auth was bearer-token at the wire level with token acquisition out of band.

---

## Comparison to current `helios-memory` (memory-captured baseline)

| Concept | v4.1 Node port | Control Plane SDK | Current Helios | Verdict |
|---|---|---|---|---|
| **Language** | TypeScript | TypeScript | Python | KEEP current |
| **Backend** | Express + Drizzle + Postgres | Unknown (TS monorepo) | FastAPI + SQLite + raw schema.sql | KEEP current |
| **Frontend** | React + Vite + 50+ deps | (consumed by another React app) | Vanilla JS + Streamlit | KEEP current |
| **Retrieval** | FAISS IVF over 128-dim hashed vectors | (engine-internal, not exposed) | FTS5 + LLM rerank | **KEEP current** (wedge #2) |
| **Tiering** | IVF + temp EMA + drift, 4 tiers | Exposes shard.tier as enum | Not implemented yet (v0.2 NEXT) | **PORT FORMULAS**, collapse to 2 tiers |
| **Multi-tenancy** | namespace + region columns | tenant + cluster + ?tenant= filter | None (productization gap) | **PORT namespace** |
| **Audit log** | None | `audit_log` table, pin/unpin actions | None | **PORT minimal shape** |
| **Distribution** | Windows SETUP.EXE + DLLs | (web app, not bundled) | PyInstaller --onefile EXE | KEEP current |
| **Schema mgmt** | drizzle-kit push | drizzle-kit push (monorepo) | schema.sql + init_db.py greenfield | **ADD migrations machinery** |

---

## Subagent findings (compressed)

Each subagent's full output is at `/agent/workspace/audit/reports/subagent_*.md` (not generated; was returned inline). Key verdicts:

### Volt (Engine + v4.1 formulas)

**PATCH-WORTHY:** all five v4.1 constants (α=0.3 EMA, promote 0.65 / demote 0.35, drift `0.02 + 0.01·cycles + 0.001·reads`, reranker weights 0.55/0.20/0.10/0.10/0.05, recency `exp(-Δt/600s)`) port verbatim into `core/tiering.py`. The `sim` slot in the reranker formula is fed by current Helios's existing FTS5 BM25 score or `llm_rerank()` output — no vector math needed. Top-K feedback loop (v4.1 line 217) applies on each rerank pass.

**REJECT (wedge violation):** FAISS IVF, 128-dim feature-hash embedder, 4-tier quantization across HBM4/NVMe/SSD/Archive, PostgreSQL backing, numpy. The tier-bonus collapses to `{hot: 1.0, cold: 0.3}` without losing the signal.

### Whirl (REST API surfaces)

**PATCH-WORTHY:** namespace column threading on all routes (header `X-Namespace` taking precedence over `?namespace=` per Whirl), `PATCH /config/retrieval` for live reranker tuning (demo wedge), `latency_ms` in response bodies, `GET /stats` for introspection, `POST /memory/batch` with per-item error capture, `GET /memory/{id}` + `DELETE /memory/{id}` namespace-gated.

**REJECT:** Express middleware stack, Drizzle ORM, IStorage repository abstraction, simulation/log/history routes, IVF cluster introspection, region partitioning, header-trust as tenancy model, Vite-in-API-process, zod replacement of Pydantic.

Important honest note: v4.1's namespace pattern alone is NOT a tenancy story — v4.1 trusts any caller's claimed namespace because it's a local tool. For hosted Helios you still need a `tenants` table + `Depends(verify_key)` that maps API key → tenant → forces namespace. That's a separate PR after the namespace column lands.

### Spin (Frontend dashboard)

**PATCH-WORTHY (Streamlit/JS additions, ~140 LOC total):** reranker weight sliders + live Σ check + formula display, namespace selector text input, recall latency caption on chat responses, event log section in vanilla JS with one CSS keyframe rule (~50 LOC, no framer-motion needed).

**REJECT (wedge violation):** full React+Vite+wouter+shadcn adoption, TanStack Query (current architecture doesn't need it), IVF centroid heatmap (no FAISS in current Helios), TierVisualizer panel (defer until tiering data exists), full ConfigPanel sliders, cluster browser, framer-motion, lucide-react, Radix primitives.

### Forge (Infra + build + distribution)

**PATCH-WORTHY:** numbered SQL migration system (`migrations/NNN_*.sql` + `PRAGMA user_version`), `uvicorn --reload` / Streamlit `runOnSave` dev flag, `build.py` cross-platform replacement for `build.bat`/`build.sh`, tighter PyInstaller `--exclude-module` allowlist (pytest, mypy, matplotlib, numpy.tests), strict-env startup mode for prod.

**REJECT:** Drizzle ORM, PostgreSQL, Radix UI ecosystem, passport/session auth stack, Replit-specific Vite plugins, `autorun.inf` USB-stick gimmick (Windows disabled USB autorun in 2011 per MS10-046), NSIS/Inno installer (defer until non-technical users), ASan debug-build distribution flow (the bundled `clang_rt.asan_dynamic-i386.dll` was an accident, not a pattern).

### Quill (Schema + domain modeling)

**PATCH-WORTHY ALTER TABLEs:** `tier INTEGER DEFAULT 'cold'`, `temperature REAL DEFAULT 0.5`, `compression_cycles INTEGER DEFAULT 0`, `read_count INTEGER DEFAULT 0`, `last_accessed REAL`, `namespace TEXT DEFAULT 'default'` on `memory_records`; `namespace TEXT DEFAULT 'default'` on `chat_history`; three indexes (`tier`, `last_accessed`, `namespace`); `PRAGMA user_version = 2` migration via `core/db.py`.

**REJECT:** Drizzle ORM, `jsonb`/`serial`/`timestamp` Postgres types, `region` column, `vector_summary` column, `centroid_id` column, `helios_query_log` as a table (no UI consumes it), separate `semantic_threads` table (current per-turn `chat_history` is the right model for chat surfaces).

### Glyph (Control Plane SDK lineage)

**PATCH-WORTHY (for B2D pitch productization gap):** minimal `audit_log` table + `GET /audit` endpoint + `GET /events` alias for the frontend event log; per-resource `tenant`-as-namespace filter on resource queries; minimal `DashboardStats`-style `/stats` tile endpoint; `ApiError` / problem+json error taxonomy (already present in v4.1's custom-fetch.ts and worth porting to current Helios's error responses); pluggable `setAuthTokenGetter` indirection for whatever SDK Helios ships.

**SKIP (separate-product, out of scope):** Policy CRUD (the "Policy" in Control Plane is a tiering *scoring* policy, not RBAC — different problem), Shard pin/unpin lifecycle, alert approve/dismiss with `autonomousFix`, tier-color UI hint fields (`borderColor`/`iconBg`), the shard-preview tabular ingestion model (would be a different product).

---

## Patch set (all proposal-only)

The eight files in `/agent/workspace/audit/patches/`:

| # | File | Target | LOC | Severity |
|---|---|---|---|---|
| 00 | `00_README.md` | (index) | — | — |
| 01 | `01_core_tiering.py` | NEW `core/tiering.py` | ~230 | **BLOCKING** for v0.2 NEXT |
| 02 | `02_schema_migration_v2.sql` | NEW `migrations/002_*.sql` | ~40 | **BLOCKING** for v0.2 NEXT |
| 03 | `03_db_migration_runner.py` | APPEND to `core/db.py` | ~60 | **BLOCKING** for v0.2 NEXT |
| 04 | `04_api_patches.py` | SPLICE into `api.py` | ~210 | IMPORTANT |
| 05 | `05_app_streamlit_reranker.py` | APPEND to `app.py` sidebar | ~60 | NICE |
| 06 | `06_frontend_event_log.js_css` | APPEND to `frontend/app.js`+`styles.css` | ~80 | NICE |
| 07 | `07_build_py.py` | NEW `build.py` replacing `.bat`/`.sh` | ~110 | NICE |
| 08 | `08_audit_log_endpoint.py` | NEW `core/audit.py` + SPLICE into `api.py` | ~150 | IMPORTANT |

Sandbox verification passed:
- `python3 -m py_compile` on all `.py` patches: clean
- Doctests in `01_core_tiering.py`: 4/4 attempted, 0 failures (one fixed mid-flight: float-representation drift on `0.5 * 0.3 + 0.5 * 0.7 = 0.6499999999999999`)
- AST parse on mixed-content patches: clean
- Brace/paren balance on all v4.1/TS uploaded files: clean (one false positive in `custom-fetch.ts` from braces inside string literals)

---

## Ranked recommendations (action list)

### BLOCKING — for v0.2 NEXT (`core/tiering.py`) to ship credibly

1. **Apply patch 02** (schema migration v2) — adds the six new columns + `audit_log` table. Affects two tables. FTS5 trigger contract is unaffected because none of the new columns are FTS-indexed.
2. **Apply patch 03** (migration runner) — adds `PRAGMA user_version`-based migration plumbing to `core/db.py`. The existing `init_schema()` call chain stays compatible with both fresh installs and existing user DBs.
3. **Apply patch 01** (`core/tiering.py`) — the new module, ~230 lines, pure-stdlib, reads existing memory_records via `core.db.connect()`.
4. **Wire `tiering.rerank_candidates()` into `core.llm.query_memories`** — replace or wrap the existing post-LLM-rerank step. This is the integration point that turns the new module into observable behavior.
5. **Add 6 tests for `core/tiering.py`** — one each for the pure functions (drift, recency, EMA, final score, tier bonus) + one DB-backed test for `apply_tiering_decision` round-trip. Run with the existing pytest infra.

### IMPORTANT — for B2D productization pitch credibility

6. **Apply patch 08** (audit log + `/events`) — closes the "no audit trail" gap that any hosted-API customer will ask about. Minimal shape; no auth dependency.
7. **Apply patch 04** (additive API routes) — namespace threading + `GET /stats` + `PATCH /config/retrieval` + `POST /memory/batch` + namespace-gated `GET`/`DELETE /memory/{id}`. The namespace column is the multi-tenant primitive; auth+tenants table is a separate later PR.
8. **Strip aspirational HNSW/sqlite-vss copy from README + schema.sql comments** — per the known doc-code drift (memory: "Helios codebase has known copy/code drift"). Either build vector or strip the mentions; the audit confirms FTS5+LLM-rerank is the defensible architecture and one of the wedges.

### NICE — for investor demo polish and dev DX

9. **Apply patches 05 + 06** — Streamlit reranker tuning + frontend event log. ~140 LOC total. The event log is best paired with patch 08 since it consumes `/events`.
10. **Apply patch 07** (`build.py`) — replaces `build.bat`/`build.sh` with one cross-platform Python build script with `--exclude-module` allowlist that shrinks the EXE.
11. **Add `uvicorn --reload` to `run_api.sh`/`.bat` behind a `--dev` flag** (Forge).
12. **Add `latency_ms` to all response bodies and SSE done events** (Whirl — currently the chat stream emits a `done` event without timings).

### REJECT — preserves wedges

13. FAISS IVF, vector DB dependency, PostgreSQL backing, React+Vite frontend, Drizzle ORM, 4-tier quantization across HBM4/NVMe/SSD/Archive, autorun.inf, NSIS installer. These are all explicitly out-of-scope.

---

## Honest gaps

- I do NOT have the current `helios-memory` source in this sandbox. All patches are written against the memory-captured architecture, which is a snapshot. If you've shipped commits since 2026-05-04 that touch `core/db.py`, `core/memory.py`, `core/llm.py`, `api.py`, or `app.py`, the patches may collide. Eyeball each before applying.
- The patches assume `memory_records.id` is `TEXT` (per memory). If actual is `INTEGER`, change the parameter types in patches 01, 04, 08.
- The patches assume `core.db.connect()` returns a context-managed `sqlite3.Connection` that auto-commits on context exit. If actual usage requires `cx.commit()` calls, add them to the patches.
- The audit baseline is one user-supplied snapshot of memory state. Memory entries may have drifted from reality. Treat the baseline as authoritative-but-stale; verify before merging.
- The three Windows binaries from the first batch were NOT analyzed in depth. `autorun.inf` is the entire 45-byte file (`[autorun]\nOPEN=SETUP.EXE\nICON=SETUP.EXE,0\n`); the two DLLs are standard Windows runtime libraries from a SETUP.EXE distribution that wasn't included.
- The "Helios Control Plane API" server (TS bundle's target) is NOT in the upload — I have the client SDK only. Backend stack, auth mechanism, and shard storage semantics are inferred from the SDK shape with stated uncertainty.
- The v4.1 Python source is 3219 lines; I read the first ~250 and confirmed the canonical formula constants. Later parts of the notebook may include alternative tuning passes I did not verify. Recommendation: port the constants as documented, instrument, tune on real workloads later.
- No test coverage was measured on the uploaded codebases (no `tests/` dir present in either bundle).
- I cannot run Docker, PyInstaller, `tsc`, or `npm install` in this sandbox. The infra-side recommendations are static analysis.

---

## Build status after this audit

— Helios Build Status —
**Phase:** Functional Multi-Surface Prototype with Streaming + Self-Contained EXE Bundling — UNCHANGED (no code modified in `helios-memory`)
**Completed:** Audit of two uploaded earlier-lineage bundles; six-subagent parallel analysis (Volt, Whirl, Spin, Forge, Quill, Glyph); sandbox verification; 8 patch files generated (3 BLOCKING for v0.2 NEXT, 3 IMPORTANT, 2 NICE); audit report + webpage shipped as deliverables.
**Pending (Helios-side, unchanged):** `core/tiering.py` (v0.2 NEXT — now patch-ready), durable SQL beyond local SQLite, retrieval API formalization, decay worker (scaffold in patch 01), DP infrastructure (v0.3), `core/induction.py` (v0.4), multi-tenant + API-key issuance (patch 04 + 08 close part of the gap; auth is still TODO), structured SSE error events.
**Pending (audit-side):** user decides which patches to apply.
**Risks:** Memory baseline is 2026-05-04 — patches may collide with newer commits; verify before applying.
