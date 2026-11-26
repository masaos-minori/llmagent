## Goal
- Create `tools/known_test_failures_baseline.txt`, the baseline read by `tools/compare_test_baseline.py`: a header that states the entry format and the rules, and no entries (REQ-003).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the new data file. Out of scope: any entry (no tracking issue exists for the current failures, Plan UNK-02), and the reader (procedure 01).

## Assumptions
- Verified in Step 3a: the other baselines under `tools/` use `#` comment headers and one entry per line (`tools/check_archived_status_baseline.txt` header read), so this file follows that style.
- The failures of `tests/mcp_servers/git/` that fail today have no issue; an entry is added only with an issue path, by the owner's decision, with `--add` (Plan D-4, D-5).

## Design decisions
- The file holds comments only. Entry format: `<test id>`, a tab, `<reason that names issues/...md>`; the test id is `classname::name` as JUnit records it, and a collection error is the dotted module name alone.

## Alternatives considered
- N/A: location and format are fixed by Plan D-4 and the existing baselines.

## Implementation
### Target file
`tools/known_test_failures_baseline.txt` (new)

### Procedure
1. Create the file with a comment header of at most 12 lines stating: the purpose; the entry format with one example written as a comment (the example id is fictitious, for instance `tests.example.test_module.TestClass::test_case[param]`, followed by a tab and `issues/20260101-000000_example_x.md`; keep it a `#` line so it is never parsed); the rules (a reason must name an issue path; entries are removed when the test passes, with `compare_test_baseline.py --update`; entries are added only with `--add` and the owner's approval; the file never hides a failure from the suite).
2. End the file with a newline and no entry line.

### Method
- Plain text, UTF-8, English, no entry lines, so `load_baseline` returns an empty dict.

### Details
- Check after procedure 01 exists: write a scratch JUnit XML with one passing test and run `uv run python tools/compare_test_baseline.py <scratch xml>`; it exits 0 and reports `known failures: 0`.

## Compatibility considerations
- N/A: a new data file read only by the new tool.

## Security considerations
- N/A: no input handling or credential involved.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- The scratch run above, and `uv run python tools/check_workitem_traceability.py --active-only` is not needed (not a work item). No linter covers a `.txt` data file under `tools/`; pre-commit hooks that run on commit are the check.

## Completion criteria
- The file exists with the header only, and the default-baseline run exits 0 with `known failures: 0`.

## Out of Scope
- Adding entries, and registering the file in `tools/TOOL_DESCRIPTIONS.md` (procedure 04 names it in the tool's description).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261126-171205 | 20261126-171205 | wfeff002: full suite 15737 passed, 4 failed (3 pre-existing tests/mcp_servers/git; 1 eventbus flake, passes alone and on the clean tree) |
| 2 | Run the validation sequence (`rules/toolchain.md`): the scratch run of Details | Completed | 20261126-171205 | 20261126-171205 | wfeff002: full suite 15737 passed, 4 failed (3 pre-existing tests/mcp_servers/git; 1 eventbus flake, passes alone and on the clean tree) |

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
- **Source issue**: issues/20261126-151437_wfeff002_test-failure-baseline.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261126-161137_wfeff002_test-failure-baseline.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-164413
- **Related target files**: `tools/known_test_failures_baseline.txt`
