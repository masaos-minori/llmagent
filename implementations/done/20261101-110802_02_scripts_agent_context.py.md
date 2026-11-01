## Goal

Add the `ToolCallRecorder` seam to `scripts/agent/context.py`: a typing-only Protocol and a
`tool_call_recorder` field on `WorkflowState`, so the producer (`tool_runner`, row 01) can
write `tool_call_state` rows without importing or owning any state store. Implements
REQ-005 (design decision D2).

## Scope

- Add `class ToolCallRecorder(Protocol)` to `scripts/agent/context.py`.
- Add one field `tool_call_recorder: ToolCallRecorder | None = None` (new) to the existing
  `@dataclass class WorkflowState` (L250-259).
- Nothing else in the file changes.

## Assumptions

- The Protocol mirrors exactly the two facade methods `tool_runner` uses (`record_tool_call`,
  `finalize_tool_call`) with signatures identical to the real facade (`state_store.py`
  L174-190: `record_tool_call(self, task_id, idempotency_key, tool, retry_class,
  snapshot_id=None)` and `finalize_tool_call(self, idempotency_key, state)` — no `task_id`
  in finalize). The real `StateStore` satisfies it structurally without inheritance. The
  facade has NO `mark_tool_call_interrupted` method anywhere in `scripts/`; the `interrupted`
  transition is owned by `classify_stale_pending` (consumer side).
- `context.py` currently imports `TYPE_CHECKING, Any, cast` from `typing` (L28) — `Protocol`
  must be added to that import. There are no existing `ApprovalProvider`/`SkillRegistryProvider`
  Protocols in the codebase (they do not exist in `scripts/`).

## Design decisions

- Structural Protocol rather than importing `agent.workflow.state_store`: `context.py` is
  imported by nearly every agent module, so a runtime import of the workflow subpackage from
  here would risk an import-cycle against the `agent -> shared` layer contract (the plan's
  dependency-flow audit lists `context.py` as a shared import hub with 7+ importers).
  Structural typing keeps the seam at zero runtime cost.
- Field default `None`: unwired contexts (unit tests, non-adapter paths) keep working with
  zero behavior change. Execution order dependency: row 02 (this field) must land BEFORE
  rows 01 and 03, which read/assign it; after 02, rows 01/03 are order-independent with each
  other.
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

1. Add `Protocol` to the existing `from typing import TYPE_CHECKING, Any, cast` line (L28).
2. Define the Protocol directly above the `WorkflowState` class (L250-251), signatures copied
   verbatim from the facade (`state_store.py` L174-190):
   ```python
   class ToolCallRecorder(Protocol):
       """Structural seam for writing agent-side tool_call_state rows.

       Implemented by agent.workflow.state_store.StateStore; deliberately not
       imported here so context.py stays import-cycle-free.
       """

       def record_tool_call(
           self,
           task_id: str,
           idempotency_key: str,
           tool: str,
           retry_class: str,
           snapshot_id: str | None = None,
       ) -> None: ...

       def finalize_tool_call(self, idempotency_key: str, state: str) -> None: ...
   ```
3. Add the field to `WorkflowState` alongside the existing per-turn fields (beside
   `current_task_id`, L259): `tool_call_recorder: ToolCallRecorder | None = None`.

### Method

Two additive edits; no existing lines modified.

### Details

- Signatures must match the facade exactly (parameter names, defaults, and types) so mypy
  accepts `StateStore` where `ToolCallRecorder` is expected at the row-03 assignment site
  under `uv run mypy --no-namespace-packages scripts/ tests/eventbus`.
- The Protocol intentionally contains no `mark_tool_call_interrupted`: that symbol does not
  exist anywhere in `scripts/`, and declaring it would make `StateStore` fail the structural
  check at the row-03 assignment. The `interrupted` transition is owned by
  `classify_stale_pending` (already merged, consumer side).

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

- `uv run mypy --no-namespace-packages scripts/ tests/eventbus` passes with the Protocol
  (mypy verifies `StateStore` satisfies it at the row 03 assignment site).
- `uv run pytest tests/agent -x -q` — no test changes needed for this row alone.
- Full sequence per `rules/toolchain.md` (baseline: 0 vulture findings in this file, 0
  bandit findings; the Protocol methods must not add vulture "unused" findings — they are
  consumed by row 01's callsites).

## Completion criteria

- `WorkflowState.tool_call_recorder` exists, defaults to `None`, is typed
  `ToolCallRecorder | None`.
- mypy accepts the adapter assigning `self._state_store` (row 03) to the field.
- All 3851 tests collected under `tests/agent/` (measured 2026-11-01) pass unchanged.

## Out of Scope

- Any runtime import of workflow/state-store modules in `context.py`.
- Recorder wiring (row 03) and producer usage (row 01).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261101-120309 | 20261101-120309 | Protocol+field added; static gates and tests/agent (3848 passed/3 skipped) green |
| 2 | Add or update tests per Validation plan | Completed | — | — | N/A for this row: test coverage lands in rows 04/05 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261101-121144 | 20261101-121144 | Full suite 10852 passed/1 drift failure (agent_api manifest stale from new symbol) fixed via generate_reference_table --manifests --type agent; diff-cover 100% |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261101-121144 | 20261101-121144 | docs/23_agent/agent_13_reference-api-generated.md re-rendered; check_docs_consistency --domain agent clean |

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