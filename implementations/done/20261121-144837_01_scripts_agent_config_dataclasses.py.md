## Goal

Move the Memory embedding endpoint out of the misnamed RAG section: delete `RAGConfig` and `AgentConfig.rag`, add `memory_embed_url` (new) to `MemoryConfig`, and make the enabled-gated non-empty check a `MemoryConfig` validation instead of an `AgentConfig` cross-field read (REQ-001, AC-001, AC-002).

## Scope
**Release unit**: RU-1

## Assumptions
- `tests/agent/test_config_dataclasses.py` is this row's companion: it lies under `tests/`, is named by exactly this row, and its test content follows the validation defined here, so it gets no document of its own.
- `scripts/shared/types.py`'s `RagConfig` Protocol is structural and keeps working without `RAGConfig` (the Plan's Assumption 5); re-check at implementation time.
- No alias reading for the old key location: the Current-Specification-Only policy rejects `embed_url` in the infrastructure block as an unknown key.

## Design decisions
- Validation ownership follows configuration ownership: the check moves into `MemoryConfig.__post_init__`, so `MemoryConfig` alone can be validated after a typed-candidate build (REQ-002 depends on this).
- The error message keeps the key name the user sees (`memory_embed_enabled=True requires memory_embed_url to be non-empty`), which is what the companion test asserts.
- `AgentConfig._validate_memory_embed_url` is deleted rather than re-pointed at the Memory field, because after the move there is no cross-section read left to perform.

## Alternatives considered
- N/A: the Plan's Design D4 fixes the shape of this change (field move plus validation move).

## Implementation
### Target file
`scripts/agent/config_dataclasses.py`
### Procedure
- Delete `class RAGConfig` and the `rag: RAGConfig` field of `AgentConfig`, including the `RAGConfig` entry in the section tuple around line 366 and the module docstring line that names `RAGConfig`.
- Add `memory_embed_url` (new) to `MemoryConfig` (default `""`) and give `MemoryConfig` a `__post_init__` containing the enabled-gated check.
- Delete `AgentConfig._validate_memory_embed_url` and its call inside `_validate_cross_field`; `_validate_memory_jsonl_dir` and `_validate_memory_max_startup_snippets` stay.
### Method
- Field: `memory_embed_url: str = ""` on `MemoryConfig`.
- Validation: `if self.memory_embed_enabled and not self.memory_embed_url: raise ValueError(...)` — evaluated on the instance itself, no cross-section access.
- `AgentConfig` keeps no `rag` attribute, so the dataclass field list shrinks by one; the docstring example (`cfg.rag.embed_url`) must be rewritten to `cfg.memory.memory_embed_url`.
### Details
- Verified 2026-11-21: `RAGConfig` carries only `embed_url` (line 156), `AgentConfig.rag` is declared at line 392, and the check lives in `_validate_memory_embed_url` (line 420); `MemoryConfig` has no embedding field and no validation of its own.
- Verified 2026-11-21: `MemoryConfig` already has a `__post_init__` calling the `config_validators` field validators, so the enabled-gated check is added inside it, not as a new `__post_init__`. The check must be evaluated after the existing validator calls: single-field-failure tests in the companion file (e.g. `memory_fts_limit`) construct with default `memory_embed_enabled=True`, so a leading check would shadow their expected errors. Default `MemoryConfig()` now raises when enabled with an empty URL; the companion defaults tests were adjusted accordingly.
- Re-checked the Assumption: `scripts/shared/types.py`'s `RagConfig` Protocol covers the RAG pipeline fields (`use_mqe`, `top_k_search`, ...), not the embedding endpoint, so it is unaffected by this row.
- The consumer set is enumerated by the Plan's rows plus the amendment rows (`config_builders.py`, `config_reload.py`, `config_service_sync.py`); this document must not be validated alone — the release unit lands together.
### Companion test files
- `tests/agent/test_config_dataclasses.py`
  - Procedure: Remove `TestRAGConfigValidation` and the `RAGConfig(...)` constructions in `TestAgentConfigValidation`; add enabled/disabled cases for `memory_embed_url` (new); keep `test_memory_layer_without_jsonl_dir_raises`.
  - Validation: `uv run pytest tests/agent/test_config_dataclasses.py -v`

## Compatibility considerations
- `mypy` sees one fewer dataclass field; every consumer that reads `ctx.cfg.rag` is a sibling procedure of this Plan, so this document is only correct once they land.
- `tools/generate_reference_table.py` output (`docs/23_agent/agent_13_reference-api-generated.md`) is a consumer of the class name and is refreshed by its own procedure row, not hand-edited here.

## Security considerations
- `memory_local_only` keeps its local-address safety check in `scripts/agent/memory/embedding_client.py` (the Plan's Design D4); no check is duplicated here.

## Rollback considerations
- N/A: revert the commit within release unit RU-1.

## Validation plan
- `uv run pytest tests/agent/test_config_dataclasses.py -v`
- `uv run ruff check scripts/agent/config_dataclasses.py`, `uv run mypy scripts/agent/config_dataclasses.py`
- `uv run python tools/check_mock_patch_targets.py` (test patch targets that name `agent.config_dataclasses` must still resolve)

## Completion criteria
- No `RAGConfig` symbol and no `AgentConfig.rag` field remain in `scripts/`; the enabled-gated URL requirement is enforced by `MemoryConfig` alone; the companion tests show both the raising and the passing path.

## Out of Scope
- Field-registry mapping, the builder, and the runtime consumers (their own procedure rows).
- Tool policy, tool catalog, and approval metadata (agentcfg001-003).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|---|---|---|---|---|---|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 2026-11-21 | 2026-11-21 | Implemented; claims verified against source; check must run after field validators (added to procedure Details) |
| 2 | Add or update tests per Validation plan (companion file) | Completed | 2026-11-21 | 2026-11-21 | Companion tests updated; 75 passed |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-11-21 | 2026-11-21 | ruff/mypy/check_mock_patch_targets clean; full suite runs once at batch end |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 2026-11-21 | 2026-11-21 | N/A: docs rows are separate procedure documents |

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
- **Requirement ID**: REQ-001 (move the Memory embedding endpoint to the Memory section)
- **Source issue**: issues/20261120-114212_agentcfg004_config-ownership-split.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261121-140444_agentcfg004_config-ownership-split.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261121-144837
- **Related target files**: `scripts/agent/config_dataclasses.py`, `tests/agent/test_config_dataclasses.py`
