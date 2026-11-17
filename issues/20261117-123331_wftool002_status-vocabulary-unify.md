# Align the Execution Status vocabulary written by complete_doc_procedure

## Priority
Medium

## Summary
`tools/complete_doc_procedure.py` writes the status `Done`, which is not in the status set that the work item tools define, and the tool has no tests. Align it with the shared vocabulary or merge it into the existing status tool.

## Background
Filed from the investigation of the issue -> plan -> implementation toolchain. Claims below were verified in this investigation by reading tool source, running `--help`, and `rg`, unless marked `Needs confirmation`.

## Problem
`tools/_workitem_status_table.py` defines the valid statuses as Pending, In Progress, Blocked, Completed, and Superseded (`Explicit in code`). `tools/complete_doc_procedure.py` writes `Done` into Execution Status rows (`Explicit in code`). No test file references the tool (`Explicit in code`, `rg` over `tests/`), and no skill or `routing.md` entry references it. `tools/set_execution_status.py` writes `Completed` and covers the same row update.

## Reason for Change
- A status outside the vocabulary can be mishandled by checkers that classify rows as finished or unfinished; how each checker treats `Done` is `Needs confirmation`.
- The vocabulary was just extended (the Superseded status), so divergent writers are likelier to drift further.
- The tool is untested and unreferenced, so nothing would catch a regression, and an operator cannot discover it from the workflow documents.

## Implementation Intent
- Every tool that writes an Execution Status row takes its values from the shared status definition.
- The overlapping row-update behavior lives in one tool; if `complete_doc_procedure.py` keeps its unique function (the Verification Findings table), that function is tested and documented.

## Target Files or Areas
- `tools/complete_doc_procedure.py`
- tools/_workitem_status_table.py (reference only)
- `tools/set_execution_status.py`
- `tools/TOOL_DESCRIPTIONS.md`
- tests/tools/ (new test for the retained tool)

## Required Changes
- Confirm how `tools/manage_workitem_stage.py detect-stale`, `tools/check_workitem_traceability.py`, and `tools/check_workitem_structure.py --archived-status` treat a `Done` row, and count existing procedures that already contain one.
- Decide: retire `complete_doc_procedure.py` in favor of `set_execution_status.py` plus a findings helper, or keep it and take the status value from the shared definition.
- Add tests for whichever tool remains, including the written status value.
- Update `tools/TOOL_DESCRIPTIONS.md`.

## Constraints
- Existing archived procedures that contain `Done` rows MUST NOT be rewritten in this issue; report their count.
- Follow `routing.md` Tools, section "Adding a new tool", for every changed `tools/*.py`: ruff format and check, mypy, bandit, a smoke run against real repository data, and `tools/TOOL_DESCRIPTIONS.md` sync (`tools/check_tool_descriptions_sync.py`).
- Respect the `tools/` module-size gate (`tools/check_module_size.py --scripts-dir tools --baseline tools/check_module_size_tools_baseline.txt`): the baseline only shrinks, so a tool at or over the limit MUST NOT grow; put new logic in a new module instead.
- Follow the tool CLI conventions recorded in `tools/TOOL_DESCRIPTIONS.md`: exit codes `0` pass, `1` findings, `2` usage or environment error; `--dry-run` and atomic writes for tools that rewrite files.
- Follow the Current-Specification-Only policy: no aliases, shims, or history-style comments for removed behavior.
- Keep code comments, log text, and documentation in English; change only the Target Files and report any other needed file as a scope amendment.

## Acceptance Criteria
- No tool under `tools/` writes a status value outside the shared vocabulary (test or `rg` evidence).
- The retained tool has tests that assert the written status.
- `tools/check_tool_descriptions_sync.py` passes.

## Testing Expectations
Unit tests under `tests/tools/`; smoke run on a copy of a real procedure; ruff, mypy, bandit. Validation sequence: `rules/toolchain.md`; after any `docs/` edit also the checkers listed in `routing.md` Tools.

## Documentation Impact
Yes. `tools/TOOL_DESCRIPTIONS.md`; the workflow documents if the tool is kept and wired in.

## Out of Scope
- Changing the status vocabulary.
- Rewriting archived procedures.

## Dependencies
- `tools/TOOL_DESCRIPTIONS.md` is also edited by the other tooling issues of this batch; fix the order with the owner.

## Unresolved Questions
- How each checker treats `Done` is `Needs confirmation` (first Required Change).
- Whether the Verification Findings function is still needed is `不明`.

## AI Implementation Instruction
- Report the `Done` handling evidence before choosing between retiring and keeping the tool.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261117-123331
- **Related target files**: `tools/complete_doc_procedure.py`; tools/_workitem_status_table.py (reference only); `tools/set_execution_status.py`; `tools/TOOL_DESCRIPTIONS.md`; tests/tools/ (new test for the retained tool)
