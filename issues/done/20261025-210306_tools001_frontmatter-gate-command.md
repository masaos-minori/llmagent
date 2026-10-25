# Fix the invalid manage_frontmatter gate command

## Priority
Medium

## Summary
Fix the `manage_frontmatter` gate in `tools/run_validation_gates.py`: it passes the literal argument `add-missing|dedupe-lists` as one argv token, which `argparse` rejects with a usage error (exit 2), so the gate is a permanent Fail. Review finding F-005.

## Background
Explicit in code: the gate entry `manage_frontmatter` in `tools/run_validation_gates.py` runs `uv run python tools/manage_frontmatter.py "add-missing|dedupe-lists"` — a single argument containing a shell-style alternation that is never split. `tools/manage_frontmatter.py` is a subcommand-based CLI (`add-missing`, `dedupe-lists`, `merge-related`, `rename-category-to-area`, `classify`) and rejects the unknown token with exit 2. Observed during gate runs at head `2e87bad46`: the gate reported Fail with the usage error every time. Confirmed by review (python-code-review finding F-005, High confidence; verified by reading both tools and by the recorded gate output).

## Problem
A validation gate defined for `docs/**` changes can never pass: its result is a harness defect, indistinguishable in gate reports from a real front-matter problem. During recent batch work it was reported as a Fail on every run and had to be dismissed manually.

## Reason for Change
Every docs-touching validation run carries a false failure, and the CI result-checking workflow that routes gate failures would keep triaging a defect that is not a content problem.

## Implementation Intent
Point the gate at one valid report-only subcommand. Evidence from the tools' own usage docs decides which: `add-missing` is report-only by default (writes require `--fix`), while `dedupe-lists` writes files unconditionally and therefore cannot be a validation gate command. The gate should run `add-missing` with its default report-only behavior.

## Target Files or Areas
- `tools/run_validation_gates.py` (`manage_frontmatter` gate entry)

## Required Changes
- Replace the invalid `"add-missing|dedupe-lists"` argument with a valid report-only invocation (`add-missing` default mode).
- Run the gate and confirm it now executes the subcommand and Passes on the current docs tree (or surfaces a real front-matter finding).
- Update any gate inventory/description docs if they quote the old command.

## Constraints
- The gate MUST remain report-only: no docs file may be modified by a validation-gate run (`dedupe-lists` is excluded because `cmd_dedupe_lists` writes on change).
- No change to `tools/manage_frontmatter.py` behavior in this issue.

## Acceptance Criteria
- `tools/run_validation_gates.py` reports the `manage_frontmatter` gate as Pass (not a usage-error Fail) on a clean docs tree.
- No `docs/` file is modified by the gate run.
- Gate harness self-tests (if any exist for `run_validation_gates.py`) pass.

## Testing Expectations
- Run the gate harness with only the docs patterns triggered and record Pass.
- Confirm exit code 0 and no side-effect writes (git status clean afterwards).

## Documentation Impact
Update gate-inventory documentation only where it quotes the previous command string; state the report-only constraint for this gate.

## Out of Scope
- Adding new subcommands or a `--dry-run` mode to `dedupe-lists`.
- Changing front-matter content in `docs/`.
- Other gate entries in `run_validation_gates.py`.

## Dependencies
- `plans/done/20261025-090535_ci001_scheduled-ci-result-check-that-routes-failures-to-the-test-and-fix-workflow.md` — related context (archived): a workflow that triages gate failures; this defect produces a false failure for it to triage.

## Unresolved Questions
N/A: none (report-only subcommand selection is settled by the tools' usage documentation).

## AI Implementation Instruction
Change only the gate entry's command tuple to the valid report-only invocation; do not touch `manage_frontmatter.py`. Verify with a real gate run and a clean `git status` afterwards.

## Traceability
- **Workflow phase**: python-code-review (finding F-005)
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261025-210306
- **Related target files**: `tools/run_validation_gates.py`
