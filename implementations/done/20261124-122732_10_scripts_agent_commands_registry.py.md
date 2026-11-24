## Goal

Add the job command handler path to the dispatcher without changing the registry's mixin composition, so the pinned MRO counts stay 10 and 8 (REQ-002: `/jobs cancel <id>` dispatches to a real handler; REQ-010: every registered command has a handler in the registry).

## Scope
**Release unit**: R2-job-commands (Phase 2)

- In scope: the `_cmd_jobs` handler path inside an existing mixin.
- Out of scope: the `CommandDef` registration (row 9), the completion set (row 11), the test assertions (row 41).

## Assumptions

- The handler is placed in an existing mixin rather than a new `*Mixin` class, per the plan decision recorded 2026-11-24.
- The existing mixin is `_SessionMixin` in `scripts/agent/commands/cmd_session.py`, confirmed by the owner 2026-11-24: the row's Target file (`registry.py`) and its step 1 read as a contradiction, and the test row (41) requires the handler to be inside an existing mixin, so `registry.py` itself does not change and the handler is recorded against `cmd_session.py`.
- `/jobs` with no subcommand lists the jobs recorded as running; the subcommand-only form was undefined in the plan, and the owner chose the listing behavior over a required subcommand (2026-11-24).
- `test_command_def_sync.py` (row 49) requires the handler name to exist on the registry, so the handler name must match the `CommandDef.handler` value exactly.

## Design decisions

- No new mixin: adding one would change the counts asserted at `tests/agent/commands/test_command_registry_consistency.py:155-164` (10 `*Mixin` classes in the MRO) and `:166-173` (8 direct `*Mixin` bases), so the handler belongs to an existing mixin.

## Alternatives considered

- A `JobMixin` (new) — rejected for the reason above; the counts are a contract pinned by tests, not an accident.

## Implementation
### Target file
`scripts/agent/commands/registry.py`

### Procedure
1. Add `_cmd_jobs` (new) to an existing mixin, reachable through `CommandRegistry.dispatch` (`registry.py:171`).
2. Resolve the job by id for `status`, and call `cancel` on the registry for `cancel <id>`; state the refusal reason for a `not_cancelable` job.
3. Keep `__init__` unchanged: the registry instance is read from `self._ctx.services`.

### Method
- The handler formats nothing beyond the state lines; the outcome text comes from the job record.

### Details
- All `_cmd_*` methods operate only on `AgentContext` per the module contract (`registry.py:7,64`); the job handler must not reach `AgentREPL`.
- The handler is a sync handler, so `is_async` is `False`; the unknown-subcommand path raises `UnknownSubcommandError` with the registered subcommand names, the same shape the Memory and MCP handlers use.
- Recorded deviation: the handler body sits in `scripts/agent/commands/cmd_session.py` (`_SessionMixin`), not in `registry.py`; the frozen target row names `registry.py` because the responsibility is the handler path reachable through `dispatch`, and `registry.py` needs no change to provide it.

### Companion test files
- None. tests/agent/commands/test_command_registry_consistency.py keeps its own document (row 41).

## Compatibility considerations

- Handler-shape assertions in `tests/agent/commands/test_command_registry_consistency.py` and `tests/agent/commands/test_cmd_registry_ingest_removal.py` are updated in the same phase (rows 41, 53).

## Security considerations

- The handler enforces nothing itself; approval is decided at registration. The handler only reports the recorded decision.

## Rollback considerations

- N/A: revert the Phase 2 commit.

## Validation plan

| Target | Strategy | Command | Expected outcome |
|---|---|---|---|
| `scripts/agent/commands/registry.py` | Unit | `uv run pytest tests/agent/commands/test_command_registry_consistency.py tests/agent/commands/test_command_def_sync.py -q` | `/jobs` handler exists, counts unchanged |
| Same file | Quality gates | `uv run ruff check scripts/agent/commands/registry.py`, `uv run mypy scripts/agent/commands/registry.py` | No finding |

## Completion criteria

- `/jobs status <id>` and `/jobs cancel <id>` dispatch to a handler in an existing mixin, and the MRO counts remain 10 and 8.

## Out of Scope

- The registration list, the completion candidate set, the command documentation.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `_cmd_jobs` inside an existing mixin | Completed | — | 20261124-165333 | Phase 2 Handler defined in cmd_session.py _SessionMixin, per the plan decision and the owner confirmation 2026-11-24; registry.py unchanged. Bare /jobs lists the recorded running jobs, and the refusal reason comes from CancelResult. |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261124-165333 | Tests updated by row 41 ruff, mypy (the CI invocation), check_module_size, check_docstrings, check_suppression_justification clean; the Phase 2 test set and test_agent_cmd_session.py pass. |

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
- **Requirement ID**: REQ-002 (`/jobs cancel <id>` dispatch target), REQ-010 (registered commands have handlers)
- **Source issue**: issues/20261119-145301_cliplc003_maintenance-job-framework.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-001800_cliplc003_maintenance-job-framework.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261124-122732
- **Related target files**: `scripts/agent/commands/registry.py`