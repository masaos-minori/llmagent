## Goal

Run the `/session` maintenance subcommands through the job registry so each run produces a job record and the emitted message names the job id and its terminal state (REQ-001: one record per run; REQ-004: success only after the postcondition; REQ-007: the renamed vector operation).

## Scope
**Release unit**: R1-registry-core (Phase 1); the rename part of this row is R6-rag-vector-contract (Phase 6)

- In scope: the `db_dispatch` table, the vector subcommand name, the message format.
- Out of scope: the operation implementations (`db_session_ops.py`, `rag_maintenance_service.py`), the `/jobs` command registration.

## Assumptions

- The registry is reached through `self._ctx.services`, so no new field is introduced in this file.
- `test_agent_cmd_session.py` (row 42) pins the current message text and dispatch shape, so the message change lands with this row.
- `scripts/agent/repl.py` (row 11) is shared with cliplc004; that Plan judges the overlap sequenced and cliplc003 lands first, so the offload shape here is not changed.

## Design decisions

- The dispatch table keeps `asyncio.to_thread` offloading; the registry does not change where the work runs, it records it. Keeping the offload is what preserves the loop-responsiveness contract the plan does not touch.
- The handler obtains the cancellation event from the job rather than creating its own, so `/jobs cancel <id>` is the only way a run stops.

## Alternatives considered

- Cancelling by cancelling the awaited task — rejected: the work runs in a thread, so the task handle does not stop the SQLite writer; the cancellation must reach it through `SQLiteHelper.interrupt_when`.
- Keeping the fixed success strings and appending the job id — rejected: the message would report success before the postcondition, which is what REQ-004 requires the result object to settle first.

## Implementation
### Target file
`scripts/agent/commands/cmd_session.py`

### Procedure
1. In the `db_dispatch` table (`cmd_session.py:224-243`), wrap each maintenance entry so the call registers a job, passes the job's cancellation event to the operation, and emits the message from the returned result object rather than from a fixed string.
2. Rename the vector entry key from `rag-rebuild-vec` to `rag-prune-vec` and rename the handler `_rag_rebuild_vec` (`cmd_session.py:161`) to match the operation it performs.
3. Read the existing job id in the emitted line as `job {job_id} {terminal state}`; the operation counts stay as the result object provides them.

### Method
- No change to `db_dispatch` as a table of callables: each entry becomes `register → run → report`, in that order, so a refused duplicate run reports the running job id instead of starting.

### Details
- `cmd_session.py:156-158` builds a `RagMaintenanceService` per call; the instance must come from the injected services so the same registry instance carries the job (Plan Design, Memory layering decision).
- `export`, `stats`, and `health` are not write jobs: they stay as they are or register with `ApprovalLevel.NONE`; the plan's record requires every maintenance run, so `stats` and `health` are read-only registrations with level `none`.

## Compatibility considerations

- `/session rag-rebuild-vec` is removed as a subcommand name; the retired name stays unregistered and is not reintroduced as an alias (`tests/agent/commands/test_removed_commands.py`, row 50).
- Eight documents and the doc-quality rule name the old command; they change in the same release unit (R6), so a half-applied rename fails `tools/check_docs_quality.py`. `tools/check_chunks_fts_invariant.py` is not affected: it whitelists the service file by path (`:36-41`) and names no command.

## Security considerations

- The vector prune is a write against `rag.sqlite`; the run must be recorded so the one-writer guard sees it.

## Rollback considerations

- Revert the Phase 1 commit for the dispatch wiring and the Phase 6 commit for the rename separately; the two are distinct commits in the plan.

## Validation plan

| Target | Strategy | Command | Expected outcome |
|---|---|---|---|
| `scripts/agent/commands/cmd_session.py` | Unit | `uv run pytest tests/agent/commands/test_agent_cmd_session.py -q` | Job-recorded calls, verified and interrupted outcomes, renamed subcommand |
| Same file | Command contract | `uv run python tools/check_docs_consistency.py` | No command-name drift |
| Same file | Quality gates | `uv run ruff check scripts/agent/commands/cmd_session.py`, `uv run mypy scripts/agent/commands/cmd_session.py` | No finding |

## Completion criteria

- Every `/session` maintenance subcommand run creates a job record and the emitted message names the job id and terminal state; the vector subcommand is `rag-prune-vec`; an interrupted run reports `cancelled` and not success.

## Out of Scope

- The postcondition logic itself (`db_session_ops.py`, row 4), the `/jobs` handler (rows 9, 10), and the documentation rows.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Wire `db_dispatch` through the registry and emit the job id and terminal state | Completed | — | 20261124-160831 | Phase 1 Phase 1 part done: each maintenance entry in db_dispatch routes through _run_maintenance_job (register, approve, start, run off-loop, finish, report). export is not a job and is unchanged; stats and health register with ApprovalLevel.NONE. |
| 2 | Update `tests/agent/commands/test_agent_cmd_session.py` for the message and dispatch shape | Completed | — | 20261124-160831 | Row 42 is its own document (named by two rows) Phase 1 part done through row 42. |
| 3 | Rename the vector subcommand and handler | Completed | 20261125-002740 | 20261125-002740 | Phase 6, same unit as the docs rows Phase 6 (R6) done: the dispatch key is rag-prune-vec with operation prune on StoreTarget.RAG, the handler is _rag_prune_vec(stop), and both RAG write handlers return the result object so the emitted message is the job record. |
| 4 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261125-002740 | 20261125-002740 | Phase 1 part: ruff, mypy pass; check_docs_consistency has no name drift while the rename is deferred to Phase 6 (row 3 step 3). Phase 6 part: ruff, ruff format, mypy pass; check_docs_consistency --domain agent reports only the pre-existing agent_14 /db warning; the targeted command tests pass. |

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
- **Requirement ID**: REQ-001 (job record per run), REQ-004 (verified result before success), REQ-007 (name matching behavior)
- **Source issue**: issues/20261119-145301_cliplc003_maintenance-job-framework.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-001800_cliplc003_maintenance-job-framework.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261124-122732
- **Related target files**: `scripts/agent/commands/cmd_session.py`