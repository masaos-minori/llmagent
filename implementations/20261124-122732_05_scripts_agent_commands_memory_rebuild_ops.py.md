## Goal

Make the Memory rebuild and reindex handlers run as tracked jobs: approval comes from the registry rather than from a flag, the success line is emitted only after the consistency check, and the repair guidance names commands that are actually registered (REQ-003: approval as an operation property; REQ-004: success only after the postcondition; REQ-006: long-running Memory work as tracked jobs; REQ-009: guidance names registered commands).

## Scope
**Release unit**: R3-memory-approval (Phase 3); the postcondition part is R4-verified-results (Phase 4)

- In scope: `MemoryRebuildOps.rebuild`, `reindex`, `check_consistency`, and the guidance strings.
- Out of scope: the registry itself, the `MemoryStore` accessors (row 12), the documentation rows.

## Assumptions

- `--confirm` and `--allow-loss` stay accepted as recorded grants; they stop being the authority that permits the run (plan decision, 2026-11-24). The registry records the grant on the job.
- The handler reaches the registry through `AgentContext`, so no second job reference is held in this mixin.
- The repair guidance must name registered forms only: `/memory reindex --fts` and `/memory reindex --vec`.

## Design decisions

- Handlers become `async` so the run is tracked off the event loop and can be cancelled through the job; a synchronous handler cannot report an interrupted outcome.
- The consistency result is folded into the job outcome before any success line, so a run that did not verify cannot report success (REQ-004).
- Approval level is taken from the operation record registered for the rebuild, not parsed from `args`.

## Alternatives considered

- Keeping flag parsing and adding a separate verification step — rejected: the flag and the level can then disagree, which is the state REQ-003 removes.

## Implementation
### Target file
`scripts/agent/commands/memory_rebuild_ops.py`

### Procedure
1. Convert `rebuild()` (`memory_rebuild_ops.py:46`) and `reindex()` (`:151`) to `async def` and run the work as a registered job.
2. Replace the flag-only decision at `:54-55` with the registry approval level for the operation; keep reading `--confirm` and `--allow-loss` as recorded grants on the job.
3. Move `check_consistency(mem)` (`:140-141`) ahead of the success emission (`:126`) and carry its result into `RebuildResult.verified`.
4. Change the guidance strings at `:236,239` to the registered `/memory reindex --fts` / `/memory reindex --vec` forms.

### Method
- `RebuildResult` (existing dataclass at `:25`) gains `job_id` and `verified`; the handler does not print success when `verified` is false — it prints the outcome state from the job record.

### Details
- `_count_sqlite_only` (`:173`) and `_backup_memories_as_jsonl` (`:184`) keep their behavior; they are read and backup paths, not job-registered writes.
- The `ValueError` raised at `import_ops.py:81-83` for `backup` without `allow_loss` is still surfaced through this handler; the message must name the job id when the run was registered.

### Companion test files
- None. tests/agent/commands/test_cmd_memory.py is named by several rows and keeps its own document (row 43).

## Compatibility considerations

- `tests/agent/commands/test_cmd_memory.py` and `tests/agent/commands/test_memory_rebuild_guard.py` currently pin the flag-based guard and the pre-check success line; both change in the same phases (rows 43, 56).
- `RebuildResult` is consumed by the audit path in `cmd_memory.py`; adding fields is additive, no removal.

## Security considerations

- The rebuild is a write against `session.sqlite`; approval enforcement moves from a user flag to the registry, so an unattended run cannot authorize itself.

## Rollback considerations

- Revert the Phase 3 commit for the async and approval change and the Phase 4 commit for the postcondition separately.

## Validation plan

| Target | Strategy | Command | Expected outcome |
|---|---|---|---|
| `scripts/agent/commands/memory_rebuild_ops.py` | Unit | `uv run pytest tests/agent/commands/test_cmd_memory.py tests/agent/commands/test_memory_rebuild_guard.py -q` | Registry approval, async handlers, guidance names registered commands, postcondition before success |
| Same file | Quality gates | `uv run ruff check scripts/agent/commands/memory_rebuild_ops.py`, `uv run mypy scripts/agent/commands/memory_rebuild_ops.py` | No finding |
| Same file | Complexity baseline | `uv run radon cc scripts/agent/commands/memory_rebuild_ops.py -s` | `rebuild` stays at baseline B(6) |

## Completion criteria

- A rebuild run is recorded as a job, its approval comes from the registry, the emitted outcome reports the job id and terminal state, and the repair guidance names only registered commands.

## Out of Scope

- The `MemoryStore` accessors the handler will call (row 12), the transaction boundaries in `rebuild_ops.py` (row 55), the documentation rows.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Make the handlers async and route approval through the registry | Pending | — | — | Phase 3 |
| 2 | Move the consistency check ahead of the success line and fold it into the result | Pending | — | — | Phase 4 |
| 3 | Correct the repair guidance to registered command forms | Pending | — | — | Phase 3 |
| 4 | Update tests per Validation plan | Pending | — | — | Row 43 is its own document; `tests/agent/commands/test_memory_rebuild_guard.py` (row 56) is covered by row 55's document |
| 5 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: REQ-003 (approval level as an operation property), REQ-004 (verified result before the success line), REQ-006 (long-running Memory work as tracked jobs), REQ-009 (repair guidance names registered commands)
- **Source issue**: issues/20261119-145301_cliplc003_maintenance-job-framework.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-001800_cliplc003_maintenance-job-framework.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261124-122732
- **Related target files**: `scripts/agent/commands/memory_rebuild_ops.py`
