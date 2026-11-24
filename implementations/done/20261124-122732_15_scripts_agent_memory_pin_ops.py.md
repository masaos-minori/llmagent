## Goal

Enforce `memory_max_pinned` inside the pin transaction so a concurrent job cannot push the count past the configured limit (REQ-008: limits and destructive maintenance are atomic).

## Scope
**Release unit**: R5-memory-layering (Phase 5)

- In scope: `_set_pinned` and `pin`.
- Out of scope: the read primitive in `count_ops.py`, the command handler in `memory_data_ops.py` (row 6).

## Assumptions

- The limit value comes from configuration (`config/agent.toml:93` `memory_max_pinned = 10`); this row does not change configuration parsing.
- The append-only change event is emitted after the transaction commits, consistent with `write_ops.py` (row 14).

## Design decisions

- The count check and the write happen in the same transaction on the same connection, so the limit is evaluated against the state the transaction will commit, not against a value read earlier on a second connection.

## Alternatives considered

- An application-level lock around the read-then-write pair — rejected: it protects only processes in this process, while the transaction is the boundary the plan's single-writer contract already defines.

## Implementation
### Target file
`scripts/agent/memory/pin_ops.py`

### Procedure
1. Move the pinned-count check into the same transaction as `_set_pinned` (`pin_ops.py:12`), inside `pin()` (`:39`).
2. Return the result shape the `MemoryStore` accessor defines (row 12), including the case where the limit was exceeded inside the transaction.
3. Keep `unpin()` (`:54`) unchanged apart from the result shape.

### Method
- The check is a single statement against the current pinned count inside the transaction; no read is performed on a separate connection.

### Details
- `_emit_event` (`pin_ops.py:69`) is called only after the transaction commits.

## Compatibility considerations

- The current read in `memory_data_ops.py:316-327` is removed by row 6 in the same phase; the behavior is asserted in `tests/agent/commands/test_memory_data_ops.py` (row 45).

## Security considerations

- N/A: no trust boundary changes.

## Rollback considerations

- N/A: revert the Phase 5 commit.

## Validation plan

| Target | Strategy | Command | Expected outcome |
|---|---|---|---|
| `scripts/agent/memory/pin_ops.py` | Unit | `uv run pytest tests/agent/commands/test_memory_data_ops.py -q` | Atomic pin limit under a concurrent job |
| Same file | Quality gates | `uv run ruff check scripts/agent/memory/pin_ops.py`, `uv run mypy scripts/agent/memory/pin_ops.py` | No finding |
| Same file | Complexity baseline | `uv run radon cc scripts/agent/memory/pin_ops.py -s` | `memory_pin` callers stay at baseline B(10) |

## Completion criteria

- A pin that would exceed `memory_max_pinned` is refused by the transaction itself, and the reported count equals the committed count.

## Out of Scope

- The command handler, the store accessors, the configuration value.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Enforce the pinned limit inside the pin transaction | Completed | — | 20261124-234217 | Phase 5. Deviation: the limit check now runs on any connection the store hands it, so the event is emitted after the commit on the injected-connection path too; the command pre-check and `MemoryDataOps._count_pinned` are gone and `max_pinned` is passed by the caller. |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261124-234217 | Tests are row 45 |

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
- **Requirement ID**: REQ-008 (atomic limits and destructive maintenance)
- **Source issue**: issues/20261119-145301_cliplc003_maintenance-job-framework.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-001800_cliplc003_maintenance-job-framework.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261124-122732
- **Related target files**: `scripts/agent/memory/pin_ops.py`
