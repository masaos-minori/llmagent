## Goal
- Determine whether `scripts/agent/services/mcp_tool_discovery.py` requires any
  change as a consequence of REQ-007's `degraded_servers`/`requires_approval`
  removal, and record the investigation result (REQ-007, part 3).

## Scope
- Investigation only. This file requires **no code change**.

## Assumptions
- N/A: this document records verified facts, not assumptions.

## Design decisions
- `discover_all()` constructs `RuntimeToolRegistry` in two places: the return of
  `_dedupe_and_build()` (`RuntimeToolRegistry(tools=built)`) and the
  `filtered_registry = RuntimeToolRegistry(tools=dict(registry._tools), unavailable_servers=unavailable_keys)` construction inside `discover_all()` itself.
  **Neither passes `degraded_servers=`.** Removing that keyword parameter (per the
  `runtime_tool_registry.py` document) therefore has no effect on either call site.
- The real consumer of the field being removed is `scripts/agent/startup.py`, which
  reads `runtime_tools.degraded_servers` directly to build a readiness-log line
  (`"Excluded tools (degraded): ..."`). That is a different file from this one and
  is not in the Plan's original "Related target files" list — it must be added as a
  target so removing the property in `runtime_tool_registry.py` does not cause an
  `AttributeError` at startup.

## Alternatives considered
- Adding a compatibility shim or dummy handling for `degraded_servers` in this file
  — unnecessary; this file never referenced the field in the first place.
- Placing the `startup.py` fix inside this document instead of a separate one —
  rejected; the two files have different responsibilities (registry construction
  here vs. readiness-log rendering in `startup.py`), and one document per target
  file is this workflow's own rule.

## Implementation
### Target file
`scripts/agent/services/mcp_tool_discovery.py` — **no change**.

### Procedure
N/A: no procedure for this file. See the companion `scripts/agent/startup.py`
document for the actual required change.

### Method
N/A: no code change.

### Details
- `tests/agent/services/test_mcp_tool_discovery.py` was checked in full: it contains
  no reference to `degraded_servers`/`requires_approval`, confirming no test update
  is needed here either.

## Compatibility considerations
- None: this file is unchanged.

## Security considerations
- N/A.

## Rollback considerations
- N/A: no change to roll back.

## Validation plan
- `uv run pytest tests/agent/services/test_mcp_tool_discovery.py -v` — confirms the
  full existing suite continues to pass unmodified, verifying this file needed no
  change.

## Out of scope
- The actual fix to `scripts/agent/startup.py` — separate document. Note: landing
  the `runtime_tool_registry.py` property removal without also landing the
  `startup.py` fix breaks the agent's startup readiness-log path; both must ship
  together.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Confirm no change is needed (per Implementation > Details) | Pending | — | — | Investigation complete; no code change required |
| 2 | Run regression tests per Validation plan | Pending | — | — | |

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
- **Source issue**: issues/20260821_h3-h4-m1-followup-implementation-tasks.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260825-095817_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260825-100839
- **Related target files**: scripts/agent/services/mcp_tool_discovery.py
