# Procedure: remove the fetch-layer presence pre-check

## Goal

Make `scripts/agent/services/mcp_tool_discovery_fetch.py` report the validator's result once
instead of running its own presence pre-check, so a missing schema-2.0 field is named in exactly
one finding (Plan REQ-003; AC-3).

## Scope

- Modify only `scripts/agent/services/mcp_tool_discovery_fetch.py`.
- In scope: deletion of `_REQUIRED_SCHEMA_V2_FIELDS` and its branch in `_entry_schema_error()`,
  and the module docstring/comment text that describes the pre-check.
- Out of scope: the validator change (procedure 01), tests (procedures 03, 04), the document
  (procedure 05), registry building and severity handling.

## Assumptions

- Procedure 01 has added the presence checks for all four fields to `validate_tool_schema_v2()`,
  so removing the pre-check does not make the discovery path more permissive (Plan Assumption:
  the fetch layer already rejects entries that lack any of the four fields).
- No test asserts the current pre-check wording "missing required schema-2.0 field(s)" (Plan
  Background; re-verify with grep before editing).

## Design decisions

- The single gate is `validate_tool_schema_v2()`; `_entry_schema_error()` keeps its existing
  shape: type checks for `description`/`inputSchema`, then the validator's joined problems
  (lines 231-236 today). Plan Design (single source): the validator is documented as the last
  line of defense.

## Alternatives considered

- Keep the pre-check and skip the validator call when it fires — rejected: it keeps two owners
  of the same contract and is exactly the double-report path the Plan removes.

## Implementation

### Target file

`scripts/agent/services/mcp_tool_discovery_fetch.py`

### Procedure

1. Delete the constant `_REQUIRED_SCHEMA_V2_FIELDS` (lines 47-52) together with its explanatory
   comment block (lines 45-46). Verify with `grep -rn _REQUIRED_SCHEMA_V2_FIELDS` that no other
   use remains before deleting.
2. Delete the `missing_fields` branch in `_entry_schema_error()` (lines 224-229). Keep the
   `description`/`inputSchema` type checks (lines 216-222) and the existing validator-call
   branch (lines 231-236) unchanged.
3. Update the module docstring (line 10 area) only if it names the removed pre-check, so it
   describes `_entry_schema_error` as: required-field type checks plus one
   `validate_tool_schema_v2()` call.

### Method

Pure deletion plus a docstring touch-up; no signature changes, no control-flow additions.

### Details

- After the change, an entry missing `resource_scope_keys` produces one finding whose message is
  `<server_key>: tool <name> failed schema-2.0 validation: resource_scope_keys is required` —
  the field name appears once, satisfying AC-3 (procedure 04 adds the single-report test).
- Exclusion and severity behavior is unchanged: `_entry_schema_error` still returns a single
  error string and the caller `_validate_entry` turns it into the same per-entry WARNING/FATAL
  finding; `mcp_tool_discovery_registry.py` (reference file) is untouched.
- `_entry_optional_field_error()` keeps validating `status`, `enabled` and `capabilities` only.

## Compatibility considerations

- Findings wording for a missing field changes from "missing required schema-2.0 field(s): X" to
  "failed schema-2.0 validation: X is required". Existing discovery tests assert only the field
  name substring (for example `test_missing_resource_scope_kind_produces_warning_and_is_excluded`
  asserts `"resource_scope_kind" in f.message`), so they keep passing; no test asserts the old
  full wording (Plan Assumption; grep `missing required schema-2.0` before editing to confirm).
- Sequencing with the mcpcompat001 plan procedures (`implementations/20261028-013216_*.md`):
  none of them edit this file, so no rebase is needed here; the shared test file rebase is
  handled in procedure 04.

## Security considerations

None beyond preserving fail-closed behavior: every missing or mistyped mandatory field still
produces a per-entry finding and exclusion from the registry.

## Rollback considerations

Single-file deletion; revert the commit restores the constant and the branch.

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| Integration | `uv run pytest tests/agent/services -q` | Pass; a missing field is reported once; exclusion and severity unchanged |
| Static | `uv run mypy --no-namespace-packages scripts/`; `PYTHONPATH=scripts uv run lint-imports`; `uv run ruff check scripts/agent/services/mcp_tool_discovery_fetch.py`; `uv run bandit -r scripts/agent/services/mcp_tool_discovery_fetch.py -c pyproject.toml -ll` | No new finding; six contracts kept; `vulture scripts/ --min-confidence 80` reports no new finding for the removed constant |

## Completion criteria

- AC-3: a tool lacking a mandatory field is excluded and the finding names the field once;
  severity unchanged.
- AC-7: the full check list passes.
- `_REQUIRED_SCHEMA_V2_FIELDS` no longer exists in the repository.

## Out of Scope

- Validator behavior (procedure 01).
- Test changes (procedures 03, 04).
- Document rewrite (procedure 05).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261028-110833 | 20261028-110833 | Changed: scripts/agent/services/mcp_tool_discovery_fetch.py (removed _REQUIRED_SCHEMA_V2_FIELDS and missing_fields branch); stale check clean; grep confirmed no other use |
| 2 | Add or update tests per Validation plan | Completed | 20261028-110833 | 20261028-111618 | agent/services tests: 306 passed, 1 failed (legacy resource_scope test owned by procedure 04) full suite 10265 passed |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261028-110833 | 20261028-111618 | ruff/mypy/lint-imports/bandit/vulture pass; full-suite run pending joint application joint full-suite run after procedures 01-05 applied: 10265 passed, 8 skipped; diff-cover 95% |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261028-111618 | 20261028-111618 | N/A: no docs/00_index.md mapping needed; docs handled by procedure 05 |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-003 (AC-3)
- **Source issue**: issues/20261027-104324_mcpcompat003_align-legacy-resource-scope.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261027-111522_mcpcompat003_align-legacy-resource-scope.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261028-065435
- **Related target files**: scripts/agent/services/mcp_tool_discovery_fetch.py