## Goal

Move the Memory data operations off direct `SQLiteHelper` use, run the prune select-and-delete in one transaction, and take approval from the registry instead of from flags (REQ-003: approval as an operation property; REQ-005: command mixins reach SQLite only through `MemoryStore`; REQ-008: destructive maintenance is atomic).

## Scope
**Release unit**: R5-memory-layering (Phase 5); the approval part is R3-memory-approval (Phase 3)

- In scope: `MemoryDataOps`, `_confirm()`, the prune path, the pin path, `_emit_prune_event`.
- Out of scope: the `MemoryStore` accessors themselves (row 12), the pin transaction in `pin_ops.py` (row 15).

## Assumptions

- The new `MemoryStore` accessors exist by the time this row runs; this document does not define them.
- `_confirm()` (`memory_data_ops.py:54-66`) stays the request-bound confirmation API; the registry calls it for `confirm` and `guard` levels, so the one-turn approval rule is unchanged.
- `count_ops.count_prunable` remains the read primitive used to re-validate candidates.

## Design decisions

- Prune selects and deletes in one transaction so a concurrent job cannot change the candidate set between the count and the delete (REQ-008); the count reported is the count actually deleted.
- Approval is resolved by the registry before the operation runs; the flags remain recorded grants, not permissions (plan decision, 2026-11-24).

## Alternatives considered

- Keeping direct `SQLiteHelper` access and adding a store facade later — rejected: the AC-5 grep gate over `scripts/agent/commands/` cannot pass while one command mixin still opens a connection.

## Implementation
### Target file
`scripts/agent/commands/memory_data_ops.py`

### Procedure
1. Replace the direct `SQLiteHelper` construction at `memory_data_ops.py:205-207`, `:386-395`, and `:425-428` with calls through `MemoryServices` → `MemoryStore`.
2. Run the prune candidate selection and the delete in the same transaction; report the deleted count from the transaction, not from a separate count call.
3. Resolve approval through the registry for the destructive runs and keep `_confirm()` as the request-bound path the registry uses.

### Method
- `_parse_prune_days` (`:151`) and `_parse_list_options` (`:83`) keep their parsing behavior; only the execution path changes.
- `_emit_prune_event` (`:38`) stays append-only; the event is emitted after the transaction commits.

### Details
- `memory_pin` (`:299`) keeps its read-then-write shape here only until the atomic enforcement lands in `pin_ops.py` (row 15); after that the handler calls the store accessor.

### Companion test files
- None. tests/agent/commands/test_memory_data_ops.py is named by several rows and keeps its own document (row 45).

## Compatibility considerations

- Existing tests pin the current count-then-delete reporting; the change lands with row 45 in the same phase.

## Security considerations

- Prune and delete are destructive writes; enforcement now comes from the registered operation's approval level, so a flag alone no longer authorizes the run.

## Rollback considerations

- Revert the Phase 5 commit; the approval change is a separate Phase 3 commit.

## Validation plan

| Target | Strategy | Command | Expected outcome |
|---|---|---|---|
| `scripts/agent/commands/memory_data_ops.py` | Unit | `uv run pytest tests/agent/commands/test_memory_data_ops.py tests/agent/commands/test_cmd_memory.py -q` | Single-transaction prune with re-validated candidates, service-layer routing, registry approval |
| Same file | Static grep gate (AC-5) | `rg -n "SQLiteHelper" scripts/agent/commands/` | No Memory maintenance construction remains |
| Same file | Quality gates | `uv run ruff check scripts/agent/commands/memory_data_ops.py`, `uv run mypy scripts/agent/commands/memory_data_ops.py` | No finding |
| Same file | Complexity baseline | `uv run radon cc scripts/agent/commands/memory_data_ops.py -s` | `memory_prune` stays at baseline B(8) |

## Completion criteria

- The file contains no direct `SQLiteHelper` construction, prune deletes exactly the candidates it selected inside one transaction, and a destructive run without registry approval is refused before any write.

## Out of Scope

- The `MemoryStore` accessors (row 12), the pin transaction (row 15), the delete/jsonl consistency in `write_ops.py` (row 14).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Route SQLite access through `MemoryStore` | Completed | — | 20261124-234217 | Phase 5 |
| 2 | Single-transaction prune select-and-delete | Completed | — | 20261124-234217 | Phase 5 |
| 3 | Resolve approval through the registry | Completed | — | 20261124-234217 | Phase 3. Deviation: `_confirm()` keeps its current `operation_id` values (memory id for delete, `prune:{days}d` for prune) because row 45 locks the request bound to the memory id; the grant is recorded on the job record and the decision is bound to the run through `registry.authorize`/`record_grant`. |
| 4 | Update tests per Validation plan | Completed | — | 20261124-234217 | Row 45 |
| 5 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261124-234217 | Includes the AC-5 grep gate |

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
- **Requirement ID**: REQ-003 (approval levels), REQ-005 (Memory service-layer boundary), REQ-008 (atomic destructive maintenance)
- **Source issue**: issues/20261119-145301_cliplc003_maintenance-job-framework.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-001800_cliplc003_maintenance-job-framework.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261124-122732
- **Related target files**: `scripts/agent/commands/memory_data_ops.py`