# Preflight gate additions not validated against all execution paths

## Priority
Medium

## Summary
Document and test coverage for the full set of execution paths gated by `check_preflight()` calls across the Agent subsystem.

## Background
Preflight gates (`check_preflight()`) have been added to multiple locations in the Agent subsystem to prevent unauthorized tool access. However, there is no documentation or test coverage verifying that all execution paths are properly gated.

## Problem
It is unclear whether all execution paths are covered by the preflight gate. Untested execution paths could bypass the gate, allowing unauthorized tool access.

## Reason for Change
The scope of the preflight gate additions needs to be documented and tested. Without verification, the security boundary may have gaps that are not visible until an incident occurs.

## Implementation Intent
1. Enumerate all execution paths that should be gated by preflight checks (map each call site to its caller chain).
2. For each enumerated path, verify that `check_preflight()` is called before the tool action executes.
3. Add tests that exercise each path and confirm the gate fires when appropriate.
4. Document the coverage map in the Agent architecture documentation.

**Known preflight-exempt paths** (must NOT be flagged as violations):
- `repository_gateway.py::read_execute()` — READ operations are intentionally preflight-exempt per design (direct passthrough for read-only tools)
- `tool_approval.py::build_preview()` — dry_run execution is preflight-exempt (read-only operation)
- `tool_runner.py::run_tool_call()` when `ctx.services_required.gateway is None` — gateway not yet configured; requires separate resolution

## Target Files or Areas
- `scripts/agent/tool_policy.py::check_preflight()` — the gate function
- `scripts/agent/repository_gateway.py` — line 114
- `scripts/agent/commands/cmd_mdq.py` — line 67
- `scripts/agent/commands/cmd_context.py` — line 206
- `scripts/agent/tool_approval.py` — line 148
- `scripts/agent/tool_runner.py` — line 119 (bypass path)
- `docs/02_agent_01_architecture.md` or equivalent Agent documentation

## Required Changes
- Define a whitelist of sanctioned preflight-exempt paths (above)
- Create a coverage map documenting all execution paths and their preflight gate status
- Add tests for each uncovered execution path
- Resolve the `tool_runner.py` gateway-bypass gap (either add preflight or document why it is safe)
- Update Agent architecture documentation to describe the preflight gate coverage
- Update the Known Issue entry REQ-003 status to reflect the resolution

## Constraints
- Tests must not change the behavior of existing code paths
- The coverage map must be accurate and up-to-date; future changes to gate placement must update the map
- No new public APIs or behavioral changes beyond what is required for testing
- dry_run operations must remain preflight-exempt (they are read-only)
- READ operations must remain preflight-exempt (intentional design decision)

## Acceptance Criteria
- All 4 `check_preflight()` call sites are mapped to their caller chains
- Each mapped path has either a passing test or a documented justification for exclusion
- The `tool_runner.py` gateway-bypass gap is resolved (either fixed or documented as safe)
- The coverage map is included in Agent architecture documentation
- New `check_preflight()` additions require a corresponding test or documented exception

## Testing Expectations
- Unit tests: verify each uncovered execution path triggers the preflight gate appropriately
- Integration tests: verify end-to-end flow with gate enabled/disabled
- Regression tests: confirm existing Agent tests still pass after adding new coverage

## Documentation Impact
- Agent architecture documentation must include the preflight gate coverage map
- The Known Issue entry REQ-003 must be updated to reflect the resolution status
- Future gate additions require documentation updates as part of the acceptance criteria

## Out of Scope
- Modifying the `check_preflight()` function logic itself
- Adding new gate conditions beyond what already exists
- Changes to MCP server preflight behavior
- Changes to Event Bus preflight behavior

## Dependencies
- None — this issue is self-contained within the Agent subsystem

## Unresolved Questions
- Are there any execution paths that intentionally bypass the preflight gate? If so, they need documented justification.
- Is the current 4-call-site count stable, or do more paths exist that were missed during the original addition?
- When `ctx.services_required.gateway is None`, is the bypass safe because no tools are available, or does it represent a real security gap?
- Should dry_run operations be subject to preflight checks even though they are read-only?

## AI Implementation Instruction
- Do not modify the `check_preflight()` function logic
- Do not change existing test expectations unless a gap is confirmed
- Preserve the existing gate behavior — only add coverage, do not alter semantics
- Report open questions about the `tool_runner.py` gateway-bypass gap before proceeding

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260924-054349
- **Related target files**: scripts/agent/tool_policy.py, scripts/agent/repository_gateway.py, scripts/agent/commands/cmd_mdq.py, scripts/agent/commands/cmd_context.py, scripts/agent/tool_approval.py, scripts/agent/tool_runner.py
