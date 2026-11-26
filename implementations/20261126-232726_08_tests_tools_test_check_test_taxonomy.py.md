## Goal

Test the checker's rule enforcement, baseline exemption, mixed-module detection, and report grouping
(REQ-003 — classification rule; REQ-004 — checker; REQ-005 — report mode).

## Scope
**Release unit**: taxonomy mechanism

## Assumptions

- Confirmed in Step 3a: `tests/tools/` holds one test module per checker, e.g.
  `tests/tools/test_check_conftest_integrity.py`, so this row follows that convention.
- This row is not a companion: it is named by four target rows (`pyproject.toml`, the checker, the baseline,
  and `tools/TOOL_DESCRIPTIONS.md`), so the companion rule's "exactly one other row" condition fails and the
  row keeps its own document.
- The tests build fixture trees under `tmp_path` rather than scanning the repository, so they do not need the
  `repo_scan` marker and are not affected by the `-m "not repo_scan"` deselection.

## Design decisions

- Assert the checker's public behavior only: reported findings, exit code, and the report sections. The
  internal AST reader is not asserted directly.
- One test per rule violation plus one for the baseline exemption, one for a mixed module, and one for the
  report grouping.

## Alternatives considered

- Running the checker against the real repository in this module — rejected: the result changes whenever a
  module is classified, which makes the test non-deterministic.

## Implementation
### Target file
`tests/tools/test_check_test_taxonomy.py` (new)
### Procedure

- Add cases for: a module with no marker outside the baseline; a `contract` module without a requirement
  citation; a module that claims both kinds at module level; a baseline module that is exempt; a mixed
  module detected through per-test markers; and the `--junit-xml` report grouping by module classname.
- Add the exit-code cases: characterization failure report-only, contract failure non-zero.

### Method

- Call the checker's entry point with a fixture tree and a fixture baseline file; assert the reported paths
  and the exit code.

### Details

- Keep the module under the test-file size convention; no repository scan.

## Compatibility considerations

- The module must not import the checker through a path that executes test collection.

## Security considerations

- N/A: no new disclosure surface.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- Unit — `uv run pytest tests/tools/test_check_test_taxonomy.py -v`.
- Sequence: lint → type → arch → security.

## Completion criteria

- Every rule violation is reported, the baseline exemption holds, mixed modules are detected, and the report
  grouping and exit codes match the run.

## Out of Scope

- The checker implementation (document 02).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Write the test module per Procedure/Method/Details | Pending | — | — | this row is the test itself |
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
- **Requirement ID**: `REQ-003` (classification rule), `REQ-004` (checker), `REQ-005` (report mode)
- **Source issue**: `issues/20261119-145310_cliplc012_characterization-test-split.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261126-215529_cliplc012_characterization-test-split.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-232726
- **Related target files**: `tests/tools/test_check_test_taxonomy.py`
