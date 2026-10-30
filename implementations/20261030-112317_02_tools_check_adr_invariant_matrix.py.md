# Implementation Procedure: check_adr_invariant_matrix.py marker and cadence rules

## Goal

Extend `tools/check_adr_invariant_matrix.py` with static skip/xfail marker detection on
cited nodes, cadence/expected-evidence validation for Manual/Partial rows, and parsing of
approved-exception references in matrix rows (REQ-002, REQ-004; plan AC-1, AC-3).

## Scope

**In scope:**
- AST-based detection of `pytest.mark.skip`, `pytest.mark.skipif`, `pytest.mark.xfail`
  decorators and module-level `pytestmark` on the file part of each cited node.
- ERROR when a cited node carries such a marker and the matrix row has no
  `Exception: <id>` reference; OK when the reference exists.
- Manual/Partial cell-text validation: missing `Cadence:` or `Expected evidence:`
  produces `WARNING`, switched to `ERROR` by one module constant (single flag flip).
- Parsing the new vocabulary fields is additive to `_matrix_rows`/`_split_row`.

**Out of scope:**
- Runtime outcome handling (row 03); manifest generation (row 05).
- `tools/check_adr_reference.py` — plan explicitly excludes it.

## Assumptions
- Verified at HEAD `124e340b4`: 447 lines; no skip/xfail logic (only "skipping the header
  row" comment at `:87`); AST node resolution already lives in `_defined_names` (`:118`)
  and `_node_problem` (`:138`); severity literals `ERROR` (`:175`) and the
  `_BODY_RULE_SEVERITY` constant.
- Depends on row 01 vocabulary landing first (plan Dependencies "checker parses the
  matrix vocabulary").

## Design decisions
- Reuse the existing AST walk in `_defined_names`: extend it to also collect decorator
  names per node while walking (single pass, no second parse).
- Severity ladder as a module constant `_CADENCE_RULE_SEVERITY` (new) (default `WARNING`) so
  REQ-004 enforcement after the migration window is a one-line change.
- Exception reference grammar lives here as the single parser shared with the runner
  (the runner already imports this module by path for single-sourcing — mirror that).

## Alternatives considered
- Detecting skips only at runtime: rejected — static markers are visible in the AST and
  catching them pre-execution is cheaper; runtime results cannot see nodes excluded by
  `-m "not integration"` selection boundaries.

## Implementation
### Target file
`tools/check_adr_invariant_matrix.py`

### Procedure
1. Extend `_defined_names` to return node → decorator-name sets (or add a parallel
   `_node_markers(path)` helper).
2. In `check_invariant_matrix_test_paths` add the marker rule producing
   `severity="ERROR"` when a marker exists without an exception reference parsed from
   the same row's Verification Status cell.
3. Add `check_manual_partial_fields(lines)` emitting
   `severity=_CADENCE_RULE_SEVERITY` Issues.
4. Register both in `collect_issues()`; keep `render_json` schema unchanged.

### Method
Extension of existing functions plus one new check function; no behavior removal.

### Details
- Exception reference substring grammar: `Exception: [A-Za-z0-9._-]+` inside the status
  cell; document it in row 01 prose.

## Compatibility considerations
- Pre-commit hook `.pre-commit-config.yaml:54-59` runs this module unchanged; new ERRORs
  appear only for rows that violate the new rules (risk: 27 existing skips — Phase 1
  classifies cited ones first, per plan Risks).

## Security considerations
- No shell, no eval; AST parse only.

## Rollback considerations
- Remove the two new check registrations to restore prior behavior; rules are additive.

## Validation plan
- `uv run pytest tests/tools/test_check_adr_invariant_matrix.py` (row 16 adds cases);
  `uv run python tools/check_adr_invariant_matrix.py` green on the live repo after row 01
  backfill; `uv run mypy tools/check_adr_invariant_matrix.py` explicitly.

## Completion criteria
- AC-1 demonstrated in fixtures; live-repo run green after classification of cited skips.

## Out of Scope
- Runner result parsing (row 03); matrix content edits (row 01).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement marker + cadence rules | Pending | — | — |  |

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
- **Requirement ID**: `REQ-002`, `REQ-004`
- **Source issue**: `issues/20261029-104505_adrcov001_contract-manifests-invariant-coverage.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261030-001153_adrcov001_contract-manifests-invariant-coverage.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-112317
- **Related target files**: `tools/check_adr_invariant_matrix.py`
