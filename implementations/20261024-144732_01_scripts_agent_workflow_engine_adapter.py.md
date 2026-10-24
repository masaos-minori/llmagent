## Goal

Make `WorkflowEngineAdapter.execute_turn` stop writing a task status that the workflow engine has
already written, stop writing `completed` entirely, record a cancelled turn as `halted`, and log a
failed best-effort status write at `error` level with the task id and the intended status
(`REQ-001`-`REQ-006`, `REQ-008`; `AC-1`-`AC-6`, `AC-10`).

## Scope

- `scripts/agent/workflow_engine_adapter.py`:
  - add `import asyncio` to the stdlib import block (`:13-18`);
  - add one module-level private pure helper `_status_for_exit` (new) above
    `class WorkflowEngineAdapter` (`:48`);
  - replace the `engine_status_handled` flag (`:142`, set at `:187`, read at `:192`) and the inline
    status choice (`:193-196`) with an explicit exit-reason classification held in one local
    variable;
  - add one `except asyncio.CancelledError` branch that records the reason and re-raises;
  - escalate the status-write failure log from `logger.warning` (`:198`) to `logger.error` carrying
    the task id and the intended status.
- No other function in the file changes. `_init_workflow_task` (`:252-296`), `_activate_workflow`
  (`:298`), `_handle_workflow_halt` (`:311-321`), `_process_turn` (`:323-356`) and
  `_handle_turn_end` (`:369-385`) are untouched. `mode_classification.classify_and_inject_mode`
  stays inside the same `try` region.
- No call-site change: `scripts/agent/orchestrator.py:167-172` is the only production caller, and the
  return tuple `answer, error_kind, is_partial` at `:204` is unchanged.

## Assumptions

- The engine's writes are authoritative for the transitions it can observe, because they happen at
  the moment of the transition and before re-raising (`scripts/agent/workflow/workflow_engine.py:121`
  `running`, `:127` `halted`, `:130` `failed`, `:132` `completed`; confirmed at HEAD `6fcbb7e0c`).
- `error_kind` non-`None` together with a normally-completing engine means a soft turn error the
  engine cannot observe (measured case C); it is the only case where the adapter is allowed to make
  the record worse than the engine reported.
- `asyncio.CancelledError` reaching `execute_turn` is always external (`repl_input_loop.py`
  `dispatch_task.cancel()` and the graceful-shutdown path); nothing under `scripts/` raises it as
  control flow. Confirmed by the engine's `except Exception` at `workflow_engine.py:129` not
  catching it.
- A turn whose engine never started keeps `pending`, the schema default
  (`scripts/agent/workflow/task_ops.py:52`; `scripts/db/schema_sql.py:172` `status TEXT NOT NULL
  DEFAULT 'pending'`, no `CHECK`), so `tasks.status` is a code convention, not a schema constraint.
- Status writes stay best-effort: a persistence failure must not abort a turn that already produced
  an answer, and must not be routed to `self._on_error` (`startup_component_init.py:81` wires
  `on_error` to the view's LLM-error renderer).

### Procedure-local findings

Re-measured at HEAD `6fcbb7e0c` on 2026-10-24. The Plan's adapter anchors (`:142`, `:145-185`,
`:186-188`, `:189-202`, `:192-196`, `:197-198`, import block `:11-19`) are accurate; the
corrections below are limits and counts, not code positions.

- Module-size gate: the Plan cites "16384 B" in `AC-10`, `UNK-05` and the Validation plan. The gate
  in force is `DEFAULT_LIMIT = 20480` (`tools/check_module_size.py:38`); 16384 appears only as a
  historical `check_docs_structure.py:32` value. Measured adapter size: 14798 B / 385 lines, so headroom
  is 5682 B, not 1586 B. No entry for this module exists in `tools/check_module_size_baseline.txt`
  (the file is empty).
- Gate command form: `uv run python tools/check_module_size.py scripts/` (Plan Validation plan) fails
  with `unrecognized arguments: scripts/` — the tool has no positional argument. Use
  `uv run python tools/check_module_size.py`, which currently prints
  `ALL OK - every scripts/ module is at most 20480 B.`
- Static-gate baselines measured today: `uv run radon cc -s scripts/agent/workflow_engine_adapter.py`
  reports `execute_turn - B (9)`, `_process_turn - B (10)`, `_init_workflow_task - B (8)`, class
  `A (3)`; `uv run mypy --no-namespace-packages scripts/` reports `Success: no issues found in 440
  source files` (Plan says 437 files).
