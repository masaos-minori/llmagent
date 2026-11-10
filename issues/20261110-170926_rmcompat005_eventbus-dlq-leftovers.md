# Remove unreachable and redundant EventBus DLQ code, fields, and names

## Priority
Medium

## Summary
Remove the DLQ code that can no longer run (unused `deadletter_dir` parameters, an unreachable `OSError` handler), the result fields and columns that repeat other data, and the old names and private-attribute access in the EventBus DLQ modules, so each fact is stored and returned once.

## Background
- Source: `memo-issue.md` item H-08 (consolidated version), re-checked against current source on 2026-11-10.
- `Explicit in code`, in `scripts/eventbus/dlq.py`: `_shared_promote`, `_shared_promote_single`, and the public wrappers (`promote_single`, `sweep_orphans`) take `deadletter_dir`, and the docstrings say it is "kept for call-site signature stability" and unused; promotion is a database-only transaction that records a `dlq_outbox` row, and file generation belongs to the outbox worker. `reconcile_missing_dlq_files` does use `deadletter_dir`, so the setting itself stays.
- `Strongly implied by code`: the `/nack` handler in `scripts/eventbus/ack_route.py` wraps `is_promotable()` and `promote_single()` in `except OSError` and logs "deferred to sweep", but both functions touch only SQLite, so the handler is unreachable; `docs/24_eventbus/eventbus_12_ack_nack_endpoints.md` still lists "Initial NACK, inline DLQ file write failed" in its state table.
- `Explicit in code`: `RequeueResult` in `scripts/eventbus/dlq_repo.py` carries `status` plus `original_event_exists` and `already_redelivered`, which are fully determined by `status`; `scripts/eventbus/dlq_route.py` branches on `status` only.
- `Strongly implied by code`: `events.dlq_requeue_count` can only be 0 or 1, because the schema allows one redelivery descendant per original (unique index), and `redelivered_from` already records the same fact; `/dlq` returns the count through `scripts/eventbus/event_repo.py`. `events.consumer_id` has no reader in `scripts/eventbus/` (search found none; the only use of the name near these modules is an empty string passed in `dlq_route.py`).
- `Explicit in code`: `scripts/eventbus/_constants.py` defines `_COL_REDISTRIBUTED_FROM = "redelivered_from"` (name does not match the column); `scripts/eventbus/route_helpers.py` reads the private attribute `counter._name` in `get_counter_value` and starts with `# /usr/bin/env python3` (missing `!`).
- Refuted memo claims: every `ERR_*` constant in `route_helpers.py`, including `ERR_EVENT_IN_DLQ` and `ERR_CONSUMER_ALREADY_CONNECTED`, has a user outside that module; `_constants.py` contains one "Shared column constants" comment, not a duplicate.

## Problem
- Parameters kept only for signature stability suggest that DLQ promotion still writes files; an unreachable error handler and a state-table row document a failure that cannot happen.
- Redundant fields and columns can disagree when one is updated and the other is not, producing contradictory API output.
- A constant named "redistributed" for a column named "redelivered" and a private-attribute read (breaks on a client-library upgrade) are leftovers that mislead or break silently.

## Reason for Change
- The current-only policy (`compatrm001`) forbids signature-stability shims and old names. No external deadline; nothing observed is failing today.

## Implementation Intent
- DLQ code contains only reachable behavior, each fact is stored and returned once, and names match the schema.
- Keep the `deadletter_dir` setting and the outbox worker, reconcile, and archive behavior unchanged.
- The schema change (removing `dlq_requeue_count`, decided 2026-11-10) is applied as a new canonical schema (no migration).

## Target Files or Areas
- `scripts/eventbus/dlq.py`, `scripts/eventbus/ack_route.py`, `scripts/eventbus/dlq_repo.py`, `scripts/eventbus/dlq_route.py`, `scripts/eventbus/event_repo.py`
- `scripts/eventbus/_constants.py`, `scripts/eventbus/route_helpers.py`
- `scripts/eventbus/schema.sql` and the schema fingerprint code (only if a column is removed)
- `tests/eventbus/test_eventbus_dlq.py`, `tests/eventbus/test_eventbus_dlq_promotion.py`, `tests/eventbus/test_eventbus_requeue_edge_cases.py` and the tests of `/nack` and `/dlq`
- `docs/24_eventbus/eventbus_04_dlq_endpoint.md`, `eventbus_05_dlq_offsets_and_delivery_semantics.md`, `eventbus_12_ack_nack_endpoints.md`, `eventbus_06` (persistence), and ADR-006 (`docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`)

