# Unify and strictly validate the RAG runtime configuration and tool contract

## Priority
High

## Summary
Build the RAG MCP runtime from one validated, immutable configuration object, validate boolean settings strictly, and make `rag_pipeline_tools.py` the single, tightly bounded definition of the four RAG tools.

## Background
Verified against master on 2026-11-25 (source: `memo-issue.md` H-01, which is a local, untracked note):
- Confirmed: `RagPipelineMCPService.start()` builds two configuration views from one `RagPipelineConfig`: `build_rag_cfg_adapter()` (`scripts/mcp_servers/rag_pipeline/rag_pipeline_models.py:163`) and `_build_module_cfg()` (`scripts/mcp_servers/rag_pipeline/rag_pipeline_service.py:80`). The dict omits `use_mqe`, `use_rerank`, `use_refiner`, `top_k_*`, and the refiner settings, so which value reaches the pipeline depends on `resolve_rag_config` layering (`scripts/rag/config_resolution.py:79-164`).
- Confirmed: booleans use `bool()` at `rag_pipeline_models.py:84-88` and in the adapter, so the TOML string `"false"` becomes `True`. Integers and floats already go through `get_typed()`, which rejects `bool` for numeric types (`scripts/shared/config_utils.py:56-78`).
- Confirmed: `rag_debug_pipeline` reads an undeclared `debug` argument (`rag_pipeline_service.py:255`), and `rag_delete_document` declares `resource_scope_keys` as `{}` (`rag_pipeline_tools.py`).
- Refuted: the note says the Agent static definition of `rag_list_documents` uses `page` and a required `page_size`. No `page_size` or `page` tool parameter exists in `scripts`, `config`, or `tests` (only unrelated DB and EventBus uses). The Agent builds its tool view from the MCP-published `TOOL_LIST` through the runtime registry, so no second hand-written Agent schema was found. The drift-prevention goal still applies to the registry and the MCP list, but the stated concrete mismatch could not be reproduced.
- Correction: `resource_scope_keys` is a mapping in this repository (for example `{"paths": "path"}` in `scripts/mcp_servers/mdq/mdq_tools.py`), not a list, so the note's `["url"]` form does not match the contract.

## Problem
The effective runtime configuration cannot be proven from one place, string booleans are silently accepted as `True`, and the tool inputs of `rag_list_documents`, `rag_debug_pipeline`, and `rag_delete_document` are loosely bounded or inconsistently declared.

## Reason for Change
A misread boolean can enable an expensive or unsafe stage that the operator disabled, and an unbounded `limit` or blank query reaches the service. The later RAG remediation issues depend on one trustworthy configuration object.

## Implementation Intent
- One frozen runtime DTO, built once after validation, used for the security posture, the service configuration, and the non-secret fingerprint.
- Strict boolean validation at the config boundary with field-specific errors; keep the existing `get_typed` numeric behavior.
- Keep `rag_pipeline_tools.py` as the canonical tool definition and tighten it: `lang` in `ja` or `en`, `limit` integer 1 to 200 (default 20), `minLength: 1` for queries and URLs, bounded `history_context`, a declared resource scope for delete (in the repository's mapping format).
- The debug tool always collects debug output; keep `rag_run_pipeline.debug` only if it changes the documented response.
- Keep the intentional decision not to compare the Agent and RAG MCP database paths at startup.

## Target Files or Areas
- `scripts/mcp_servers/rag_pipeline/rag_pipeline_models.py`, `rag_pipeline_tools.py`, `rag_pipeline_service.py`, `document_manager.py`
- `scripts/rag/config_resolution.py`, `scripts/rag/models_config.py`, `scripts/rag/pipeline.py`
- `scripts/shared/config_utils.py`, `scripts/shared/config_validator.py`
- `config/rag_pipeline_mcp_server.toml`, `config/agent.toml` (only where a key is affected)
- `tests/mcp_servers/rag_pipeline/`, `tests/shared/test_rag_tools_consistency.py`

## Required Changes
- Replace the adapter plus `module_cfg` pair with one frozen DTO covering stage flags, prompts, top-k values, thresholds, RRF, MQE, Refiner, URLs, DB settings, and timeouts; remove the layering gap in `resolve_rag_config` for this path.
- Reject non-boolean values for boolean keys (strings, integers, null) with the key name in the error; validate numeric ranges (positive retries, workers, top-k; non-negative busy timeout; score ranges) at startup.
- Derive the posture view, service configuration, and fingerprint from the same DTO instance.
- Tighten the four tool schemas as listed under Implementation Intent and reject blank-after-trim query and URL values at the service boundary.
- Remove the undeclared `debug` read from the debug tool.

## Constraints
- Do not change the Agent-to-MCP RAG database path policy.
- Keep the existing published tool names, status, and safety metadata; only the input contract and scope metadata change.
- No new configuration keys without an entry in the configuration reference (`docs/21_rag/rag_05_01-configuration-reference.md`).

## Acceptance Criteria
- Every supported configuration key maps to exactly one DTO field, and runtime values equal the validated TOML values in tests.
- The DTO cannot be mutated after posture validation.
- A string, integer, or null for a boolean key fails startup with a field-specific message.
- Invalid `lang`, `limit`, blank query, and blank URL return argument errors.
- A test compares the Agent-visible schema (from the registry) with `TOOL_LIST` for name, properties, required, types, enums, bounds, write metadata, serial metadata, and resource scope.

## Testing Expectations
Unit tests for the DTO, boolean and numeric validation, and each tool schema bound; a registry-versus-`TOOL_LIST` comparison test; the whole-suite run per `rules/toolchain.md`; ruff, mypy, and the contract manifest checks for changed paths.

## Documentation Impact
Update `docs/21_rag/rag_05_01-configuration-reference.md` and the RAG MCP tool reference for the new bounds and the single configuration object; state intent and constraints only.

## Out of Scope
- Comparing Agent and RAG MCP database paths at startup.
- Health and readiness behavior (issues/20261125-093147_ragrem002_rag-startup-posture-readiness.md), pipeline outcomes (issues/20261125-093149_ragrem004_rag-pipeline-outcomes.md).

## Dependencies
- Blocks issues/20261125-093147_ragrem002_rag-startup-posture-readiness.md, issues/20261125-093148_ragrem003_rag-consistency-structured-probes.md, issues/20261125-093149_ragrem004_rag-pipeline-outcomes.md.
- No open sibling issue overlaps these files (checked: `rg -l` over `issues` and `plans`).

## Unresolved Questions
- `不明`: the intended value format of `resource_scope_keys` for `rag_delete_document` (mapping form such as `{"url": "url"}` is assumed from mdq tools); confirm with the registry validation rules.
- `不明`: whether `rag_run_pipeline.debug` has a documented response difference; if not it should be removed.
- `不明`: where the Agent-side static tool definition mentioned in the source note lives, if it exists outside this repository state.

## AI Implementation Instruction
Change only the files above; keep public behavior except the stated validation; stop and ask if the registry rejects the chosen resource-scope form; do not touch the Agent database-path decision.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261125-093146
- **Related target files**: `scripts/mcp_servers/rag_pipeline/rag_pipeline_models.py`, `scripts/mcp_servers/rag_pipeline/rag_pipeline_tools.py`, `scripts/mcp_servers/rag_pipeline/rag_pipeline_service.py`, `scripts/rag/config_resolution.py`, `scripts/shared/config_utils.py`
