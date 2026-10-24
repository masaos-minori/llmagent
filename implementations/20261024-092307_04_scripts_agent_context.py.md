## Goal

Delete the six dead `TurnState` members that no code in `scripts/` produces or consumes
(`REQ-009`), leaving `current_turn_id` and `background_tasks` as the only fields.

## Scope

- **In-Scope**: removing from `TurnState` (`:193-216`): `last_error_kind` (`:202`),
  `tool_calls` (`:203`), `turn_count` (`:204`), `_lock` (`:205`), `add_tool_call` (`:207`),
  `get_tool_calls` (`:213`).
- **Out-of-Scope**: keeping `current_turn_id` (`:198`) and `background_tasks` (`:200`); the class
  docstring ("Per-turn transient state") stays accurate and is NOT rewritten; `WorkflowState`,
  `SessionState`, `RuntimeStats`, and `AgentContext` are not touched.

## Assumptions

- The only consumer of these members is `tests/agent/test_context.py:23-36`
  (`test_turn_state_concurrency`), which the sibling test document deletes (`REQ-010`).
- `docs/23_agent/agent_13_reference-api-generated.md` is generated from this file; deleting fields
  must produce no diff there (verified by `generate_reference_table.py --type agent --check`, not
  by editing).

## Design decisions

- Delete the members wholesale rather than deprecating them: they are unreachable from
  `scripts/` (measured — see below), so deletion is the Plan's chosen correction over population.

## Alternatives considered

`N/A: populating the members with real values was explicitly rejected by the user (REQ-009; the
issue's "user chose deletion over population"). Deprecating instead of deleting would leave dead
code that `vulture` flags.`

## Implementation

### Target file

`scripts/agent/context.py`

### Procedure

1. Open `TurnState` (`:193-216`).
2. Delete the field `last_error_kind: str | None = None` (`:202`) and its comment.
3. Delete the field `tool_calls: list[dict[str, Any]] = field(default_factory=list)` (`:203`) and
   its comment.
4. Delete the field `turn_count: int = 0` (`:204`) and its comment.
5. Delete the field `_lock: asyncio.Lock = field(default_factory=asyncio.Lock)` (`:205`) and its
   comment.
6. Delete the method `async def add_tool_call(self, call: dict[str, Any]) -> None:` (`:207-210`).
7. Delete the method `async def get_tool_calls(self) -> list[dict[str, Any]]:` (`:213-...`).
8. Keep `current_turn_id` and `background_tasks` and the class docstring unchanged.
9. Confirm `asyncio` is still used elsewhere in the file; if `_lock` was its only use, adjust the
   import (unlikely — `AgentContext._history_lock` uses `asyncio.Lock`).

### Method

Inline deletions within the `TurnState` dataclass; no new symbols. The file shrinks (from
14350 B; no baseline entry needed).

### Details

- Measured zero-consumer: `rg` over `scripts/` finds `last_error_kind` only at its declaration,
  and `tool_calls` / `turn_count` / `add_tool_call` / `get_tool_calls` / `_lock` appear only inside
  `context.py` itself (the `add_tool_call`/`get_tool_calls` methods operate on `self.tool_calls`;
  deleting both together removes the only accessors). `background_tasks` IS consumed by
  `resource_shutdown_coordinator.py:119-122` and `current_turn_id` by the emitter, so both stay.
- Do not touch the surrounding classes; the generated API reference (`agent_13`) emits only a
  class-level row for `TurnState`, so no field rows disappear there.

## Compatibility considerations

`TurnState` is a per-turn dataclass constructed internally; no external module constructs it with
keyword arguments referencing the deleted members. `tests/agent/test_context.py` is the sibling
document that drops its one test.

## Security considerations

`N/A: no auth, secret, or input-handling change.`

## Rollback considerations

`N/A: revert the single commit.`

## Validation plan

- `generate_reference_table.py --type agent --check` reports no drift (the generated API reference
  must not change).
- `vulture` reports no dead-code warnings for the deleted members.
- `tests/agent/test_context.py` (sibling document) no longer references the deleted members; the
  remaining `AgentContext` / `AppServices` tests pass.
- `ruff` + `mypy` + full agent test suite pass (`rules/toolchain.md`).

## Completion criteria

`TurnState` declares only `current_turn_id` and `background_tasks` (plus the unchanged docstring);
the six deleted members are gone, no `rg` reference to them remains in `scripts/` or `tests/`
(beyond the concurrently-deleted test), and `generate_reference_table.py --type agent --check`
passes.

## Out of Scope

The Orchestrator bracket (`orchestrator.py`), the adapter deletions
(`workflow_engine_adapter.py`), the emitter (`audit_event_emitter.py`), the test deletion
(`test_context.py`), and the doc passages are handled by sibling documents.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Delete the six dead `TurnState` members (`Implementation > Procedure`) | Pending | — | — | run after adapter deletes remove their last callers |
| 2 | Add or update tests per Validation plan | N/A: deletion only | | | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | `vulture`, `generate_reference_table.py --type agent --check`, full suite |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A: no doc edit in this file | | | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|--------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-009` (delete dead `TurnState` members; user chose deletion over
  population)
- **Source issue**: `issues/20261021-093421_turn004_turn-end-events-duplicated-or-missing.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261023-140855_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261024-092307
- **Related target files**: `scripts/agent/context.py`
