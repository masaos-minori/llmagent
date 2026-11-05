# Make the tool inventory count self-checking

## Priority
Low

## Summary
Stop the module count in `tools/TOOL_DESCRIPTIONS.md` from drifting: either verify it in `check_tool_descriptions_sync.py` or remove the number from the heading.

## Background
Confirmed by repository evidence on 2026-11-04: the heading `## Index (N modules)` in `tools/TOOL_DESCRIPTIONS.md` read `61 modules` while `tools/` held 73 non-package modules; it was corrected to 65 by hand after eight scripts were removed. `tools/check_tool_descriptions_sync.py` cross-checks the backticked `*.py` names in the document against `tools/*.py` and verifies `tools/<name>.py` and `-m tools.<name>` references in workflows, `.pre-commit-config.yaml`, and `tox.ini`; no check of the number was found in this review (the checker's code was only skimmed).

## Problem
A hand-maintained number in a document that already has a mechanical checker drifts silently, so the checker's clean result does not mean the document is accurate.

## Reason for Change
Documentation/code mismatch. Low severity and easy to fix.

## Implementation Intent
Prefer removing the number from the heading (nothing depends on it); if a count is wanted, derive it in the checker from the Index table rows and compare with the module list.

## Target Files or Areas
- `tools/check_tool_descriptions_sync.py`
- `tools/TOOL_DESCRIPTIONS.md`
- `tests/tools/test_check_tool_descriptions_sync.py`

## Required Changes
- Remove the count from the heading, or add a check that the stated count equals the number of Index rows and the number of non-package `tools/*.py` modules.
- Add a test for the chosen behavior (a drifted count fails, a correct one passes), if a check is kept.

## Constraints
- Preserve the existing checks and exit codes.
- Do not require the number if it is removed.

## Acceptance Criteria
- A stale module count can no longer pass the checker, or no count exists to go stale.
- `uv run python tools/check_tool_descriptions_sync.py` and its tests pass.

## Testing Expectations
- Unit test for the drift case; run the checker and `uv run pytest tests/tools/test_check_tool_descriptions_sync.py -q`.

## Documentation Impact
Update `tools/TOOL_DESCRIPTIONS.md` accordingly (and mention the convention for batch-specific tools there only if that is decided separately).

## Out of Scope
- Reworking the document structure or the other tables.

## Dependencies
N/A: none; touches the same document as `issues/20261104-152002_toolcli001_define-cli-and-exit-code-convention.md`, so apply in either order.

## Unresolved Questions
- Whether anything parses the heading's number: unknown (none found).

## AI Implementation Instruction
Prefer deleting the number; if kept, derive it from the table in the checker.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261104-152002
- **Related target files**: `tools/check_tool_descriptions_sync.py`, `tools/TOOL_DESCRIPTIONS.md`, `tests/tools/test_check_tool_descriptions_sync.py`
