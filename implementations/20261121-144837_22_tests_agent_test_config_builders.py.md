## Goal

Replace the RAG-section builder tests with tests for the Memory-section key, so the moved ownership is asserted at the builder boundary (REQ-001; AC-001, AC-002).

## Scope
**Release unit**: RU-1

## Assumptions
- This row is not a companion: `tests/agent/test_config_builders.py` is named by two rows (`config_section_builders.py` and `config/agent.toml`), so it keeps its own document.
- The refiner-key rejection message that names `config/rag_pipeline_mcp_server.toml` must keep being asserted; `check_agent_refiner_keys()` stays as the definition of that message.
- Where the refiner-key check is invoked after `_build_rag_config()` is removed is unknown (see Open question); the test target follows that decision.

## Design decisions
- `TestBuildRAGConfig` is replaced by cases on `_build_memory_config()` for `memory_embed_url` (new): an empty mapping yields the default, and a supplied value is reflected.
- The parametrized refiner-key rejection test is kept in some form, because rejecting those keys is current behaviour that the Plan's AC-001 preserves.

## Alternatives considered
- Delete the refiner-key test with the RAG builder: rejected — the behaviour it protects is not removed by this Plan, so its coverage would be lost.

## Implementation
### Target file
`tests/agent/test_config_builders.py`
### Procedure
- Remove `TestBuildRAGConfig` (lines 122-144) and the `RAGConfig` import (line 21).
- In `TestBuildMemoryConfig`, add cases asserting `memory_embed_url` defaults to `""` and reflects a supplied value.
- Keep the refiner-key rejection assertions against the surviving call site once the open question is resolved.
### Method
- Direct calls to `_build_memory_config()` with plain dicts; no fixture changes beyond the `_MIN_CFG` comment that describes the cross-field check removed by Plan row 1.

### Details
- Verified 2026-11-21: the existing `TestBuildMemoryConfig` cases assert defaults from `_MEMORY_DEFAULTS`, so adding the key there keeps the assertion style identical; `_MIN_CFG` currently exists to satisfy the `memory_embed_enabled` cross-field check that Plan row 1 moves into `MemoryConfig`.

## Compatibility considerations
- `tests/agent/services/test_config_reload_classification.py` is unaffected; it does not import `RAGConfig`.

## Security considerations
- N/A: test-only change.

## Rollback considerations
- N/A: revert the commit within release unit RU-1.

## Validation plan
- `uv run pytest tests/agent/test_config_builders.py -v`
- `uv run ruff check tests/agent/test_config_builders.py`, `uv run mypy tests/agent/test_config_builders.py`

## Completion criteria
- The Memory builder's new key read is covered by a passing and a failing case; no test imports or constructs `RAGConfig`; the refiner keys are still proven to be rejected.

## Out of Scope
- The builder implementation (Plan row 2), the dataclass validation (Plan row 1).

## Open question
- 不明: after `_build_rag_config()` is removed, `check_agent_refiner_keys()` needs a call site (the Memory builder receives only the Memory mapping, so the top-level refiner keys can only be reached by the production validator or another surviving path). The plan does not name that call site; confirm which one before moving the assertions.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|---|---|---|---|---|---|
| 1 | Implement the change described in Implementation > Procedure/Method | Pending | — | — | Gated: issues/20261119-145303_cliplc005_staged-reload-transaction.md phase all - the typed-candidate model is defined by that Issue; coordination dependency, either order works |
| 2 | Add or update tests per Validation plan | Pending | — | — | Gated: same - shared field-registry/validation surface must be re-verified after that Issue lands |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | Gated: same - shared surface must be re-verified after that Issue lands |
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
- **Requirement ID**: REQ-001 (builder tests for the Memory-owned key)
- **Source issue**: issues/20261120-114212_agentcfg004_config-ownership-split.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261121-140444_agentcfg004_config-ownership-split.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261121-144837
- **Related target files**: `tests/agent/test_config_builders.py`
