## Goal

Capture the session target when the first-turn title task is created and register the task with the monitor (REQ-004 target capture, REQ-005 monitor registration; AC-2).

## Scope
**Release unit**: N/A: not part of a release unit

Single-file change; row 28 is covered as this document's companion.

## Assumptions
- Current code verified: `conversation_state_manager.py:105-113` creates the title task with `asyncio.create_task` from `on_first_turn(line)` when `stat_turns == 1`; `on_first_turn` is wired to the command-layer title generator via `startup_component_init.py:124` and stays signature-unchanged (plan Assumption).
- A task copies its creation context, so a context variable set immediately before `create_task` is visible inside the task (plan Assumption).

## Design decisions
- Set a module-level `contextvars.ContextVar` (new) holding `ctx.session.capture_target()` right before `asyncio.create_task`; the title modules (seq 10-11) read it — one documented helper for set/read (plan Design; the rejected alternative is an `on_first_turn(line, target)` signature change touching orchestrator and audit plumbing).
- Register the created task with the monitor's new register API (seq 08) with type "session_title" and the captured session id and generation.

## Alternatives considered
- Passing the target through the callback signature: explicitly rejected in the plan Design section.

## Implementation
### Target file
`scripts/agent/conversation_state_manager.py`
### Procedure
1. Capture the target and set the context variable immediately before the `create_task` call at 105-113; reset it after the creation line.
2. Replace the bare `self._tasks.add` bookkeeping for the title task with monitor registration (new register API, seq 08) when a monitor is reachable, keeping current discard behavior otherwise.
### Method
Context-variable binding plus one registration call; no signature changes in this or adjacent modules.
### Details
- `orchestrator.py:261-266` constructs the monitor and `startup_component_init.py` wires `on_first_turn`; both are reference rows (read-only) — if the monitor is not reachable from this module at execution time, register through the existing task-done path rather than modifying a reference file (additional-target discovery would stop the row per the skill rule).

### Companion test files
- `tests/agent/test_orchestrator.py`
  - Procedure: assert the title task is created with the captured target visible in the task context and registered with the monitor.
  - Validation: `uv run pytest tests/agent/test_orchestrator.py -q`.

## Compatibility considerations
- The context variable is invisible at the call site (plan Risk): the helper is documented in the module docstring so readers find the binding.

## Security considerations
N/A: no new data surface; target values are internal ids.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/agent/test_orchestrator.py -q`.

## Completion criteria
The title task sees the target captured at its creation time and appears in the monitor with type and session identity (AC-2).

## Out of Scope
Monitor internals (seq 08), title-side reads (seq 10-11).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | After seq 01, 08 |
| 2 | Add or update tests per Validation plan (companion row 28) | Pending | — | — | Tests written first per plan Phase 4 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | Generated docs via seq 18 |

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
- **Requirement ID**: `REQ-004` (capture target at task creation), `REQ-005` (monitor registration)
- **Source issue**: `issues/20261119-145300_cliplc002_session-transition-generation.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261122-232757_cliplc002_session-transition-generation.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261123-094714
- **Related target files**: `scripts/agent/conversation_state_manager.py`, `tests/agent/test_orchestrator.py`
