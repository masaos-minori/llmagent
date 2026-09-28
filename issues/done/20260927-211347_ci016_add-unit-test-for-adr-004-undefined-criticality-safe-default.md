# Add unit test for ADR-004 undefined-criticality safe default (CI-016)

## Priority
Medium

## Summary
Add automated test coverage for ADR-004 Decision #12/INV-14's requirement that undefined or undeterminable component criticality never be assumed non-required, currently confirmed correct only by code inspection (Known Issue CI-016 in `governance_03`).

## Background
CI-016 has been open since 2026-09-15, one of five sibling "ADR invariant verified by code inspection, no automated test" entries (CI-009, CI-010, CI-012, CI-014, CI-016), previously batched in `governance_03` as one cross-cutting initiative pending an ownership decision. A deep-dive investigation (2026-09-27) found no existing cross-cutting engineering role anywhere in this repo — only a per-area RACI model (`docs/00_governance/governance_01_documentation-policy.md`) — and recommends reverting to per-area ownership rather than creating a new role (see the Configuration Ownership Map precedent, `governance_01` line 342). This issue assigns CI-016 specifically to `@agent-dev` (Agent), per that recommendation.

## Problem
`McpServerConfig.required` defaults to `True`, enforcing a safety net for unspecified criticality values (`scripts/shared/mcp_config.py`) — confirmed correct via code inspection — but no automated test verifies this default-required safety net, and ADR-004's own Completion Checklist still lists INV-14 as unverified/Manual-Review-only.

## Reason for Change
Without test coverage, a future change to the default value (e.g. `required: bool = False`) would silently violate INV-14 with no automated check to catch the regression.

## Implementation Intent
Add a unit test asserting the `required` field's default-`True` behavior for unspecified criticality values, and/or a test asserting undefined-criticality components are never routed as non-required, following existing conventions in the agent/MCP config test suite. No production code change is expected.

## Target Files or Areas
- `scripts/shared/mcp_config.py` (reference only, not expected to change)
- `scripts/agent/services/mcp_tool_discovery.py` (reference only)
- Agent/MCP config test suite (new or updated test)

## Required Changes
- Add a unit test asserting `McpServerConfig.required` defaults to `True` when criticality is unspecified.
- Optionally add a test asserting `mcp_tool_discovery.py` never treats an undefined-criticality component as non-required.

## Constraints
N/A: no constraints beyond standard repository test conventions.

## Acceptance Criteria
- A new test exists covering ADR-004 Decision #12/INV-14's safe-default invariant and passes.
- Full test suite passes with no regression.
- ADR-004's own Completion Checklist can be updated to reflect automated (not only Manual-Review) verification, once the test lands.

## Testing Expectations
Unit test (pytest). Run the targeted test, then the full suite once per `rules/toolchain.md`.

## Documentation Impact
Once the test lands and passes, remove the CI-016 entry from `docs/00_governance/governance_03_issue-and-uncertainty-management.md` Part 1 (Known Issues), update the CI-009/010/012/014/016 batching note to reflect one fewer remaining member, and update ADR-004's Completion Checklist/Manual Review notes for INV-14 if that document tracks verification status per-invariant.

## Out of Scope
- CI-009, CI-010, CI-012, CI-014 — tracked as separate issues.
- Any change to `mcp_config.py`'s or `mcp_tool_discovery.py`'s actual behavior (already confirmed correct; this is a test-coverage-only gap).

## Dependencies
N/A: none.

## Unresolved Questions
N/A: none — the per-area ownership recommendation (`@agent-dev` for this item) was already established via a 2026-09-27 deep-dive investigation.

## AI Implementation Instruction
Add only the missing test(s). Do not modify `scripts/shared/mcp_config.py` or `scripts/agent/services/mcp_tool_discovery.py` unless the new test reveals an actual bug (none is currently expected). Keep the diff scoped to the new test file/function(s) only.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260927-211347
- **Related target files**: Agent/MCP config test suite (new test, exact module TBD), scripts/shared/mcp_config.py (reference), scripts/agent/services/mcp_tool_discovery.py (reference)
