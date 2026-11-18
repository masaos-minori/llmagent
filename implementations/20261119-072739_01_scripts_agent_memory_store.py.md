## Goal

Add a public read-only `embed_dim` accessor to `scripts/agent/memory/store.py` that returns the dimension stored in `MemoryStore.__init__`, removing the only cross-module private dependency on `self._embed_dim` (`REQ-002`, `REQ-003`).

## Scope
**Release unit**: Part of the `accessor-and-caller` release unit with `ingestion.py` (Phase 1 + Phase 2 land together); Phase 2 cannot be validated alone without Phase 1.

## Assumptions

- `self._embed_dim` stays the single source of truth; the accessor merely exposes it.
- The accessor is a read-only property; no setter is added (matches the plan's "public read-only accessor").
- No `.importlinter` layer relationship changes: adding a member property does not alter imports (`lint-imports` reports 6 contracts kept / 0 broken).

## Design decisions

- Add `@property def embed_dim(self) -> int | None: return self._embed_dim` inside the existing `# ── Read-only API ──` section (L44), directly after `__init__`. This keeps the new accessor next to the private field it exposes and within the documented read-only surface.
- Keep `self._embed_dim` as the single implementation; the accessor delegates to it, so no logic is duplicated (addresses the "second public name becomes duplication" risk).

## Alternatives considered

- Constructor injection of the dimension into `MemoryIngestionService`: rejected as primary (recorded as UNK-01 in the plan); it changes the service constructor and `factory.py` wiring, a wider blast radius. Option (a) public accessor is preferred and satisfies every requirement.

## Implementation
### Target file
`scripts/agent/memory/store.py`
### Procedure
Add a public read-only `embed_dim` property returning `self._embed_dim`.
### Method
1. In `scripts/agent/memory/store.py`, insert a property immediately after `__init__` (L39-42) and before the `# ── Read-only API ──` marker (L44):
   ```python
   @property
   def embed_dim(self) -> int | None:
       """The embedding dimension configured at construction, or None when unset."""
       return self._embed_dim
   ```
2. Leave `self._embed_dim = embed_dim` (L42) unchanged as the single source of truth.
3. Do not add a setter or any other member.
### Details

- The property return type is `int | None` to mirror the constructor parameter and preserve the `None`-disables-validation semantics (REQ-003).
- No import change: the property uses only `self`.

## Compatibility considerations

N/A: purely additive public property; no existing public signature or behavior changes. The `None`-means-unvalidated contract is preserved (REQ-003).

## Security considerations

N/A: no change to query construction, binding, or side-effect semantics.

## Rollback considerations

N/A: revert the commit.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `scripts/agent/memory/store.py` | Unit: accessor returns constructor dimension and `None` | `uv run pytest tests/agent/memory/test_memory_store.py` | all pass |
| `scripts/agent/memory/store.py` | Static: format, lint, type | `uv run ruff check` / `uv run mypy` on the touched files | clean |

## Completion criteria

- `MemoryStore` exposes a public read-only `embed_dim` property returning `self._embed_dim` (REQ-002).
- `None` remains valid and disables dimension validation (REQ-003).
- ruff check and mypy are clean on the touched file (REQ-002, REQ-003).

## Out of Scope

- Changing the `write_upsert` / `add` signatures or write paths in `write_ops.py` (REQ-004).
- Changing how `embed_dim` is validated against embeddings.
- Touching the manual-write path (`_persist_entry`).
- Refactoring dedup or duplicate-link behavior.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add public read-only `embed_dim` accessor to store.py (`scripts/agent/memory/store.py`, REQ-002) | Pending | — | — | Part of release unit accessor-and-caller (Phases 1+2) |
| 2 | Verify accessor mirrors constructor dimension; run ruff/mypy/tests (`scripts/agent/memory/store.py`, REQ-002, REQ-003) | Pending | — | — | |

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
- **Requirement ID**: `REQ-002`, `REQ-003`
- **Source issue**: `issues/20261118-224711_encap001_ingestion-embed-dim-accessor.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261119-001953_encap001_ingestion-embed-dim-accessor.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261119-072739
- **Related target files**: `scripts/agent/memory/store.py`
