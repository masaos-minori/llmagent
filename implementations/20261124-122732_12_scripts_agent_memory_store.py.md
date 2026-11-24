## Goal

Give `MemoryStore` the maintenance accessors the command mixins currently bypass it for, with cancellation and transaction boundaries, so the Memory write path has one SQLite owner (REQ-005: command mixins reach SQLite only through `MemoryStore`; REQ-002: cooperative interruption; REQ-008: atomic limits and destructive maintenance).

## Scope
**Release unit**: R5-memory-layering (Phase 5); the cancellation parameter is R1-registry-core (Phase 1)

- In scope: the new accessors on `MemoryStore` and their transaction boundaries.
- Out of scope: the command-mixin call sites (rows 6, 7, 8), the index rebuild internals in `rebuild_ops.py` (row 55).

## Assumptions

- `MemoryStore` is the injected instance reached through `MemoryServices`, so the one-writer-per-store guard in the registry sees every write that goes through these accessors.
- `count_ops.py` remains the read primitive; the new accessors do not duplicate its counts.

## Design decisions

- The accessors take an optional `threading.Event` and pass it to `SQLiteHelper.interrupt_when` (`scripts/db/helper.py:158-162`), so cancellation is expressed through the existing progress-handler mechanism rather than a new interrupt path.
- Each write accessor runs inside one transaction boundary owned by the store, because the plan's atomicity requirement (REQ-008) is about the whole select-and-delete, not a single statement.

## Alternatives considered

- Letting the command mixins keep direct connections and adding a thin wrapper later — rejected: the AC-5 grep gate cannot pass with any direct construction left in `scripts/agent/commands/`.

## Implementation
### Target file
`scripts/agent/memory/store.py`

### Procedure
1. Add the maintenance accessors on `MemoryStore` (class at `store.py:33`): `rebuild` (existing indexes), `reindex` (fts or vec), `prune`, and `pinned_count` (new), matching the names the command mixins need.
2. Each accessor takes `stop: threading.Event | None` and calls `db.interrupt_when(stop)` inside the `SQLiteHelper` context.
3. Wrap the prune select-and-delete in one transaction and return the number of rows actually deleted.

### Method
- Accessors return result objects with the measured postcondition (`verified: bool`), not dicts, so the caller cannot report success without the check (REQ-004).
- Read-only accessors (`count_vec` at `:106`, `check_consistency` at `:112`) keep their behavior and are reused by the status path.

### Details
- The existing public methods (`search_by_type` `:58`, `list_entries` `:78`, `get_by_id` `:124`) are unchanged; the new accessors sit alongside them.

### Companion test files
- None. tests/agent/memory/test_memory_layer.py (row 54) is covered by row 13's document; this row's own test file keeps its own document (row 44), so no companion is listed here.

## Compatibility considerations

- 23 tests reference this module through the Memory test paths; the accessor additions are additive, so existing call sites keep working.

## Security considerations

- The store is where the single-writer contract for `session.sqlite` is enforced in-process (`docs/10_adr/adr_02_05_008_db-six-sqlite-store-separation.md`); moving writes here is what makes the guard effective.

## Rollback considerations

- Remove the new accessors; no persisted state or config key depends on them.

## Validation plan

| Target | Strategy | Command | Expected outcome |
|---|---|---|---|
| `scripts/agent/memory/store.py` | Unit | `uv run pytest tests/agent/memory/test_memory_store.py -q` | Accessors exist, transaction boundaries honored, cancellation honored |
| Same file | Layering | `PYTHONPATH=scripts uv run lint-imports` | 6 contracts kept, 0 broken |
| Same file | Quality gates | `uv run ruff check scripts/agent/memory/store.py`, `uv run mypy scripts/agent/memory/store.py`, `uv run bandit -c pyproject.toml scripts/agent/memory/store.py` | No finding |

## Completion criteria

- Every Memory maintenance write reachable from a command mixin goes through a `MemoryStore` accessor, and an interrupted run leaves no partial index or partial delete.

## Out of Scope

- The command-mixin routing (rows 6, 7, 8), the index rebuild transaction internals (row 55), the pin limit enforcement (row 15).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the maintenance accessors with the cancellation event | Pending | — | — | Phase 1 for the parameter, Phase 5 for the accessors |
| 2 | Single-transaction boundary for prune and rebuild accessors | Pending | — | — | Phase 5; UNK-02 must be resolved here |
| 3 | Update tests per Validation plan | Pending | — | — | Row 44 |
| 4 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: REQ-002 (cancellation through the progress handler), REQ-005 (Memory service-layer boundary), REQ-008 (atomic limits and destructive maintenance)
- **Source issue**: issues/20261119-145301_cliplc003_maintenance-job-framework.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-001800_cliplc003_maintenance-job-framework.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261124-122732
- **Related target files**: `scripts/agent/memory/store.py`
