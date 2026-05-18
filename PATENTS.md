# PATENTS

> **PUBLIC PATENT-PENDING NOTICE.**
> Travis Papenbrock asserts inventorship of the methods, systems, and
> architectures described in this repository, including but not limited to
> the two anchor inventions enumerated below. Patent applications are in
> preparation. Licensing inquiries: `tpapenb@iu.edu`.

---

## Anchor Inventions

### 1. Harmonic Vector Decomposition Retrieval Method

A method for retrieving vectors from a database by computing harmonic-band
similarity scores `cos(n × Δθ)` for multiple frequencies n in place of
single-scalar cosine similarity, returning typed-similarity output that
scalar cosine collapses. Integrated into the Helios CRM 6-stage workflow as
a Stage-3 (Read/Rerank) plugin. See `core/harmonic.py` for the reference
implementation and `tests/test_harmonic.py` for the verification suite.

### 2. Substrate-Frozen Memory Architecture with Retrospective Concept Induction and Prompt-Compiled Skills

A three-layer memory backend architecture for LLM-mediated agentic systems
comprising (a) immutable substrate, (b) retrospective asynchronous concept
induction, and (c) prompt-compiled skill templates. The joint commitment
to all three architectural disciplines is the load-bearing claim element.
See `core/memory.py`, `core/audit.py`, `core/tenants.py`, `schema.sql`,
`migrations/`, and `docs/research/helios-ip-claimables-v1.md` for the full
technical disclosure.

---

## Public Disclosure Timeline

See `INVENTORSHIP_AND_PRIOR_ART.md` §4 for the full disclosure record. The
commit timestamp of this file serves as a primary documentary record.

---

## Licensing

This repository is licensed under the **PolyForm Noncommercial License 1.0.0**
with the **Commons Clause** condition (see `LICENSE`).

- **Non-commercial use** (research, personal projects, education,
  open-source) is freely permitted under the license terms.
- **Commercial use** — including selling, hosting as a service, or
  incorporating into a commercial product — is **prohibited** without a
  separate commercial license from Travis Papenbrock.

Patent rights, where granted by a competent patent office on the asserted
inventions, are reserved by the inventor independent of the source code
license. Use of source code under the PolyForm Noncommercial License does
not convey any patent license.

For commercial licensing or patent licensing inquiries, contact:
`tpapenb@iu.edu`

---

## Legal Caveat

This document is a public notice of patent-pending status. It is NOT a
filed patent application, NOT a legal opinion, and does NOT establish
patent rights on its own. Patent rights arise only from filed applications
evaluated and granted under applicable jurisdiction's law.
