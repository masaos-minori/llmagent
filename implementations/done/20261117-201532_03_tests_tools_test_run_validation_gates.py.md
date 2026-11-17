## Goal

Extend `tests/tools/test_run_validation_gates.py` with the classification and renderer tests
the plan's Phase 1 writes first: `Not available` reasons, hidden vs visible rows, the count
line, `--verbose`, and the header base.

## Scope
**Release unit**: N/A: not part of a release unit

Single-file procedure for row 3 of the plan's frozen `Implementation Target Files` table:
`tests/tools/test_run_validation_gates.py` (REQ-001 to REQ-004 test coverage, AC-1 to AC-4).
The module already tests `classify`, `run_gate`, and selection; it never tests `main` or the
printed summary.

## Assumptions
- Written before the code (plan Phase 1): the new tests fail until the seq 01 renderer and
  the seq 02 runner edits land.
- Overlap with the wftool001 Plan on this file is compatible: that Plan adds gate-selection
  and hook-parity tests, these are classification and renderer tests (plan Assumptions).
- `run_gate` already takes an injectable `runner`, so reason tests need no new fixtures.

## Design decisions
- Assert on the rendered text through `main`/the renderer output (capsys), not by
  re-implementing the hide rule inside the test.

## Alternatives considered
N/A: test-only row; the cases are fixed by AC-1 to AC-4.

## Implementation
### Target file
`tests/tools/test_run_validation_gates.py`
### Procedure
Add, in one pass before any production change (plan Phase 1):
- reason classification of `run_gate`: `runtime-argument` for a placeholder gate,
  `missing-tool` for a not-found command, `os-error` for another `OSError`, empty for `Pass`
  and `Fail`; a constructor call without the new field still works (AC-1);
- renderer cases: a hidden runtime-argument row plus visible `missing-tool` and `Fail` rows
  → no hidden row printed, exactly one count line; none hidden → no count line (AC-2);
- `--verbose` prints every row and the exit code and selected gates equal a run without it
  (AC-3);
- `--base <ref>` prints that ref in the header (AC-4).
### Method
Keep existing test functions unchanged; reuse the module's existing gate fixtures.
### Details
N/A: no fixtures beyond what the module already has.

## Compatibility considerations
Tests run against the current code until the seq 01/02 documents land; keep each new test
independent so partial landing is diagnosable.

## Security considerations
N/A: test-only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/tools/test_run_validation_gates.py -v` — new tests fail first (plan
  Phase 1), pass after seq 01 and seq 02 land.
- `uv run ruff format tools tests/tools`; `uv run ruff check tools tests/tools`;
  `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools` — clean.

## Completion criteria
AC-1 to AC-4 each map to a named test that passes after the seq 01/02 code lands, and no
existing test changed (plan Tests section).

## Out of Scope
The renderer module (seq 01), the runner edits (seq 02), documentation (seq 04, 05).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Write the classification, renderer, `--verbose`, and header tests (they fail first) | Completed | — | 20261117-231500 | plan Phase 1 tests written first: 12 failed, 86 existing passed |
| 2 | Re-run the module green after the seq 01 and seq 02 code lands; lint and types | Completed | — | 20261117-231500 | plan Phase 5 98 passed after seq 01/02 landed; ruff clean; mypy scripts/ tests/eventbus tools clean |

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
- **Requirement ID**: `REQ-001` to `REQ-004` (classification and output-behavior test coverage)
- **Source issue**: issues/20261117-123335_wftool006_gate-output-noise.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261117-125737_wftool006_gate-output-noise.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261117-201532
- **Related target files**: `tests/tools/test_run_validation_gates.py`