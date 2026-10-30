## Goal

Add one strict UTC ISO-8601 parser next to `now_iso()` in `scripts/shared/json_utils.py` (`REQ-001`, strict parser for the persisted timestamp format), so recovery reads what production writes without local-time conversion.

## Scope

- Modify only `scripts/shared/json_utils.py`.
- The local `Z` handling in `scripts/agent/memory/scoring.py` stays unchanged (out of scope).

## Assumptions

- Plan Dependencies (`plans/20261030-114516_wflease001_stale-attempt-lease.md` Scope): this row is Plan Phase 1 and has no dependency on the schema, on `plans/20261029-214108_dbmig001_forward-only-db-migrations.md`, or on `plans/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md`; it can land first. Execution order follows the Plan's phases, not `seq`.
- `now_iso()` returns `YYYY-MM-DDTHH:MM:SSZ` (`json_utils.py:45-51`) and the workflow DDL defaults use the same format.
- Python is 3.13 (`AGENTS.md` Environment): `datetime.fromisoformat` accepts a trailing `Z`, offsets, and fractional seconds.
- No existing helper named `parse_iso_utc` (new) exists in `scripts/` (checked in this cycle).

## Design decisions

- `parse_iso_utc` (new) is strict: naive input (no timezone) is rejected with `ValueError`, so a malformed or legacy value is never silently read as local time.
- Success returns an aware `datetime` converted to UTC.

## Alternatives considered

- Reuse the local `fromisoformat(created_at.replace("Z", "+00:00"))` in `scripts/agent/memory/scoring.py`: rejected, not importable from `agent.workflow` without coupling to an unrelated module, and it accepts naive input.

## Implementation

### Target file

`scripts/shared/json_utils.py`

### Procedure

1. Add `parse_iso_utc` (new) directly after `now_iso` (`:45`), typed `(value: str) -> datetime`.
2. Parse with `datetime.fromisoformat`; if the result has no `tzinfo`, raise `ValueError` naming the value; convert aware results to UTC with `astimezone(UTC)`.
3. Document the accepted forms in the docstring (`Z`, explicit offset, fractional seconds) and that naive and malformed strings raise `ValueError`.

### Method

- Reuse the existing imports (`UTC`, `datetime` at `:14`); no new dependency.
- Let `fromisoformat` raise its own `ValueError` for malformed input; do not catch and re-wrap beyond the naive-input case.

### Details

- Keep the function pure (no logging); callers decide how to report.
- The module is a shared helper (`scripts/shared/`); do not import from `agent`.

## Compatibility considerations

- Additive public helper; no existing behavior changes.

## Security considerations

- Input is a persisted timestamp string; the parser raises on anything unexpected and does not evaluate it.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run pytest tests/shared/test_json_utils.py -v` (`Z`, offset, fractional seconds, malformed, naive; a test using `now_iso()` output)
- `uv run ruff format scripts/shared/json_utils.py`, `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus`, `PYTHONPATH=scripts uv run lint-imports`

## Completion criteria

- `parse_iso_utc` (new) returns the correct UTC instant for `now_iso()` output, `+09:00`-style offsets, and fractional seconds, and raises `ValueError` for naive and malformed input.

## Out of Scope

- Callers (`state_store.py` row), tests (`tests/shared/test_json_utils.py` row), changing `now_iso()` output.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `parse_iso_utc` (new) and its docstring | Pending | — | — | Plan Phase 1; independent |
| 2 | Add or update tests per Validation plan | Pending | — | — | Test row's document |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: REQ-001 (strict UTC ISO-8601 parser)
- **Source issue**: issues/20261030-105723_wflease001_stale-attempt-lease.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261030-114516_wflease001_stale-attempt-lease.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-130005
- **Related target files**: scripts/shared/json_utils.py
