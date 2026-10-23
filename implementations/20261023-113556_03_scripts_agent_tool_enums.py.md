## Goal

Add the closed two-member `ToolCallStopReason` enum that names why a round did not
answer a declared id, consumed by the synthesis in `scripts/agent/tool_result_pairing.py`
(`REQ-004`).

## Scope

`scripts/agent/tool_enums.py` only. Appends one `StrEnum` after the existing
members. Reference reads: the existing `RiskLevel` / `OperationType` /
`ApprovalDecisionType` / `GuardDecisionType` `StrEnum` definitions (`:15-47`) for
the pattern to follow. Dependent test: `tests/agent/test_tool_result_pairing.py`.

## Assumptions

- The two reasons are exhaustive and closed: "the round stopped by a guard
  observation" and "the round did not complete". No third member will be added
  without widening this Plan (`REQ-004`).
- `GuardDecisionType` (`:40-47`) is not extended: a synthesized row is a result,
  not a guard decision.

## Design decisions

- Follow the existing `StrEnum` pattern (`:15-47`): `class ToolCallStopReason(StrEnum)`
  with two string-valued members. The string values are stable identifiers used
  as dict keys for the payload constants in `tool_result_pairing.py`.

## Alternatives considered

- A `Literal[...]` union instead of an enum — rejected because the plan wants a
  typed, closed, inspectable set (`REQ-004`), matching the file's existing enum
  convention.

## Implementation

### Target file

`scripts/agent/tool_enums.py`

### Procedure

Append after `GuardDecisionType` (`:40-47`):

```python
class ToolCallStopReason(StrEnum):
    """Why a declared tool call was not executed in a round."""

    GUARD_STOP = "guard_stop"
    ROUND_NOT_COMPLETED = "round_not_completed"
```

No call site exists yet; `tool_result_pairing.py` (row 2) imports it.

### Method

- Append-only; do not touch any existing member. Keep the file's single blank
  line between classes.

### Details

- Two members only. Adding a third widens this Plan (`REQ-004`).

## Compatibility considerations

- Pure addition; no existing symbol changes. `tool_runner.py` imports the new
  enum (row 1).

## Security considerations

- N/A: enum definition only.

## Rollback considerations

- Delete the appended class; `git checkout -- scripts/agent/tool_enums.py`
  restores HEAD.

## Validation plan

- `uv run pytest tests/agent/test_tool_result_pairing.py -q` — each member yields
  its own distinct text; neither equals `format_error_payload()` output or the
  `"Tool execution denied by user."` literal; an unknown reason cannot be
  constructed.
- `uv run ruff check scripts/`, `uv run ruff format --check scripts/`,
  `uv run mypy scripts/ --config-file scripts/mypy.ini`.

## Completion criteria

`ToolCallStopReason` exists as a two-member `StrEnum` following the file's existing
pattern; both members have distinct string values; all checks pass.

## Out of Scope

- The payload texts — `tool_result_pairing.py` (row 2).
- Consuming the enum — `tool_runner.py` (row 1).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Append two-member `ToolCallStopReason` `StrEnum` (REQ-004) | Pending | — | — | Phase 1 |
| 2 | Run validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: REQ-004
- **Source issue**: `issues/20261021-093421_tool002-tool-call-persisted-without-tool-results.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261022-105432_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261023-113556
- **Related target files**: `scripts/agent/tool_enums.py`
