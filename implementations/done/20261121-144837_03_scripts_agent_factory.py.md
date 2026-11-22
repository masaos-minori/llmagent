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
- Finding (adversarial verification, 2026-11-21): this claim did not hold as written. The test file explicitly sets `ctx.cfg.rag.embed_url` and constructs `MemoryConfig()` / `_build_memory_config({})` with default `memory_embed_enabled=True`; once the enabled-gated check moved into `MemoryConfig` (Plan row 1), those constructions raise. Four tests failed until the fixture assignments were switched to `ctx.cfg.memory.memory_embed_url` and the builder/default constructions were given a non-empty `memory_embed_url`. No assertion semantics changed; only the inputs were adjusted. The file is not a Plan target row; it is an affected test requiring this adjustment.

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
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 2026-11-21 | 2026-11-21 | Implemented; no ctx.cfg.rag reference remains |
| 2 | Add or update tests per Validation plan | Completed | 2026-11-21 | 2026-11-21 | Affected-test claim disproved; fixture inputs adjusted (see Compatibility finding); 10 passed |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-11-21 | 2026-11-21 | ruff/mypy clean |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 2026-11-21 | 2026-11-21 | N/A |

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
