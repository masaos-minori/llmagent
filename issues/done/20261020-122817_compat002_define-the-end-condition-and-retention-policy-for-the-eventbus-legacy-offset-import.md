# Define the end condition and the retention policy for the EventBus legacy offset import

## Priority
High

## Summary
Decide when the EventBus startup step that imports legacy file-based consumer offsets into the database may be retired, what happens to the old offset files, and which side is authoritative. Record the decisions in the operations and database documents. Do not remove code in this issue; file follow-up issues for any removal or behavior change the decisions require.

## Background
- Source: an investigation of the design documents dated 2026-10-20 that listed persistent-data migrations. It read documents only; the facts below were re-checked against the current code and documents on 2026-10-20.
- `migrate_legacy_offsets()` in `scripts/eventbus/offset_migrator.py` reads each offset file under `offsets_dir`, recovers the consumer id from the `.map` companion (or from the sanitized file name when the companion is missing or empty), and inserts the offset into `consumer_offsets` with `INSERT OR IGNORE`. It never modifies or deletes the files. (Explicit in code)
- The EventBus lifespan in `scripts/eventbus/app.py` calls it on every start, inside a `try` block that only logs `failed to migrate legacy offsets` and lets startup continue. (Explicit in code)
- When two legacy files without a `.map` companion sanitize to the same consumer id, the function raises `ValueError` from inside its loop. The lifespan catches it, so the rest of the import is skipped and startup continues. (Explicit in code)
- The current runtime no longer writes offset files: `scripts/eventbus/ack_route.py` states that `write_offset` was replaced by the transactional `ack_event_for_consumer()` path, and `write_offset()` / `read_offset()` in `scripts/eventbus/offsets.py` have no caller outside tests and themselves. (Explicit in code)
- `migrate_legacy_offsets()` is covered by several tests in `tests/eventbus/test_eventbus_offsets.py`. (Verified by test)
- Documentation: the database document describes the import as idempotent and as not modifying or deleting the files, and the EventBus ADR lists the offset files as read only by this function. No document states why the files are kept, who owns them, which side wins after the import, or when the import ends. (Documentation only; absence verified by search of `docs/`)

## Problem
The import runs on every start with no completion marker and no stated end. The legacy files stay in place indefinitely, so an operator cannot tell whether they are still authoritative, a rollback aid, or garbage. A collision aborts the whole import silently relative to startup, leaving some consumers unmigrated with only a log line. Nothing records when the import may be removed.

## Reason for Change
Consumer offsets decide where each consumer resumes; losing or mis-restoring one repeats or skips events. The import is therefore a data-integrity path that cannot be deleted on a guess, and it also should not stay on the startup path forever without an owner and an exit condition. Writing the decisions down now lets the removal be reviewed against a fixed criterion.

## Implementation Intent
- Record decisions, not code: the end condition, the retention policy for the files, the authority rule after import, and the owner.
- State the authority rule in present tense: after the import, the database is the source of truth, and the files are never read again for resume.
- Decide whether the import should keep running on every start or stop once a completion condition holds, and whether a collision should block startup or only be reported. Implementing either decision is a separate follow-up issue.
- Decide whether the unused file-based offset helpers are removed together with the import.

## Target Files or Areas
- `docs/24_eventbus/eventbus_07_configuration-and-operations.md` (operator-facing retention and cleanup notes)
- `docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md` (offset authority and resume behavior)
- `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md` (the offset seeding section)
- `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md` (read only; must not be contradicted)
- Read for evidence: `scripts/eventbus/offset_migrator.py`, `scripts/eventbus/app.py` (lifespan), `scripts/eventbus/offsets.py`, `scripts/eventbus/ack_route.py`, `config/eventbus.toml` (`offsets_dir`)
- Tests, read only: `tests/eventbus/test_eventbus_offsets.py`