- The Plan's measured exit table (cases A-H) was reproduced independently with a scratch harness
  driving the real `WorkflowEngine`, the real adapter and a real `StateStore` on a temporary
  `workflow.sqlite`. Result: A `running, completed, completed`; B `running, failed, completed`;
  C `running, completed, failed`; D `running, halted`; E `running, completed` with the in-flight
  `attempts` row left `running`; F `running, halted`; G `running, halted`; H no write and
  `pending`. `AC-1`'s `attempts` triple is `(stage_id, status, error_kind)` and reads
  `('verify', 'failed', 'exception')` (`workflow_engine.py:25-26`, `:241`).
- The scratch probe paths named in the Plan (`/tmp/opencode/turn003_probe5.py`, `probe6.py`,
  `probe7.py`) no longer exist; `tools/stale_detector.py` reports
  `source_missing: Source file does not exist: /tmp/opencode/turn003_probe5.py` for the Plan. They are
  scratch files by design and are not re-created here.
- Sequencing (Blocked until resolved): `implementations/20261024-083059_01_scripts_agent_workflow_engine_adapter.py.md`
  (turn002) already owns a rewrite of `execute_turn` and `_process_turn`, and
  `implementations/20261024-092307_02_scripts_agent_workflow_engine_adapter.py.md` (turn004) states
  that the `:189-202` status block is "turn003's shape" and must stay untouched by it. This procedure
  therefore lands **after** `083059_01` and its line anchors must be re-taken against the post-split
  file. `implementations/20261024-100151_*` (turn005) touches shutdown/`context.py`, not this file's
  status block.
- Plan `UNK-04` (docs index registration of `agent_03_03` / `agent_06_04`) is unresolved and is not
  blocking this row; it is carried by `_03`.

## Design decisions

- One local `exit_reason` (new) string in `execute_turn` replaces the boolean flag, so the exit reason is
  classified in a single place and the `finally` contains one decision call (`REQ-005`).
- The helper is a module-level `def` with a leading underscore, not a method: it reads no state, and
  `tools/generate_reference_table.py:226` skips `_`-prefixed names, so no generated reference row
  changes.
- The write stays in the `finally`, so every exit path is covered by one code path instead of four;
  the `CancelledError` branch only records the reason and re-raises.
- The status write remains synchronous inside the `finally`: awaiting during `CancelledError`
  unwinding is not reliable, and `StateStore.update_task_status` is sync
  (`scripts/agent/workflow/state_store.py:94`).
- Vocabulary: `halted` is reused for cancellation (Plan `DR-001`, user decision); no new status
  string is introduced anywhere under `scripts/` (`REQ-003`, `AC-3`).

## Alternatives considered

- Recompute the status from the exception type in the adapter and write it again: keeps the double
  write of case A and keeps two owners (Plan `DR-002`, rejected).
- Teach `WorkflowEngine.run` to handle `CancelledError`: puts the change in
  `scripts/agent/workflow/`, which the Plan's forbidden-edit-scope excludes and which the engine's
  own tests already pin (`tests/agent/workflow/test_workflow_engine.py:282`), and still cannot see
  soft turn errors (case C).
- Read `tasks.status` back in the `finally` and write only if it is still `running`: adds a read on
  every turn, races with the engine's own write, and does not remove the duplicate `completed` write.
- Add an `error_kind` for halts: explicitly out of scope (Plan `DR-003`).

## Implementation
### Target file

`scripts/agent/workflow_engine_adapter.py`

- 385 lines / 14798 B at HEAD `6fcbb7e0c`; size gate 20480 B (`tools/check_module_size.py:38`); no
  baseline entry.
- Regions in scope: import block `:13-18`, `execute_turn` `:131-204`, insertion point for the helper
  directly above `class WorkflowEngineAdapter` (`:48`).

### Procedure

- Phase 2 step 1 (Plan `Implementation steps` item 2): `import asyncio`, `_status_for_exit` (new),
  exit-reason classification, `CancelledError` branch.
- Phase 2 step 2: escalate the status-write failure log to `logger.error` with task id and intended
  status.
- Phase 2 step 3: static gates on the changed file (`radon`, module size, `lint-imports`, `ruff`,
  `mypy`, `vulture`, `bandit`).
