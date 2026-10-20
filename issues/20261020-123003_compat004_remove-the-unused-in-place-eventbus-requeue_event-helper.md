# Remove the unused in-place EventBus requeue_event helper

## Priority
Medium

## Summary
Delete `requeue_event()` from `scripts/eventbus/dlq_repo.py` and its re-export from `scripts/eventbus/db.py`, so the in-place requeue that bypasses the lineage model no longer exists next to the lineage-preserving `redeliver_event()`. Refresh the generated reference table, which still lists the helper as a "legacy helper".

## Background
- Source: an investigation of the design documents dated 2026-10-20 that listed backward-compatibility candidates. It read documents only; the facts below were re-checked against the current code on 2026-10-20. The investigation proposed High pending a reachability check; the check found no caller, which supports Medium (dead code, no runtime path).
- `requeue_event(conn, event_id)` updates the original `events` row in place: it increments `dlq_requeue_count` and clears `dlq_at`. Its docstring calls it an "Unused legacy helper with no callers" and names `redeliver_event()` as the active requeue path. (Explicit in code)
- `redeliver_event()` inserts a new row with a fresh event id and `redelivered_from` set to the original, and guards against concurrent redelivery. The route `POST /dlq/{event_id}/requeue` in `scripts/eventbus/dlq_route.py` calls `redeliver_event()` only. (Explicit in code)
- A search of `scripts/`, `tests/`, and `tools/` finds no call to `requeue_event(`. The only other references are its import and `__all__` entry in `scripts/eventbus/db.py` and a row in the generated table `docs/24_eventbus/eventbus_08_reference_api.md`. A test named `test_requeue_event_at_max_retry_then_re_promoted` exercises the HTTP route, not the helper. (Explicit in code)
- `eventbus_08_reference_api.md` is generated between `AUTO-GENERATED` guard comments by `tools/generate_reference_table.py --type eventbus`; it must not be edited by hand. (Explicit in code)

## Problem
Two requeue implementations exist with different contracts: the live one preserves event lineage, while the unused one mutates the original row and clears its dead-letter marker. If anything started calling the helper, it would bypass the lineage, audit, and concurrency guard that the DLQ policy relies on. Today nothing reaches it, so it is dead code that looks like a supported API.

## Reason for Change
Removing it leaves one requeue contract and removes a latent way to break lineage. It also removes an inventory line that describes a function as "legacy" without a caller, owner, or end condition.

## Implementation Intent
- Delete the function and its re-export only; keep `redeliver_event()` and the route unchanged.
- Keep the `dlq_requeue_count` column and its use by the live path; this issue does not change the schema.
- Do not replace the helper with a test-only version; no test needs it.
- Refresh the generated reference by running the generator, not by hand edit.

## Target Files or Areas
- `scripts/eventbus/dlq_repo.py` (remove `requeue_event`; check for imports that become unused)
- `scripts/eventbus/db.py` (remove the import and the `__all__` entry)
- `docs/24_eventbus/eventbus_08_reference_api.md` (regenerate the guarded block)
- `tests/eventbus/` (a small test that the helper is gone, beside the existing requeue tests)
- Read for evidence: `scripts/eventbus/dlq_route.py`

## Required Changes
- Remove `requeue_event()` from `dlq_repo.py` and remove its import and `__all__` entry from `db.py`; remove constants or imports that only it used.
- Run `uv run python tools/generate_reference_table.py --type eventbus` and commit the regenerated block.
- Add a test asserting that `eventbus.dlq_repo` and `eventbus.db` no longer expose `requeue_event`, so the in-place path cannot return unnoticed.
- Confirm the existing DLQ and requeue tests still pass unchanged.

## Constraints
- Do not change `redeliver_event()`, the `/dlq/{event_id}/requeue` route, the lineage fields, or the database schema.
- Preserve the idempotency and concurrency guard of the live requeue path.
- Do not hand-edit the generated reference block.
- Follow `rules/coding.md`; a suppression comment is not allowed to hide an unused import.

## Acceptance Criteria
- `requeue_event` is absent from `scripts/eventbus/dlq_repo.py` and from `scripts/eventbus/db.py`.
- A test fails if `requeue_event` is restored on either module.
- `uv run python tools/generate_reference_table.py --check` reports no drift, and the reference table has no `requeue_event` row.
- The existing EventBus DLQ, requeue, and replay tests pass without modification.
- ruff and mypy pass.

## Testing Expectations
- New regression test for the removed helper.
- `uv run pytest tests/eventbus`, `uv run mypy --no-namespace-packages`, `uv run ruff check`, `uv run python tools/generate_reference_table.py --check`, `uv run python tools/check_docs_consistency.py --domain overview`, and `uv run python tools/check_db_separation.py`.

## Documentation Impact
Yes, limited to the generated reference block, refreshed by the generator. No hand-written document describes the helper; if one is found during the change, remove the mention rather than describe the removal.

## Out of Scope
- Changing the lineage requeue (`redeliver_event()`), the DLQ policy, or any schema.
- The legacy file-offset import (`compat002`).
- Other items in the same investigation (`read_json_file()`, the Agent package re-exports, the export `md` alias).

## Dependencies
- Sibling-issue check: no open issue under `issues/` touches `scripts/eventbus/dlq_repo.py` or `scripts/eventbus/db.py`. `20261020-115744_ebstart003_...` edits `scripts/eventbus/app.py` only.
- No dependency on the other `compat` issues; this one can be done independently.

## Unresolved Questions
- Does anything outside the repository call `eventbus.db.requeue_event` (an operator script, for example)? The helper is exported from `eventbus.db`, so the repository cannot rule it out. (Needs confirmation)

## AI Implementation Instruction
- Remove only `requeue_event` and its re-export; do not edit `redeliver_event()` or the route.
- If a caller outside the code paths listed here turns up, stop and report it instead of keeping the helper.
- Regenerate the reference table with the generator; do not hand-edit it.
- Run the commands in Testing Expectations before finishing.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261020-123003
- **Related target files**: `scripts/eventbus/dlq_repo.py`, `scripts/eventbus/db.py`, `docs/24_eventbus/eventbus_08_reference_api.md`, `scripts/eventbus/dlq_route.py`, `tests/eventbus/test_eventbus_requeue_edge_cases.py`
