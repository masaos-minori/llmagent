## Goal

Replace the RAG-section builder tests with tests for the Memory-section key, so the moved ownership is asserted at the builder boundary (REQ-001; AC-001, AC-002).

## Scope
**Release unit**: RU-1

## Assumptions
- This row is not a companion: `tests/agent/test_config_builders.py` is named by two rows (`config_section_builders.py` and `config/agent.toml`), so it keeps its own document.
- The refiner-key rejection message that names `config/rag_pipeline_mcp_server.toml` must keep being asserted; `check_agent_refiner_keys()` stays as the definition of that message.
- Resolved 2026-11-21 (owner decision): the check is invoked from `ProductionConfigValidator.validate()` (Plan row 7), so the assertion for this behaviour belongs to `tests/agent/test_production_config_validator.py` and not to this file.

## Design decisions
- `TestBuildRAGConfig` is replaced by cases on `_build_memory_config()` for `memory_embed_url` (new): an empty mapping yields the default, and a supplied value is reflected.
- The refiner-key rejection coverage is kept by moving it to `tests/agent/test_production_config_validator.py` (Plan row 7's companion), because rejecting those keys is current behaviour that the Plan's AC-001 preserves.

## Alternatives considered
- Delete the refiner-key test with the RAG builder: rejected — the behaviour it protects is not removed by this Plan, so its coverage would be lost.

## Implementation
### Target file
`tests/agent/test_config_builders.py`
### Procedure
- Remove `TestBuildRAGConfig` (lines 122-144), `TestRagConfigValidationReporting` (lines 670-694), and the `_build_rag_config` calls in `TestBuilderExceptionTypeUniformity` (lines 824, 829); remove the `_build_rag_config` import (lines 3, 24).
- In `TestBuildMemoryConfig`, add cases asserting `memory_embed_url` defaults to `""` and reflects a supplied value.
- Do not re-assert the refiner-key message in this file: after the owner decision the assertion belongs to `tests/agent/test_production_config_validator.py`, which is Plan row 7's companion, so this document only deletes the RAG-builder cases.
- Drop the two RAG-builder reporting characterizations rather than retarget them: the builder that logs per validator result no longer exists, and the equivalent path is covered by the existing production-validator tests in this file's own scope.
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
- The Memory builder's new key read is covered by a passing and a failing case; no test imports or constructs `RAGConfig`; no test asserts the refiner-key message here, because that coverage is held by Plan row 7's companion test file.

## Out of Scope
- The builder implementation (Plan row 2), the dataclass validation (Plan row 1).

## Open question
- Resolved 2026-11-21 (owner decision): the call site is `ProductionConfigValidator.validate()` (Plan row 7), so the refiner-key assertion is asserted through the validator and lives in `tests/agent/test_production_config_validator.py`.

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