- Prerequisite: implement
  `implementations/20261024-083059_01_scripts_agent_workflow_engine_adapter.py.md` first, then re-take
  every anchor in `Method` against the resulting file. Do not start this procedure while `_01` of that
  procedure set is unimplemented.
- Paired row: `implementations/20261024-144732_02_tests_agent_test_orchestrator.py.md` must land in the
  same commit, because removing the `completed` write breaks
  `tests/agent/test_orchestrator.py:2012-2052`.

### Method

1. Insert `import asyncio` as the first stdlib import, i.e. before `import logging` at `:13`
   (stdlib group first, alphabetical; compare `scripts/agent/repl_input_loop.py:10-12`).
2. Insert the helper above `class WorkflowEngineAdapter` (`:48`):

   ```python
   def _status_for_exit(exit_reason: str, error_kind: str | None) -> str | None:
       """Return the status the adapter must write, or None when the engine already wrote it.

       `exit_reason` (new) is one of "not-started" (the engine call was never reached),
       "engine-started" (engine.run raised), "halted", "cancelled" or "completed".
       None also covers the soft-error-free success case, where the engine's own
       `completed` write at `workflow_engine.py:132` is the only one.
       """
       if exit_reason == "cancelled":
           return "halted"
       if exit_reason == "completed" and error_kind is not None:
           return "failed"
       return None
   ```

3. In `execute_turn`, replace `engine_status_handled: bool = False` at `:142` with
   `exit_reason: str = "not-started"`. Keep the `task: TaskRecord | None = None` declaration at `:143`
   unchanged.
4. Inside the `try`, immediately after `engine = self._workflow_engine` (`:156`) and before
   `await engine.run(task, plan_fn, execute_fn, verify_fn)` (`:185`), set
   `exit_reason = "engine-started"`; after that `await`, set `exit_reason = "completed"`.
5. In `except (WorkflowHaltError, WorkflowTimeoutError) as exc:` (`:186-188`), replace
   `engine_status_handled = True` with `exit_reason = "halted"` and keep
   `self._handle_workflow_halt(exc)` unchanged.
6. Add, directly after that handler, `except asyncio.CancelledError:` with
   `exit_reason = "cancelled"` followed by `raise`. Do not call `_handle_workflow_halt` here and do
   not call `self._on_error`.
7. Replace the `finally` body at `:190-198` with the decision call, the guarded write and the
   error-level log (see `Details`). Keep `self._deactivate_workflow(self._ctx)` (`:199`) and the
   owned-store teardown (`:200-202`) exactly where they are, and keep `return answer, error_kind,
   is_partial` at `:204`.
8. Confirm no literal `"completed"` remains as an `update_task_status` argument in the file.

### Details

Target shape of the `finally` (replaces `:190-198`):

```python
        finally:
            intended_status = _status_for_exit(exit_reason, error_kind)
            if intended_status is not None and task is not None and task.task_id:
                try:
                    self._state_store.update_task_status(task.task_id, intended_status)
                except Exception as exc:  # noqa: BLE001 — updating task status on engine exit is best-effort; failure must not abort the turn
                    logger.error(
                        "Failed to update task status for task %s to %s: %s",
                        task.task_id,
                        intended_status,
                        exc,
                    )
            self._deactivate_workflow(self._ctx)
            if self._owns_state_store:
                self._state_store.close()
                self._owns_state_store = False
```

Decision table the helper must implement (Plan `Design` `:345-352`):

| `exit_reason` (new) | `error_kind` | Write | Case |
|---|---|---|---|
| `cancelled` | any | `halted` | E |
| `halted` | any | none | D, F, G |
| `engine-started` | any | none | B |
| `completed` | not `None` | `failed` | C |
| `completed` | `None` | none | A |
| `not-started` | `None` | none | H |

- `AC-2` check after the change: `grep -n 'update_task_status' scripts/agent/workflow_engine_adapter.py`
  must show one call site with `intended_status` (new), and `grep -n '"completed"'` must not appear as a
  status argument.
- Complexity budget: `execute_turn` is `B (9)` today. The inline `if/else` at `:193-196` is removed,
  the compound guard keeps the same shape, and radon counts the new `except` handler. If
  `uv run radon cc -s -n C scripts/agent/workflow_engine_adapter.py` reports a block, extract the
  guarded write and log into a private `_record_exit_status(...)` method rather than adding a
  baseline entry (`rules/toolchain.md`); do not widen `DEFAULT_LIMIT`.
