# Remove agent imports from the shared production config validator

## Priority
Medium

## Summary
Restore the import-layer contract "shared must not import from agent, mcp_servers, rag, or db" by removing the two agent imports in the shared production config validator.

## Background
`PYTHONPATH=scripts uv run lint-imports` reports one broken contract out of five. The layer contract is a documented architectural rule, and the standard validation sequence includes this check.

## Problem
- The shared production config validator imports from the agent package in two places: the tool policy module (inside a function that resolves tool risk) and the config dataclasses module.
- This inverts the allowed dependency direction (shared code depending on agent code), which blocks reuse of the shared module outside the agent and keeps the layer check red.

## Reason for Change
A permanently broken architecture contract hides new layering violations and makes the shared layer harder to test and reuse.

## Implementation Intent
- Move the needed definitions (the risk-level mapping and the config dataclass types used by the validator) to a location both layers may import, or invert the dependency by passing the needed values into the validator from the agent side.
- Keep validation behavior unchanged.

## Target Files or Areas
- `scripts/shared/production_config_validator.py`
- `scripts/agent/tool_policy.py` and `scripts/agent/config_dataclasses.py` (sources of the imported names)
- `.importlinter` (read only, to confirm the contract)

## Required Changes
- Remove both agent imports from the shared validator by relocating or injecting what it needs.
- Update the importing call sites and tests accordingly.

## Constraints
- No behavior change in validation results; the existing tests must pass unchanged in meaning.
- Follow the repository's import layer contract; do not add an ignore entry to hide the violation.

## Acceptance Criteria
- `PYTHONPATH=scripts uv run lint-imports` reports all contracts kept.
- Production config validation tests pass and the full suite passes.

## Testing Expectations
Run the import-boundary check, mypy, ruff, the validator's tests, and the full suite once.

## Documentation Impact
Possibly: if module responsibility or the location of shared definitions is documented, update that documentation (check the Shared/DB domain documents).

## Out of Scope
- Other layer contracts or unrelated modules.
- Redesigning the config validation rules.

## Dependencies
- N/A: none.

## Unresolved Questions
- Which callers import the relocated names today (unknown; measure the blast radius before moving them, per the impact-radius check).

## AI Implementation Instruction
Measure the blast radius of each moved symbol first. Keep behavior identical, do not suppress the contract, and stop to report if the fix requires changing a public interface used outside these modules.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/done/20261008-111323_plan.md
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261008-115809
- **Related target files**: `scripts/shared/production_config_validator.py`, `scripts/agent/tool_policy.py`, `scripts/agent/config_dataclasses.py`
