# Implementation Procedure: Add fail-closed else branch to MCPServer.run_http()

## Traceability
- **Source issue**: issues/20260907-131738_h02b_config_loader_fail_closed_remaining_gaps.md
- **Source plan**: plans/20260907-234317_plan.md
- **Related target files**: scripts/mcp_servers/server.py

## Goal
Add fail-closed else branch to `MCPServer.run_http()` raising an error when `own_config_file` is falsy instead of silently skipping Config Isolation restriction.

## Priority
High

## Scope
- **In-Scope**: Add fail-closed else branch to MCPServer.run_http() when own_config_file is falsy
- **Out-of-Scope**: Any other server.py behavior change; ProductionConfigValidator logic changes

## Background
`scripts/mcp_servers/server.py::MCPServer.run_http()` still guards `restrict_to()` with a bare `if self.own_config_file:` (no `else`/fail-closed branch) — a falsy `own_config_file` silently skips Config Isolation restriction (REQ-003 unmet). The original H-02 issue identified this as a security-relevant fail-closed gap.

## Problem
A falsy `own_config_file` value bypasses Config Isolation enforcement without raising an error, allowing unrestricted access to MCP servers.

## Reason for change
This is a security fix — Config Isolation must be enforced at startup regardless of whether `own_config_file` is set. Without the fail-closed branch, a falsy value silently disables the security control.

## Implementation Steps

### Step 1: Locate the current guard in run_http()
Read `scripts/mcp_servers/server.py` around line 226 where `restrict_to()` is called.
Expected outcome: Find the bare `if self.own_config_file:` guard without an else/fail-closed branch.

### Step 2: Implement the fail-closed else branch
Add an else branch that raises an error when `own_config_file` is falsy:
```python
if self.own_config_file:
    # existing restrict_to() call
else:
    raise ValueError("Config Isolation requires own_config_file to be set")
```
Expected outcome: The else branch raises immediately on falsy own_config_file, consistent with strict=True default established by REQ-001.

### Step 3: Verify no bypass caller exists outside run_http()
Search for other callers of `restrict_to()` or places where Config Isolation could be bypassed:
Run: `rg "restrict_to\|own_config_file" scripts/mcp_servers/server.py`
Expected outcome: Only the guarded path in run_http() references restrict_to/own_config_file.

### Step 4: Classify the cluster
If the fail-closed branch is added → classify as **implementation regression** (security gap closed).
If the fail-closed branch cannot be added due to API constraints → report as Plan Gap.

## Acceptance criteria
- [ ] Fail-closed else branch added to MCPServer.run_http()
- [ ] Error raised when own_config_file is falsy
- [ ] No bypass caller exists outside run_http()
- [ ] REQ-003 satisfied

## Tests
New unit/integration tests for the falsy-`own_config_file` fail-closed path in `tests/shared/test_config_loader.py` (see related target file).

## Documentation Impact
Yes: ADR-002 and ADR-004 documentation updates required (see related target files).

## Dependencies
- REQ-003: MCPServer.run_http() fails closed when own_config_file is falsy
- REQ-001: strict=True default (already implemented, out of scope here)

## Assumptions
- The error message should be clear and actionable for operators
- The fail-closed behavior is consistent with the strict=True default established by REQ-001

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether the fail-closed branch may cause startup failures in development environments where own_config_file is intentionally falsy | Need to verify all four environments before deploying | Check environment configurations | False |

## Affected areas
`skills/DESIGN.md` Change-impact table — high blast radius (runtime behavior change).

## Design
This is a Path A task (single file, runtime interface change). The approach is simple: add an else branch to the existing if-guard, raising a ValueError when own_config_file is falsy. This is consistent with the strict=True default established by REQ-001.

## Alternatives considered
- Using None as a sentinel value instead of a bare falsy check — rejected because it would require changing the type signature and would not address the root cause (silent skip)
- Adding a warning instead of raising — rejected because this is a security-relevant gap that must fail closed, not warn

## Compatibility considerations
- Existing deployments with falsy own_config_file will now fail at startup — ensure each environment has a valid own_config_file configured before deploying
- The error message should be clear enough for operators to understand what needs to be fixed

## Security considerations
- This is a security fix — Config Isolation must be enforced at startup regardless of whether own_config_file is set
- The fail-closed behavior prevents silent bypass of the security control

## Rollback considerations
- If the fail-closed branch causes unexpected startup failures, revert to the bare if-guard temporarily while investigating environment configurations
- Ensure rollback procedure includes verifying own_config_file configuration in all environments

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Locate current guard in run_http() | Pending | — | — | |
| 2 | Implement fail-closed else branch | Pending | — | — | |
| 3 | Verify no bypass caller | Pending | — | — | |
| 4 | Classify cluster | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Source issue**: issues/20260907-131738_h02b_config_loader_fail_closed_remaining_gaps.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260907-234317_plan.md
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20260908-093609
- **Related target files**: scripts/mcp_servers/server.py

(End of file - total 100 lines)
