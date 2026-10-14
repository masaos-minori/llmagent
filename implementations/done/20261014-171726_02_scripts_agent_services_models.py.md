# Implementation Procedure

## Goal

Extend the frozen `SessionRow` dataclass with a `message_count` field so the new count from `list_sessions()` flows through the dataclass rather than being read ad hoc (`REQ-001` / `AC-1`).

## Scope

Modify only the `SessionRow` dataclass in `scripts/agent/services/models.py` (lines 241-248). Add one field; do not touch any other dataclass.

## Assumptions

- `SessionRow` is a frozen dataclass with a single construction site (`_session_list` in `scripts/agent/commands/cmd_session.py`, line 100), so adding a field cannot break other constructors.
- `list_sessions()` already returns `message_count` (sibling procedure for `scripts/agent/session.py`).

## Design decisions

- Add `message_count: int` after `is_current: bool` (line 248). Position after existing fields keeps positional-construction order stable for the single caller.
- Type is `int` (not `Optional[int]`): `COUNT()` always returns a value (`0` or more).

## Alternatives considered

- `message_count: int | None`: rejected — `COUNT()` never returns `None` for a `LEFT JOIN` group, so `int` is the honest type.

## Implementation

### Target file

`scripts/agent/services/models.py`

### Procedure

1. Add the field line `    message_count: int` after `    is_current: bool` inside `SessionRow` (after line 248).
2. Optionally note the field in the class docstring (line 243) — keep it one line.

### Method

Add exactly one field. Do not reorder existing fields and do not add a default value (frozen dataclass constructed positionally by the single caller).

### Details

- The construction site (`cmd_session.py:100`) must pass `message_count=...` — that is the sibling procedure's responsibility; this document names it only as a verification dependency, not a modification target.

## Compatibility considerations

Single construction site; the sibling procedure updates that call. No external API surface exposes `SessionRow` beyond `_session_list`.

## Security considerations

N/A: dataclass field addition, no runtime behavior change.

## Rollback considerations

Revert the commit touching `scripts/agent/services/models.py`.

## Validation plan

| Target/Module | Strategy | Command | Expected |
|---|---|---|---|
| `scripts/agent/services/models.py` | Construction carries the field via `_session_list` | `uv run pytest tests/agent/commands/test_agent_cmd_session.py` | `SessionRow` constructs and renders without error |

## Completion criteria

`SessionRow` exposes an integer `message_count` field and `_session_list` constructs it with the value from `list_sessions()`.

## Out of scope

Query change (`scripts/agent/session.py`) and table rendering (`scripts/agent/commands/cmd_session.py`) are separate rows.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Extend `SessionRow` with `message_count` | Completed | 20261014-192531 | 20261014-192531 | field added after is_current; single construction site updated by sibling row 03 |
| 2 | Add/update tests per Validation plan | Completed | 20261014-192531 | 20261014-192531 | test_agent_cmd_session.py 54 pass; new tests belong to rows 04/05 (out of batch) |
| 3 | Run validation sequence (`rules/toolchain.md`) | Completed | 20261014-192531 | 20261014-192531 | ruff/mypy/bandit/lint-imports clean; full suite 8248 passed, 17 pre-existing unrelated failures |
| 4 | Update documentation | N/A | — | — | not in scope for this row |

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
- **Requirement ID**: `REQ-001` — add per-session message count to `/session list`
- **Source issue**: `issues/20261014-150311_sess001_finalize-session-list-command.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261014-160933_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261014-171726
- **Related target files**: `scripts/agent/services/models.py`
