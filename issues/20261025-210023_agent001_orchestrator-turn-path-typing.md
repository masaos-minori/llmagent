# Type-annotate the Orchestrator turn path

## Priority
Medium

## Summary
Add type annotations to `Orchestrator.handle_turn` and `Orchestrator._execute_turn` in `scripts/agent/orchestrator.py` so the core REPL turn-execution body is type-checked by mypy. Review finding F-001.

## Background
Explicit in code: at the reviewed head (`2e87bad46`), mypy reports `annotation-unchecked` notes in `scripts/agent/orchestrator.py` because `handle_turn(self, line)` and `_execute_turn(self, line)` carry no parameter or return annotations, and mypy does not check the bodies of untyped functions by default. The Orchestrator is the per-turn hub of the REPL runtime (input loop dispatch calls `handle_turn`), so its central body currently bypasses the type gate. Confirmed by review (python-code-review finding F-001, High confidence).

## Problem
The per-turn execution path — pause check, turn bracket, error-kind classification, and history persistence — is invisible to static type checking. A type error introduced in the turn path is not caught by the `mypy` gate that currently passes on the rest of `scripts/agent`.

## Reason for Change
Type-safety degradation at the highest-traffic code path in the agent runtime. Every per-turn change goes through these two methods, and the static gate provides no protection there today.

## Implementation Intent
Annotate the existing signatures with their real input and return types (the dispatched REPL line type as determined from the input-loop call site, and the actual return type), without changing runtime behavior or the public API. Fix only the type errors the annotations surface in these two method bodies; anything larger is reported, not fixed.

## Target Files or Areas
- `scripts/agent/orchestrator.py` (`Orchestrator.handle_turn`, `Orchestrator._execute_turn`)

## Required Changes
- Add parameter and return annotations to `handle_turn` and `_execute_turn`.
- Run the project mypy gate and resolve any type errors the now-checked bodies reveal, minimally.
- Confirm the call site in `scripts/agent/repl_input_loop.py` matches the chosen parameter type.

## Constraints
- No runtime behavior change; no public API change.
- Keep changes to these two methods and their immediate body; do not enable `--check-untyped-defs` repo-wide as part of this issue.
- Follow `rules/coding.md` typing conventions; suppressions require the `rules/coding.md` em-dash justification format.

## Acceptance Criteria
- `mypy` no longer reports `annotation-unchecked` notes for `handle_turn` / `_execute_turn` in `scripts/agent/orchestrator.py`.
- The mypy gate passes over `scripts/agent`.
- Full test suite result is unchanged from the pre-fix baseline.

## Testing Expectations
- Existing Orchestrator/turn-path tests must pass unchanged (regression: behavior must not change).
- `uv run mypy --no-namespace-packages scripts/` gate: Pass.
- `uv run ruff check scripts/agent`: Pass.

## Documentation Impact
No documentation update required: the change adds static annotations only. If body fixes reveal a behavior question, it is reported, not documented.

## Out of Scope
- Annotating other untyped functions elsewhere in `scripts/agent`.
- Enabling `--check-untyped-defs` for the repository.
- Any refactor of the turn bracket logic.

## Dependencies
N/A: none

## Unresolved Questions
- The exact declared parameter type for `line` at the `ReplInputLoop` → `Orchestrator.handle_turn` call site (presumed `str`; confirm against the call site before annotating).

## AI Implementation Instruction
Minimal diff: annotate the two signatures, run the mypy gate, and fix only type errors the newly-checked bodies surface inside these two methods. If a surfaced error requires a behavior change or touches other modules, stop and report it. Do not reformat unrelated code.

## Traceability
- **Workflow phase**: python-code-review (finding F-001)
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261025-210023
- **Related target files**: `scripts/agent/orchestrator.py`