- `# noqa: BLE001` stays on the same line as the `except Exception`, with the existing explanatory
  comment preserved.

## Compatibility considerations

- `execute_turn`'s public contract is unchanged (`REQ-007`, `AC-7`): signature `:131-137`, halt path
  returning `("", None, False)` via `:204`, plain exceptions and `CancelledError` propagating,
  `_handle_workflow_halt` (`:311-321`) untouched.
- Halts stay swallowed: `WorkflowHaltError` / `WorkflowTimeoutError` are not re-raised by the
  adapter, so `orchestrator.py:171` and the REPL containment are unaffected.
- Tests that must pass **unmodified** after this change:
  `tests/agent/test_orchestrator.py:1922-2010` (`TestHandleWorkflowEngineStatusPreservation`, halted
  and timeout cases — the adapter now writes nothing there, which is what those tests assert),
  `tests/agent/test_orchestrator.py:2054-2095` (`test_writes_failed_on_execute_failure`, soft-error
  downgrade preserved by `REQ-004`), `tests/agent/workflow/` (engine-side transitions),
  `tests/integration/test_orchestrator_integration.py:718-790` (`TestWorkflowResumeWithRealDB`).
- Test that breaks by design and must be migrated in the same commit by `_02`:
  `tests/agent/test_orchestrator.py:2012-2052` (`test_writes_completed_on_normal_success`, assertion
  at `:2052`).
- Audit and event flow unchanged: `audit_stage_completed`, `audit_workflow_start`, `_tool_override`
  (`:359-367`) and `_handle_turn_end` (`:369-385`) are not edited, so the `turn_end` event keeps its
  current shape and a halted turn still emits no event of its own — halt visibility today is the log
  line at `:198` plus the engine's `halted` write. Changing turn-end ownership is turn004's row
  (`implementations/20261024-092307_02_scripts_agent_workflow_engine_adapter.py.md`).
- No generated documentation row changes: the adapter's public docstrings are untouched and the new
  helper is private, so `tools/generate_reference_table.py --check` stays green for
  `docs/23_agent/agent_13_reference-api-generated.md`.
- No config, schema, service-port or `deploy.sh` / `init_db.sh` impact. Production
  `/opt/llm/db/workflow.sqlite` holds 0 rows in `tasks` and `attempts` (measured), so no deployed data
  depends on the old behavior.

## Security considerations

- No new input is parsed. The only value the adapter writes is one of the existing vocabulary strings
  (`pending`, `running`, `completed`, `failed`, `halted`); the helper cannot produce any other string.
- The escalated log line carries only the task UUID, the intended status and the exception text. It
  must not include turn text, tool arguments, or message content: `args_preview` content leakage is a
  separate issue (`issues/20261024-124138_tool005-args-preview-is-written-to-the-audit-log-unbounded.md`)
  and must not be widened here.
- `logger.error` on a persistence failure is the observability fix (`REQ-006`); it must not be routed
  to `self._on_error`, which renders user-visible LLM error output.

## Rollback considerations

- Revert with `git checkout HEAD~1 -- scripts/agent/workflow_engine_adapter.py` together with the
  matching test revert from `_02`; the two rows are one commit and revert together.
- The removed shape is preserved in `Details` (decision table plus the replaced `finally`) so the
  pre-change `failed`/`completed` choice can be restored verbatim.
- No data migration exists in either direction. Rows written as `halted` by a cancelled turn between
  deploy and rollback keep `halted`; `_init_workflow_task` (`:284-290`) rejects resuming a `halted`
  task, which is the behavior the Plan accepts under `DR-001` and `UNK-01`.

## Validation plan

- `uv run pytest tests/agent/test_orchestrator.py tests/agent/workflow/ tests/integration/test_orchestrator_integration.py -q`
  — baseline measured 2026-10-24 at HEAD `6fcbb7e0c`: 217 passed. After this row: 217 plus the new
  class from `_02`, and no failure naming the adapter.
- `uv run pytest tests/agent/test_orchestrator.py -k "TaskStatusPerTurnOutcome or HandleWorkflowEngineStatusPreservation or writes_failed_on_execute_failure" -q`
  — targeted first run.
- `uv run radon cc -s -n C scripts/agent/workflow_engine_adapter.py` — no block reported (`AC-10`).
- `uv run python tools/check_module_size.py` — `ALL OK`; the adapter stays under 20480 B (14798 B at
  HEAD).
