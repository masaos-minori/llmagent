## Goal

## Goal

Add the `owner_id` and `lease_expires_at` columns to the canonical `attempts` DDL and set the workflow schema version string in `scripts/db/schema_sql.py` (REQ-004 / AC-8).

## Scope

- Extend the `attempts` CREATE block (`schema_sql.py:197-206`) with `owner_id TEXT` and `lease_expires_at TEXT` (both nullable, no CHECK, no index).
- Bump `WORKFLOW_SCHEMA_VERSION` (`:27`) from the current `"1.2.0"` to the landing-order value: `"1.3.0"` if this Plan's migration step registers before wftaskapi001's pending step, else `"1.4.0"` (Plan Assumptions, ledger landing order).

## Assumptions

- Plan `plans/20261030-114516_wflease001_stale-attempt-lease.md` is Frozen; its 18-row `Implementation Target Files` table (rows 17-18 added by the 2026-11-01 amendment) is the canonical scope and every target of this procedure is a row of that table.
- All baseline cites below were re-verified against branch `master` on 2026-11-01 (Plan Assumptions 'Re-verification record').
- Canonical semantics come from the Plan REQs (Plan `:37-46`): `parse_iso_utc` rejects naive input (REQ-001); no `mktime`/`strptime`/local time in recovery (REQ-002); unparseable timestamps are reported with distinct counts (REQ-003); nullable `owner_id`/`lease_expires_at` via a registered migration (REQ-004); owner and lease stamped at attempt start from the stage timeout plus a 30 s margin constant (REQ-005); staleness means lease expiry and `_STALE_GRACE_SEC` is removed (REQ-006); takeover is a conditional update requiring one row (REQ-007); legacy rows without a lease use the 3600 s age (REQ-008); tests use the production timestamp format (REQ-009); docs and ADR-001 INV-07 are amended (REQ-010).
- Owner decision (Plan UNK-02, 2026-10-30): deadline lease only — no heartbeat renewal, because `asyncio.wait_for` already bounds a normal stage.
- Ledger landing order (Plan UNK-06): `master` records code 2 / "1.2.0" (`migrations_workflow.py:42`); wftaskapi001 procedure 12 (`implementations/20261101-140834_12_scripts_db_migrations_workflow.py.md`, Pending) reserves the next slot. This Plan takes code 3 / "1.3.0" only if its step registers before wftaskapi001's, otherwise 4 / "1.4.0" (same rule as `implementations/20261101-145309_26_scripts_db_migrations_workflow.py.md`).
- Fencing dependency (Plan UNK-06): REQ-007's rejection of a late finish by the fenced owner lands with the wfrecovery001 conditional `finish_attempt` procedure (`implementations/20261101-145309_04_scripts_agent_workflow_attempt_ops.py.md`, Pending); at `master` `finish_attempt` is still unconditional (`attempt_ops.py:44-45`).
- `schema_sql.py` is row 6 of the frozen table and must land before rows 3-5 and the lease part of row 2 even though its table position is later (Plan Assumptions execution-order item); this document states that rule.

## Design decisions

- Nullable columns with no defaults so an existing database migrates with all-null values (AC-8) and lease-less legacy rows keep flowing through the REQ-008 age rule.
- The version string is the shared single source consumed by `workflow_schema.py:114` and the registry fingerprint; it must equal the target version of the registered step in procedure 17 at landing time.

## Alternatives considered

- Separate `workflow_attempt_lease` table — rejected: REQ-004 names columns on `attempts`, and takeover compare-and-swap needs them on the same row the `find` reads.

## Implementation
### Target file
`scripts/db/schema_sql.py`

### Procedure
1. Add the two columns to the `attempts` CREATE text (`:197-206`).
2. Update `WORKFLOW_SCHEMA_VERSION` (`:27`) to the agreed landing-order value at implementation time (coordinate with `implementations/20261101-140834_12_scripts_db_migrations_workflow.py.md` and `implementations/20261101-145309_26_scripts_db_migrations_workflow.py.md`).

### Method
DDL string and constant edits in the canonical schema template.

### Details
- The no-vec0 copy in `tests/db/test_create_schema.py` (`:392-421`) must be edited in the same commit (procedure 13) to keep the parity tests green.
- `tools/check_db_separation.py` ownership inventory is unaffected (same table, same domain file).

## Compatibility considerations

- High blast radius recorded in the Plan Risks: `schema_sql.py` had 12 commits in 30 days with sibling plans; only the `attempts` block is touched here.

## Security considerations

- All recovery/attempt SQL stays parameter-bound; owner and lease values are produced by the server (clock, host identity), never by caller-supplied strings.

## Rollback considerations

- Revert the DDL edit; if procedure 17 already registered, its step and the version constant revert in the same plan-internal order (17 before 06).

## Validation plan

- `uv run pytest tests/db/test_create_schema.py -v` (procedure 13).
- `uv run python tools/check_db_separation.py`
- Full sequence per `rules/toolchain.md`: `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus`, `PYTHONPATH=scripts uv run lint-imports`, `uv run bandit -r scripts/ -c pyproject.toml -ll`, `uv run python tools/check_module_size.py`.

## Completion criteria

- AC-8: the version constant differs from `"1.2.0"` and the new columns appear in the canonical DDL.

## Out of Scope

- The migration registration itself (procedure 17); required-column startup enforcement (procedure 07).

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
- **Requirement ID**: `REQ-004`
- **Source issue**: issues/20261030-105723_wflease001_stale-attempt-lease.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261030-114516_wflease001_stale-attempt-lease.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261101-163219
- **Related target files**: `scripts/db/schema_sql.py`, `scripts/db/migrations_workflow.py`, `scripts/agent/services/workflow_schema.py`, `tests/db/test_create_schema.py`, `tests/agent/test_repl_health.py`
