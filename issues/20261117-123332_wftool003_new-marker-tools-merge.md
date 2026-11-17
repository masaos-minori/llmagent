# Merge the two procedure new-marker tools into one guarded tool

## Priority
Medium

## Summary
`tools/fix_procedure_new_markers.py` and `tools/mark_procedure_new_symbols.py` both insert the `(new)` marker that `tools/stale_detector.py` recognizes, and neither is referenced by any skill. Keep the guarded one, retire the other, and wire the remaining tool into the workflows that hit the failure it fixes.

## Background
Filed from the investigation of the issue -> plan -> implementation toolchain. Claims below were verified in this investigation by reading tool source, running `--help`, and `rg`, unless marked `Needs confirmation`.

## Problem
Both tools insert ` (new)` after backticked symbol names in procedure documents (`Explicit in code`). `mark_procedure_new_symbols.py` has a `list` step and refuses names that `stale_detector.py` does not report as missing; `fix_procedure_new_markers.py` has no such guard, so it can mark an existing symbol as new and silence the staleness check that protects it. Neither tool is referenced in `skills/`, `routing.md`, or the templates (`Explicit in code`, `rg`). `tools/TOOL_DESCRIPTIONS.md` describes the fix tool with a `--files` option, while its `--help` takes files as positional arguments (`Explicit in code`).

## Reason for Change
- Two tools with one purpose leave the operator without a rule for which to use, and the unguarded one can defeat a validation guard.
- `plan-to-implementation-procedure` Step 3 and `code-implementation` both run `stale_detector.py` and can hit `symbol_missing` for a name the procedure creates, but neither names a remedy tool.
- The documented option name does not match the real interface, so a copy-pasted command fails.

## Implementation Intent
- One tool inserts the marker, with the guard that refuses to mark an existing symbol.
- Its multi-file capability is preserved if the retired tool's users need it.
- The two workflows name the tool where `symbol_missing` is handled.

## Target Files or Areas
- tools/fix_procedure_new_markers.py (retire)
- tests/tools/test_fix_procedure_new_markers.py (retire or migrate cases)
- `tools/mark_procedure_new_symbols.py`
- `skills/plan-to-implementation-procedure/workflow.md`
- `skills/code-implementation/workflow.md`
- `tools/TOOL_DESCRIPTIONS.md`

## Required Changes
- Confirm that no code, hook, or workflow calls `fix_procedure_new_markers.py` (zero-caller `rg` re-check).
- Add multi-file input to `mark_procedure_new_symbols.py` if the retired tool's batch use is needed; migrate its useful test cases.
- Remove `fix_procedure_new_markers.py` and its test, and remove its mentions in the shared convention paragraphs of `tools/TOOL_DESCRIPTIONS.md`.
- Name `mark_procedure_new_symbols.py` in the two workflows' `symbol_missing` handling.

## Constraints
- No alias or wrapper for the removed tool (Current-Specification-Only, deprecation policy in `rules/coding.md`).
- Follow `routing.md` Tools, section "Adding a new tool", for every changed `tools/*.py`: ruff format and check, mypy, bandit, a smoke run against real repository data, and `tools/TOOL_DESCRIPTIONS.md` sync (`tools/check_tool_descriptions_sync.py`).
- Respect the `tools/` module-size gate (`tools/check_module_size.py --scripts-dir tools --baseline tools/check_module_size_tools_baseline.txt`): the baseline only shrinks, so a tool at or over the limit MUST NOT grow; put new logic in a new module instead.
- Follow the tool CLI conventions recorded in `tools/TOOL_DESCRIPTIONS.md`: exit codes `0` pass, `1` findings, `2` usage or environment error; `--dry-run` and atomic writes for tools that rewrite files.
- Follow the Current-Specification-Only policy: no aliases, shims, or history-style comments for removed behavior.
- Keep code comments, log text, and documentation in English; change only the Target Files and report any other needed file as a scope amendment.

## Acceptance Criteria
- `rg fix_procedure_new_markers` finds no reference outside archived `plans/done/` and `issues/done/` files.
- `mark_procedure_new_symbols.py` still refuses a symbol that `stale_detector.py` does not report as missing (test).
- Both workflows name the remaining tool, and `tools/check_tool_descriptions_sync.py` passes.

## Testing Expectations
Unit tests under `tests/tools/`; smoke run on a copy of a real procedure; ruff, mypy, bandit; `tools/check_skills_references.py`. Validation sequence: `rules/toolchain.md`; after any `docs/` edit also the checkers listed in `routing.md` Tools.

## Documentation Impact
Yes. Two workflow documents and `tools/TOOL_DESCRIPTIONS.md`.

## Out of Scope
- Changing `stale_detector.py` behavior.
- Marking symbols in existing archived procedures.

## Dependencies
- `tools/TOOL_DESCRIPTIONS.md` is also edited by the other tooling issues of this batch; fix the order with the owner.

## Unresolved Questions
- Whether any operator relies on the retired tool's multi-file call is `不明`.

## AI Implementation Instruction
- Run the zero-caller `rg` check first and stop if a caller exists.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261117-123332
- **Related target files**: tools/fix_procedure_new_markers.py (retire); tests/tools/test_fix_procedure_new_markers.py (retire or migrate cases); `tools/mark_procedure_new_symbols.py`; `skills/plan-to-implementation-procedure/workflow.md`; `skills/code-implementation/workflow.md`; `tools/TOOL_DESCRIPTIONS.md`
