## Goal
- Add the gate mapping that `uv run python tools/run_validation_gates.py drift` requires for the new `rules/tool-gates.md` row of `tools/compare_test_baseline.py` (REQ-005). Found while executing procedure 05: Plan D-7 assumed a placeholder row needs no mapping; the drift check says otherwise.

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: one `Gate` entry in `tools/_validation_gate_defs.py`. Out of scope: any pattern, mode change, hook, or CI step, and any other gate.

## Assumptions
- Verified: `uv run python tools/run_validation_gates.py drift` reports `rules/tool-gates.md checker has no mapping entry: compare_test_baseline:<junit-xml>`; the `scan_change_consumers` entry of `tools/_validation_gate_defs.py` is the model of a manual, placeholder-only gate (`source=SOURCE_ROUTING`, `mode=MODE_FAST`, `patterns=()`).
- The Plan was amended for this file as a fallout amendment (checker keeps working), reported in the final report; the archived Plan was moved back to `plans/` for `tools/amend_plan.py` and archived again afterwards.
- A gate with `patterns=()` is never auto-selected, and a placeholder token (`<`) makes it `Not available` at run time.

## Design decisions
- Copy the `scan_change_consumers` shape exactly, with name `compare_test_baseline` and the argv `uv run python tools/compare_test_baseline.py <junit-xml>`, placed directly after that entry, with the comment `# Run-after-failure report: manual, `<junit-xml>` is a runtime placeholder.`.

## Alternatives considered
- Drop the row from `rules/tool-gates.md`: rejected, REQ-005 requires it.

## Implementation
### Target file
`tools/_validation_gate_defs.py`

### Procedure
1. Run the drift check and confirm it reports the missing mapping.
2. Add the `Gate` entry after the `scan_change_consumers` entry.
3. Re-run the drift check and the gate tests.

### Method
- One inserted tuple-literal entry; no other line changes.

### Details
- The command tuple is `("uv", "run", "python", "tools/compare_test_baseline.py", "<junit-xml>")`.

## Compatibility considerations
- N/A: a manual gate with no patterns changes no selection.

## Security considerations
- N/A: no input handling.

## Rollback considerations
- N/A: revert the commit (the row of `rules/tool-gates.md` must then be reverted too).

## Validation plan
- `uv run python tools/run_validation_gates.py drift`; `uv run pytest tests/tools/test_run_validation_gates.py`; ruff format and check, mypy (CI invocation) on the file.

## Completion criteria
- The drift check passes and the gate tests pass.

## Out of Scope
- Hooks, CI steps, and auto-selection of the tool.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261126-171205 | 20261126-171205 | wfeff002: full suite 15737 passed, 4 failed (3 pre-existing tests/mcp_servers/git; 1 eventbus flake, passes alone and on the clean tree) |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261126-171205 | 20261126-171205 | wfeff002: full suite 15737 passed, 4 failed (3 pre-existing tests/mcp_servers/git; 1 eventbus flake, passes alone and on the clean tree) |

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
- **Related target files**: `tools/_validation_gate_defs.py`
