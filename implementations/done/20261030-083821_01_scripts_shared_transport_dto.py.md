# Implementation Procedure: transport_dto.py DynamicAvailabilityHint contract

## Goal

Add the advisory dynamic-availability hint contract to `scripts/shared/transport_dto.py`:
a new `DynamicAvailabilityHint` (new) dataclass plus an `availability_hint` (new) field on
`ToolCallResult` (REQ-001, REQ-002; plan AC-2).

## Scope

**In scope:**
- `scripts/shared/transport_dto.py`: define `DynamicAvailabilityHint` (new) and add
  `availability_hint: DynamicAvailabilityHint | None = None` to `ToolCallResult`.

**Out of scope:**
- Producing hint values (rows 02, 03). Consuming hints (rows 04, 05). This row changes no
  behavior: every existing call path produces `availability_hint=None`, identical to today.

## Assumptions
- Verified at HEAD `124e340b4`: `ToolCallResult` is a **frozen** dataclass
  (`transport_dto.py:8`) with fields `output`, `is_error`, `request_id`, `server_key`,
  `source=""`, `error_type=""` and the `from_transport()` classmethod.
- Construction sites use keywords (`_error_result`, `from_transport`); `HttpTransport`
  uses `dataclasses.replace` (`http_transport.py`), which preserves frozen semantics.
- `McpServerHealthState` import (`shared.mcp_health`) into `transport_dto` is a
  shared→shared import and passes `lint-imports` (import contract: shared must not import
  agent/services/tools/cli; `mcp_health.py` is shared).

## Design decisions
- `DynamicAvailabilityHint` (new) is a frozen dataclass matching the plan Design section:
  `reason: Literal["server_unavailable", "half_open_trial_in_progress"]`,
  `circuit_state: McpServerHealthState`, `retry_after_seconds: int | None`. The reason
  literal is a closed enum-by-literal (prompt-injection risk mitigation: no
  server-controlled strings enter the hint).
- `reason` is stored as the literal string; the canonical constants live with the
  registry row (02) — this module owns only the shape. Import direction:
  `transport_dto` → `mcp_health` (for `McpServerHealthState` only).
- `availability_hint=None` means "no dynamic availability signal" — the default keeps
  today's behavior for all healthy and non-health error results.
- Field appended last so positional construction at all sites is unaffected.
- The hint never blocks, reroutes, or retries by itself (REQ-001): this row adds data
  only; no gate logic.

## Alternatives considered
- Reuse `error_type`/`output` free text instead of a structured field: rejected — the plan
  fixes the contract on the structured result so consumers key on normalized codes, and
  free text must stay backward compatible for existing tests/operators.
- Hint on `RuntimeTool` static fields: explicitly forbidden by ADR-003 static/dynamic
  separation (plan Implementation Intent); carried on the result only.

## Implementation
### Target file
`scripts/shared/transport_dto.py`

### Procedure
1. Import `McpServerHealthState` from `shared.mcp_health` and `Literal` from `typing`.
2. Define frozen dataclass `DynamicAvailabilityHint` (new) with the three fields above.
3. Append `availability_hint: DynamicAvailabilityHint | None = None` to `ToolCallResult`
   after `error_type`.
4. Leave `from_transport`, `TransportErrorInfo`, and all existing fields untouched.

### Method
- Additive-only edit; no renames or deletions.

### Details
- `retry_after_seconds` (new) is `int | None` (seconds, never negative; derivation owned by
  row 02). No validation in the DTO — construction discipline lives at the producer
  (row 03).

## Compatibility considerations
- Frozen semantics preserved: attaching a hint at producer sites uses keyword
  construction in `_error_result` or `dataclasses.replace` (row 03).
- Audit/serialization consumers (`TransportErrorInfo.detail` JSON writers, log
  redaction) are untouched; `dataclasses.asdict` consumers gain the nested hint key —
  row 07 tests lock existing serialized shapes that must not change when the hint is
  None.

## Security considerations
- Closed `Literal` reason set prevents server-controlled text from entering the hint;
  server free-text remains only in `output` (unchanged channel).

## Rollback considerations
- Reverting this file removes the field and dataclass; rows 02/03 producers fail to
  import `DynamicAvailabilityHint` (new) and must be reverted together.

## Validation plan
- Row 07 (`tests/shared/test_transport_dto.py`): default `availability_hint is None` on
  `from_transport` and legacy construction; hint field round-trip when constructed.
- Full suite green with no consumer edits (`uv run pytest`).
- `uv run mypy --no-namespace-packages scripts/` and `PYTHONPATH=scripts uv run
  lint-imports` clean (new shared→shared import only).

## Completion criteria
- `DynamicAvailabilityHint` (new) exists with the exact plan shape; `ToolCallResult` accepts
  the optional field; all existing tests pass unchanged.

## Out of Scope
- Reason-code constants and `retry_after_seconds` (new) derivation (row 02), invoker attachment
  (row 03), guard/runner consumption (rows 04-05), docs (rows 12-14).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Define `DynamicAvailabilityHint` (new) and append `availability_hint` (new) to `ToolCallResult` | Completed | 20261030-201712 | 20261030-202710 |  |
| 2 | Confirm all existing construction sites unaffected (`uv run pytest`) | Completed | — | 20261030-202710 |  |
| 3 | Run `uv run mypy --no-namespace-packages scripts/` and `lint-imports` | Completed | — | 20261030-202710 |  |

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
- **Related target files**: `scripts/shared/transport_dto.py`