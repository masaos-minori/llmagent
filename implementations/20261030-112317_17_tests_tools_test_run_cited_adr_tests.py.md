# Implementation Procedure: tests/tools/test_run_cited_adr_tests.py

## Goal

Create the runner's test module with passed/skipped/xfailed/missing result fixtures
(REQ-003; test-side of doc 03).

## Scope

**In scope:**
- New module testing `extract_cited_node_ids`, the new `_classify_outcome` (new) and
  `_cited_exceptions` (new) (doc 03) with synthetic pytest outputs and a synthetic matrix,
  plus one end-to-end case against a tmp generated test file that skips.

**Out of scope:**
- Runner implementation (doc 03).

## Assumptions
- No test module exists today for the runner (`tests/tools/` has no runner tests at
  HEAD); naming follows `tests/tools/test_check_*` siblings.
- The runner is loaded by file path in tests the same way it loads the checker
  (`.github/run_cited_adr_tests.py:33-44`) since `.github/` is not an importable
  package — use `importlib.util.spec_from_file_location` in the fixture helper (new).
- `_run_pytest` becomes output-capturing (doc 03) so tests monkeypatch it to inject
  canned `(rc, output)` pairs for classification cases.

## Design decisions
- Unit-level classification tests (monkeypatched subprocess) + one real end-to-end skip
  case (tmp dir pytest run) — keeps the suite fast and hermetic while proving the real
  pytest `-rsq` summary parsing works.

## Alternatives considered
- CI-output recording files: rejected — brittle across pytest versions.

## Implementation
### Target file
`tests/tools/test_run_cited_adr_tests.py` (new)

### Procedure
1. Loader helper (new) importing the runner by path from `.github/`.
2. `test_classify_passed/skipped/xfailed/missing` (new) using canned outputs.
3. `test_exception_marker_allows_skip` (new): synthetic matrix lines with
   `Exception: <id>` → approved-exception reason.
4. `test_end_to_end_skipped_citation` (new): tmp package with one `skip`-marked test,
   cite it via a tmp matrix, assert failure without marker and pass with marker.

### Method
New module only; no existing tests touched.

### Details
- Canned outputs mirror real pytest 8 `-rsq` summary lines (`SKIPPED [1] ...`,
  `XFAIL ...`).

## Compatibility considerations
Test-only file; must be collected by the default `-m "not integration"` selection.

## Security considerations
N/A.

## Rollback considerations
N/A: delete the file (single target).

## Validation plan
- `uv run pytest tests/tools/test_run_cited_adr_tests.py` (red until doc 03 lands);
  full `rules/toolchain.md`.

## Completion criteria
All four outcome classes and both exception states are covered and green after doc 03.

## Out of Scope
Runner code, checker code.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Create the test module per Procedure | Pending | — | — | Test-first: red until doc 03 |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-003`
- **Source issue**: `issues/20261029-104505_adrcov001_contract-manifests-invariant-coverage.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261030-001153_adrcov001_contract-manifests-invariant-coverage.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-112317
- **Related target files**: `tests/tools/test_run_cited_adr_tests.py`
