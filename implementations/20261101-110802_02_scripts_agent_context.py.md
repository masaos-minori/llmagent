## Goal

Add the `ToolCallRecorder` seam to `scripts/agent/context.py`: a typing-only Protocol and a
`tool_call_recorder` field on `WorkflowState`, so the producer (`tool_runner`, row 01) can
write `tool_call_state` rows without importing or owning any state store. Implements
REQ-005 (design decision D2).

## Scope

- Add `class ToolCallRecorder(Protocol)` to `scripts/agent/context.py`.
- Add one field `tool_call_recorder: ToolCallRecorder | None = None` to the existing
  `@dataclass class WorkflowState` (L248 onward).
- Nothing else in the file changes.

## Assumptions

- The Protocol mirrors only the three facade methods `tool_runner` uses
  (`record_tool_call`, `finalize_tool_call`, `mark_tool_call_interrupted`); the concrete
  `StateStore` already exposes exactly these (facade, `state_store.py` L174-199) and
  satisfies it structurally without inheritance.
- `context.py` already imports `Protocol` for `ApprovalProvider`/`SkillRegistryProvider`, so
  no new import line is needed.

## Design decisions

- Structural Protocol rather than importing `agent.workflow.state_store`: `context.py` is
  imported by nearly every agent module, so a runtime import of the workflow subpackage from
  here would risk an import-cycle against the `agent -> shared` layer contract (the plan's
  dependency-flow audit lists `context.py` as a shared import hub with 7+ importers).
  Structural typing keeps the seam at zero runtime cost.
- Field default `None`: unwired contexts (unit tests, non-adapter paths) keep working with
  zero behavior change; this makes rows 01 and 02 individually deployable in any order.
- The field lives on `WorkflowState` (not `AgentContext` directly): it is per-session turn
  runtime state, exactly like `current_task_id`, and `tool_runner` already reaches
  `ctx.workflow` (frozen context-flow audit row 11).

## Alternatives considered

- ContextVar (the wiped-WIP design, plan UNK-05): rejected — ambient implicit state, and the
  committed `execute_one_tool_call` already receives `ctx` (`context-flow audit`, row 11).
- New `recorder` keyword threaded through `execute_all_tool_calls` → `_execute_with_dag` →
  `_run_plan_batches` → `_run_group_calls` → `_recorded_call`: rejected — four signature
  changes for what one dataclass field does.
- Importing `StateStore` directly in `tool_runner`: rejected — concrete coupling and an
  agent-module owning state-store construction, against the plan's injection design.

## Implementation
### Target file

`scripts/agent/context.py`

### Procedure

1. Define the Protocol near the existing `ApprovalProvider`/`SkillRegistryProvider`
   Protocols, method signatures copied from the facade (`state_store.py` L174-199):
   ```python
   class ToolCallRecorder(Protocol):
       """Structural seam for writing agent-side tool_call_state rows.

       Implemented by agent.workflow.state_store.StateStore; deliberately not
       imported here so context.py stays import-cycle-free.
       """

       def record_tool_call(
           self, task_id: str, idempotency_key: str, tool: str, retry_class: str
       ) -> None: ...

       def finalize_tool_call(self, task_id: str, idempotency_key: str, state: str) -> None: ...

       def mark_tool_call_interrupted(self, task_id: str, idempotency_key: str) -> None: ...
   ```
2. Add the field to `WorkflowState` alongside the existing per-turn fields:
   `tool_call_recorder: ToolCallRecorder | None = None`.

### Method

Two additive edits; no existing lines modified.

### Details

- Signatures must match the facade exactly (parameter names and types) so mypy accepts
  `StateStore` where `ToolCallRecorder` is expected under `uv run mypy scripts/` with
  `disallow_untyped_defs = true`.
- `mark_tool_call_interrupted` is included in the Protocol for completeness of the facade
  triad even though the producer does not call it (the consumer's `classify_stale_pending`
  owns that transition); keeping it prevents a Protocol-vs-implementation complaint about
  narrowing the facade surface.

## Compatibility considerations

- `WorkflowState` is constructed only as a `field(default_factory=WorkflowState)` member of
  `AgentContext` and never positional-built elsewhere (the plan's compatibility audit
  confirms no direct `WorkflowState(...)` call sites in scripts/ or tests/); a defaulted
  field is additive.
- `AgentContext` copying: the field holds `None` in all existing paths, so no behavior
  change.

## Security considerations

- N/A: typing-only addition, no I/O.

## Rollback considerations

- Removing the field and Protocol reverts cleanly. Roll back rows 01/02/03 as a unit when
  abandoning the feature: row 01 reads the field, so revert 01 (and 03) before 02.

## Validation plan

- `uv run mypy scripts/` passes with the Protocol (mypy verifies `StateStore` satisfies it
  at the row 03 assignment site).
- `uv run pytest tests/agent -x -q` — no test changes needed for this row alone.
- Full sequence per `rules/toolchain.md` (baseline: 0 vulture findings in this file, 0
  bandit findings; the Protocol methods must not add vulture "unused" findings — they are
  consumed by row 01's callsites).

## Completion criteria

- `WorkflowState.tool_call_recorder` exists, defaults to `None`, is typed
  `ToolCallRecorder | None`.
- mypy accepts the adapter assigning `self._state_store` (row 03) to the field.
- All 321 agent tests pass unchanged.

## Out of Scope

- Any runtime import of workflow/state-store modules in `context.py`.
- Recorder wiring (row 03) and producer usage (row 01).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: REQ-005
- **Source issue**: issues/done/20261031-175803_toolstate001_tool-call-state-producer.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261101-105136_toolstate001_tool-call-state-producer.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261101-110802
- **Related target files**: scripts/agent/context.py
