# Add unit test for ADR-003 RuntimeToolRegistry routing authority (CI-010)

## Priority
Medium

## Summary
Add automated test coverage for ADR-003's `RuntimeToolRegistry`-is-sole-routing-authority invariant, currently confirmed correct only by code inspection (Known Issue CI-010 in `governance_03`).

## Background
CI-010 has been open since 2026-09-03, one of five sibling "ADR invariant verified by code inspection, no automated test" entries (CI-009, CI-010, CI-012, CI-014, CI-016), previously batched in `governance_03` as one cross-cutting initiative pending an ownership decision. A deep-dive investigation (2026-09-27) found no existing cross-cutting engineering role anywhere in this repo — only a per-area RACI model (`docs/00_governance/governance_01_documentation-policy.md`) — and recommends reverting to per-area ownership rather than creating a new role (see the Configuration Ownership Map precedent, `governance_01` line 342). This issue assigns CI-010 specifically to `@mcp-dev` (MCP), per that recommendation.

## Problem
`scripts/shared/route_resolver.py::resolve()` only looks up in `_runtime_registry`, never falling back to `ToolRegistry` — confirmed correct via code inspection — but no automated test covers this routing-authority invariant.

## Reason for Change
Without test coverage, a future change to `resolve()` could silently reintroduce a fallback to `ToolRegistry`, violating ADR-003, with no automated signal.

## Implementation Intent
Add a focused unit test asserting `resolve()` never falls back to `ToolRegistry` when `RuntimeToolRegistry` is available, following existing test conventions for MCP routing tests. No production code change is expected.

## Target Files or Areas
- `scripts/shared/route_resolver.py` (reference only, not expected to change)
- MCP/routing test area (exact test file: `Unknown` — locate the existing routing test module before adding)

## Required Changes
- Add a unit test exercising `resolve()` that asserts it consults only `RuntimeToolRegistry` and never falls back to `ToolRegistry`.

## Constraints
N/A: no constraints beyond standard repository test conventions.

## Acceptance Criteria
- A new test exists covering ADR-003's routing-authority invariant and passes.
- Full test suite passes with no regression.

## Testing Expectations
Unit test (pytest). Run the targeted test, then the full suite once per `rules/toolchain.md`.

## Documentation Impact
Once the test lands and passes, remove the CI-010 entry from `docs/00_governance/governance_03_issue-and-uncertainty-management.md` Part 1 (Known Issues), and update the CI-009/010/012/014/016 batching note to reflect one fewer remaining member.

## Out of Scope
- CI-009, CI-012, CI-014, CI-016 — tracked as separate issues.
- Any change to `route_resolver.py`'s actual behavior (already confirmed correct; this is a test-coverage-only gap).

## Dependencies
N/A: none.

## Unresolved Questions
N/A: none — the per-area ownership recommendation (`@mcp-dev` for this item) was already established via a 2026-09-27 deep-dive investigation.

## AI Implementation Instruction
Add only the missing test. Do not modify `scripts/shared/route_resolver.py` unless the new test reveals an actual bug (none is currently expected). Keep the diff scoped to the new test file/function only.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260927-211338
- **Related target files**: tests/ (new test, exact module TBD), scripts/shared/route_resolver.py (reference)
