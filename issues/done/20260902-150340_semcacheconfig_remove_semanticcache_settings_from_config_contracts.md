# Remove SemanticCache settings from Agent, RAG, and RAG MCP configuration contracts

## Priority
Medium

## Summary
Remove `use_semantic_cache`, `semantic_cache_threshold`, and `semantic_cache_max_size` from
every active configuration contract and conversion path, and make supplying a removed key
produce a clear configuration error rather than a silent no-op.

## Background
Investigation confirmed these three fields currently exist in `scripts/rag/models_config.py`,
`scripts/shared/types.py` (the shared `RagConfig` protocol), and
`scripts/agent/config_dataclasses.py` (the Agent `RAGConfig` dataclass), consistent with this
memo's description of duplication across the RAG configuration DTO, shared protocol, Agent
configuration, cross-field validation, and the RAG MCP configuration adapter.

## Problem
SemanticCache configuration is duplicated across the concrete RAG configuration DTO, the
shared `RagConfig` protocol, Agent configuration dataclasses and builders, cross-field
validation, shared RAG validation, the RAG MCP configuration adapter, and module configuration
translation. Leaving these fields after deleting the runtime cache (`semcacherm`) would
advertise a feature that cannot operate and would force adapters, fixtures, and callers to
provide obsolete values.

## Reason for Change
Once `semcacherm` removes the runtime cache, these configuration fields have no implementation
to configure; retaining them either silently discards operator input or misleads operators into
believing the feature is still tunable.

## Implementation Intent
Remove `use_semantic_cache`, `semantic_cache_threshold`, and `semantic_cache_max_size` from
every active configuration contract and conversion path. Treat the removed keys consistently
rather than silently ignoring an operator's obsolete configuration. Preserve `embed_url`
because semantic retrieval and memory embeddings still depend on it.

## Target Files or Areas
- `scripts/rag/models_config.py`
- `scripts/shared/types.py`
- `scripts/shared/config_validator.py`
- `scripts/shared/config_loader.py`
- `scripts/agent/config_dataclasses.py`
- `scripts/agent/config_builders.py`
- `scripts/mcp_servers/rag_pipeline/rag_pipeline_models.py`
- `scripts/mcp_servers/rag_pipeline/rag_pipeline_service.py`
- Agent configuration files and examples
- RAG MCP configuration files and examples
- Configuration and reload tests

Verify every path and ownership boundary before editing; add only files confirmed by a
repository-wide reference search at implementation time.

## Required Changes
- Remove the three SemanticCache fields from `RagConfigImpl`, the shared `RagConfig` protocol, and the Agent `RAGConfig` dataclass.
- Stop reading the three keys in `_build_rag_config()`; stop passing the three values to the Agent `RAGConfig` constructor.
- Remove `AgentConfig._validate_semantic_cache_url()` and its invocation; preserve `_validate_memory_embed_url()` and all other non-cache `embed_url` validation.
- Remove SemanticCache threshold and maximum-size checks from `RagConfigValidator`.
- Remove cache fields from `RagPipelineConfig` after inspecting its complete definition.
- Remove cache attributes from `build_rag_cfg_adapter()`.
- Remove `semantic_cache_max_size` and `semantic_cache_threshold` from `RagPipelineMCPService._build_module_cfg()`.
- Remove the three keys from Agent, RAG MCP, deployment, and example configuration files.
- Remove cache references from configuration reload paths, namespaces, mocks, and fixtures.
- Determine how `ConfigLoader` handles unknown keys; if unknown keys are otherwise ignored, add explicit validation that rejects the three removed keys with a clear migration message, applied consistently to Agent and RAG MCP configuration loading.
- Correct configuration docstrings and examples that reference `cfg.rag.use_semantic_cache`.

## Constraints
- Limit the change to SemanticCache removal and its direct contracts.
- Do not redesign remote/local fallback behavior in this issue set.
- Do not remove `embed_url`; it remains required outside the deleted cache path.
- Do not preserve a no-op cache API or configuration switch that suggests the removed feature still exists.
- Preserve unrelated behavior and update only verified callers.
- Update documentation only after code and tests establish the final behavior (see `semcachedocs`).

## Acceptance Criteria
- No active Agent, RAG, or RAG MCP configuration type contains a SemanticCache field.
- The shared `RagConfig` protocol does not require obsolete cache attributes.
- Agent builders and RAG MCP adapters do not read, create, or forward cache values.
- `_build_module_cfg()` does not copy cache settings.
- No SemanticCache-specific cross-field or shared RAG validation remains.
- Active and example configuration files contain none of the removed keys.
- Supplying a removed key does not silently succeed; it produces the documented configuration error.
- `embed_url` remains available to local RAG search and Agent memory embeddings.
- Agent configuration, RAG configuration, RAG MCP configuration, and reload tests pass.

## Testing Expectations
Run a repository-wide reference search before editing. Confirm each replacement regression
test fails before the implementation change and passes afterward. Run the complete affected
test suites, type checking, and linting. Verify that unrelated remote/local fallback behavior
is not changed by this issue. Record any missing file or unresolved design decision before
implementation rather than guessing.

## Documentation Impact
Yes — covered by `semcachedocs` (filed alongside this issue), not performed here.

## Out of Scope
- Removing the `SemanticCache` implementation itself and its invalidation paths — covered by `semcacherm`, which this issue depends on.
- Test and documentation replacement — covered by `semcachedocs`.
- Redesigning remote/local RAG fallback behavior.

## Dependencies
Depends on `semcacherm` landing first — these configuration fields should not be removed while
the runtime cache still reads them.

## Unresolved Questions
Whether `ConfigLoader` currently rejects unknown keys by default or ignores them — determine
this during implementation (Implementation Tasks) rather than assuming, since the correct
migration-error behavior depends on it.

## AI Implementation Instruction
Confirm `ConfigLoader`'s current unknown-key handling before deciding how to reject the three
removed keys. Run a repository-wide reference search for `use_semantic_cache`,
`semantic_cache_threshold`, and `semantic_cache_max_size` before editing, since call sites may
have changed since this issue was filed. Do not remove `embed_url` or any other non-cache
configuration field.
