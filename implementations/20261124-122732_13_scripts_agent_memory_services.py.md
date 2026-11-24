## Goal

Expose the new Memory maintenance accessors on the injected `MemoryServices` facade so the command mixins can reach them without opening a connection (REQ-005: the Memory service layer is the only path to SQLite from a command mixin).

## Scope
**Release unit**: R5-memory-layering (Phase 5)

- In scope: the facade surface that carries the new accessors.
- Out of scope: the accessors themselves (row 12), the command-mixin call sites (rows 6, 7, 8).

## Assumptions

- `MemoryServices` (`scripts/agent/memory/services.py:20`) stays a facade over the store and its op modules; it does not gain behavior, only reachability.

## Design decisions

- The facade forwards to `MemoryStore` rather than implementing the operations, so the store remains the single owner of the transaction boundary (REQ-008).

## Alternatives considered

- N/A: any other shape would put transaction ownership outside the store and break the AC-5 grep gate.

## Implementation
### Target file
`scripts/agent/memory/services.py`

### Procedure
1. Make the new `MemoryStore` accessors reachable through `MemoryServices`.
2. Keep the existing fields and docstring contract unchanged.

### Method
- No new logic in the facade; each reachable name is the store accessor of the same name.

### Details
- `get_stats` (`services.py:59`) keeps its behavior; the status path reads through it or through the store accessors.

### Companion test files
- `tests/agent/memory/test_memory_layer.py`
  - Procedure: assert the new accessors are reachable through the facade and delegate to `MemoryStore`.
  - Validation: `uv run pytest tests/agent/memory/test_memory_layer.py -q` (REQ-005; AC-5).

## Compatibility considerations

- Additive surface; no existing facade method changes signature.

## Security considerations

- N/A: the trust boundary is unchanged by a forwarding layer.

## Rollback considerations

- N/A: revert the Phase 5 commit.

## Validation plan

| Target | Strategy | Command | Expected outcome |
|---|---|---|---|
| `scripts/agent/memory/services.py` | Unit | `uv run pytest tests/agent/memory/test_memory_layer.py -q` | Accessors reachable through the facade |
| Same file | Layering | `PYTHONPATH=scripts uv run lint-imports` | 6 contracts kept, 0 broken |

## Completion criteria

- A command mixin can perform every Memory maintenance operation through `MemoryServices` alone.

## Out of Scope

- The store accessors, the command mixins, the documentation.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Expose the new accessors on the facade | Pending | — | — | Phase 5 |
| 2 | Update the companion test per Validation plan | Pending | — | — | Covered by this document |
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
- **Requirement ID**: REQ-005 (Memory service-layer boundary)
- **Source issue**: issues/20261119-145301_cliplc003_maintenance-job-framework.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-001800_cliplc003_maintenance-job-framework.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261124-122732
- **Related target files**: `scripts/agent/memory/services.py`, `tests/agent/memory/test_memory_layer.py`
