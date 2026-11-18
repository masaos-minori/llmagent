## Goal

Add a test asserting the public `MemoryStore.embed_dim` accessor mirrors the constructor dimension, including the `None` (unset) case (`REQ-006`).

## Scope
**Release unit**: N/A: test-only addition, does not break production callers.

## Assumptions

- `tests/agent/memory/test_memory_store.py` already imports `MemoryStore` (L27) and constructs real `MemoryStore()` instances (e.g. L156, L750), so a real-instance assertion fits the existing style.
- The accessor returns `int | None`; the `None` case exercises the "unset disables validation" contract (REQ-003).

## Design decisions

- Add one test that constructs a `MemoryStore(embed_dim=<int>)` and asserts `store.embed_dim == <int>`, plus the `None` case `MemoryStore()` → `store.embed_dim is None`. Place it near the other construction/property tests in the module.

## Alternatives considered

- Asserting via the private `_embed_dim` directly: rejected; the point of REQ-006 is to pin the *public* accessor, not the private field.

## Implementation
### Target file
`tests/agent/memory/test_memory_store.py`
### Procedure
Add a test asserting the public accessor mirrors the constructor dimension, including the `None` case.
### Method
1. In `tests/agent/memory/test_memory_store.py`, add a test (near other real-`MemoryStore()` construction tests):
   ```python
   def test_embed_dim_accessor_mirrors_constructor() -> None:
       assert MemoryStore(embed_dim=768).embed_dim == 768
       assert MemoryStore().embed_dim is None
   ```
2. Confirm the test runs under the existing `pytest` collection (no fixtures required; `MemoryStore()` opens a temp/session helper as the rest of the module already does).
### Details

- Cover both the set (`int`) and unset (`None`) cases so the `None`-disables-validation contract is pinned through the public accessor (REQ-002, REQ-003, REQ-006).

## Compatibility considerations

N/A: test-only addition; no production impact.

## Security considerations

N/A: no change to guards, bindings, or side-effect semantics.

## Rollback considerations

N/A: revert the commit.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `tests/agent/memory/test_memory_store.py` | Unit: new accessor-mirror assertion passes (set and `None` cases) | `uv run pytest tests/agent/memory/test_memory_store.py` | all pass |
| `tests/agent/memory/test_memory_store.py` | Static: format, lint | `uv run ruff check` / `uv run ruff format --check` | clean |

## Completion criteria

- A test asserting `MemoryStore(embed_dim=...).embed_dim == ...` and `MemoryStore().embed_dim is None` exists (REQ-006).
- `tests/agent/memory/test_memory_store.py` passes; the new assertion covers both the set and `None` cases (REQ-002, REQ-003, REQ-006).
- ruff check/format are clean on the file.

## Out of Scope

- Changing any production code in `store.py` or `ingestion.py` (handled by sibling documents).
- Editing `tests/agent/memory/test_memory_layer.py` or `tests/integration/test_rag_llm_integration.py` (handled by their own sibling documents).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add accessor-mirror assertion (set + None cases) (`tests/agent/memory/test_memory_store.py`, REQ-006) | Pending | — | — | |
| 2 | Run test + ruff (`tests/agent/memory/test_memory_store.py`, REQ-006) | Pending | — | — | |

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
- **Requirement ID**: `REQ-006`
- **Source issue**: `issues/20261118-224711_encap001_ingestion-embed-dim-accessor.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261119-001953_encap001_ingestion-embed-dim-accessor.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261119-072739
- **Related target files**: `tests/agent/memory/test_memory_store.py`
