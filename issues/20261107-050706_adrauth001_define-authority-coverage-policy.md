# Define the coverage policy of the ADR authority model

## Priority
Low

## Summary
Document whether `config/adr_authority.toml` registration is comprehensive or selective, define inclusion criteria for decision targets, and record an explicit decision on whether the authority model needs a target governing itself.

## Background
ADR-016 Decision item 1 requires exactly one `primary_adr` per registered decision target, and item 8 requires a registry change whenever an ADR is added or its authority changes. The registry currently holds 14 `decision_target` entries, transcribed from the prose authorities in the ADR index (file header comment). Neither ADR-016 nor the registry states whether registration is meant to cover every ADR decision or only selected ones, and no registered target governs the authority model itself (Explicit in file: `config/adr_authority.toml`, ADR-016 Decision Details).

## Problem
Uniqueness and completeness are different properties. A registry can have one primary per registered target while intentionally covering only some decisions. Without a stated coverage policy, contributors may assume every ADR needs a target or may omit an important decision unknowingly. The absence of a self-governance target is not by itself a confirmed violation.

## Reason for Change
A stated policy prevents inconsistent registration over time. Self-governance registration may add clarity but can also add metadata or dependency cycles without a defined purpose. It is Low because it is a non-blocking governance clarification with no present defect.

## Implementation Intent
Establish whether registration is comprehensive or selective, define inclusion criteria, and separate the coverage rules from the primary-authority uniqueness rules in ADR-016. Decide with a documented rationale whether to add a self-governance target. Change configuration, the generated index content, and validators only where the decision requires it.

## Target Files or Areas
- `docs/10_adr/adr_02_07_016_adr-authority-model.md`
- `docs/10_adr/adr_01_index.md` (generated sections only via `tools/generate_adr_authority.py`)
- `config/adr_authority.toml`
- `tools/check_adr_authority.py`, `tools/generate_adr_authority.py`, only if required

## Required Changes
- Determine whether registration is comprehensive or selective.
- Define inclusion criteria for decision targets.
- Separate coverage rules from primary-authority uniqueness rules.
- Evaluate whether authority governance requires its own target and document the rationale for adding or not adding it.
- Update configuration, index content, and validators only where required.
- Check for dependency cycles and inconsistent authority assignments.

## Constraints
- Do not classify missing self-registration as a confirmed defect.
- Do not register every ADR automatically.
- Follow existing target naming conventions.
- Do not merge invariant evidence management into authority management.
- Generated index sections must be refreshed with the generator, not hand-edited.
- If coverage intent cannot be established, report the governance decision required.

## Acceptance Criteria
- Coverage and uniqueness requirements are separately documented.
- Contributors can determine when registration is required.
- The self-governance decision has an explicit rationale.
- Documentation and configuration agree.
- Applicable authority validation passes.

## Testing Expectations
Run `uv run python tools/check_adr_authority.py`, `uv run python tools/generate_adr_authority.py --check`, `check_adr_reference.py`, and the documentation checks in `routing.md`. If a validator changes, add or update its tests and follow `rules/toolchain.md`.

## Documentation Impact
Yes. ADR-016 coverage policy and rationale; the index changes only through the generator.

## Out of Scope
- Authority model redesign
- Unapproved comprehensive registration
- Invariant evidence registry changes

## Dependencies
- Coordinate shared governance wording with `issues/20261107-050707_adrdoc001_separate-adr-current-history.md`.
- Sibling check: no open issue or in-flight plan targets these files.

## Unresolved Questions
- 不明: the intended coverage (comprehensive or selective); this requires an owner decision.
- 不明: whether a self-governance target serves a concrete purpose.

## AI Implementation Instruction
Keep changes minimal. Do not register additional ADRs without an approved decision. Report the governance decision required if the coverage intent cannot be established.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261107-050706
- **Related target files**: `docs/10_adr/adr_02_07_016_adr-authority-model.md`, `docs/10_adr/adr_01_index.md`, `config/adr_authority.toml`, `tools/check_adr_authority.py`, `tools/generate_adr_authority.py`
