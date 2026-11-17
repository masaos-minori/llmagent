# Correct the validation runner rows in the tool descriptions

## Priority
Low

## Summary
The two `tools/TOOL_DESCRIPTIONS.md` rows for `tools/run_validation_gates.py` name a `--fast` option and say the runner stops on the first failure, and the runner has neither. Make the rows match the code.

## Background
Filed as a follow-up of `plans/20261117-125737_wftool006_gate-output-noise.md` (its Unknowns table, UNK-02). The same drift was noted on 2026-11-02 in `implementations/done/20261102-084648_06_tools_TOOL_DESCRIPTIONS.md.md` (Step 3a, "not changed here") and was never tracked as an issue.

## Problem
`uv run python tools/run_validation_gates.py --help` lists `--base`, `--full`, `--jobs`, and the `drift` subcommand; there is no `--fast` (`Explicit in code`, `Operationally observed`). The default mode is fast, selected by the absence of `--full`. The runner runs every selected gate and exits `1` when any result is `Fail`; it does not stop at the first one (`Explicit in code`, the result aggregation in the run function). The rows state both of the contrary behaviors (`Explicit in code`).

## Reason for Change
- A reader who copies `--fast` from the description gets an argument error, and one who relies on stop-at-first-failure misreads a run that reports every failure.
- The drift has stood since 2026-11-02, so it is not corrected by chance. The severity is low.

## Implementation Intent
- The rows describe the options and the failure behavior that the code has, and nothing they state about the runner is left unverified.

## Target Files or Areas
- tools/TOOL_DESCRIPTIONS.md (the two rows for `run_validation_gates.py`)

## Required Changes
- Remove `--fast` and state that fast mode is the default and `--full` adds the toolchain sequence.
- State that the runner runs every selected gate, reports each result, and exits non-zero when any gate failed.
- Verify every other claim of both rows against `--help` and the code, and correct what differs.
- Run the description sync check.

## Constraints
- Documentation follows the code; do not add a `--fast` option or a stop-at-first-failure mode in this issue.
- Follow `routing.md` Tools, section "Adding a new tool", for every changed `tools/*.py`: ruff format and check, mypy, bandit, a smoke run against real repository data, and `tools/TOOL_DESCRIPTIONS.md` sync (`tools/check_tool_descriptions_sync.py`).
- Respect the `tools/` module-size gate (`tools/check_module_size.py --scripts-dir tools --baseline tools/check_module_size_tools_baseline.txt`): the baseline only shrinks, so a tool at or over the limit MUST NOT grow; put new logic in a new module instead.
- Follow the tool CLI conventions recorded in `tools/TOOL_DESCRIPTIONS.md`: exit codes `0` pass, `1` findings, `2` usage or environment error; `--dry-run` and atomic writes for tools that rewrite files.
- Follow the Current-Specification-Only policy: no aliases, shims, or history-style comments for removed behavior.
- Keep code comments, log text, and documentation in English; change only the Target Files and report any other needed file as a scope amendment.

## Acceptance Criteria
- Neither row mentions `--fast` or stopping at the first failure.
- Each remaining claim of both rows is confirmed against `--help` or the code, and the confirmation is recorded in the commit message body or the review.
- `tools/check_tool_descriptions_sync.py` passes.

## Testing Expectations
Not required (documentation-only). Run `tools/check_tool_descriptions_sync.py`. Validation sequence: `rules/toolchain.md`; after any `docs/` edit also the checkers listed in `routing.md` Tools.

## Documentation Impact
Yes. The two rows of `tools/TOOL_DESCRIPTIONS.md`.

## Out of Scope
- Changing runner behavior or options.
- Other rows of the descriptions file.

## Dependencies
- `plans/20261117-125737_wftool006_gate-output-noise.md` also edits these two rows in its phase 4 (default output and the new flag): follows that phase so one pass verifies the final text.

## Unresolved Questions
- Whether stop-at-first-failure was ever intended is `不明`; the code and `rules/toolchain.md` describe a run of all selected gates.

## AI Implementation Instruction
- Keep the edit to the two rows; verify each claim you keep.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261117-132203
- **Related target files**: tools/TOOL_DESCRIPTIONS.md (the two rows for `run_validation_gates.py`)
