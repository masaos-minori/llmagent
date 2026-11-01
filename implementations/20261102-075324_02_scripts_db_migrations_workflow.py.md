# Pin each workflow step to its own version literal

## Goal

Replace the `WORKFLOW_SCHEMA_VERSION` f-string in the three string-stamping workflow
steps with each step's own pinned literal so a later head-version bump cannot rewrite
an earlier step's marker (Plan REQ-005).

## Scope

- `_TOOL_STATE_MUTATION_SQL` → literal `1.2.0`.
- `_TASK_NONCE_MUTATION_SQL` → literal `1.3.0`.
- `_ATTEMPT_LEASE_MUTATION_SQL` → literal `1.4.0`.
- Drop the then-unused `from db.schema_sql import WORKFLOW_SCHEMA_VERSION` import.

## Assumptions

- Verified 20261102: all three constants interpolate `{WORKFLOW_SCHEMA_VERSION}` and it
  has no other use in this module (only the `WORKFLOW_VERSION_CODES` comment mentions
  the constant by name; comments stay).
- `WORKFLOW_VERSION_CODES` head (`1.4.0` → 4) and `WORKFLOW_TARGET_VERSION` are not
  touched here; the wfrecovery001 bump (next ledger code) lands after this fix.

## Design decisions

- Literals inline in each `_*_MUTATION_SQL` constant — no new helper: each step's
  marker is a fixed fact about that step's shape, not the head version.

## Alternatives considered

- A per-step stamp-version attribute resolved by the runner — rejected: adds a
  `MigrationSpec` contract no other domain needs for this defect.

## Implementation
### Target file
`scripts/db/migrations_workflow.py`

### Procedure
1. In `_TOOL_STATE_MUTATION_SQL` (line ~125), `_TASK_NONCE_MUTATION_SQL` (~136) and
   `_ATTEMPT_LEASE_MUTATION_SQL` (~149): replace
   `VALUES ('{WORKFLOW_SCHEMA_VERSION}')` with `VALUES ('1.2.0')`, `VALUES ('1.3.0')`
   and `VALUES ('1.4.0')` respectively; the f-string prefix stays for the
   `PRAGMA user_version = {code}` part.
2. Remove the `from db.schema_sql import WORKFLOW_SCHEMA_VERSION` import (line 34).

### Method
- Three single-line edits plus one import removal; no logic change.

### Details
- Keep each line's `# nosec B608` justification comment.
- Ledger codes stay: steps remain 1→2, 2→3, 3→4 (`_TOOL_STATE_VERSION`,
  `_TASK_NONCE_VERSION`, `_ATTEMPT_LEASE_VERSION` unchanged).

## Compatibility considerations

- A database already migrated by these steps keeps the (wrong) `1.4.0` markers it was
  written; the forward-only model never re-runs applied steps, so no repair step is in
  scope. Fresh and resumed databases get the pinned values from here on.

## Security considerations

- N/A: same fixed-constant SQL, no new dynamic text.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run pytest tests/db/test_migrations_workflow.py` (pinned-literal tests from
  procedure 05 pass; failing-first per Plan Phase 1).
- `uv run ruff format`, `uv run ruff check`, `uv run mypy --no-namespace-packages
  scripts/db/migrations_workflow.py`.

## Completion criteria

- Migrating a legacy fixture writes `1.2.0` after the tool_call_state step, `1.3.0`
  after task_nonce, `1.4.0` after attempt_lease regardless of
  `db.schema_sql.WORKFLOW_SCHEMA_VERSION`; ruff/mypy clean.

## Out of Scope

- Runner transaction changes (procedure 01), CLI option (procedure 03), test edits
  (procedure 05), adding future steps or bumping `WORKFLOW_SCHEMA_VERSION`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | execute after procedure 05's failing tests land (Plan Phase 1) |
| 2 | Add or update tests per Validation plan | Pending | — | — | owned by procedure 05 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A (docs row is procedure 06) |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-005` (per-step pinned version literals), `REQ-008` (existing
  step results unchanged)
- **Source issue**: issues/20261101-133004_dbmigrunner001_runner-unsafe-table-rebuild.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261101-133244_dbmigrunner001_runner-unsafe-table-rebuild.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261102-075324
- **Related target files**: scripts/db/migrations_workflow.py
