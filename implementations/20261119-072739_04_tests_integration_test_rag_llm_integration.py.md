## Goal

Set `store.embed_dim = 0` on the `MagicMock(spec=MemoryStore)` in `tests/integration/test_rag_llm_integration.py` instead of `store._embed_dim`, so the public accessor yields a real value (`REQ-005`).

## Scope
**Release unit**: N/A: test-only change, does not break production callers.

## Assumptions

- There is one assignment `store._embed_dim = 0` at L81 on a `MagicMock(spec=MemoryStore)` (verified at L80-81).
- The integration test drives `MemoryIngestionService`, which now reads `self._store.embed_dim`; without updating this mock, a child mock would be forwarded as `embed_dim`.

## Design decisions

- Replace the single `store._embed_dim = 0` with `store.embed_dim = 0`, preserving the value `0`.

## Alternatives considered

- PropertyMock configuration: simpler to just assign the public attribute directly, matching the pattern used in `test_memory_layer.py`.

## Implementation
### Target file
`tests/integration/test_rag_llm_integration.py`
### Procedure
Replace the single `store._embed_dim = 0` assignment with `store.embed_dim = 0`.
### Method
1. In `tests/integration/test_rag_llm_integration.py`, replace line 81:
   ```python
   store._embed_dim = 0
   ```
   with:
   ```python
   store.embed_dim = 0
   ```
   (the `store = MagicMock(spec=MemoryStore)` at L80 is unchanged).
2. Confirm zero remaining `._embed_dim` assignments on `MagicMock(spec=MemoryStore)` remain in this file.
### Details

- Preserve the value `0`; only the attribute name changes.

## Compatibility considerations

N/A: test-only change; no production impact.

## Security considerations

N/A: no change to guards, bindings, or side-effect semantics.

## Rollback considerations

N/A: revert the commit.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `tests/integration/test_rag_llm_integration.py` | Integration: embedding-failure path still passes a real embed_dim | `uv run pytest tests/integration/test_rag_llm_integration.py` | all pass |
| `tests/integration/test_rag_llm_integration.py` | Static: format, lint | `uv run ruff check` / `uv run ruff format --check` | clean |

## Completion criteria

- `store._embed_dim = 0` is now `store.embed_dim = 0` (REQ-005).
- `tests/integration/test_rag_llm_integration.py` passes and forwards a real dimension value (REQ-005).
- ruff check/format are clean on the file.

## Out of Scope

- Changing any production code in `store.py` or `ingestion.py` (handled by sibling documents).
- Editing `tests/agent/memory/test_memory_layer.py` (handled by its own sibling document).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Set `store.embed_dim = 0` instead of `store._embed_dim` (`tests/integration/test_rag_llm_integration.py`, REQ-005) | Pending | — | — | |
| 2 | Run integration test + ruff (`tests/integration/test_rag_llm_integration.py`, REQ-005) | Pending | — | — | |

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
- **Requirement ID**: `REQ-005`
- **Source issue**: `issues/20261118-224711_encap001_ingestion-embed-dim-accessor.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261119-001953_encap001_ingestion-embed-dim-accessor.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261119-072739
- **Related target files**: `tests/integration/test_rag_llm_integration.py`
