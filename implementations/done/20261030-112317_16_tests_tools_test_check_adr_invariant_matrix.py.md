# Implementation Procedure: test_check_adr_invariant_matrix.py new rule cases

## Goal

Extend the checker's test module with synthetic-repo fixtures for marker detection,
cadence/expected-evidence rules, and exception parsing (REQ-002, REQ-004; test-side of
docs 01-02).

## Scope

**In scope:**
- New test functions in `tests/tools/test_check_adr_invariant_matrix.py` covering:
  cited node carrying `@pytest.mark.skip`/`skipif`/`xfail` → `ERROR`; Manual/Partial
  row missing cadence/expected-evidence → `_CADENCE_RULE_SEVERITY` (new) severity (doc 02);
  row with `Exception: <id>` marker → OK; malformed marker → reported.
- Synthetic fixtures use the existing `_matrix(*rows)` builder
  (`tests/tools/test_check_adr_invariant_matrix.py:28`, re-verified 2026-10-31) plus
  temp-dir fake test files for the AST marker cases.
- Add a negative case: a synthetic cited file carrying only
  `pytestmark = pytest.mark.usefixtures(...)` must NOT trigger the marker rule — pins
  the match to `skip`/`skipif`/`xfail` only (the live cited file
  `tests/mcp_servers/shell/test_shell_server_auth.py` has exactly this marker).

**Out of scope:**
- Live-repo validation (already excluded by the module docstring convention at `:5-8`).

## Assumptions
- Existing module calls checker functions directly (`:17-21`) — new cases follow the
  same pattern; the AST marker path needs a `tmp_path` synthetic test file since the
  checker reads real files for decorator parsing.
- Test-first: new cases are red until doc 02 lands; they gate its completion.

## Design decisions
- One fixture matrix per rule (not a shared mega-matrix) so severity changes in doc 02
  flip exactly the intended assertions.

## Alternatives considered
- Live-repo fixture snapshots: rejected — module already delegates live validation to
  running the tool (docstring `:5-8`).

## Implementation
### Target file
`tests/tools/test_check_adr_invariant_matrix.py`

### Procedure
1. Add `test_skipped_citation_reports_error` (new), `test_xfail_citation_reports_error` (new),
   `test_exception_marker_suppresses_skip_error` (new) backed by tmp synthetic test
   files.
2. Add `test_missing_cadence_warning` (new), `test_cadence_present_ok` (new) driving the
   cadence rule against matrix rows built with `_matrix`.
3. Add marker-grammar cases (valid/invalid `Exception:` strings).

### Method
Pure additions; existing tests byte-identical as characterization locks.

### Details
- Assert severity via the Issue/severity objects the checker functions already return.

## Compatibility considerations
No public API change; existing test names unchanged.

## Security considerations
N/A.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/tools/test_check_adr_invariant_matrix.py` (new cases red before
  doc 02, green after); full `rules/toolchain.md`.

## Completion criteria
Each REQ-002/REQ-004 rule has a passing fixture case, and all pre-existing cases still
pass.

## Out of Scope
Checker implementation, runner tests (doc 17).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add or update tests per Validation plan | Completed | 20261031-095642 | 20261031-095642 | Test-first: red until doc 02 Cases co-authored with doc 02 cycle |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261031-095642 | pytest 67 passed; ruff+mypy green; live checker green |

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
- **Related target files**: `tests/tools/test_check_adr_invariant_matrix.py`