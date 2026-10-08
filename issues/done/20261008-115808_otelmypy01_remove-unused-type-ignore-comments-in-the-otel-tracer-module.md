# Remove unused type-ignore comments in the OTel tracer module

## Priority
Low

## Summary
Make the repository-wide type check pass by removing or correcting the type-ignore comments that mypy reports as unused in the OTel tracer module.

## Background
The type check run for the EventBus route fix reported errors in a file that the change did not touch. The repository's convention allows a suppression only with a rule code and justification, and the type check is part of the standard validation sequence.

## Problem
- `uv run mypy --no-namespace-packages scripts/` reports five `unused-ignore` errors in the OTel tracer module (the exact count differed between two runs in the same session; confirm on a clean run).
- The type-check step therefore never reports a clean result, so a new type error elsewhere is harder to notice.
- Whether the ignores are needed depends on the installed OpenTelemetry stubs; an optional dependency may be missing in this environment, which can make an ignore appear unused here but needed elsewhere (unknown).

## Reason for Change
A clean type check is part of the completion checklist; a permanent known failure erodes it.

## Implementation Intent
- Determine whether each ignore is unused because the stubs are present (remove it) or because an optional package is absent in this environment (keep it with a proper justification, or configure mypy so the result is consistent across environments).

## Target Files or Areas
- `scripts/shared/otel_tracer.py`
- Possibly the mypy settings in `pyproject.toml` if the fix is a per-module override

## Required Changes
- Resolve each reported ignore comment with the root cause fixed or a justified suppression.
- Confirm the result in the CI environment as well as locally.

## Constraints
- Follow the suppression governance: every remaining suppression has an error code and a justification, checked by the repository's suppression checker.
- Do not change tracing behavior.

## Acceptance Criteria
- `uv run mypy --no-namespace-packages scripts/` reports no errors.
- The suppression checker passes.

## Testing Expectations
Run mypy, ruff, the suppression checker, and the tests that cover the tracer module.

## Documentation Impact
Not required.

## Out of Scope
- Other type errors outside this module.
- Changing OpenTelemetry dependencies.

## Dependencies
- N/A: none.

## Unresolved Questions
- Whether the OpenTelemetry packages are installed in the development environment and in CI (unknown).

## AI Implementation Instruction
Fix the root cause first; do not add new ignores. Keep the change to the tracer module (and a mypy override if truly needed). Run the full mypy command before and after and report the counts.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/done/20261008-111323_plan.md
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261008-115808
- **Related target files**: `scripts/shared/otel_tracer.py`
