# Obtain owner schema inventory to set the minimum supported schema baseline

## Priority
High

## Summary
Obtain from the database owner the deployed schema state of `workflow.sqlite`, `eventbus.sqlite`, and `mdq.sqlite`, and the minimum supported source schema for each, so that `compat001` can record the migration baseline. This issue tracks the owner input; it is not code work. Once the answers are recorded here, close this issue and proceed with `compat001`.

## Background
- `compat001` records, per database, the oldest schema the current release must still upgrade from, why each migration is kept, the removal condition, and the owner. That baseline is a data-integrity decision that cannot be derived from the repository.
- An investigation dated 2026-10-20 re-checked the migration code against the current source: `_WORKFLOW_MIGRATIONS` / `_EVENTBUS_MIGRATIONS` in `scripts/db/schema_sql.py`, `apply_workflow_migrations()` / `apply_eventbus_migrations()` invoked from `scripts/db/create_schema.py`, the second EventBus path in `scripts/eventbus/schema.py`, `_migrate_legacy_chunks_schema()` in `scripts/mcp_servers/mdq/db_schema.py`, and the startup version-mismatch check in `scripts/agent/services/workflow_schema.py`. All exist as described. (Confirmed by repository evidence)
- A search of `docs/` found no minimum supported schema version or baseline. (Confirmed by repository evidence: absence verified by search)
- The deployed-database inventory lives outside the repository and must not be guessed.

## Problem
No document or code defines the oldest schema each database must still be upgraded from. Without that baseline nobody can say which migration is removable, and there is no recorded owner or removal condition for any of them. Removing a migration without knowing which schemas still exist in deployment would make the service fail to start on, or silently misread, an older database.

## Reason for Change
Migration removal is a data-integrity decision that must rest on a stated baseline, not on the absence of recent complaints. Recording the baseline now lets later cleanup work be filed and reviewed against a fixed criterion, and exposes whether the duplicated EventBus path and the missing version marker are intentional.

## Implementation Intent
This is an inquiry-and-record task, not a code change. Ask the database owner the questions below, record the answers verbatim in the Owner Input Record section of this issue, and hand the recorded answers to `compat001`. Do not infer versions or deployments from the repository.

## Target Files or Areas
- `issues/20261021-092312_owner001_...` (this issue; the answer record lives here)
- `issues/20261020-122549_compat001_...` (the parent issue this unblocks)
- `owner-question-packet.md` (working questionnaire; being retired once these issues exist)

## Required Changes
- Obtain, per database, the currently deployed schema state:
  - `workflow.sqlite`: the recorded schema version (`workflow_schema_version`).
  - `eventbus.sqlite`: the columns of `events` and `consumer_delivery`.
  - `mdq.sqlite`: the shape of `chunks`.
- Obtain, per database, the decision on the minimum supported source schema (the oldest schema the current release must upgrade from).
- Record the decisions on the EventBus second migration path and the missing schema-version marker, and on rollback expectations for a failed migration.
- Record every answer in the Owner Input Record section below with the answerer and date.

## Constraints
- Do not guess or derive the deployed schema state from the repository. Record only owner-supplied answers.
- Do not change any file under `scripts/`, `config/`, or `tests/`, and do not edit migration SQL or schema DDL. That work belongs to `compat001`.
- Answers may be supplied in English or Japanese; record them verbatim.

## Acceptance Criteria
- **AC-1**: The Owner Input Record section contains the deployed schema state for all three databases, answered by the owner.
- **AC-2**: The Owner Input Record section contains the minimum supported source schema decision for all three databases.
- **AC-3**: The decisions on the EventBus second path, the version marker, and rollback are recorded or explicitly listed as open with an owner.
- **AC-4**: Every answer carries an answerer and a date.

## Testing Expectations
Not required: this issue produces recorded owner input, not code. Verify AC-1..AC-4 by inspection.

## Documentation Impact
None beyond this issue's own Owner Input Record. The recorded answers feed `compat001`, which writes the canonical database document.

## Out of Scope
- Any change to migrations, migration SQL, or schema DDL.
- Writing the migration baseline into the canonical database document. That is `compat001`.
- Deciding which migrations to remove. Filed separately once the baseline exists.

## Dependencies
- **Unblocks**: `compat001` (`issues/20261020-122549_compat001_...`); `compat001` cannot record its baseline without this input.
- **Depends on**: the database owner being reachable to supply the inventory.
- Sibling-issue check: no other open issue under `issues/` tracks the owner-supplied schema inventory; `compat002` shares the same baseline decision but depends on this one.

## Unresolved Questions
- Who owns the deployed databases, and can they supply the inventory?
- Which releases must the current version upgrade from? Is any installation older than the current baseline still in use?
- Is the second EventBus migration path in `scripts/eventbus/schema.py` intentionally separate from `apply_eventbus_migrations()`, or a leftover?
- Is the absence of an EventBus schema-version marker intentional?
- Is there a rollback expectation for a failed migration beyond the pre-upgrade backup the deployment document already requires for `workflow.sqlite`?

## AI Implementation Instruction
- This issue is an inquiry-and-record task. Do not touch `scripts/`, `config/`, or `tests/`, and do not edit migration SQL or schema DDL.
- Ask the database owner the questions above and record the answers verbatim in the Owner Input Record section with an answerer and date.
- Do not infer or guess the deployed schema state from the repository. If an answer is unavailable, leave it open with an owner rather than filling a gap.
- When all owner inputs are recorded and AC-1..AC-4 hold, close this issue and hand the recorded answers to `compat001`.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261021-092312
- **Related target files**: `issues/20261021-092312_owner001_...`, `issues/20261020-122549_compat001_...`

## Owner Input Record
| Database | Item | Answer | Answerer / Date |
|---|---|---|---|
| workflow.sqlite | recorded schema version | _pending_ | — |
| eventbus.sqlite | `events` / `consumer_delivery` columns | _pending_ | — |
| mdq.sqlite | `chunks` shape | _pending_ | — |
| all | minimum supported source schema (per DB) | _pending_ | — |
| eventbus | second migration path / version marker / rollback | _pending_ | — |
