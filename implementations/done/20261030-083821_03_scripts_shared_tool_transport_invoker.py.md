# Implementation Procedure: tool_transport_invoker.py hint attachment

## Goal

Attach `DynamicAvailabilityHint` (new) values to the UNAVAILABLE and HALF_OPEN-busy
`_error_result`s produced by the health gate in `scripts/shared/tool_transport_invoker.py`
(REQ-001, REQ-002; plan AC-2).

## Scope

**In scope:**
- `scripts/shared/tool_transport_invoker.py`: `_error_result()` gains an optional
  `availability_hint` (new) keyword; `_check_health()` builds hints for its two rejection
  branches.

**Out of scope:**
- Any new gate or retry behavior: the gate chain (`_run_precall_gates`: health → disabled
  → lifecycle → transport → semaphore → dispatch) and its decision semantics are
  unchanged — the hint is data carried on results the gate already returns (REQ-001
  "advisory only").
- Transport-failure results from `_record_transport_error` / lifecycle errors: no hint
  (plan scope is the two health-gate outcomes only).

## Assumptions
- Verified at HEAD `124e340b4`: `_error_result()` builds results by keyword
  (`tool_transport_invoker.py:141-155`); `_check_health()` returns the fixed texts
  "MCP server 'X' has a HALF_OPEN trial already in progress" and "... currently
  unavailable (health check failed)" (`:157-195`); `health_registry` is a required
  constructor keyword (`:41`).
- Free-text messages stay byte-identical: existing tests and operators key on them
  (plan Design: "free-text message preserved for backward compatibility").

## Design decisions
- `HALF_OPEN`-busy branch: hint
  `(reason=HEALTH_REASON_HALF_OPEN_TRIAL_IN_PROGRESS, circuit_state=HALF_OPEN, retry_after_seconds=None)`
  — state read directly from `_check_health`'s existing `get_state()` result (no extra
  call).
- UNAVAILABLE rejection branch: after `is_unavailable()` returns True the registry state
  is still `UNAVAILABLE` (the transition to HALF_OPEN only happens when it returns
  False), so hint uses `circuit_state=McpServerHealthState.UNAVAILABLE` and
  `retry_after_seconds=registry.retry_after_seconds(server_key)` (row 02).
- `retry_after_seconds` (new) is computed after `is_unavailable()` runs, so the value reflects
  the same monotonic instant the rejection was decided (plan Assumption: computed at
  result-build time).
- Reason constants and `DynamicAvailabilityHint` (new) are imported from `shared.mcp_health` /
  `shared.transport_dto` — shared→shared only.

## Alternatives considered
- `dataclasses.replace(result, availability_hint=...)` at return sites: rejected —
  `_error_result` already centralizes construction; a keyword parameter is smaller and
  keeps every health-gate result hint-carrying by one edit.
- Attaching hints to all transport errors: rejected — plan REQ-002 names exactly the
  UNAVAILABLE and HALF_OPEN-busy outcomes; transport-failure results keep today's shape.

## Implementation
### Target file
`scripts/shared/tool_transport_invoker.py`

### Procedure
1. Import `DynamicAvailabilityHint` (new) from `shared.transport_dto` and the reason constants
   from `shared.mcp_health`.
2. Add `availability_hint: DynamicAvailabilityHint | None = None` to `_error_result()`.
3. In `_check_health()`, pass the HALF_OPEN-busy hint and the UNAVAILABLE hint per the
   branch mapping above.

### Method
- Three localized edits; no gate ordering or counter changes.

### Details
- `from_transport` and `_invoke_and_record` paths never pass a hint (default None).
- `get_error_counters()` and stat counters unchanged.

## Compatibility considerations
- Consumers that ignore the new DTO field see identical behavior.
- `tests/shared/test_tool_transport_invoker.py` existing assertions on exact error texts
  must remain green (row 09 adds, never relaxes, assertions).

## Security considerations
- Only closed-enum reason codes and enum states enter the hint; `output` free text is
  unchanged (row 01 same policy).

## Rollback considerations
- Reverting this file alone leaves rows 01/02 primitives unused but harmless; consumers
  of hinted results (rows 04-05) fall back to `availability_hint=None` behavior.

## Validation plan
- Row 09: UNAVAILABLE rejection carries hint with correct reason/state/int retry_after;
  HALF_OPEN-busy rejection carries reason/state and `retry_after_seconds is None`;
  healthy calls and tool errors carry `availability_hint is None`; legacy texts
  unchanged.
- `uv run pytest tests/shared/test_tool_transport_invoker.py
  tests/shared/test_tool_transport_invoker_merge.py`; mypy; `lint-imports`.

## Completion criteria
- Exactly the two health-gate rejection results carry hints; no other result shape or
  gate decision changes; all existing invoker tests pass.

## Out of Scope
- Guard counters (row 04), runner surfacing (row 05), registry derivation (row 02),
  docs (row 14).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add hint keyword to `_error_result` and build hints in `_check_health` | Completed | 20261030-202827 | 20261030-202923 |  |
| 2 | Confirm existing invoker tests (exact texts) pass unchanged | Completed | — | 20261030-202923 |  |
| 3 | Run mypy and `lint-imports` (shared-only imports) | Completed | — | 20261030-202923 |  |

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
- **Requirement ID**: `REQ-001`, `REQ-002`
- **Source issue**: `issues/20261029-104507_toolhint001_dynamic-tool-health-hints.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/done/20261029-215111_toolhint001_dynamic-tool-health-hints.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-083821
- **Related target files**: `scripts/shared/tool_transport_invoker.py`