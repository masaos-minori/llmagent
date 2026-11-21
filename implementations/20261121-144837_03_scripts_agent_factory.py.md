## Goal

Construct the Memory embedding client from the Memory-owned endpoint instead of the RAG section (REQ-001, AC-002).

## Scope
**Release unit**: RU-1

## Assumptions
- `EmbeddingClientConfig` in `scripts/agent/memory/embedding_client.py` keeps its shape; only the source of the value moves (the Plan's Reference Files row).
- No test asserts this line directly; the row is verified by the tests run per the Validation plan.

## Design decisions
- Single-line source change: `build_embed_url()` keeps receiving the raw configured value, so the URL-normalisation behaviour is untouched.
- `memory_embed_timeout_sec` and `memory_local_only` already read from `ctx.cfg.memory`; after this row the whole client construction reads one section.

## Alternatives considered
- N/A: the Plan's Design D4 fixes the source; no alternative source exists.

## Implementation
### Target file
`scripts/agent/factory.py`
### Procedure
- In `_build_embedding_client()`, change `embed_url=build_embed_url(ctx.cfg.rag.embed_url)` (line 246) to read `ctx.cfg.memory.memory_embed_url`.
### Method
- One attribute path change inside an existing keyword argument; no signature change.
### Details
- Verified 2026-11-21: `_build_embedding_client()` already reads `ctx.cfg.memory.memory_embed_timeout_sec` and `ctx.cfg.memory.memory_local_only`, so the mixed-section read is the only defect here.

## Compatibility considerations
- `tests/agent/test_memory_local_only.py` passes `MagicMock()` contexts and fake config objects, so it is unaffected as long as the attribute it reads is the one being set.

## Security considerations
- The local-only guard in `scripts/agent/memory/embedding_client.py` continues to reject a non-loopback endpoint when `memory_local_only` is true; moving the source does not weaken it.

## Rollback considerations
- N/A: revert the commit within release unit RU-1.

## Validation plan
- `uv run pytest tests/agent/test_memory_local_only.py -v` (affected test)
- `uv run ruff check scripts/agent/factory.py`, `uv run mypy scripts/agent/factory.py`

## Completion criteria
- `_build_embedding_client()` reads the endpoint from `ctx.cfg.memory`; no reference to `ctx.cfg.rag` remains in this module.

## Out of Scope
- The dataclass field and validation (Plan row 1); the health-check read (Plan row 4).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|---|---|---|---|---|---|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Gated: issues/20261119-145303_cliplc005_staged-reload-transaction.md phase all - the typed-candidate model REQ-002 validates through is defined by that Issue; coordination dependency, either order works |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: no test asserts this line; the row is covered by the affected tests listed in the Validation plan. Gated: same as step 1 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | Gated: same - shared field-registry/validation surface must be re-verified |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | Gated: same - documentation rows are separate procedure documents |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|---|---|---|---|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---|---|---|---|---|---|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-001 (consumers read the endpoint from the Memory section)
- **Source issue**: issues/20261120-114212_agentcfg004_config-ownership-split.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261121-140444_agentcfg004_config-ownership-split.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261121-144837
- **Related target files**: `scripts/agent/factory.py`
