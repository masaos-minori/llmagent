## Goal
- Remove the two dead attempt methods of `StateStore` and make the live `finish_attempt` delegate to `attempt_ops`, so attempt CRUD has one owner (`REQ-001`: delete `start_attempt` and `count_attempts`; `REQ-002`: delegate `finish_attempt`; `REQ-004`: drop imports left unused).

## Scope
**Release unit**: N/A: not part of a release unit
- Edits `scripts/agent/workflow/state_store.py` only. `recover_stale_attempts` keeps its own `UPDATE attempts` (a stale-recovery transition, outside this Issue).
- `attempt_ops.start_attempt` / `count_attempts` stay: tests use them and the wfrecovery001 Plan rewrites them.

## Assumptions
- `StateStore.start_attempt` and `count_attempts` have no caller in `scripts/`, `tests/`, `docs/`, `config/`, or `tools/` (`rg` in the Plan and re-run when this procedure is executed).
- `StateStore.finish_attempt` and `attempt_ops.finish_attempt` run the same `UPDATE` and end with `commit()`; delegation is behavior-neutral.
- `plans/done/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md` (consumed, not implemented) also removes the `start_attempt` bypass and changes `finish_attempt`; after this change its `finish_attempt` edit lands only in `attempt_ops.py`.

## Design decisions
- `attempt_ops` is the owner, mirroring how this module already delegates task operations to `task_ops`; the module is imported as `attempt_ops`, like `tool_call_state_ops`, so the method name does not shadow a function.
- Delete rather than delegate the two dead methods; the lease-less `start_attempt` is a trap.

## Alternatives considered
- Delegate `start_attempt` / `count_attempts` too: rejected, because with no callers a delegate only keeps a misleading public surface.

## Implementation
### Target file
`scripts/agent/workflow/state_store.py`

### Procedure
1. Change `from agent.workflow import tool_call_state_ops` to `from agent.workflow import attempt_ops, tool_call_state_ops`.
2. Delete `StateStore.start_attempt` and `StateStore.count_attempts`.
3. Replace the body of `StateStore.finish_attempt` with a single call `attempt_ops.finish_attempt(self._db, attempt_id, status, error_msg, error_kind, error_detail)`, keeping the method signature and the docstring.
4. Remove `import uuid` and `AttemptRecord` from `from agent.workflow.models import AttemptRecord, TaskRecord` (leaving `TaskRecord`), since only the deleted method used them; keep `_now`, which `recover_stale_attempts` still uses.

### Method
- Keep the `# ── Attempt` section header in place, with `finish_attempt` as its only method.
- Pass the arguments positionally in the order of `attempt_ops.finish_attempt(db, attempt_id, status, error_msg, error_kind, error_detail)`.
- Do not touch `recover_stale_attempts` or any other method.

### Details
- After the edit: `rg "def (start_attempt|count_attempts)" scripts/agent/workflow/state_store.py` finds nothing, and `rg "UPDATE attempts SET status=\?" scripts` finds one match, in `attempt_ops.py`.
- Run `uv run ruff check --fix scripts/agent/workflow/state_store.py` only to confirm no unused import remains.

## Compatibility considerations
- Two public methods are removed; they have no callers in the repository, so only an out-of-tree script could be affected (none is known).
- `finish_attempt` keeps its signature, SQL, and commit, so `workflow_engine.py`'s five calls are unaffected.

## Security considerations
- N/A: no input handling, secrets, or trust boundary involved.

## Rollback considerations
- Revert the commit; no persisted data changes.

## Validation plan
- `uv run pytest tests/agent/workflow tests/agent/test_orchestrator.py` passes unchanged (the real-database engine tests drive `StateStore.finish_attempt`).
- `uv run ruff check scripts/agent/workflow/state_store.py`; `uv run mypy --no-namespace-packages scripts/ tests/eventbus`; `uv run bandit -r scripts/ -c pyproject.toml -ll`; `uv run python tools/check_module_size.py`; `uv run python tools/generate_reference_table.py --check`.

## Completion criteria
- The two methods are gone, `finish_attempt` contains no SQL, no unused import remains, and the checks above pass.

## Out of Scope
- `recover_stale_attempts`, `attempt_ops.py`, `begin_stage_if_new` (procedure `_02`), and any schema change.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Re-run the caller search for `start_attempt` and `count_attempts` and record the result | Pending | — | — | |
| 2 | Delete the two methods, delegate `finish_attempt`, and remove the unused imports | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-001` (remove dead methods), `REQ-002` (delegate `finish_attempt`), `REQ-004` (unused imports)
- **Source issue**: issues/20261103-134148_wfreview006_duplicate-attempt-crud-apis.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261105-090240_wfreview006_duplicate-attempt-crud-apis.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261105-093002
- **Related target files**: `scripts/agent/workflow/state_store.py`
