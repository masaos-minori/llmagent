# Supervise EventBus background tasks and clean up EventBus code

## Priority
Medium

## Summary
The TTL sweep task can stop without any signal, the NACK idempotency key is stored in a column with a different meaning, and the EventBus code has dead and duplicate items.

## Background
Filed from the consolidated ADR review task list `memo-issue.md` (package `ADRCHK2-M05`; merged from ADRCHK-M15, M18, L14 (review findings N51, N58 and round 3 Low findings)). The review's claims carry the evidence label `Documentation only` unless this issue marks them otherwise; the implementer MUST re-verify each claim against current source before changing anything.

## Problem
Claims come from the review (`Documentation only` until re-verified).

## Reason for Change
- The sweep task is not supervised: `authz_sweep_loop` catches only OSError and ValueError, so any other exception ends the task, and `/health` monitors only the DLQ task. If the sweep stops, expired grants stay active and nothing reports it, which is a security problem.
- A column is misused: the NACK idempotency key is stored through `last_nack_attempt`, and `consumer_delivery` has no foreign key to `events`.
- Dead and duplicate code remains: `_ENVELOPE_SCHEMA_PATH` is unused in `app.py`, `idx_events_seq` duplicates the primary key, the outbox comment states the wrong direction, `db_tools version` always returns 0, and `auth.py` imports `hashlib` twice and has two fingerprint helpers.

## Implementation Intent
- `/health` reports every background task the EventBus depends on, and a stopped task affects liveness.
- Column names state their purpose, and the schema carries no redundant index.
- No dead code remains.

## Target Files or Areas
- `scripts/eventbus/authz_ttl.py`
- `scripts/eventbus/health_route.py`
- `scripts/eventbus/app.py`
- `scripts/eventbus/ack_route.py`
- `scripts/eventbus/delivery_repo.py`
- `scripts/eventbus/schema.sql`
- `scripts/eventbus/db_tools.py`
- `scripts/eventbus/auth.py`
- `tests/eventbus/`

## Required Changes
- (no decision needed) Report the sweep task status and its last result and time in `/health`; a stopped task is a degraded reason and sets liveness to false, as for the DLQ task.
- (no decision needed) Remove `_ENVELOPE_SCHEMA_PATH`, the duplicate import, and the duplicate fingerprint helper; fix the outbox comment; remove or fix `db_tools version`.
- (after the data lifecycle decision) Add a dedicated idempotency column, decide on the foreign key, drop `idx_events_seq`, and update the fingerprint tests.

## Constraints
- Do not change `schema.sql` until the data lifecycle decision is recorded; a DDL change changes the schema fingerprint.
- Do not write, paraphrase, or simulate a maintainer approval statement. A change to an ADR decision, invariant, Blocking value, or authority edge needs an approval record in the same change (governance_01, governance_05).
- Follow the Current-Specification-Only policy: no migrations, aliases, shims, tolerant fallbacks, or history-style comments such as removed on or formerly.
- Change only the Target Files; if another file must change, stop and report it as a scope amendment.
- Keep code comments, log text, and documentation in English.
- Before editing, re-run the searches named in Acceptance Criteria. Other plans edit the same files; if a defect is already gone, record the evidence and skip that task.
- Do not edit generated files (`registry/manifests/*.yaml`, guarded blocks) by hand; regenerate with `tools/generate_reference_table.py` or `tools/generate_adr_authority.py`.

## Acceptance Criteria
- A test that makes the sweep raise RuntimeError shows `/health` returning 503 with a sweep reason.
- `uv run vulture scripts/eventbus --min-confidence 80` reports none of the listed items.
- After the schema task, the fingerprint tests pass.

## Testing Expectations
Tests under `tests/eventbus/` (failing first for the health case); vulture, ruff, mypy, bandit; `tools/check_db_separation.py` after schema work. Validation sequence: `rules/toolchain.md`; after any `docs/` edit also the checkers listed in `routing.md` Tools.

## Documentation Impact
Yes if `/health` fields change: the EventBus operations guide.

## Out of Scope
- Authorization model changes.
- Schema changes before the lifecycle decision.

## Dependencies
- `issues/20261117-123008_adrchk008_db-data-lifecycle.md` blocks the schema task (depends on).
- `issues/20261117-123002_adrchk002_eventbus-authz-model.md` edits `auth.py` and `authz_ttl.py`; fix the order with the owner.

## Unresolved Questions
- `scripts/eventbus/delivery_repo.py` was not reviewed; the NACK key storage is `Needs confirmation`.

## AI Implementation Instruction
- Do not change `schema.sql` until the data lifecycle decision is recorded.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261117-123017
- **Related target files**: `scripts/eventbus/authz_ttl.py`; `scripts/eventbus/health_route.py`; `scripts/eventbus/app.py`; `scripts/eventbus/ack_route.py`; `scripts/eventbus/delivery_repo.py`; `scripts/eventbus/schema.sql`; `scripts/eventbus/db_tools.py`; `scripts/eventbus/auth.py`; `tests/eventbus/`