- `PYTHONPATH=scripts uv run lint-imports` — `Contracts: 6 kept, 0 broken.` (config lives in
  `.importlinter`, not `pyproject.toml`).
- `uv run ruff check scripts/`, `uv run ruff format --check scripts/`,
  `uv run mypy --no-namespace-packages scripts/` (440 files today),
  `uv run vulture scripts/agent/workflow_engine_adapter.py --min-confidence 80`,
  `uv run bandit -c pyproject.toml -ll scripts/agent/workflow_engine_adapter.py`.
- Mutation control (Plan `Tests` `:262-264`): re-add
  `self._state_store.update_task_status(task.task_id, "completed")` to the `finally` and confirm the
  case-A and case-B tests from `_02` fail; revert. Delete the `except asyncio.CancelledError` branch
  and confirm the case-E test fails; revert.
- Read-only production confirmation:
  `sqlite3 /opt/llm/db/workflow.sqlite "SELECT status, COUNT(*) FROM tasks GROUP BY status;"` —
  unchanged (0 rows at HEAD).

## Completion criteria

- The file contains no `update_task_status(..., "completed")` call (`REQ-002`, `AC-2`).
- Cases A-H from the Plan's `Problem` table hold with a real engine and a real store, as pinned by
  `implementations/20261024-144732_02_tests_agent_test_orchestrator.py.md` (`AC-1`-`AC-5`, `AC-8`).
- A cancelled turn ends `halted` and `CancelledError` still escapes `execute_turn` (`AC-3`).
- A status-write failure logs at `ERROR` with the task id and the intended status, does not call
  `self._on_error`, and does not raise (`AC-6`).
- `radon` reports no C-or-worse block in the file, `check_module_size.py` is OK, and
  `lint-imports` reports 6 kept / 0 broken (`AC-10`).
- No file under `scripts/agent/workflow/`, `scripts/db/`, `scripts/agent/orchestrator.py`,
  `scripts/agent/repl_input_loop.py` or `config/` is modified (`REQ-008`).

## Out of Scope

- Closing the in-flight `attempts` row a cancelled turn leaves `running` (Plan Out-of-Scope, `DR-006`,
  `UNK-02`); `StateStore.recover_stale_attempts()` (`state_store.py:279-316`, `_STALE_GRACE_SEC = 30`
  at `:22`) repairs `attempts` rows only, never a `tasks` row.
- Any change to `WorkflowEngine`, `StateStore`, `task_ops.py`, `scripts/db/schema_sql.py`,
  `config/workflows/default.json`, or the status vocabulary (`REQ-008`).
- A `cancelled` status string, a schema `CHECK` on `tasks.status`, and resumability of a
  cancellation-halted task (`UNK-01`; follow-up after `turn005`).
- Adding an `error_kind` for halts (`DR-003`).
- Splitting `_process_turn` and moving entry work out of the execute stage — owned by
  `implementations/20261024-083059_01_scripts_agent_workflow_engine_adapter.py.md`.
- Removing the adapter's turn-end ownership and teardown — owned by
  `implementations/20261024-092307_02_scripts_agent_workflow_engine_adapter.py.md`.
- Registering `agent_03_03` / `agent_06_04` in `docs/00_index.md` (`UNK-04`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Blocked until `083059_01` (turn002) lands; re-take anchors afterwards |
| 2 | Add or update tests per Validation plan | Pending | — | — | Owned by `_02`; must land in the same commit |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | Baselines measured 2026-10-24: 217 passed, 440 mypy files, 6 contracts kept |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A: docs rows are `_03` and `_04` | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | `implementations/20261024-083059_01_*` (turn002) rewrites `execute_turn` / `_process_turn` first; `092307_02` (turn004) declares `:189-202` this row's shape and must stay out of it | False | — |
| 1 | Plan `UNK-04` (docs index registration) has no owner decision | False | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| `implementations/20261024-144732_02_tests_agent_test_orchestrator.py.md` | 2 | implementation procedure | Open | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-001`, `REQ-002`, `REQ-003`, `REQ-004`, `REQ-005`, `REQ-006`, `REQ-007`, `REQ-008`
- **Source issue**: `issues/20261021-093421_turn003_task-status-overwritten-after-failure.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261023-125756_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261024-144732
- **Related target files**: `scripts/agent/workflow_engine_adapter.py`
