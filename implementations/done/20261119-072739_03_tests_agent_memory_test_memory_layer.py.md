## Goal

Update the `MagicMock`-based stores in `tests/agent/memory/test_memory_layer.py` to set `.embed_dim` instead of `._embed_dim`, so the public accessor yields a real value (not a child mock) when `ingestion.py` reads it (`REQ-005`).

## Scope
**Release unit**: N/A: test-only change, does not break production callers.

## Assumptions

- There are exactly 10 assignments `mock_store._embed_dim = ...` on `MagicMock()` stores (verified at L76, 351, 391, 627, 669, 713, 733, 771, 804, 848).
- Reading a property off a `MagicMock` returns an auto-created child mock, so leaving these as `._embed_dim` while `ingestion.py` reads `.embed_dim` would forward a mock as `embed_dim` (the risk the plan documents).

## Design decisions

- Replace every occurrence of `mock_store._embed_dim =` with `mock_store.embed_dim =` in this file, preserving the assigned values (`None` or `768`). This keeps each test's intended dimension while exposing the public accessor.

## Alternatives considered

- Configuring a property-style shim on the mocks: more fragile than simply setting the public attribute; the plan's mitigation is explicit `.embed_dim` assignment.

## Implementation
### Target file
`tests/agent/memory/test_memory_layer.py`
### Procedure
Replace all 10 `mock_store._embed_dim =` assignments with `mock_store.embed_dim =`.
### Method
1. In `tests/agent/memory/test_memory_layer.py`, replace every occurrence of `mock_store._embed_dim =` with `mock_store.embed_dim =` (10 occurrences across L76, 351, 391, 627, 669, 713, 733, 771, 804, 848), preserving each RHS value.
2. Confirm zero remaining `._embed_dim` assignments on `MagicMock()` stores remain in this file.
### Details

- Do not change the assigned values (`None` stays `None`; `768` stays `768`); only the attribute name changes.
- Do not touch any non-MagicMock store construction.

## Compatibility considerations

N/A: test-only change; no production impact.

## Security considerations

N/A: no change to guards, bindings, or side-effect semantics.

## Rollback considerations

N/A: revert the commit.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `tests/agent/memory/test_memory_layer.py` | Unit: memory-layer tests pass with the accessor forwarding a real dimension | `uv run pytest tests/agent/memory/test_memory_layer.py` | all pass |
| `tests/agent/memory/test_memory_layer.py` | Static: format, lint | `uv run ruff check` / `uv run ruff format --check` | clean |

## Completion criteria

- All 10 `mock_store._embed_dim` assignments are now `mock_store.embed_dim` (REQ-005).
- `tests/agent/memory/test_memory_layer.py` passes and forwards a real dimension value (REQ-005).
- ruff check/format are clean on the file.

## Out of Scope

- Changing any production code in `store.py` or `ingestion.py` (handled by sibling documents).
- Editing `tests/integration/test_rag_llm_integration.py` (handled by its own sibling document).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Set `mock_store.embed_dim` instead of `mock_store._embed_dim` (all occurrences) (`tests/agent/memory/test_memory_layer.py`, REQ-005) | Completed | 20261119-104112 | 20261119-104112 | — |
| 2 | Run memory-layer tests + ruff (`tests/agent/memory/test_memory_layer.py`, REQ-005) | Completed | 20261119-104112 | 20261119-104112 | — |

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
- **Related target files**: `tests/agent/memory/test_memory_layer.py`