## Required Changes
- Obtain from the owner the state of `offsets_dir` in every deployment: whether any offset or `.map` file exists, and whether any consumer still depends on it.
- Decide and record the end condition for the import (for example, no deployment holds a legacy file, and the minimum supported schema from `compat001` is past the file-based era).
- Decide and record the retention policy for the files: keep for rollback or audit, archive, or delete, with the permissions and backup treatment that follows.
- Record that the database is authoritative after import and that the files are not a resume source.
- Decide whether a consumer-id collision should stop startup or be reported, and whether the import should leave a completion marker; file a follow-up issue for any behavior change.
- Decide whether `write_offset()` and `read_offset()` are removed with the import; file a follow-up issue for the removal.
- Update the three documents above with the decisions in present tense; register anything unconfirmed in the Needs Confirmation inventory.

## Constraints
- No change to `scripts/` or `config/` in this issue; the import keeps its current behavior, including idempotence and not touching the files.
- The decisions must be consistent with ADR-006 (SQLite persistence and delivery semantics) and with the baseline decision in `compat001`.
- Documentation follows the docs content policy: intent, boundaries, constraints, and operational notes only; no history of earlier file-based offsets beyond what the current rule needs.
- Documentation is written in English.

## Acceptance Criteria
- The documents state the end condition, the file retention policy, the authority rule after import, and the owner.
- The operator documentation tells an operator whether the files may be deleted and how to check that no consumer still needs them.
- The decisions on collision handling, a completion marker, and the helper removal are recorded, each either decided or listed as an open question with an owner.
- Every follow-up the decisions require is filed as its own issue.
- No file under `scripts/`, `config/`, or `tests/` is changed.
- The documentation checkers pass and no Needs Confirmation marker is left unregistered.

## Testing Expectations
- Not required for code: documentation-only change.
- Run `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py`, `uv run python tools/check_docs_content_policy.py --strict`, `uv run python tools/check_docs_consistency.py --domain overview`, and `uv run python tools/check_needs_confirmation_inventory.py`.

## Documentation Impact
Yes. Update the EventBus operations and semantics documents and the database document with the end condition, retention policy, authority rule, and owner (intent, boundaries, constraints, operational notes). Add a Needs Confirmation entry for any decision the owner has not made.

## Out of Scope
- Changing `migrate_legacy_offsets()`, its startup call, or the file-based helpers.
- The schema migrations of `eventbus.sqlite` (covered by `compat001`).
- Deleting any offset file or changing `offsets_dir`.
- The Event Bus post-start verification failure handled by `20261020-115744_ebstart003_...`.

## Dependencies
- Depends on: `compat001` for the minimum supported schema baseline.
- Sibling-issue check: `20261020-115744_ebstart003_...` edits `scripts/eventbus/app.py` but only the post-start loopback verification in `_main`, not the lifespan import call; the two do not overlap. No other open issue covers the legacy offset import.
- Blocks: any follow-up that stops the import, adds a completion marker, changes collision handling, or removes the helpers.

## Unresolved Questions
- Does any deployment still hold legacy offset or `.map` files, and does any consumer rely on them? (Needs confirmation; the repository cannot answer this)
- Does `migrate_legacy_offsets()` make its inserts durable? It issues `INSERT OR IGNORE` and never calls `commit()`; whether a later commit on the same connection always follows before shutdown was not verified. (Needs confirmation)
- Should a consumer-id collision stop startup, or is a logged, partial import acceptable?
- Are the file-based `write_offset()` and `read_offset()` kept for a reason other than tests?
- Who owns the offset files and the decision to delete them?

## AI Implementation Instruction
- Do not change `scripts/`, `config/`, or `tests/`, and do not delete or move any offset file.
- Do not guess whether a deployment still holds legacy files; record it as an open question for the owner and stop.
- Keep the documentation to decisions, constraints, and operational notes; do not describe the removed file-based writer's history.
- File a separate issue for every code change a decision requires; do not implement it here.
- Run the documentation checkers listed above before finishing.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261020-122817
- **Related target files**: `docs/24_eventbus/eventbus_07_configuration-and-operations.md`, `docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md`, `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md`, `scripts/eventbus/offset_migrator.py`, `scripts/eventbus/app.py`, `scripts/eventbus/offsets.py`, `config/eventbus.toml`
