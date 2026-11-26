## Goal
- Register `tools/compare_test_baseline.py` and its baseline in `tools/TOOL_DESCRIPTIONS.md` so `tools/check_tool_descriptions_sync.py` passes (REQ-005).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: one Index row and one row of the Test-Related Checkers table. Out of scope: any other row or section, and the naming-convention list (existing tools such as `scan_change_consumers.py` already use verbs outside it).

## Assumptions
- Verified in Step 3a: the Index table starts at line 61 and lists `check_mock_patch_targets.py` among the test-related checkers; the Test-Related Checkers table (line 240) ends with the `check_conftest_integrity.py` row; `tools/check_tool_descriptions_sync.py` requires every `tools/*.py` to be listed in the document.
- Procedure 01 creates the tool first (`seq` order), so the sync check can pass here.

## Design decisions
- The Index row goes directly after the `check_mock_patch_targets.py` row with Category `Test`; the detail row goes after the `check_conftest_integrity.py` row. The description states: input (`--junitxml` file), the baseline path, exit codes 0, 1, 2, the four result classes, that a plain run writes nothing, `--update` and `--add ID --reason TEXT` with `--dry-run`, and that it never changes test selection.

## Alternatives considered
- N/A: placement follows the existing grouping.

## Implementation
### Target file
`tools/TOOL_DESCRIPTIONS.md`

### Procedure
1. Add the Index row: `| `compare_test_baseline.py` | Test | Read-only: classify the failures of a pytest JUnit XML file against `known_test_failures_baseline.txt` (new, fixed, not run, known count); explicit `--update` and `--add` modes |` (write real backticks, not the escapes shown here).
2. Add the detail row in the Test-Related Checkers table: Target column `a JUnit XML file from `pytest --junitxml`` and the description above, in the style of the neighboring rows.
3. Run the sync check.

### Method
- Two inserted table rows; no other line changes. The text is English.

### Details
- Do not claim a hook, a gate, or a CI step: none exists (Plan Out of Scope).

## Compatibility considerations
- N/A: documentation only.

## Security considerations
- N/A: documentation only.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run python tools/check_tool_descriptions_sync.py`; `uv run python tools/check_docs_quality.py` is not applicable (the file is under `tools/`); the pre-commit hook "Check tools/TOOL_DESCRIPTIONS.md sync" runs on commit.

## Completion criteria
- The sync check passes and both rows exist.

## Out of Scope
- The tool-gates row (procedure 05) and the workflow rule (procedure 06).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261126-171205 | 20261126-171205 | wfeff002: full suite 15737 passed, 4 failed (3 pre-existing tests/mcp_servers/git; 1 eventbus flake, passes alone and on the clean tree) |
| 2 | Run the documentation checkers named in `rules/tool-gates.md` "When to run which tool" | Completed | 20261126-171205 | 20261126-171205 | wfeff002: full suite 15737 passed, 4 failed (3 pre-existing tests/mcp_servers/git; 1 eventbus flake, passes alone and on the clean tree) |

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
- **Requirement ID**: `REQ-005`
- **Source issue**: issues/20261126-151437_wfeff002_test-failure-baseline.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261126-161137_wfeff002_test-failure-baseline.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-164413
- **Related target files**: `tools/TOOL_DESCRIPTIONS.md`
