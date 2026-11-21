## Goal

Read the embedding endpoint from the Memory section in the builder and remove the RAG section builder (REQ-001, AC-001).

## Scope
**Release unit**: RU-1

## Assumptions
- `tests/agent/test_config_builders.py` is not a companion of this row: it is named by two rows (this row and `config/agent.toml`), so it keeps its own document (Plan row 22).
- The refiner-key rejection message that names `config/rag_pipeline_mcp_server.toml` is part of the existing behaviour asserted by the companion-adjacent test file; the rejected keys must keep being rejected after `_build_rag_config()` is removed.

## Design decisions
- `_build_memory_config()` gains one key read, `memory_embed_url`, using the same `get_typed`/`_get_str_or_default` pattern as its sibling reads, so typed validation stays in one place (REQ-004 pattern reference).
- `_build_rag_config()` is deleted, not kept as a thin alias: the Current-Specification-Only policy rejects the old key location, so there is no section left to build.

## Alternatives considered
- Keep `_build_rag_config()` returning `MemoryConfig`: rejected — the builder is called by `config_builders.py`, which the Plan amends as a fallout row; keeping an alias would reintroduce the ownership mismatch this Plan removes.

## Implementation
### Target file
`scripts/agent/config_section_builders.py`
### Procedure
- Delete `_build_rag_config()` (line 169) and its import of `RAGConfig`.
- In `_build_memory_config()` (line 231), set `memory_embed_url` from the Memory-section mapping.
- Keep the refiner-key rejection path that raises for `use_refiner`, `refiner_max_tokens`, `refiner_timeout`, `refiner_max_chars_per_chunk`.
### Method
- Single key read at the point the Memory dataclass is constructed; no new helper, no alias fallback.
### Details
- Verified 2026-11-21: the caller `agent.config_builders._assemble_agent_config()` passes `rag=_build_rag_config(cfg)` at line 125; that call site is a separate procedure row (Plan row 32), so this document does not change it.
- `_build_memory_config()` currently reads no endpoint key, which is the defect this row repairs.

## Compatibility considerations
- Import-layer contract: this module stays inside `agent`, no new cross-layer import.
- The module docstring's "Import from here" example lists `_build_rag_config`; update it.

## Security considerations
- N/A: no trust-boundary change; the value is a URL string read from the owning file.

## Rollback considerations
- N/A: revert the commit within release unit RU-1.

## Open question
- 不明: `check_agent_refiner_keys()` is currently called only from `_build_rag_config()`. Once that builder is removed there is no call site left, and `_build_memory_config()` receives only the Memory mapping, so the top-level refiner keys can be reached only through the production validator or another surviving path. The Plan does not name that call site; confirm it before removing the builder.

## Validation plan
- `uv run pytest tests/agent/test_config_builders.py -v`
- `uv run ruff check scripts/agent/config_section_builders.py`, `uv run mypy scripts/agent/config_section_builders.py`
- `PYTHONPATH=scripts uv run lint-imports`

## Completion criteria
- No `_build_rag_config()` definition remains; a Memory-section `memory_embed_url` value reaches `MemoryConfig`, and the refiner keys are still rejected as unknown.

## Out of Scope
- The assembly call site (`scripts/agent/config_builders.py`) and the test assertions (Plan row 22).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|---|---|---|---|---|---|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Gated: issues/20261119-145303_cliplc005_staged-reload-transaction.md phase all - the typed-candidate model REQ-002 validates through is defined by that Issue; coordination dependency, either order works |
| 2 | Add or update tests per Validation plan | Pending | — | — | Gated: same - assertions live in Plan row 22 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | Gated: same - shared field-registry/validation surface must be re-verified |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | Gated: same - documentation rows are separate procedure documents |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|---|---|---|---|
| 1 | Call site for `check_agent_refiner_keys()` after `_build_rag_config()` removal is undecided (see Open question) | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---|---|---|---|---|---|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-001 (the Memory builder owns the Memory-section key)
- **Source issue**: issues/20261120-114212_agentcfg004_config-ownership-split.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261121-140444_agentcfg004_config-ownership-split.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261121-144837
- **Related target files**: `scripts/agent/config_section_builders.py`
