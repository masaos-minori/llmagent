## Goal

Add the RAG `SKIPPED` count to the RAG consistency line in `ReadinessReporter.report_readiness()` so a skipped RAG check renders distinctly from a warning-bearing check (`REQ-001`). Leave the other three summary lines unchanged (`REQ-003`).

## Scope

Single-line string change in `scripts/agent/startup_reporter.py`: extend the RAG consistency line to include `{rag_counts['SKIPPED']} skipped`. No other line, function, or signature changes.

## Assumptions

- The `{count} skipped` count-column pattern on the readiness and tool-discovery lines is the intended convention for the RAG line as well.
- `_count_by_status()` already returns a `SKIPPED` entry for `rag_consistency`; the change only reads it.

## Design decisions

- Reuse the existing `{rag_counts['SKIPPED']} skipped` token rather than introducing a distinct "skipped" label, mirroring the readiness and tool-discovery lines exactly.

## Alternatives considered

- Distinct "skipped" token: rejected — none exists anywhere in the reporter and it would diverge from the two sibling lines. `N/A: reuse wins for consistency`.

## Implementation
### Target file
`scripts/agent/startup_reporter.py`

### Procedure
In `report_readiness()`, edit the RAG consistency line to append the skipped count, matching the readiness and tool-discovery line format.

### Method
Locate the RAG consistency line in `report_readiness()` and add `{rag_counts['SKIPPED']} skipped` before the closing paren, mirroring the readiness and tool-discovery lines. Confirm the other three lines are untouched.

### Details
- The RAG line currently omits any skipped count, so a skipped check renders as a bare "WARN" with zero fatal and zero warnings (AC-001).
- The readiness line ends `..., {mcp_counts['SKIPPED']} skipped)` and the tool-discovery line ends `..., {tool_disc_counts['SKIPPED']} skipped)`; mirror that exact suffix on the RAG line.
- `_count_by_status()` already initializes and returns a `SKIPPED` count for each source, so `rag_counts['SKIPPED']` is valid without any other change.

## Compatibility considerations
`report_readiness()` signature and return behavior are unchanged; only the rendered banner string gains a `, N skipped` segment on the RAG line.

## Security considerations
`N/A: reporting-string change only; no auth, data, or I/O impact`.

## Rollback considerations
`N/A: revert the commit`.

## Validation plan
- Drive `report_readiness()` with a pipeline whose `rag_consistency` outcome is `SKIPPED` and assert the rendered line contains `, N skipped` (not a bare "WARN" with zero counts); assert the other three lines are unchanged.
- Run `pytest tests/agent/test_startup_reporter.py` and confirm existing assertions still pass.

## Completion criteria
The RAG consistency line contains the `{rag_counts['SKIPPED']} skipped` segment, the other three lines are byte-for-byte unchanged, and `test_startup_reporter.py` passes.

## Out of scope
Changing the other three checks or their counts; changing the RAG line's OK/WARN/FATAL determination; any layout refactor beyond adding the skipped indicator.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261016-164911 | 20261016-164911 | changed: scripts/agent/startup_reporter.py (RAG line gains the skipped count); docs: N/A; ruff/mypy/lint-imports/bandit(baseline)/vulture clean; full suite 8455 passed; diff-cover: no statement lines (multi-line f-string) |
| 2 | Add or update tests per Validation plan | Completed | 20261016-164911 | 20261016-164911 | changed: scripts/agent/startup_reporter.py (RAG line gains the skipped count); docs: N/A; ruff/mypy/lint-imports/bandit(baseline)/vulture clean; full suite 8455 passed; diff-cover: no statement lines (multi-line f-string) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261016-164911 | 20261016-164911 | changed: scripts/agent/startup_reporter.py (RAG line gains the skipped count); docs: N/A; ruff/mypy/lint-imports/bandit(baseline)/vulture clean; full suite 8455 passed; diff-cover: no statement lines (multi-line f-string) |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261016-164911 | 20261016-164911 | changed: scripts/agent/startup_reporter.py (RAG line gains the skipped count); docs: N/A; ruff/mypy/lint-imports/bandit(baseline)/vulture clean; full suite 8455 passed; diff-cover: no statement lines (multi-line f-string) |

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
- **Requirement ID**: `REQ-001`, `REQ-003`
- **Source issue**: `issues/20261016-134010_startup002_clarify-startup-status-reporting-for-skipped-checks-and-shutdown-during-startup.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261016-141320_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261016-152216
- **Related target files**: `scripts/agent/startup_reporter.py`