## Required Changes
- Remove `deadletter_dir` from the promotion and sweep functions and their callers.
- Remove the `except OSError` block and its log message from `/nack`, and remove the obsolete row from the NACK state table in `eventbus_12`.
- Reduce `RequeueResult` to `status`, `new_event_id`, and `new_seq`.
- Remove `dlq_requeue_count` (maintainer decision, 2026-11-10): DDL, fingerprint, the requeue write, the `/dlq` response, and `eventbus_05`/`eventbus_04`.
- Search all readers of `events.consumer_id` and remove the column if none exist (same schema update).
- Rename `_COL_REDISTRIBUTED_FROM` to match the column name; replace the private-attribute access in `get_counter_value` with a public API; fix the shebang line of `route_helpers.py` (or remove it, since the module is not executed).

## Constraints
- No migration of an existing `eventbus.sqlite` (`compatrm001`): a schema change makes an old file fail the schema check and requires archive and recreate.
- A change to the `/dlq` response is an API change and must be documented.
- `scripts/eventbus/schema.sql` and the fingerprint code are also changed by `plans/20261110-095137_adrrev005_schema-fingerprint-unify.md`; apply schema edits after that plan lands.

## Acceptance Criteria
- No DLQ promotion or sweep function takes `deadletter_dir`, and `/nack` has no `except OSError`.
- `RequeueResult` has no field that duplicates `status`.
- Any removed column is absent from `schema.sql` and from the fingerprint, and a database with the old shape is refused with the archive-and-recreate error.
- `rg -n "REDISTRIBUTED" scripts/` returns nothing, and `get_counter_value` uses no attribute starting with an underscore.
- The `eventbus_12` state table has no "inline DLQ file write failed" row.
- The EventBus tests, the validation sequence, and the documentation checks pass.

## Testing Expectations
- Update and run `tests/eventbus/`; add a test for the refusal of an old-shape database only if the schema changes.
- Run `rules/toolchain.md` validation (ruff, mypy with `--no-namespace-packages`, import-linter, bandit, pytest), `uv run python tools/check_db_separation.py` for a DDL change, `uv run python tools/check_docs_consistency.py --domain eventbus`, and the ADR checkers (`tools/check_adr_preservation.py`, `tools/check_adr_structure.py`) for ADR-006 edits.

## Documentation Impact
- Documentation must be updated: `eventbus_12` (NACK state table), `eventbus_04`, `eventbus_05`, `eventbus_06`, and ADR-006 (with an approval record if a decision text changes) wherever they describe the removed fields, columns, or failure path. Describe behavior and failure handling, not field catalogs.

## Out of Scope
- The `deadletter_dir` configuration key, the outbox worker, `reconcile_missing_dlq_files`, and archive behavior.
- EventBus configuration, authorization, and audit (`issues/20261110-170832_rmcompat004_eventbus-config-auth-audit.md` in this batch).
- `ERR_*` constants (all have users).

## Dependencies
- Schema edits depend on `plans/20261110-095137_adrrev005_schema-fingerprint-unify.md` (it replaces the fingerprint module and removes `user_version` stamping in `schema.sql`); apply them after it.
- Blocks the history-comment sweep issue in this batch (`issues/20261110-171040_rmcompat007_history-comment-sweep.md`).
- Related, documentation only: `issues/20261109-113421_adrrev019_docs-stale-statements.md` (a stale DLQ statement in `eventbus_01`).

## Unresolved Questions
- Decided (2026-11-10): remove `events.dlq_requeue_count`; this is an API change to the `/dlq` response and must be documented.
- `不明`: the operator's plan for the deployed `eventbus.sqlite`, which the adrrev005 plan records as already differing from the current schema (`user_version 0`); removing columns makes every older file fail the schema check, so the archive-and-recreate timing and the handling of undelivered events in the old file are not decided.
- `Needs confirmation`: whether any operator script or external consumer reads `dlq_requeue_count` or `events.consumer_id` (no reader found in `scripts/eventbus/`).
- `Needs confirmation`: the public API of the metrics library that replaces the `counter._name` read.

## AI Implementation Instruction
- Change only the files listed above; do not touch the outbox worker, reconcile, or archive logic.
- Re-run the zero-reference searches (readers of `events.consumer_id`, users of removed fields) before deleting anything.
- Remove `dlq_requeue_count` together with the schema, fingerprint, and `/dlq` response change; do not leave a partial removal.
- Keep comments and log text in English.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261110-170926
- **Related target files**: `scripts/eventbus/dlq.py`, `scripts/eventbus/ack_route.py`, `scripts/eventbus/dlq_repo.py`, `scripts/eventbus/dlq_route.py`, `scripts/eventbus/event_repo.py`, `scripts/eventbus/_constants.py`, `scripts/eventbus/route_helpers.py`, `scripts/eventbus/schema.sql`
