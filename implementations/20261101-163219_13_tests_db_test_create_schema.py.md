## Goal

## Goal

Update schema-parity and version assertions in `tests/db/test_create_schema.py` for the two new `attempts` columns (REQ-004, REQ-009 / AC-8).

## Scope

- Extend the embedded no-vec0 `attempts` DDL copy (`:392-421`) with `owner_id TEXT` and `lease_expires_at TEXT` so the parity test keeps the template and the copy identical.
- Update the workflow version assertion (currently pinned to the landed `"1.2.0"` behavior via the `workflow_schema_version` assertions at `:662-728`) to the new landing-order version together with procedure 17's registry codes.
- Extend the attempts-column assertions (`INSERT` shape test around `:575-581`) to write and read back the two columns.

## Assumptions

- Plan `plans/20261030-114516_wflease001_stale-attempt-lease.md` is Frozen; its 18-row `Implementation Target Files` table (rows 17-18 added by the 2026-11-01 amendment) is the canonical scope and every target of this procedure is a row of that table.
- All baseline cites below were re-verified against branch `master` on 2026-11-01 (Plan Assumptions 'Re-verification record').
- Canonical semantics come from the Plan REQs (Plan `:37-46`): `parse_iso_utc` rejects naive input (REQ-001); no `mktime`/`strptime`/local time in recovery (REQ-002); unparseable timestamps are reported with distinct counts (REQ-003); nullable `owner_id`/`lease_expires_at` via a registered migration (REQ-004); owner and lease stamped at attempt start from the stage timeout plus a 30 s margin constant (REQ-005); staleness means lease expiry and `_STALE_GRACE_SEC` is removed (REQ-006); takeover is a conditional update requiring one row (REQ-007); legacy rows without a lease use the 3600 s age (REQ-008); tests use the production timestamp format (REQ-009); docs and ADR-001 INV-07 are amended (REQ-010).
- Owner decision (Plan UNK-02, 2026-10-30): deadline lease only — no heartbeat renewal, because `asyncio.wait_for` already bounds a normal stage.
- Ledger landing order (Plan UNK-06): `master` records code 2 / "1.2.0" (`migrations_workflow.py:42`); wftaskapi001 procedure 12 (`implementations/20261101-140834_12_scripts_db_migrations_workflow.py.md`, Pending) reserves the next slot. This Plan takes code 3 / "1.3.0" only if its step registers before wftaskapi001's, otherwise 4 / "1.4.0" (same rule as `implementations/20261101-145309_26_scripts_db_migrations_workflow.py.md`).
- Fencing dependency (Plan UNK-06): REQ-007's rejection of a late finish by the fenced owner lands with the wfrecovery001 conditional `finish_attempt` procedure (`implementations/20261101-145309_04_scripts_agent_workflow_attempt_ops.py.md`, Pending); at `master` `finish_attempt` is still unconditional (`attempt_ops.py:44-45`).
- The exact expected version string is filled at implementation time from the landing-order decision (procedure 06/17); this document does not fix it.

## Design decisions

- Column assertions use `PRAGMA table_info` on a fresh DB so a forgotten DDL edit breaks immediately rather than surfacing in the startup check only.

## Alternatives considered

- Rely on the startup-check tests alone — rejected: `tests/db/` is the canonical schema-parity home (Plan Tests section).

## Implementation
### Target file
`tests/db/test_create_schema.py`

### Procedure
1. Edit the DDL copy at `:392-421`.
2. Add the column-presence assertions for `attempts`.
3. Adjust the ledger/version assertions in sync with procedure 17.

### Method
Fixture-string and assertion edits in the existing test module.

### Details
- `test_create_schema.py` had 15 commits in 30 days (Plan Affected areas) — keep the diff surgical: only the workflow `attempts` blocks and version pins.

## Compatibility considerations

- Must land in the same commit as procedure 06 or the parity test breaks.

## Security considerations

- All recovery/attempt SQL stays parameter-bound; owner and lease values are produced by the server (clock, host identity), never by caller-supplied strings.

## Rollback considerations

- Revert with procedure 06.

## Validation plan

- `uv run pytest tests/db/test_create_schema.py -v`

## Completion criteria

- AC-8: columns present in a freshly created DB; version differs from the previous value.

## Out of Scope

- Non-workflow domain schema blocks.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: Phase 2 (Schema)
- **Requirement ID**: `REQ-004`, `REQ-009`
- **Source issue**: issues/20261030-105723_wflease001_stale-attempt-lease.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261030-114516_wflease001_stale-attempt-lease.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261101-163219
- **Related target files**: `tests/db/test_create_schema.py`, `scripts/db/schema_sql.py`, `scripts/db/migrations_workflow.py`, `tests/db/test_migrations_workflow.py`
