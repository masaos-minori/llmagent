## Goal

Route `ingestion.py`'s forward of the embedding dimension through the newly added public `MemoryStore.embed_dim` accessor instead of the private `self._store._embed_dim`, removing the last cross-module private dependency (`REQ-001`, `REQ-003`).

## Scope
**Release unit**: Part of the `accessor-and-caller` release unit with `store.py` (Phase 1 + Phase 2 land together); applying Phase 2 without Phase 1 leaves `self._store.embed_dim` undefined (`AttributeError`), so this phase cannot be validated alone.

## Assumptions

- The public `embed_dim` accessor is added to `MemoryStore` by the sibling `store.py` document (declared `(new)` there); this file must not reference the private `_embed_dim` anymore (REQ-001).
- The accessor preserves the `None`-disables-validation semantics, so routing through it changes no runtime behavior (REQ-003).

## Design decisions

- Replace only the attribute access `self._store._embed_dim` with `self._store.embed_dim` on the `write_upsert` call; leave the surrounding function body, signature, and the `write_upsert` import untouched.

## Alternatives considered

- Injecting the dimension via `MemoryIngestionService`'s constructor: recorded as UNK-01 in the plan and rejected as primary; it would change the service constructor and `factory.py` wiring.

## Implementation
### Target file
`scripts/agent/memory/ingestion.py`
### Procedure
Replace the private attribute access with the public accessor on the `write_upsert` call.
### Method
1. In `scripts/agent/memory/ingestion.py`, `_persist_entry_with_embedding` (L137-142), replace line 142:
   ```python
   write_upsert(entry, embedding=embedding, embed_dim=self._store._embed_dim)
   ```
   with:
   ```python
   write_upsert(entry, embedding=embedding, embed_dim=self._store.embed_dim)
   ```
2. Confirm no other production reference to `self._store._embed_dim` (or any `_embed_dim`) remains in `ingestion.py` (REQ-001).
### Details

- The value forwarded is identical for identical input (the accessor returns `self._embed_dim`), preserving the `None`-unvalidated behavior (REQ-003).
- Do not change the `write_upsert` / `add` signatures or any write path in `write_ops.py` (REQ-004).

## Compatibility considerations

N/A: no public/runtime interface change beyond reading the new accessor; the forwarded value is unchanged (REQ-003).

## Security considerations

N/A: no change to query construction, binding, or side-effect semantics.

## Rollback considerations

N/A: revert the commit.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `scripts/agent/memory/ingestion.py` | Integration: persist forwards a real dimension via the accessor | `uv run pytest tests/agent/memory/test_memory_layer.py` | all pass |
| `scripts/agent/memory/ingestion.py` | Static: format, lint, type | `uv run ruff check` / `uv run mypy` on the touched files | clean |

## Completion criteria

- No code in `ingestion.py` references `MemoryStore._embed_dim` (REQ-001).
- The accessor forwards the same dimension value, including `None` (REQ-003).
- ruff check and mypy are clean on the touched file (REQ-001, REQ-003).

## Out of Scope

- Changing the `write_upsert` / `add` signatures or write paths in `write_ops.py` (REQ-004).
- Changing how `embed_dim` is validated against embeddings.
- Touching the manual-write path (`_persist_entry`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Route `ingestion._persist_entry_with_embedding` through the accessor (`scripts/agent/memory/ingestion.py`, REQ-001) | Completed | 20261119-104112 | 20261119-104112 | Part of release unit accessor-and-caller (Phases 1+2) |
| 2 | Verify no private access remains; run ruff/mypy/tests (`scripts/agent/memory/ingestion.py`, REQ-001, REQ-003) | Completed | 20261119-104112 | 20261119-104112 | — |

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
- **Requirement ID**: `REQ-001`, `REQ-003`
- **Source issue**: `issues/20261118-224711_encap001_ingestion-embed-dim-accessor.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261119-001953_encap001_ingestion-embed-dim-accessor.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261119-072739
- **Related target files**: `scripts/agent/memory/ingestion.py`
