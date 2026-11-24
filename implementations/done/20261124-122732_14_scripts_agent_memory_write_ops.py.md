## Goal

Make a Memory delete keep the SQLite row removal and the jsonl change event consistent when the run is interrupted, so an interrupted delete does not leave an archive event for a row that is gone (REQ-006: long-running Memory work as tracked jobs with a cancellation boundary; REQ-008: atomicity of destructive maintenance).

## Scope
**Release unit**: R5-memory-layering (Phase 5)

- In scope: `delete()` and `_emit_delete_event()`.
- Out of scope: the job record and the registry, the command handler that calls this path.

## Assumptions

- The jsonl change events stay append-only (`docs/23_agent/agent_11_04_memory-module-reference-generated.md:71`); this row does not make the archive writable, only orders the two steps so they agree.
- `SQLiteMemoryDeleteStore` (`scripts/db/store_impl.py:170`) keeps its signature; only the caller changes.

## Design decisions

- The SQLite delete is committed inside one transaction and the append-only event is emitted only after that commit; an interrupt before the commit emits nothing, so the event set matches the row set.
- The event is not written inside the same transaction as the row, because the archive is a file and cannot join a SQLite transaction; the ordering rule is the closest enforceable contract.

## Alternatives considered

- Writing the event first and the row second — rejected: the current order is what the append-only contract tests assert (`tests/agent/memory/test_jsonl_store.py`, row 58), and reversing it would make an interrupted delete report a change that never happened.

## Implementation
### Target file
`scripts/agent/memory/write_ops.py`

### Procedure
1. Take `stop: threading.Event | None` in `delete()` (`write_ops.py:114`) and pass it to `db.interrupt_when`.
2. Keep the row removal and its FTS/vec row handling inside one transaction boundary before `_emit_delete_event` (`:140`) is called.
3. Return the result object the store accessor defines (row 12), with the interrupted flag.

### Method
- `_write_fts` (`:39`) and `_write_vec` (`:47`) are not changed; they are already inside the same connection scope.

### Details
- On interruption the result reports that the row was not removed and no event was emitted; the caller reports `cancelled`, not success.

## Compatibility considerations

- The delete path is exercised by `tests/agent/commands/test_memory_data_ops.py` (row 45) and the append-only contract by `tests/agent/memory/test_jsonl_store.py` (row 58); both run in this phase.

## Security considerations

- Delete is a destructive write; the registry decides approval before this module is reached, so no approval logic belongs here.

## Rollback considerations

- N/A: revert the Phase 5 commit.

## Validation plan

| Target | Strategy | Command | Expected outcome |
|---|---|---|---|
| `scripts/agent/memory/write_ops.py` | Unit | `uv run pytest tests/agent/commands/test_memory_data_ops.py tests/agent/memory/test_jsonl_store.py -q` | Delete and event stay consistent under interruption |
| Same file | Quality gates | `uv run ruff check scripts/agent/memory/write_ops.py`, `uv run mypy scripts/agent/memory/write_ops.py` | No finding |

## Completion criteria

- A delete either removes the row and emits the event, or is cancelled before either side changes; no state where one happened without the other.

## Out of Scope

- The registry, the command handler, the pin limit (row 15).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the cancellation event and one transaction boundary for the delete | Completed | — | 20261124-234217 | Phase 5 |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261124-234217 | Tests are rows 44 and 45. Correction: the earlier note named row 62, which is `tests/db/test_rag_consistency.py` and covers the Phase 6 repair guidance, not this file. |

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
- **Requirement ID**: REQ-006 (tracked Memory work with a cancellation boundary), REQ-008 (atomicity of destructive maintenance)
- **Source issue**: issues/20261119-145301_cliplc003_maintenance-job-framework.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-001800_cliplc003_maintenance-job-framework.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261124-122732
- **Related target files**: `scripts/agent/memory/write_ops.py`
