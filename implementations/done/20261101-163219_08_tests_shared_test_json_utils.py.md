## Goal

Add parser tests for `parse_iso_utc` to `tests/shared/test_json_utils.py` (REQ-001, REQ-009 / AC-1).

## Scope

- New `TestParseIsoUtc` class after `TestNowIsoRaw` (`:453-514`): `Z` format (including `now_iso()` output round-trip, `:45`), `+09:00` offset converted to the same instant, fractional seconds, naive string rejected (`ValueError`), malformed string rejected, non-string rejected, result is timezone-aware UTC.

## Assumptions

- Plan `plans/20261030-114516_wflease001_stale-attempt-lease.md` is Frozen; its 18-row `Implementation Target Files` table (rows 17-18 added by the 2026-11-01 amendment) is the canonical scope and every target of this procedure is a row of that table.
- All baseline cites below were re-verified against branch `master` on 2026-11-01 (Plan Assumptions 'Re-verification record').
- Canonical semantics come from the Plan REQs (Plan `:37-46`): `parse_iso_utc` rejects naive input (REQ-001); no `mktime`/`strptime`/local time in recovery (REQ-002); unparseable timestamps are reported with distinct counts (REQ-003); nullable `owner_id`/`lease_expires_at` via a registered migration (REQ-004); owner and lease stamped at attempt start from the stage timeout plus a 30 s margin constant (REQ-005); staleness means lease expiry and `_STALE_GRACE_SEC` is removed (REQ-006); takeover is a conditional update requiring one row (REQ-007); legacy rows without a lease use the 3600 s age (REQ-008); tests use the production timestamp format (REQ-009); docs and ADR-001 INV-07 are amended (REQ-010).
- Owner decision (Plan UNK-02, 2026-10-30): deadline lease only — no heartbeat renewal, because `asyncio.wait_for` already bounds a normal stage.
- Ledger landing order (Plan UNK-06; fixed by the 2026-11-01 pre-execution verification): wftaskapi001 procedure 12 has landed (`implementations/done/20261101-140834_12_scripts_db_migrations_workflow.py.md`) and registered code 3 / "1.3.0" (`migrations_workflow.py:42`, `WORKFLOW_TARGET_VERSION` = 3 at `:49`). This Plan takes code 4 / "1.4.0": procedure 17 registers `workflow_attempt_lease` with `from_version=3, to_version=4`, and procedure 06 sets `WORKFLOW_SCHEMA_VERSION` to "1.4.0". The still-Pending wfrecovery001 procedure 26 (`implementations/20261101-145309_26_scripts_db_migrations_workflow.py.md`) takes 5 / "1.5.0" when it lands after this Plan.
- Fencing dependency (Plan UNK-06): REQ-007's rejection of a late finish by the fenced owner lands with the wfrecovery001 conditional `finish_attempt` procedure (`implementations/20261101-145309_04_scripts_agent_workflow_attempt_ops.py.md`, Pending); at `master` `finish_attempt` is still unconditional (`attempt_ops.py:44-45`).
- Test style follows the existing classes in this file (plain `unittest`-style classes with pytest-compatible asserts).

## Design decisions

- The `now_iso()` round-trip case is the AC-1 anchor: `parse_iso_utc(now_iso())` parses to the same wall second and the returned value carries `timezone.utc`.

## Alternatives considered

- Hypothesis property tests — rejected: not used in this repo's shared test convention.

## Implementation
### Target file
`tests/shared/test_json_utils.py`

### Procedure
1. Append `TestParseIsoUtc` with the case list above.
2. Import `parse_iso_utc` in the module import block at `:15-23` (insert after `now_iso_raw` at `:19`).

### Method
Test-only file; no fixtures needed.

### Details
- Naive rejection is asserted with `pytest.raises(ValueError)` and a message-substring check (`naive`).
- Offset equality compares aware datetimes (`==`), never wall-clock strings.

## Compatibility considerations

- Existing `TestNowIso` (`:382-450`) and `TestNowIsoRaw` (`:453-514`) tests stay untouched (out-of-scope functions).

## Security considerations

- All recovery/attempt SQL stays parameter-bound; owner and lease values are produced by the server (clock, host identity), never by caller-supplied strings.

## Rollback considerations

- Delete the class.

## Validation plan

- `uv run pytest tests/shared/test_json_utils.py -v` — new cases pass on procedure 01's implementation and fail against `master` without it.

## Completion criteria

- AC-1 fully covered by the new class.

## Out of Scope

- Any change to existing `now_iso`/`now_iso_raw` tests.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20261101-205438 |  |
| 2 | Add or update tests per Validation plan | Completed | — | 20261101-205438 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261101-205438 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20261101-205449 | N/A: no docs/00_index.md task-scope mapping for these files |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: Phase 1 (Timezone-safe parsing and conservative detection)
- **Requirement ID**: `REQ-001`, `REQ-009`
- **Source issue**: issues/20261030-105723_wflease001_stale-attempt-lease.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261030-114516_wflease001_stale-attempt-lease.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261101-163219
- **Related target files**: `tests/shared/test_json_utils.py`, `scripts/shared/json_utils.py`