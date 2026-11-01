## Goal

## Goal

Register the lease `ADD COLUMN` migration step and version codes in `scripts/db/migrations_workflow.py` (REQ-004 / AC-8).

## Scope

- Append a `MigrationSpec` `workflow_attempt_lease` to `REGISTRY` (`:246-262`): `from_version=2`, `to_version=3` (or `4` if wftaskapi001's pending step registers first), `mutation_sql` = `ALTER TABLE attempts ADD COLUMN owner_id TEXT;` + `ALTER TABLE attempts ADD COLUMN lease_expires_at TEXT;`, precondition: attempts table exists and the prior workflow step is applied, postcondition: both columns present via `PRAGMA table_info`.
- Extend `WORKFLOW_VERSION_CODES` (`:42`, currently `{"1.1.0": 0, "1.2.0": 2}`) with the landing-order mapping (`"1.3.0": 3` or `"1.4.0": 4`) and raise `WORKFLOW_TARGET_VERSION` (`:48`) to match procedure 06's version string.

## Assumptions

- Plan `plans/20261030-114516_wflease001_stale-attempt-lease.md` is Frozen; its 18-row `Implementation Target Files` table (rows 17-18 added by the 2026-11-01 amendment) is the canonical scope and every target of this procedure is a row of that table.
- All baseline cites below were re-verified against branch `master` on 2026-11-01 (Plan Assumptions 'Re-verification record').
- Canonical semantics come from the Plan REQs (Plan `:37-46`): `parse_iso_utc` rejects naive input (REQ-001); no `mktime`/`strptime`/local time in recovery (REQ-002); unparseable timestamps are reported with distinct counts (REQ-003); nullable `owner_id`/`lease_expires_at` via a registered migration (REQ-004); owner and lease stamped at attempt start from the stage timeout plus a 30 s margin constant (REQ-005); staleness means lease expiry and `_STALE_GRACE_SEC` is removed (REQ-006); takeover is a conditional update requiring one row (REQ-007); legacy rows without a lease use the 3600 s age (REQ-008); tests use the production timestamp format (REQ-009); docs and ADR-001 INV-07 are amended (REQ-010).
- Owner decision (Plan UNK-02, 2026-10-30): deadline lease only — no heartbeat renewal, because `asyncio.wait_for` already bounds a normal stage.
- Ledger landing order (Plan UNK-06): `master` records code 2 / "1.2.0" (`migrations_workflow.py:42`); wftaskapi001 procedure 12 (`implementations/20261101-140834_12_scripts_db_migrations_workflow.py.md`, Pending) reserves the next slot. This Plan takes code 3 / "1.3.0" only if its step registers before wftaskapi001's, otherwise 4 / "1.4.0" (same rule as `implementations/20261101-145309_26_scripts_db_migrations_workflow.py.md`).
- Fencing dependency (Plan UNK-06): REQ-007's rejection of a late finish by the fenced owner lands with the wfrecovery001 conditional `finish_attempt` procedure (`implementations/20261101-145309_04_scripts_agent_workflow_attempt_ops.py.md`, Pending); at `master` `finish_attempt` is still unconditional (`attempt_ops.py:44-45`).
- Landing-order rule (Plan UNK-06, shared with `implementations/20261101-145309_26_scripts_db_migrations_workflow.py.md` and `implementations/20261101-140834_12_scripts_db_migrations_workflow.py.md`): the plan whose step registers first takes code 3 / "1.3.0"; the others shift up. The codes are fixed at implementation time, not in this document.
- dbmig001 registry semantics (forward-only, backup gate, per-step pre/post conditions) are already implemented in this module (`MigrationRunner`, stamped markers).

## Design decisions

- Two nullable `ADD COLUMN` statements in one step (Plan Design 'Migration'): an existing database with `running` rows migrates with null values, which is exactly the legacy-row population REQ-008 governs.
- The step runs before the code that writes the columns (procedures 03-05) and before the required-column check (procedure 07) — the plan-internal order 17 → 03/04/05 → 07.

## Alternatives considered

- Table-rebuild migration — rejected: SQLite `ADD COLUMN` is in-place and the columns are nullable with no constraints.
- Un-registered ad-hoc ALTER — rejected: dbmig001 forward-only registry is the contract (Plan Reference Files).

## Implementation
### Target file
`scripts/db/migrations_workflow.py`

### Procedure
1. Add the `MigrationSpec` entry after `workflow_tool_call_state`.
2. Update `WORKFLOW_VERSION_CODES` and `WORKFLOW_TARGET_VERSION` with the landing-order values.
3. Extend the fingerprint/validation path (`:159-163` version-code check) automatically through the codes map — verify no hardcoded list exists elsewhere in the module.

### Method
Registry data edit; runner code unchanged.

### Details
- Mutation SQL follows the existing `_TOOL_STATE_MUTATION_SQL` pattern (module-level SQL constants near `:246`).
- Postcondition raises on missing columns exactly like `_postcondition_tool_state` (`:240-242` pattern).

## Compatibility considerations

- Shared file with wfrecovery001 (landed codes 0-2) and pending wftaskapi001 code 3 reservation — coordinate at landing (Blocker Log).
- Deploy prerequisite per Plan Phase 5: the `/opt/llm/db/workflow.sqlite` migration runs with the dbmig001 backup gate; deploying is the user's decision.

## Security considerations

- All recovery/attempt SQL stays parameter-bound; owner and lease values are produced by the server (clock, host identity), never by caller-supplied strings.

## Rollback considerations

- Forward-only registry: rollback is restoring the pre-migration backup taken by the dbmig001 gate (Plan Design 'Migration').

## Validation plan

- `uv run pytest tests/db/test_migrations_workflow.py tests/db/test_create_schema.py -v` (procedure 18).
- `uv run python tools/check_db_separation.py`
- Full sequence per `rules/toolchain.md`: `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus`, `PYTHONPATH=scripts uv run lint-imports`, `uv run bandit -r scripts/ -c pyproject.toml -ll`, `uv run python tools/check_module_size.py`.

## Completion criteria

- AC-8: a database at the previous version with existing `running` rows migrates with the new columns null.

## Out of Scope

- Data backfill of `owner_id`/`lease_expires_at` for existing rows (they stay null by design).

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
| 1 | Ledger code/version values are Blocked until the landing order against pending wftaskapi001 step (code 3 / "1.3.0" reservation) is fixed | No | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: Phase 2 (Schema)
- **Requirement ID**: `REQ-004`
- **Source issue**: issues/20261030-105723_wflease001_stale-attempt-lease.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261030-114516_wflease001_stale-attempt-lease.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261101-163219
- **Related target files**: `scripts/db/migrations_workflow.py`, `scripts/db/schema_sql.py`, `scripts/agent/services/workflow_schema.py`, `tests/db/test_migrations_workflow.py`, `tests/db/test_create_schema.py`
