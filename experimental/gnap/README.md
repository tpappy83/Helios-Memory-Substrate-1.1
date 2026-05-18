# Helios — GNAP-Style Background Worker Coordination

**Status:** Experimental — scaffolds GNAP (Git-Native Agent Protocol) coordination for Helios background workers per the user's design directive.

**Reference:** [GNAP spec](https://github.com/farol-team/gnap) by farol-team.

## Why this directory exists

The Helios v0.3+ research blueprint §4.5 originally proposed Kubernetes + Celery + RabbitMQ + Redis for the background worker fleet (concept induction, drift neutralization, audit log processing). User audit-feedback called this out: it contradicts Helios's wedge #3 (dev-loop simplicity) and wedge #1 (local-first single-binary).

GNAP's text-based task board offers a zero-infrastructure alternative:

```
board/todo/   ← coordinator (or any agent) creates task files
board/doing/  ← worker claims by moving the file
board/done/   ← worker commits results by moving the file
```

Background workers (drift neutralization, concept induction) poll `board/todo/`, move claimed tasks to `board/doing/`, persist results, and finally move to `board/done/`. Git history provides the audit trail.

**Wedge preservation:** zero new infrastructure beyond a git repo. Local-first single-binary deployment unaffected. Optional: when a Helios deployment grows beyond a single machine, the same task-board protocol works across machines via shared git remote.

## Directory layout

```
experimental/gnap/
├── README.md                  ← this file
├── board/                     ← task board root
│   ├── todo/                  ← pending tasks
│   ├── doing/                 ← claimed/in-flight tasks
│   └── done/                  ← completed tasks
└── workers/                   ← worker implementations (next milestone)
    ├── drift_neutralization.py
    └── concept_induction.py
```

## Task file format

Each task is a markdown file with frontmatter. Filename includes a UUID for uniqueness.

```yaml
---
task_id: drift-neutralize-{ISO-8601-timestamp}
worker_class: drift_neutralization
created_at: 2026-05-17T22:00:00Z
namespace: default
priority: normal
inputs:
  cutoff_seconds: 86400
  threshold: 0.5
---

# Drift Neutralization — {date}

Apply Strategy A (counter halving with float attenuation; NOT integer floor
division — see erratum v1) to records with drift > 0.5 last accessed before
2026-05-16.
```

## Coordination protocol (simplified)

**Coordinator (helios scheduler, runs periodically e.g. via cron or systemd timer):**
1. Generate task file (e.g., daily drift sweep at 03:00 ET)
2. `git add experimental/gnap/board/todo/<task-id>.md`
3. `git commit -m "task: create <task-id>"`
4. `git push` (if remote)

**Worker (drift_neutralization daemon):**
1. Poll `experimental/gnap/board/todo/` (filesystem or `git fetch` then `git ls-files`)
2. Pick a task matching its `worker_class`
3. Atomic move to `board/doing/`: `git mv` + commit + push
4. Execute the work (e.g., `core.tiering.decay_inactive_records(stale_seconds=86400)`)
5. Append results to the task file's body
6. Move to `board/done/`: `git mv` + commit + push

**Conflict resolution:** two workers claiming the same task → push collision → second worker fetches, sees task already moved, picks a different task. Optimistic concurrency via git.

## What's NOT in this scaffold

- The actual worker implementations (next milestone)
- A scheduler/coordinator daemon (defer to systemd timer + cron in deployment)
- Git remote configuration (depends on user's deployment topology)
- Auth/RBAC on the task board (single-tenant local-first doesn't need it; multi-tenant deployment uses git's existing access control)

## IP context

The git-native task board pattern itself is GNAP prior art (third-party, farol-team). Helios does NOT claim IP on the protocol. Helios MAY claim IP on the specific application to LLM memory consolidation if the combination is non-obvious. See `reports/helios-claim-2-architecture-disclosure.md` for the architecture claim that includes worker coordination as one element.

## Honest gaps

- Git operations have non-trivial latency (clone, push, fetch). For high-frequency tasks (sub-second), GNAP is the wrong primitive. For Helios's hourly/daily background work, latency is fine.
- Task file format above is provisional. GNAP spec may have a different canonical schema.
- Git history grows unboundedly. Periodic `git gc` or branch rotation needed at scale.
- No retry semantics built in. Failed tasks stay in `doing/` until manually rescued.
