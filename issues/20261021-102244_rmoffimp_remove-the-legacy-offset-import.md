# Remove the legacy offset import

## Priority
Medium

## Summary
Remove the EventBus startup step that imports legacy file-based consumer offsets into `consumer_offsets`, because the end condition recorded in the operations document holds for the only supported deployment.

## Background
The EventBus operations document (section "Legacy Offset Files") states that the import may be removed when no supported deployment keeps files in `offsets_dir`, and that `consumer_offsets` in `eventbus.sqlite` is the only resume source. The owner decided on 2026-10-21 that the only supported deployment is the single host using `/opt/llm`; a read-only inspection that day found `/opt/llm/offsets` empty (no offset file and no `.map` file) and `consumer_offsets` empty after the database was recreated from the current schema. `migrate_legacy_offsets()` in `scripts/eventbus/offset_migrator.py` runs on every EventBus start (called from the lifespan in `scripts/eventbus/app.py` inside a `try` that only logs a failure). The current runtime writes offsets only through the transactional acknowledgement path, so nothing else produces these files. (Confirmed by code and by read-only inspection)

Known behaviors of the import that become moot on removal (recorded as open decisions in the EventBus semantics document): a consumer-ID collision between two files without a `.map` companion raises and skips the rest of the import; there is no completion marker; the function does not commit its inserts (a test run on 2026-10-21 showed an open transaction and no row visible to a second connection), so durability depends on a later commit on the shared connection.

## Problem
An import with no completion marker runs on every start for files that do not exist, carries an uncommitted-insert and a collision behavior that were never settled, and keeps a startup `try`/log path that can hide a failure. It also keeps legacy file-offset documentation alive.

## Reason for Change
Consumer offsets decide where each consumer resumes; a data-integrity path that runs on every start and does not commit explicitly is a liability once nothing needs it. Removing it ends the open decisions about collisions, the completion marker, and commit behavior in one step.

## Implementation Intent
Delete the import function and its startup call, and its re-export, and keep everything else about offsets unchanged. Do not change how offsets are stored, advanced, or used to resume. The `offsets_dir` configuration key and the file-based `write_offset()`/`read_offset()` helpers stay for now, because their removal is a separate undecided question (see Unresolved Questions); this issue must not widen into it.

## Target Files or Areas
- `scripts/eventbus/offset_migrator.py` (delete the module)
- `scripts/eventbus/app.py` (the import and the call in the lifespan)
- `scripts/eventbus/db.py` (the re-export and its `__all__` entry)
- `tests/eventbus/test_eventbus_offsets.py` (the tests of the import)
- `docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md`, `docs/24_eventbus/eventbus_07_configuration-and-operations.md`, `docs/24_eventbus/eventbus_08_reference_api.md`, `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md`

## Required Changes
- Delete `scripts/eventbus/offset_migrator.py` and remove its import, re-export, and call.
- Remove the tests of the import; keep the tests of ACK-advanced offsets and of resume behavior.
- Update the documentation: remove the legacy offset import description, the "Legacy Offset Files" operations section (or reduce it to the statement that offset files are not used by the service), and the open decisions about the import; refresh the generated reference table with `generate_reference_table.py` and confirm `--check` passes.
- State no history of the removal in current documents.

## Constraints
- Offset storage, monotonicity, ACK-advanced offsets, and resume position computation must not change.
- The `offsets_dir` configuration key and its tests are not touched (about 70 test sites build the configuration object with it).
- Existing statements in the EventBus ADR about the import must not be left contradicting the code (see Unresolved Questions).

## Acceptance Criteria
- `rg "migrate_legacy_offsets|offset_migrator" scripts tests docs tools` returns no match, except any ADR text the owner decides to keep verbatim.
- The EventBus starts normally with an empty `offsets_dir`, and with a non-empty one it ignores the files and does not modify them.
- Offset ACK and resume tests pass unchanged.
- `ruff`, `mypy --no-namespace-packages`, `lint-imports`, the full suite, `generate_reference_table.py --check`, and the documentation checkers pass.

## Testing Expectations
- Run `tests/eventbus/test_eventbus_offsets.py`, `tests/eventbus/test_eventbus_restart_resume.py`, and `tests/eventbus/test_eventbus_startup.py`, then the full suite once.
- Run `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/`, `PYTHONPATH=scripts uv run lint-imports`, `uv run python tools/generate_reference_table.py --check`, `uv run python tools/check_module_size.py`, and the documentation checkers.
- Manual: list `offsets_dir` of the deployed host (read-only) and confirm it is empty before deploying.

## Documentation Impact
Yes. Remove the import and its open decisions from the semantics and operations documents and the database document, and refresh the generated reference table; keep the statement that `consumer_offsets` is the only resume source.

## Out of Scope
- Removing the `offsets_dir` key, `write_offset()`, `read_offset()`, or their tests (separate decision).
- Deleting any offset file from any host.
- The schema migrations of `eventbus.sqlite`, `workflow.sqlite`, and `mdq.sqlite` (separate issues).

## Dependencies
- Depends on the end condition recorded in the EventBus operations document and the baseline in the database design document; both are already merged.
- Shares the database design document with the other removal issues; apply the edits one after another.
- Related to the EventBus schema migration removal issue (same service, different files); independent in order.
- Sibling-issue check: no open issue under `issues/` touches these files.

## Unresolved Questions
- How to update the EventBus ADR text that describes the import (`docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`, offset store paragraph, file list, and offset-file entry): the ADR preservation check guards its decisions, so the owner must decide whether to edit the ADR text or keep it as the decision record.
- Whether `write_offset()`, `read_offset()`, and the `offsets_dir` key are removed afterwards (owned by the EventBus service); this issue neither decides nor prepares it beyond not touching them.
- Re-run the read-only directory listing of the deployed host immediately before the removal lands.

## AI Implementation Instruction
- Change only the files under Target Files or Areas; keep the diff minimal and do not refactor unrelated EventBus code.
- Do not add a replacement import, a one-off tool, or a deletion of offset files.
- Do not edit the ADR without the owner's decision recorded in this issue.
- Stop and report if a caller outside the listed files uses the removed function.
- Write documentation in English and follow the repository's documentation checkers.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/done/20261020-233641_plan.md`
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261021-102244
- **Related target files**: `scripts/eventbus/offset_migrator.py`, `scripts/eventbus/app.py`, `scripts/eventbus/db.py`, `tests/eventbus/test_eventbus_offsets.py`, `docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md`, `docs/24_eventbus/eventbus_07_configuration-and-operations.md`, `docs/24_eventbus/eventbus_08_reference_api.md`, `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md`
