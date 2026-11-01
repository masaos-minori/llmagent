# Keep validation gates and pre-commit hooks in parity

## Priority
High

## Summary
Make `tools/run_validation_gates.py` and `.pre-commit-config.yaml` agree on which checkers exist: extend the gate runner's drift check to cover the tool-backed pre-commit hooks, map the checkers that only the hooks run today, and make a new hook without a gate mapping fail the drift check, so that a change that passes the gates cannot be rejected by the commit hooks for a reason the gates never ran.

## Background
- `Operationally observed` (2026-10-30): `uv run python tools/run_validation_gates.py` reported every gate `Pass`, and the commit was then rejected by the `adr-invariant-matrix` pre-commit hook because a test cited by `docs/10_adr/adr_01_index.md` had been removed. The failure was found at commit time, after the full validation sequence and a multi-minute test run.
- `Explicit in code`: the `drift` subcommand of `tools/run_validation_gates.py` verifies that every checker named in the `routing.md` "When to run which tool" table has a gate mapping. It does not read `.pre-commit-config.yaml`.
- `Explicit in code` (comparison of the hook entries with `tools/run_validation_gates.py` and `routing.md`, 2026-10-30): seven tool-backed hooks run a checker that neither the gate mapping nor the `routing.md` table names: `check_adr_invariant_matrix`, `check_adr_reference`, `check_adr_structure`, `check_known_deviation_sync`, `check_plan_target_overlaps`, `check_conftest_integrity`, and `check_workitem_traceability`.
- `Explicit in code`: `skills/code-implementation/workflow.md` Step 3e and `skills/git-commit-and-sync/workflow.md` Phase 4 treat `run_validation_gates.py` as the single entry point, and `AGENTS.md` Global Rule 9 tells the executor to run the checkers listed in `routing.md`; both therefore miss the seven.
- Related closed work: `issues/done/20261025-210306_tools001_frontmatter-gate-command.md` (an earlier gate-mapping addition).

## Problem
Three lists describe the checkers (pre-commit hooks, the `routing.md` table, the gate mapping) and only one pair is compared. A checker that exists only as a hook is run for the first time at commit, where a failure costs the most.

## Reason for Change
Test removal and renaming, ADR edits, and Plan target changes are routine in this workflow; the ADR invariant check alone fired once in a single release. Each miss repeats a validation round at commit time.

## Implementation Intent
Add the missing parity check instead of relying on memory. The drift check compares the tool-backed hooks with the gate mapping, with a small reviewed allowlist for hooks that are intentionally commit-only (each with a reason). The seven unmapped checkers get mapping entries whose file triggers mirror the hook's own `files` and `types` filters, so a change a hook would inspect also selects the gate. The `routing.md` table gets the matching rows so the manual path (`AGENTS.md` Global Rule 9) stays consistent. The drift check itself runs in pre-commit so that a new hook without a mapping fails the commit that adds it.

## Target Files or Areas
- `tools/run_validation_gates.py` and `tests/tools/test_run_validation_gates.py`
- `.pre-commit-config.yaml` (a hook for the drift check)
- `routing.md` ("When to run which tool" rows)
- `rules/toolchain.md` (a sentence naming the parity rule)
- `tools/TOOL_DESCRIPTIONS.md` (if the tool's described behavior changes)

## Required Changes
- Extend `drift` to read `.pre-commit-config.yaml` and report each tool-backed hook that has no gate mapping and no allowlist entry.
- Add mapping entries and `routing.md` rows for the seven checkers, with triggers matching the hooks' file filters; record any that must stay commit-only in the allowlist with a reason.
- Add the drift check as a pre-commit hook.
- Measure the run time the new gates add in fast mode and report it.

## Constraints
- Fast mode must stay fast; a checker that is slow in fast mode is mapped to full mode only, with the reason recorded.
- No change to what any checker verifies.
- The allowlist is reviewed text, not a silent default.

## Acceptance Criteria
- Before the change, `drift` run against the current hooks names the seven checkers; after the change it reports none unmapped.
- A fixture pre-commit config with an added tool-backed hook and no mapping makes `drift` exit non-zero.
- On a fixture where an ADR cites a removed test, running the gates with that change selects the ADR invariant gate and reports `Fail`.
- `check_tool_descriptions_sync.py` passes, and the drift check passes on the live repository.

## Testing Expectations
- Unit tests for the new drift behavior (unmapped hook, allowlisted hook, malformed config) and for trigger selection of the newly mapped gates.
- A live run of `tools/run_validation_gates.py drift` and of the default mode on a representative diff.
- `ruff`, `mypy tools/run_validation_gates.py`, and `bandit` per "Adding a new tool" (the file is an existing tool; the lighter sequence still applies to the changed file).

## Documentation Impact
Yes. `routing.md` lists the checkers and `rules/toolchain.md` states that gates and hooks must stay in parity. Intent and failure behavior only.

## Out of Scope
- Merging the gate runner and the hooks into one mechanism.
- Changing CI workflows.
- Changing the behavior of any existing checker.

## Dependencies
N/A: none. No open issue or Plan targets these files (checked with `rg` over `issues/*.md` and `plans/*.md`, 2026-10-30).

## Unresolved Questions
- `不明`: whether any of the seven checkers is intentionally commit-only.
- `不明`: the fast-mode run time of each of the seven checkers.
- Assumption: the hooks' `files` and `types` filters can be transcribed as gate triggers without loss.

## AI Implementation Instruction
Change only the gate runner, its tests, the pre-commit config entry, and the named docs. Do not alter any checker. Record every commit-only exception with a reason. Stop and report if a checker cannot be given a trigger that matches its hook filter.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261030-191302
- **Related target files**: `tools/run_validation_gates.py`, `tests/tools/test_run_validation_gates.py`, `.pre-commit-config.yaml`, `routing.md`, `rules/toolchain.md`, `tools/TOOL_DESCRIPTIONS.md`
