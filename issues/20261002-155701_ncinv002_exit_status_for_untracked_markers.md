# Decide whether untracked-marker warnings should cause a non-zero exit code

## Priority

Medium

## Summary

Record the decision on whether `check_needs_confirmation_inventory.py` should exit non-zero when it finds orphaned Needs Confirmation markers in governance documents. Currently the checker exits 0 even when such warnings exist.

## Background

The Needs Confirmation Inventory in `docs/00_governance/governance_03_issue-and-uncertainty-management.md` is the single central place for unresolved items; a marker left only in an individual document is not allowed. The checker `check_needs_confirmation_inventory.py` reports orphaned markers at WARNING severity but exits 0 regardless of findings. This was observed on 2026-10-01 with 8 warnings in `docs/23_agent/` and `docs/21_rag/`.

## Problem

Whether warnings from the checker should cause a non-zero exit is currently undecided. The original issue (`issues/20261001-103602_ncinv001_detect-orphaned-needs-confirmation-markers-in-governance-docs.md`) explicitly states: "Whether warnings should fail verification is Needs confirmation." This means the decision has not been made and remains open.

## Reason for Change

The checker's exit status affects CI/CD pipelines and automated verification workflows. If warnings should block verification, the exit code must reflect that. If warnings are informational only, exit 0 is correct. A decision is needed to avoid ambiguity in downstream consumers.

## Implementation Intent

Make a decision based on the following criteria:
- If the checker's purpose is to **detect** problems (informational), exit 0 is appropriate.
- If the checker's purpose is to **enforce** that no unconfirmed claims remain, exit non-zero is appropriate.
- Consider whether the checker will be used in CI gates — if so, the exit status determines whether CI passes or fails.

## Target Files or Areas

- `tools/check_needs_confirmation_inventory.py` (exit code logic)
- `docs/00_governance/governance_04_documentation-checks.md` (if check description references exit behavior)

## Required Changes

- Document the decision in the checker's docstring or configuration
- If exit non-zero is chosen, modify `check_untracked_inline_markers()` to return a non-zero exit code when warnings are found
- Update any CI configuration that runs this checker

## Constraints

- Do not change the checker's warning messages or severity levels
- Preserve backward compatibility if the checker is already used in CI

## Acceptance Criteria

- A clear decision is recorded (either "warnings → exit 0" or "warnings → exit non-zero")
- The decision is reflected in the checker's code or documentation
- Any affected CI configuration is updated accordingly

## Testing Expectations

- Run `uv run python tools/check_needs_confirmation_inventory.py` and verify the exit code matches the decision
- Verify existing CI pipelines are not broken by the change

## Documentation Impact

If the decision changes the exit behavior, update the check description in `docs/00_governance/governance_04_documentation-checks.md` and any CI documentation.

## Out of Scope

- Resolving the actual orphaned markers themselves (handled by other issues)
- Changing the checker's warning format or severity levels
- Adding new checks beyond the exit-status decision

## Dependencies

- Supports `canon001` verification. Depends on the outcome of `issues/20261001-103602_ncinv001_detect-orphaned-needs-confirmation-markers-in-governance-docs.md` for the classification rule (UNK-01).

## Unresolved Questions

- None remaining after this issue resolves the exit-status question.

## AI Implementation Instruction

- Make a decision based on the checker's intended role (detection vs enforcement).
- If enforcement: modify the exit code logic in `check_untracked_inline_markers()`.
- If detection: document the decision as-is and ensure no one assumes exit 0 means "all clean".
- Update documentation if the decision differs from current behavior.

## Traceability

- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/done/20261002-070708_plan.md
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261002-155701
- **Related target files**: tools/check_needs_confirmation_inventory.py, docs/00_governance/governance_04_documentation-checks.md
