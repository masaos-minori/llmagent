## Goal
- Remove the RAG remote-delegation path (`HttpAugment`, `call_rag_service()`, the fallback identity gate, and the keys `rag_query_service_url`, `rag_auth_token`, `rag_identity_mismatch_policy`) so RAG is reached only through rag-pipeline-mcp over the common MCP transport, and withdraw ADR-010 (with ADR-004 Group 10 amended) once the maintainer states the approval.

## Priority
High

## Scope
- **In-Scope**: Delete `scripts/rag/http_augment.py` and `scripts/rag/pipeline_service.py`; remove the HTTP branch, HTTP diagnostics, and the fallback identity gate from `scripts/rag/` (keep `compute_local_identity` and `corpus_identity` pieces used by rag-pipeline-mcp and the maintenance service); remove the three keys from code, configuration, validators, and fixtures with removed-key rejection tests; update ADR-010, ADR-004, the ADR index and authority files, the RAG documents, and `governance_03`.
- **Out-of-Scope**: Aligning the consistency-check severity policy (`issues/20261109-113123_adrrev013_rag-consistency-policy.md`); any new fallback or remote-delegation mechanism; `corpus_identity` and the identity view exposed by `rag_pipeline_server.py`; the maintainer approval record itself (not written by the implementer).
- **Dependencies**: Depends on none. Blocks `issues/20261109-113123_adrrev013_rag-consistency-policy.md`. Sequencing: none against the other Plans in `plans/` (no shared target file).
  - **Depends on**: N/A: none

## Background
- Source: `memo-issue.md` item H-03, re-verified on 2026-11-10.
- `Confirmed by repository evidence`: no caller reaches the delegation path in production. `scripts/rag/pipeline.py:218` enters the HTTP branch only when `rag_query_service_url` is non-empty; no `config/*.toml` sets it, `/opt/llm/config/` contains only a comment mentioning `rag_auth_token` (`rag_pipeline_mcp_server.toml:35`), and the only `RagPipeline` constructor outside tests is in `scripts/mcp_servers/rag_pipeline/rag_pipeline_service.py:115`, whose config sets `rag_query_service_url=""` (`rag_pipeline_models.py:171`). `call_rag_service()` posts to `{rag_url}/v1/call_tool` with `rag_run_pipeline`, that is, it is a private client of the same MCP server, bypassing the common transport, with its own `_MAX_ATTEMPTS = 3` and `_REQUEST_TIMEOUT_SECONDS = 10.0` (`pipeline_service.py:22-23`) and no header when `auth_token` is empty.
- `Confirmed by repository evidence`: the Issue's "the Agent imports `rag.corpus_identity`" holds (`scripts/agent/services/rag_maintenance_service.py:16`: `CorpusIdentity`, `ensure_corpus_meta`); the Agent has no `rag.pipeline` import. The identity-mismatch gate (`_identity_gate`, called at `pipeline.py:252`) runs only inside `RagPipeline.augment()`, so inside rag-pipeline-mcp, and only after the HTTP branch returned `None`; with the branch removed it can never run. Under `reject` it fires only when both identities are present and unequal; otherwise the unverifiable state proceeds, which matches the Issue's "ineffective or unusable" problem.
- `Refuted`/narrowed: the Issue's target list is incomplete. Gate-only and HTTP-only code outside it: `scripts/rag/identity_gate.py` (`GateDecision`, `_identity_gate`, `_safe_corpus_id`; `compute_local_identity` is used by `rag_pipeline_server.py:100` and stays), `scripts/rag/corpus_identity.py` (`parse_remote_identity`, used only by `pipeline_service.py`), `scripts/rag/diagnostics.py` and `scripts/rag/models_result.py` (`HttpResultKind`, `http_result_kind`, `remote_status_code`, `identity_degraded`; consumed only inside `scripts/rag/`), `config/adr_authority.toml`, `registry/manifests/invariant_coverage.yaml`, `docs/10_adr/adr_00_document-guide.md`, `docs/10_adr/adr_02_07_016_adr-authority-model.md`, and about a dozen RAG, agent, and MCP documents. Tests with the removed keys in config fixtures span 20 files, not the six the Issue names.
- `Confirmed by repository evidence`: the removed keys are not only the Agent's: `rag_query_service_url`/`rag_auth_token` are fields of `shared/types.py` and `rag/models_config.py`, and `rag_identity_mismatch_policy` is also validated in `production_config_validator.py:203` and set in `config/agent.toml:8`.
- `Documentation only` (read from the repository documents): ADR-010 is the sole Fallback exception ADR-004 permits (`config/adr_authority.toml:174`); `governance_03` still lists NC-42, NC-43, NC-44; `rag_05_07` line 26 describes the gate at fallback time.
- `Needs confirmation`: whether `/opt/llm` environment overrides (not config files) set the keys; the config files in `/opt/llm/config/` do not (UNK-01).

## Problem
- A feature with no configured user keeps code, 20 test files, configuration keys, and an Accepted ADR alive, and the ADR carries open items (NC-42..44) and contradictions.
- The path bypasses the common MCP transport with its own retry and timeout constants and an empty-token default (ADR-007, ADR-004).

## Reason for Change
- Removal costs less than repairing an unused feature and closes several review items at once; it is a prerequisite for the RAG consistency-policy alignment Issue. No external deadline.

## Implementation Intent
- RAG is reached only through rag-pipeline-mcp over the common MCP transport; no remote-delegation or fallback path remains. `RagPipeline.augment()` runs the in-process pipeline only.
- Remove only what the delegation path alone uses; keep `compute_local_identity`, `CorpusIdentity`, `ensure_corpus_meta`, `compute_identity`, and the refiner.
- Config load rejects the removed keys as unknown, with no shim.
- ADR work (ADR-010 Withdrawn, ADR-004 Group 10 amendment) is written only after the maintainer states the approval; until then the records are clearly marked pending.

## Requirements
- `REQ-001`: Delete `HttpAugment`, `call_rag_service()`, and their result types; remove the HTTP branch from `RagPipeline.augment()`, the HTTP state and `run_http_augment` from `AugmentRefiner`, and the HTTP-only diagnostics and result fields; delete or trim their tests; leave no reference under `scripts/`, `tests/`, `config/`, `docs/`.
- `REQ-002`: Remove the fallback identity gate (`GateDecision`, `_identity_gate`, `_safe_corpus_id`, the `IdentityGate` stage record, `_identity_degraded`, `parse_remote_identity`) while keeping `compute_local_identity` and the identity pieces rag-pipeline-mcp and `rag_maintenance_service.py` use.
- `REQ-003`: Remove `rag_query_service_url`, `rag_auth_token`, and `rag_identity_mismatch_policy` from code, configs, validators, and fixtures; config load rejects each removed key (tests for the `agent.toml`, rag config resolution, and rag-pipeline-mcp config paths).
- `REQ-004`: Mark ADR-010 Withdrawn and amend ADR-004 Decision Group 10 to "fallback is prohibited without exception", each with an approval record that stays marked pending until the maintainer states it; the implementer does not write the maintainer's decision.
- `REQ-005`: Update `rag_05_01`, `rag_05_07` (remove the gate and the "unverifiable" state), the other RAG, agent, and MCP documents, the ADR index (status, verification matrix, reference graph), `config/adr_authority.toml`, `registry/manifests/invariant_coverage.yaml`, and the ADR guide and authority model; close NC-42, NC-43, NC-44 in `governance_03` citing this Issue.
- `REQ-006`: Verification: `rg` over `scripts/ tests/ config/ docs/` returns none of the removed symbols and keys (apart from the Withdrawn ADR-010 record), the in-process RAG pipeline and rag-pipeline-mcp tests pass, and the documentation checkers pass.

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/rag/http_augment.py` | Delete: Delete the HTTP augment stage | Delete the HTTP augment stage; no caller outside `augment.py` | REQ-001 / AC-01 | `scripts/rag/http_augment.py:76` `HttpAugment`; sole importer `scripts/rag/augment.py:27` (checked in Step 3) | `tests/rag/test_rag_http_mode.py` (deleted) | Verified |
| `scripts/rag/pipeline_service.py` | Delete: Delete `call_rag_service` and `CallRagResult` | Delete `call_rag_service` and `CallRagResult`; only `http_augment.py` imports it | REQ-001 / AC-01 | `scripts/rag/pipeline_service.py:76`; importer `scripts/rag/http_augment.py:12` (checked in Step 3) | `tests/rag/test_rag_pipeline_service.py` (deleted) | Verified |
| `scripts/rag/augment.py` | Modify: Remove `run_http_augment`, HTTP state, `last_remote_identity`, `http_stage_results`, `map_http_result_kind` | Remove `run_http_augment`, HTTP state, `last_remote_identity`, `http_stage_results`, `map_http_result_kind`; keep the refiner | REQ-001, REQ-002 / AC-01, AC-02 | `scripts/rag/augment.py:27,73-179,230` (checked in Step 3) | `tests/rag/test_augment_refiner.py`, `tests/rag/test_augment_integration.py` | Verified |
| `scripts/rag/pipeline.py` | Modify: Remove the HTTP branch, `_merge_http_state`, the fallback identity gate, and `_identity_degraded` | Remove the HTTP branch, `_merge_http_state`, the fallback identity gate, and `_identity_degraded`; `augment()` runs the in-process pipeline only | REQ-001, REQ-002 / AC-01, AC-02 | `scripts/rag/pipeline.py:39-40,99,184-293,318-393` (checked in Step 3) | `tests/rag/test_rag_pipeline.py`, `tests/rag/test_rag_pipeline_no_cache_freshness.py` | Verified |
| `scripts/rag/identity_gate.py` | Modify: Remove `GateDecision`, `_identity_gate`, `_safe_corpus_id` | Remove `GateDecision`, `_identity_gate`, `_safe_corpus_id`; keep `compute_local_identity` (used by `rag_pipeline_server.py:100`) | REQ-002 / AC-02 | `scripts/rag/identity_gate.py:38,68,90,98` (checked in Step 3) | `tests/rag/test_identity_gate.py` | Verified |
| `scripts/rag/corpus_identity.py` | Modify: Remove `parse_remote_identity` (only `pipeline_service.py` used it) and the docstring paragraph about the fallback gate | Remove `parse_remote_identity` (only `pipeline_service.py` used it) and the docstring paragraph about the fallback gate; keep `CorpusIdentity`, `ensure_corpus_meta`, `compute_identity` | REQ-002 / AC-02 | `scripts/rag/corpus_identity.py:16-22,159`; `rag_maintenance_service.py:16` keeps the rest (checked in Step 3) | `tests/rag/test_identity_gate.py` | Verified |
| `scripts/rag/diagnostics.py` | Modify: Remove the HTTP-derived fields (`http_result_kind` and the remote fields) | Remove the HTTP-derived fields (`http_result_kind` and the remote fields) | REQ-001 / AC-01 | `scripts/rag/diagnostics.py:16,68,79,108,135,148` (checked in Step 3) | `tests/rag/test_diagnostics.py` | Verified |
| `scripts/rag/models_result.py` | Modify: Remove `HttpResultKind`, `remote_status_code`, `identity_degraded`, and the remote `ResultSource` member if unused | Remove `HttpResultKind`, `remote_status_code`, `identity_degraded`, and the remote `ResultSource` member if unused | REQ-001, REQ-002 / AC-01, AC-02 | `scripts/rag/models_result.py:29,109-118` (checked in Step 3) | `tests/rag/test_diagnostics.py` | Verified |
| `scripts/rag/models_config.py` | Modify: Remove `rag_query_service_url`, `rag_auth_token`, `rag_identity_mismatch_policy` from the config model | Remove `rag_query_service_url`, `rag_auth_token`, `rag_identity_mismatch_policy` from the config model | REQ-003 / AC-03 | `scripts/rag/models_config.py:26,27,46` (checked in Step 3) | `tests/rag/test_config_resolution.py` | Verified |
| `scripts/rag/config_resolution.py` | Modify: Remove the three keys from the allowed-key sets and defaults so they are rejected as unknown | Remove the three keys from the allowed-key sets and defaults so they are rejected as unknown | REQ-003 / AC-03 | `scripts/rag/config_resolution.py:34,35,52,67,68,85` (checked in Step 3) | `tests/rag/test_config_resolution.py` | Verified |
| `scripts/rag/llm_client.py` | Modify: Reword two docstrings that cite `call_rag_service` | Reword two docstrings that cite `call_rag_service` | REQ-001 / AC-01 | `scripts/rag/llm_client.py:123,288` (checked in Step 3) | `tests/rag/test_llm_client_timeout.py` | Verified |
| `scripts/shared/types.py` | Modify: Remove the three keys from the runtime config contract | Remove the three keys from the runtime config contract | REQ-003 / AC-03 | `scripts/shared/types.py:97,98,117` (checked in Step 3) | `tests/agent/test_rag_get_cfg.py` | Verified |
| `scripts/agent/production_config_validator.py` | Modify: Remove `rag_identity_mismatch_policy` from the allowed keys so `agent.toml` rejects it | Remove `rag_identity_mismatch_policy` from the allowed keys so `agent.toml` rejects it | REQ-003 / AC-03 | `scripts/agent/production_config_validator.py:203` (checked in Step 3) | `tests/agent/test_production_config_validator.py` | Verified |
| `scripts/mcp_servers/rag_pipeline/rag_pipeline_models.py` | Modify: Remove `rag_auth_token` and the `rag_query_service_url=""` loop guard from the server config | Remove `rag_auth_token` and the `rag_query_service_url=""` loop guard from the server config | REQ-003 / AC-03 | `scripts/mcp_servers/rag_pipeline/rag_pipeline_models.py:65,94,122,134,171-172` (checked in Step 3) | `tests/mcp_servers/rag_pipeline/test_rag_pipeline_models.py` | Verified |
| `scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py` | Modify: Correct the module docstring that says the server replaces `augment()` when `rag_query_service_url` is configured | Correct the module docstring that says the server replaces `augment()` when `rag_query_service_url` is configured | REQ-001 / AC-01 | `scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py:7-8` (checked in Step 3) | `tests/mcp_servers/rag_pipeline/test_rag_pipeline_mcp_service.py` | Verified |
| `config/agent.toml` | Modify: Delete `rag_identity_mismatch_policy` | Delete `rag_identity_mismatch_policy` | REQ-003 / AC-03 | `config/agent.toml:8` (checked in Step 3) | `tests/agent/test_production_config_validator.py` | Verified |
| `config/rag_pipeline_mcp_server.toml` | Modify: Delete the comment block describing `rag_auth_token` | Delete the comment block describing `rag_auth_token` | REQ-003 / AC-03 | `config/rag_pipeline_mcp_server.toml:35` (checked in Step 3) | `tests/mcp_servers/rag_pipeline/test_rag_pipeline_models.py` | Verified |
| `config/adr_authority.toml` | Modify: Remove ADR-010 node and edges | Remove ADR-010 node and edges; adjust the ADR-004 Fallback note | REQ-005 / AC-05 | `config/adr_authority.toml:89,94,96,171,174,254-264` (checked in Step 3) | `uv run python tools/check_adr_authority.py` | Verified |
| `registry/manifests/invariant_coverage.yaml` | Modify: Remove the ADR-010 invariant coverage entries | Remove the ADR-010 invariant coverage entries | REQ-005 / AC-05 | `registry/manifests/invariant_coverage.yaml:231,238,247` (checked in Step 3) | `uv run python tools/check_adr_invariant_matrix.py` | Verified |
| `tests/rag/test_rag_http_mode.py` | Delete: Delete: tests only the HTTP delegation mode | Delete: tests only the HTTP delegation mode | REQ-001 / AC-01 | 47 hits for removed symbols (rg count) (checked in Step 3) | N/A: deleted with its subject | Verified |
| `tests/rag/test_pipeline_http_result_kind.py` | Delete: Delete: tests the HTTP result kind | Delete: tests the HTTP result kind | REQ-001 / AC-01 | 31 hits (rg count) (checked in Step 3) | N/A: deleted with its subject | Verified |
| `tests/rag/test_rag_pipeline_service.py` | Delete: Delete: tests `call_rag_service` | Delete: tests `call_rag_service` | REQ-001 / AC-01 | 27 hits (rg count) (checked in Step 3) | N/A: deleted with its subject | Verified |
| `tests/rag/test_augment_refiner.py` | Modify: Remove HTTP-augment cases | Remove HTTP-augment cases; keep refiner cases | REQ-001 / AC-01 | 103 hits (rg count) (checked in Step 3) | `uv run pytest tests/rag/test_augment_refiner.py -v` | Verified |
| `tests/rag/test_augment_integration.py` | Modify: Remove HTTP-augment cases | Remove HTTP-augment cases; keep refiner integration | REQ-001 / AC-01 | 103 hits (rg count) (checked in Step 3) | `uv run pytest tests/rag/test_augment_integration.py -v` | Verified |
| `tests/rag/test_identity_gate.py` | Modify: Remove gate-decision tests | Remove gate-decision tests; keep `compute_local_identity` tests | REQ-002 / AC-02 | 11 hits (rg count) (checked in Step 3) | `uv run pytest tests/rag/test_identity_gate.py -v` | Verified |
| `tests/rag/test_config_resolution.py` | Modify: Replace key-acceptance cases with rejection cases for the three keys | Replace key-acceptance cases with rejection cases for the three keys | REQ-003 / AC-03 | 10 hits (rg count) (checked in Step 3) | `uv run pytest tests/rag/test_config_resolution.py -v` | Verified |
| `tests/rag/test_diagnostics.py` | Modify: Drop the removed diagnostics field | Drop the removed diagnostics field | REQ-001 / AC-01 | 1 hit (rg count) (checked in Step 3) | `uv run pytest tests/rag/test_diagnostics.py -v` | Verified |
| `tests/rag/test_rag_pipeline.py` | Modify: Drop the removed config keys from the test config fixture | Drop the removed config keys from the test config fixture | REQ-003 / AC-03 | 4 hits for the removed keys (rg count) (checked in Step 3) | `uv run pytest tests/rag/test_rag_pipeline.py -v` | Verified |
| `tests/rag/test_rag_pipeline_no_cache_freshness.py` | Modify: Drop the removed config keys from the test config fixture | Drop the removed config keys from the test config fixture | REQ-003 / AC-03 | 2 hits for the removed keys (rg count) (checked in Step 3) | `uv run pytest tests/rag/test_rag_pipeline_no_cache_freshness.py -v` | Verified |
| `tests/rag/test_rag_pipeline_stage.py` | Modify: Drop the removed config keys from the test config fixture | Drop the removed config keys from the test config fixture | REQ-003 / AC-03 | 4 hits for the removed keys (rg count) (checked in Step 3) | `uv run pytest tests/rag/test_rag_pipeline_stage.py -v` | Verified |
| `tests/rag/test_rag_quality_regression.py` | Modify: Drop the removed config keys from the test config fixture | Drop the removed config keys from the test config fixture | REQ-003 / AC-03 | 2 hits for the removed keys (rg count) (checked in Step 3) | `uv run pytest tests/rag/test_rag_quality_regression.py -v` | Verified |
| `tests/rag/test_stage_lifecycle.py` | Modify: Drop the removed config keys from the test config fixture | Drop the removed config keys from the test config fixture | REQ-003 / AC-03 | 2 hits for the removed keys (rg count) (checked in Step 3) | `uv run pytest tests/rag/test_stage_lifecycle.py -v` | Verified |
| `tests/rag/test_stage_observability.py` | Modify: Drop the removed config keys from the test config fixture | Drop the removed config keys from the test config fixture | REQ-003 / AC-03 | 2 hits for the removed keys (rg count) (checked in Step 3) | `uv run pytest tests/rag/test_stage_observability.py -v` | Verified |
| `tests/rag/test_llm_client_timeout.py` | Modify: Drop the removed config keys from the test config fixture | Drop the removed config keys from the test config fixture | REQ-003 / AC-03 | 2 hits for the removed keys (rg count) (checked in Step 3) | `uv run pytest tests/rag/test_llm_client_timeout.py -v` | Verified |
| `tests/agent/commands/test_agent_rag.py` | Modify: Drop the removed keys from the config fixture | Drop the removed keys from the config fixture | REQ-003 / AC-03 | `tests/agent/commands/test_agent_rag.py:21,24` (checked in Step 3) | `uv run pytest tests/agent/commands/test_agent_rag.py -v` | Verified |
| `tests/agent/test_rag_get_cfg.py` | Modify: Drop the removed keys from the config fixture | Drop the removed keys from the config fixture | REQ-003 / AC-03 | `tests/agent/test_rag_get_cfg.py:26,27` (checked in Step 3) | `uv run pytest tests/agent/test_rag_get_cfg.py -v` | Verified |
| `tests/agent/test_production_config_validator.py` | Modify: Add a test that `agent.toml` containing `rag_identity_mismatch_policy` is rejected | Add a test that `agent.toml` containing `rag_identity_mismatch_policy` is rejected | REQ-003 / AC-03 | validator tests live here (checked in Step 3) (checked in Step 3) | `uv run pytest tests/agent/test_production_config_validator.py -v` | Verified |
| `tests/mcp_servers/rag_pipeline/test_rag_pipeline_models.py` | Modify: Drop `rag_auth_token`/`rag_query_service_url` from fixtures and assertions | Drop `rag_auth_token`/`rag_query_service_url` from fixtures and assertions; add a removed-key rejection case in the models test | REQ-003 / AC-03 | 8 hits (rg count) (checked in Step 3) | `uv run pytest tests/mcp_servers/rag_pipeline/test_rag_pipeline_models.py -v` | Verified |
| `tests/mcp_servers/rag_pipeline/test_rag_pipeline_mcp_service.py` | Modify: Drop `rag_auth_token`/`rag_query_service_url` from fixtures and assertions | Drop `rag_auth_token`/`rag_query_service_url` from fixtures and assertions; add a removed-key rejection case in the models test | REQ-003 / AC-03 | 9 hits (rg count) (checked in Step 3) | `uv run pytest tests/mcp_servers/rag_pipeline/test_rag_pipeline_mcp_service.py -v` | Verified |
| `tests/mcp_servers/rag_pipeline/test_rag_security_validation.py` | Modify: Drop `rag_auth_token`/`rag_query_service_url` from fixtures and assertions | Drop `rag_auth_token`/`rag_query_service_url` from fixtures and assertions; add a removed-key rejection case in the models test | REQ-003 / AC-03 | 6 hits (rg count) (checked in Step 3) | `uv run pytest tests/mcp_servers/rag_pipeline/test_rag_security_validation.py -v` | Verified |
| `docs/10_adr/adr_02_06_010_rag-fallback.md` | Modify: Mark ADR-010 Withdrawn | Mark ADR-010 Withdrawn; approval record left pending until the maintainer states it | REQ-004 / AC-04 | 35 hits; `## Status` section (checked in Step 3) (checked in Step 3) | `check_adr_structure.py`, `check_adr_authority.py` | Verified |
| `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md` | Modify: Amend Decision Group 10 to "fallback is prohibited without exception" | Amend Decision Group 10 to "fallback is prohibited without exception"; pending approval record | REQ-004 / AC-04 | `### Group 10: Fallback Boundary` (line 106); 12 ADR-010 hits (checked in Step 3) | `check_adr_preservation.py` (expected ERROR on the amended decision; the maintainer-approved amendment is the intended change) | Verified |
| `docs/10_adr/adr_01_index.md` | Modify: Update ADR-010 status, verification matrix, and reference graph | Update ADR-010 status, verification matrix, and reference graph | REQ-005 / AC-05 | 13 hits for ADR-010/removed symbols (checked in Step 3) | `uv run python tools/generate_adr_authority.py --check` | Verified |
| `docs/10_adr/adr_00_document-guide.md` | Modify: Remove or mark the ADR-010 entry | Remove or mark the ADR-010 entry | REQ-005 / AC-05 | ADR-010 hit (rg) (checked in Step 3) | `uv run python tools/check_docs_structure.py` | Verified |
| `docs/10_adr/adr_02_07_016_adr-authority-model.md` | Modify: Update the ADR-010 reference in the authority model | Update the ADR-010 reference in the authority model | REQ-005 / AC-05 | ADR-010 hit (rg) (checked in Step 3) | `uv run python tools/check_adr_authority.py` | Verified |
| `docs/00_governance/governance_03_issue-and-uncertainty-management.md` | Modify: Close NC-42, NC-43, NC-44 citing this Issue | Close NC-42, NC-43, NC-44 citing this Issue; remove their inline markers | REQ-005 / AC-05 | `governance_03` lines 134, 151, 168 (checked in Step 3) | `uv run python tools/check_needs_confirmation_inventory.py` | Verified |
| `docs/00_governance/governance_05_change-impact-and-dependency-graphs.md` | Modify: Remove the remote-delegation edge if present | Remove the remote-delegation edge if present | REQ-005 / AC-05 | 1 hit (rg) (checked in Step 3) | `uv run python tools/check_docs_quality.py` | Verified |
| `docs/21_rag/rag_05_01-configuration-reference.md` | Modify: Remove the three keys and the fallback description | Remove the three keys and the fallback description | REQ-005 / AC-05 | 8 hits (rg) (checked in Step 3) | `uv run python tools/check_docs_consistency.py --domain rag` | Verified |
| `docs/21_rag/rag_05_07-rag-index-consistency-checks.md` | Modify: Remove the identity gate and the "unverifiable" state | Remove the identity gate and the "unverifiable" state | REQ-005 / AC-05 | line 26 (augment gate rejects at fallback time) (checked in Step 3) | `uv run python tools/check_docs_consistency.py --domain rag` | Verified |
| `docs/21_rag/rag_00_document-guide.md` | Modify: Remove the HTTP delegation, fallback, and identity gate description | Remove the HTTP delegation, fallback, and identity gate description | REQ-005 / AC-05 | 1 hits (rg) (checked in Step 3) | `uv run python tools/check_docs_consistency.py --domain rag` | Verified |
| `docs/21_rag/rag_01_system_overview.md` | Modify: Remove the HTTP delegation, fallback, and identity gate description | Remove the HTTP delegation, fallback, and identity gate description | REQ-005 / AC-05 | 4 hits (rg) (checked in Step 3) | `uv run python tools/check_docs_consistency.py --domain rag` | Verified |
| `docs/21_rag/rag_03_01_query_pipeline-overview.md` | Modify: Remove the HTTP delegation, fallback, and identity gate description | Remove the HTTP delegation, fallback, and identity gate description | REQ-005 / AC-05 | 3 hits (rg) (checked in Step 3) | `uv run python tools/check_docs_consistency.py --domain rag` | Verified |
| `docs/21_rag/rag_03_02_query_pipeline-rag-pipeline-class.md` | Modify: Remove the HTTP delegation, fallback, and identity gate description | Remove the HTTP delegation, fallback, and identity gate description | REQ-005 / AC-05 | 9 hits (rg) (checked in Step 3) | `uv run python tools/check_docs_consistency.py --domain rag` | Verified |
| `docs/21_rag/rag_03_03_query_pipeline-context-and-diagnostics.md` | Modify: Remove the HTTP delegation, fallback, and identity gate description | Remove the HTTP delegation, fallback, and identity gate description | REQ-005 / AC-05 | 5 hits (rg) (checked in Step 3) | `uv run python tools/check_docs_consistency.py --domain rag` | Verified |
| `docs/21_rag/rag_03_05_query_pipeline-augment-stages.md` | Modify: Remove the HTTP delegation, fallback, and identity gate description | Remove the HTTP delegation, fallback, and identity gate description | REQ-005 / AC-05 | 3 hits (rg) (checked in Step 3) | `uv run python tools/check_docs_consistency.py --domain rag` | Verified |
| `docs/21_rag/rag_03_06_query_pipeline-helpers-and-cache.md` | Modify: Remove the HTTP delegation, fallback, and identity gate description | Remove the HTTP delegation, fallback, and identity gate description | REQ-005 / AC-05 | 1 hits (rg) (checked in Step 3) | `uv run python tools/check_docs_consistency.py --domain rag` | Verified |
| `docs/21_rag/rag_04_dto-models-types.md` | Modify: Remove the HTTP delegation, fallback, and identity gate description | Remove the HTTP delegation, fallback, and identity gate description | REQ-005 / AC-05 | 1 hits (rg) (checked in Step 3) | `uv run python tools/check_docs_consistency.py --domain rag` | Verified |
| `docs/21_rag/rag_05_04-error-handling-reference.md` | Modify: Remove the HTTP delegation, fallback, and identity gate description | Remove the HTTP delegation, fallback, and identity gate description | REQ-005 / AC-05 | 1 hits (rg) (checked in Step 3) | `uv run python tools/check_docs_consistency.py --domain rag` | Verified |
| `docs/22_mcp/mcp_04_03_rag-pipeline-and-cicd.md` | Modify: Remove the delegation reference | Remove the delegation reference | REQ-005 / AC-05 | 2 hits (rg) (checked in Step 3) | `uv run python tools/check_docs_consistency.py --domain mcp` | Verified |
| `docs/23_agent/agent_10_06_operations-and-observability-rag-diagnostics-and-memory.md` | Modify: Remove the remote-result diagnostics description | Remove the remote-result diagnostics description | REQ-005 / AC-05 | 2 hits (rg) (checked in Step 3) | `uv run python tools/check_docs_consistency.py --domain agent` | Verified |
| `docs/23_agent/agent_09_02_data-layer-access-patterns.md` | Modify: Remove the removed-symbol reference | Remove the removed-symbol reference | REQ-005 / AC-05 | 1 hit (rg) (checked in Step 3) | `uv run python tools/check_docs_consistency.py --domain agent` | Verified |

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/mcp_servers/rag_pipeline/rag_pipeline_service.py` | The one production `RagPipeline` constructor; its config must keep working without the removed keys | REQ-003 |
| `scripts/agent/services/rag_maintenance_service.py` | Keeps using `rag.corpus_identity`; must stay valid | REQ-002 |
| `tests/mcp_servers/mdq/test_mdq_rag_boundary.py` | Boundary test the Issue requires in the final validation | REQ-006 |
| `.importlinter` | `rag`/`agent`/`shared` layer contracts that must stay satisfied | REQ-001 |
| `tools/check_compat_shims.py` | No-compatibility-shim rule for the key removal | REQ-003 |
| `docs/10_adr/adr_02_03_007_mcp-http-adoption-and-stdio-non-support.md` | ADR-007 INV-02/07 (common transport, no retry) the removal aligns with | REQ-004 |

## Acceptance Criteria
- `AC-01` (REQ-001): `rg -n "HttpAugment|call_rag_service|run_http_augment|http_augment|CallRagResult|HttpResultKind|http_result_kind|remote_status_code" scripts/ tests/ config/ docs/ registry/` returns no match.
- `AC-02` (REQ-002): `rg -n "_identity_gate|GateDecision|parse_remote_identity|identity_degraded|IdentityGate" scripts/ tests/ docs/` returns no match; `compute_local_identity` and its tests remain and pass.
- `AC-03` (REQ-003): `rg -n "rag_query_service_url|rag_auth_token|rag_identity_mismatch_policy" scripts/ tests/ config/ docs/` returns only the removed-key rejection tests; each load path rejects the keys (tests).
- `AC-04` (REQ-004): ADR-010 shows Withdrawn and ADR-004 Group 10 shows no exception, each with a marked pending (or maintainer-stated) approval record; no approval text is invented.
- `AC-05` (REQ-005): `check_adr_authority.py`, `check_adr_invariant_matrix.py`, `check_adr_structure.py`, `generate_adr_authority.py --check`, `check_docs_consistency.py --domain rag`, `check_needs_confirmation_inventory.py` pass; NC-42..44 are closed.
- `AC-06` (REQ-006): `uv run pytest tests/rag tests/mcp_servers/rag_pipeline tests/agent -v` and `tests/mcp_servers/mdq/test_mdq_rag_boundary.py` pass.

## Tests
- `REQ-001`, `REQ-002`: surviving `tests/rag/test_augment_*.py`, `test_rag_pipeline*.py`, `test_identity_gate.py` (local identity only), `test_diagnostics.py`.
- `REQ-003`: new rejection cases in `tests/rag/test_config_resolution.py`, `tests/agent/test_production_config_validator.py`, and `tests/mcp_servers/rag_pipeline/test_rag_pipeline_models.py`.
- `REQ-004`..`REQ-006`: documentation checkers and the `rg` acceptance checks.

## Documentation Impact
- Required (REQ-004, REQ-005): ADR-010 status, ADR-004 Group 10, the ADR index, the ADR guide and authority model, `rag_05_01`, `rag_05_07`, the RAG overview, pipeline, diagnostics, and DTO documents, `governance_03`, `governance_05`, and the agent and MCP documents named in the target table. State intent, failure behavior ("no fallback"), and the closed Needs Confirmation items; do not add implementation-location mappings or config values (`skills/DESIGN.md` Docs content policy).

## Assumptions
- With the HTTP branch gone, the `RagPipeline.augment()` fallback chain reduces to: in-process search, refiner, raw chunks. Falsifiable by `tests/rag/test_rag_pipeline.py` and `tests/rag/test_rag_quality_regression.py`.
- `ResultSource` members that only the remote path used may be removed; a member another module still reads is kept. Falsifiable by `rg ResultSource scripts/`.
- The ADR withdrawal follows the project ADR process; the approval record is a maintainer statement. Phase 4 starts only after the maintainer states it (UNK-02).
- Overlap with other Frozen Plans (`tools/check_plan_target_overlaps.py`, Step 8b), all judged compatible: `config/agent.toml`, `scripts/agent/production_config_validator.py`, `tests/agent/test_production_config_validator.py`, and `governance_05` with `plans/20261110-091327_adrrev002_agent-eventbus-coupling.md` (different keys and statements: `eventbus_db_path` vs `rag_identity_mismatch_policy`; EventBus vs RAG edges), and `docs/21_rag/rag_05_01-configuration-reference.md` with `plans/20261108-170335_ragrev014_robots-policy-gaps.md` (robots keys vs the three removed keys). Sequencing: either order works; the validator allowed-key set is edited in two separate entries.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether an `/opt/llm` environment override sets `rag_query_service_url` or `rag_identity_mismatch_policy` | Deployed environment variables and service files outside the repository (the deployed config files do not set them) | Maintainer confirms before deploy; if one is set, stop and report (Issue instruction) | False |
| UNK-02 | The maintainer's approval statement for withdrawing ADR-010 and amending ADR-004 Group 10 | A maintainer statement | Implementation Phase 4 writes pending records only; the maintainer states the decision, then the records are completed | False |
| UNK-03 | Whether the `rag_pipeline_mcp_server.toml` loader and the `rag` config loader already reject unknown keys, or the rejection must be added | Loader behavior for unknown keys at `rag_pipeline_models.py:94` and `config_resolution.py` | Procedure phase reads both loaders; REQ-003 tests fail first if rejection is missing, and the loader change is a Plan amendment if a new file is needed | False |
| UNK-04 | Whether any `ResultSource` or `StageResult` consumer outside `scripts/rag/` reads the removed result fields | The `rg` for the fields over `scripts/agent/` and `scripts/mcp_servers/` found none, but dynamic access is not detected | Re-run during Phase 1; keep a field a consumer reads | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/rag/http_augment.py` | delete | Medium | N/A | N/A | not applicable (rsynced) |
| `scripts/rag/pipeline_service.py` | delete | Medium | N/A | N/A | not applicable (rsynced) |
| `scripts/rag/augment.py` | modify | High | N/A | N/A | not applicable (rsynced) |
| `scripts/rag/pipeline.py` | modify | High | N/A | N/A | not applicable (rsynced) |
| `scripts/rag/identity_gate.py` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `scripts/rag/corpus_identity.py` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `scripts/rag/diagnostics.py` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `scripts/rag/models_result.py` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `scripts/rag/models_config.py` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `scripts/rag/config_resolution.py` | modify | Medium | N/A | N/A | not applicable (rsynced) |
| `scripts/rag/llm_client.py` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `scripts/shared/types.py` | modify | Medium | N/A | N/A | not applicable (rsynced) |
| `scripts/agent/production_config_validator.py` | modify | Medium | N/A | N/A | not applicable (rsynced) |
| `scripts/mcp_servers/rag_pipeline/rag_pipeline_models.py` | modify | Medium | N/A | N/A | not applicable (rsynced) |
| `scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `config/agent.toml` | modify | Medium | N/A | N/A | not applicable (rsynced) |
| `config/rag_pipeline_mcp_server.toml` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `config/adr_authority.toml` | modify | Medium | N/A | N/A | not applicable (rsynced) |
| `registry/manifests/invariant_coverage.yaml` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/rag/test_rag_http_mode.py` | delete | Low | N/A | N/A | not applicable (rsynced) |
| `tests/rag/test_pipeline_http_result_kind.py` | delete | Low | N/A | N/A | not applicable (rsynced) |
| `tests/rag/test_rag_pipeline_service.py` | delete | Low | N/A | N/A | not applicable (rsynced) |
| `tests/rag/test_augment_refiner.py` | modify | Medium | N/A | N/A | not applicable (rsynced) |
| `tests/rag/test_augment_integration.py` | modify | Medium | N/A | N/A | not applicable (rsynced) |
| `tests/rag/test_identity_gate.py` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/rag/test_config_resolution.py` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/rag/test_diagnostics.py` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/rag/test_rag_pipeline.py` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/rag/test_rag_pipeline_no_cache_freshness.py` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/rag/test_rag_pipeline_stage.py` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/rag/test_rag_quality_regression.py` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/rag/test_stage_lifecycle.py` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/rag/test_stage_observability.py` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/rag/test_llm_client_timeout.py` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/agent/commands/test_agent_rag.py` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/agent/test_rag_get_cfg.py` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/agent/test_production_config_validator.py` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/mcp_servers/rag_pipeline/test_rag_pipeline_models.py` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/mcp_servers/rag_pipeline/test_rag_pipeline_mcp_service.py` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/mcp_servers/rag_pipeline/test_rag_security_validation.py` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `docs/10_adr/adr_02_06_010_rag-fallback.md` | modify | Medium | N/A | N/A | not applicable (rsynced) |
| `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md` | modify | Medium | N/A | N/A | not applicable (rsynced) |
| `docs/10_adr/adr_01_index.md` | modify | Medium | N/A | N/A | not applicable (rsynced) |
| `docs/10_adr/adr_00_document-guide.md` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `docs/10_adr/adr_02_07_016_adr-authority-model.md` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `docs/00_governance/governance_03_issue-and-uncertainty-management.md` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `docs/00_governance/governance_05_change-impact-and-dependency-graphs.md` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `docs/21_rag/rag_05_01-configuration-reference.md` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `docs/21_rag/rag_05_07-rag-index-consistency-checks.md` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `docs/21_rag/rag_00_document-guide.md` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `docs/21_rag/rag_01_system_overview.md` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `docs/21_rag/rag_03_01_query_pipeline-overview.md` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `docs/21_rag/rag_03_02_query_pipeline-rag-pipeline-class.md` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `docs/21_rag/rag_03_03_query_pipeline-context-and-diagnostics.md` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `docs/21_rag/rag_03_05_query_pipeline-augment-stages.md` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `docs/21_rag/rag_03_06_query_pipeline-helpers-and-cache.md` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `docs/21_rag/rag_04_dto-models-types.md` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `docs/21_rag/rag_05_04-error-handling-reference.md` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `docs/22_mcp/mcp_04_03_rag-pipeline-and-cicd.md` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `docs/23_agent/agent_10_06_operations-and-observability-rag-diagnostics-and-memory.md` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `docs/23_agent/agent_09_02_data-layer-access-patterns.md` | modify | Low | N/A | N/A | not applicable (rsynced) |

## Design
- **Approach**: delete the delegation path leaf-first. Phase 1 removes the HTTP branch, `HttpAugment`, `call_rag_service`, and HTTP diagnostics together with their tests; Phase 2 removes the identity gate that only the branch fed; Phase 3 removes the configuration keys and fixtures; Phase 4 does documents and ADRs; Phase 5 verifies and hands off to deploy. Alternatives rejected: keeping `call_rag_service` as the Agent's MCP client (it bypasses the common transport) and keeping the gate for a future delegation (no consumer).
- **Compatibility impact**: `agent.toml` and the rag configs that still contain a removed key fail to load after the change; no shipped config sets them, and `config/agent.toml` loses `rag_identity_mismatch_policy` in the same change. The shape of RAG diagnostics returned to callers loses the HTTP-derived fields; they are read only inside `scripts/rag/` (UNK-04).
- **Consumer scan** (`tools/scan_change_consumers.py --seed rag_query_service_url --seed rag_auth_token --seed rag_identity_mismatch_policy --seed HttpAugment --seed call_rag_service`): reconciled with `rg` for the symbols; every consumer is a target row; `not affected`: `scripts/rag/corpus_identity.py::compute_identity`, `ensure_corpus_meta`, `CorpusIdentity` (kept), `scripts/rag/identity_gate.py::compute_local_identity` (kept), `scripts/mcp_servers/rag_pipeline/rag_pipeline_service.py` (name collision with `scripts/rag/pipeline_service.py`; unaffected), and `tools/stale_detector.py`/`tests/tools/test_stale_detector.py` (mention `rag_pipeline_service.py` in a text example only). The scan lists candidates only (text search).
- **Path B analysis** (Step 5): architecture: `PYTHONPATH=scripts uv run lint-imports` (6 contracts kept); removing modules only shrinks `rag` imports. Dependency graph: `http_augment` importer is `augment.py`; `pipeline_service` importer is `http_augment.py`; no importer outside `scripts/rag/`. Historical: churn per file was not measured (`N/A`, `git log --since=30.days -- scripts/rag/` not run for this Plan). Operational: no port or process change; rag-pipeline-mcp restarts on deploy; `ss`, `fuser`, and `pip-audit` not run (no dependency or lock change). Persisted schema check: not applicable (no DDL).
- **Validation quality baseline**: `vulture scripts/ --min-confidence 80` reports findings only in `scripts/rag/db_connection.py`, `scripts/rag/ingestion/document_manager.py`, and `scripts/shared/runtime_paths.py`, none in the HTTP path; `bandit` baseline: 3 High pre-existing in `scripts/eventbus`; `radon` and diff-cover: `N/A: no code diff yet`; implementation raises diff coverage to the `rules/toolchain.md` threshold.
- **Path classification**: Path B (more than 3 files; changes a runtime interface and configuration).

## Implementation steps
1. **Phase 1: Remove the HTTP delegation path and its tests**
   - [ ] Delete `scripts/rag/http_augment.py`, `scripts/rag/pipeline_service.py`, `tests/rag/test_rag_http_mode.py`, `tests/rag/test_pipeline_http_result_kind.py`, `tests/rag/test_rag_pipeline_service.py`; remove the HTTP branch and state from `scripts/rag/augment.py` and `scripts/rag/pipeline.py`; remove the HTTP diagnostics and result fields from `scripts/rag/diagnostics.py` and `scripts/rag/models_result.py`; trim `tests/rag/test_augment_refiner.py`, `tests/rag/test_augment_integration.py`, `tests/rag/test_diagnostics.py`; reword the docstrings in `scripts/rag/llm_client.py` and `scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py` (REQ-001).
2. **Phase 2: Remove the fallback identity gate**
   - [ ] Remove `_identity_gate`, `GateDecision`, `_safe_corpus_id` from `scripts/rag/identity_gate.py`, `parse_remote_identity` from `scripts/rag/corpus_identity.py`, the gate block from `scripts/rag/pipeline.py`, and the gate tests from `tests/rag/test_identity_gate.py` (REQ-002). Phases 1 and 2 form one release unit.
3. **Phase 3: Remove the configuration keys**
   - [ ] Remove the three keys from `scripts/rag/models_config.py`, `scripts/rag/config_resolution.py`, `scripts/shared/types.py`, `scripts/agent/production_config_validator.py`, `scripts/mcp_servers/rag_pipeline/rag_pipeline_models.py`, `config/agent.toml`, `config/rag_pipeline_mcp_server.toml`; update every config fixture and add the removed-key rejection tests in `tests/rag/test_config_resolution.py`, `tests/agent/test_production_config_validator.py`, `tests/mcp_servers/rag_pipeline/test_rag_pipeline_models.py` and the other fixture files of the target table (REQ-003).
4. **Phase 4: ADRs and documents (after the maintainer's statement for the ADR rows)**
   - [ ] Update the RAG, agent, MCP, and governance documents, `config/adr_authority.toml`, `registry/manifests/invariant_coverage.yaml`, and `governance_03` NC-42..44 (REQ-005); mark ADR-010 Withdrawn and amend ADR-004 Group 10 with pending approval records, and complete them only after the maintainer states the decision (REQ-004).
5. **Phase 5: Deployment and verification**
   - [ ] Run the full validation sequence in `rules/toolchain.md`; after the change is committed and pushed (the user's decision), hand off to `skills/deploy/SKILL.md` because `scripts/` and `config/` changed, noting UNK-01 (REQ-006; `config/agent.toml`, `config/rag_pipeline_mcp_server.toml`).

### Release units
**Unit**: http-path-and-gate | **Phases**: 1, 2 | **Reason**: the identity gate in `scripts/rag/pipeline.py` is fed by the HTTP branch and shares its code block; removing the branch without the gate (or the reverse) leaves unreachable or broken references.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/rag/`, `scripts/mcp_servers/rag_pipeline/` | Unit and integration | `uv run pytest tests/rag tests/mcp_servers/rag_pipeline tests/agent -v` | All pass |
| Config rejection | Unit | the three rejection tests listed under Tests | Removed keys rejected |
| Whole repository | Full validation sequence | `rules/toolchain.md`: ruff format/check, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`, `PYTHONPATH=scripts uv run lint-imports`, bandit, full `uv run pytest`, `tests/mcp_servers/mdq/test_mdq_rag_boundary.py` | No new findings; all pass |
| Impact radius | Search | `rg -l 'HttpAugment|call_rag_service|rag_query_service_url' tests/ scripts/` before deletion; AC-01..03 greps after | Every hit reviewed; none remain |
| Compat shims | Repository check | `uv run python tools/check_compat_shims.py` | Passes |
| ADR and docs | Documentation checks | `check_adr_authority.py`, `check_adr_invariant_matrix.py`, `check_adr_structure.py`, `generate_adr_authority.py --check`, `check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py --strict`, `check_docs_consistency.py --domain rag|mcp|agent`, `check_needs_confirmation_inventory.py`, `check_adr_preservation.py` (an ERROR on the maintainer-approved ADR-004 amendment is the intended change) | Pass, with the recorded exception |
| Diff coverage | Coverage | `rules/toolchain.md` section 7 sequence | At or above the Completion checklist threshold |

## Risks
- **Risk**: A deployed environment still sets one of the removed keys, so a service refuses to start after deploy → **Mitigation**: UNK-01 confirmation before deploy; the change is reverted with `git revert` if needed.
- **Risk**: Removing diagnostics fields breaks a consumer that reads them dynamically → **Mitigation**: UNK-04 re-check in Phase 1; Phase 1 tests and the full suite.
- **Risk**: The ADR amendment is written before or without the maintainer's approval → **Mitigation**: Phase 4 gate; records stay marked pending; no text is invented (Issue instruction).
- **Risk**: `check_adr_preservation.py` reports an ERROR on the ADR-004 Group 10 amendment → **Mitigation**: the amendment is the approved intent; record the finding in the report.
- **Risk**: Removal of 20 test fixtures' keys hides a gap in remaining RAG coverage → **Mitigation**: surviving in-process tests are listed in Tests; coverage is checked with diff-cover.
- **Risk**: Removing the gate loses the only consumer of corpus identity comparison and leaves dead code in `corpus_identity.py` → **Mitigation**: REQ-002 keeps only members with a named consumer; `vulture` is rerun after Phase 2.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove the HTTP delegation path and its tests | Pending | — | — | |
| 2 | Remove the fallback identity gate | Pending | — | — | |
| 3 | Remove the configuration keys | Pending | — | — | |
| 4 | ADRs and documents (after the maintainer's statement for the ADR rows) | Pending | — | — | |
| 5 | Deployment and verification | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261109-112608_adrrev003_rag-http-delegation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261110-092546
- **Related target files**: `scripts/rag/http_augment.py`, `scripts/rag/pipeline_service.py`, `scripts/rag/augment.py`, `scripts/rag/pipeline.py`, `scripts/rag/identity_gate.py`, `scripts/rag/corpus_identity.py`, `scripts/rag/diagnostics.py`, `scripts/rag/models_result.py`, `scripts/rag/models_config.py`, `scripts/rag/config_resolution.py`, `scripts/rag/llm_client.py`, `scripts/shared/types.py`, `scripts/agent/production_config_validator.py`, `scripts/mcp_servers/rag_pipeline/rag_pipeline_models.py`, `scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py`, `config/agent.toml`, `config/rag_pipeline_mcp_server.toml`, `config/adr_authority.toml`, `registry/manifests/invariant_coverage.yaml`, `tests/rag/test_rag_http_mode.py`, `tests/rag/test_pipeline_http_result_kind.py`, `tests/rag/test_rag_pipeline_service.py`, `tests/rag/test_augment_refiner.py`, `tests/rag/test_augment_integration.py`, `tests/rag/test_identity_gate.py`, `tests/rag/test_config_resolution.py`, `tests/rag/test_diagnostics.py`, `tests/rag/test_rag_pipeline.py`, `tests/rag/test_rag_pipeline_no_cache_freshness.py`, `tests/rag/test_rag_pipeline_stage.py`, `tests/rag/test_rag_quality_regression.py`, `tests/rag/test_stage_lifecycle.py`, `tests/rag/test_stage_observability.py`, `tests/rag/test_llm_client_timeout.py`, `tests/agent/commands/test_agent_rag.py`, `tests/agent/test_rag_get_cfg.py`, `tests/agent/test_production_config_validator.py`, `tests/mcp_servers/rag_pipeline/test_rag_pipeline_models.py`, `tests/mcp_servers/rag_pipeline/test_rag_pipeline_mcp_service.py`, `tests/mcp_servers/rag_pipeline/test_rag_security_validation.py`, `docs/10_adr/adr_02_06_010_rag-fallback.md`, `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md`, `docs/10_adr/adr_01_index.md`, `docs/10_adr/adr_00_document-guide.md`, `docs/10_adr/adr_02_07_016_adr-authority-model.md`, `docs/00_governance/governance_03_issue-and-uncertainty-management.md`, `docs/00_governance/governance_05_change-impact-and-dependency-graphs.md`, `docs/21_rag/rag_05_01-configuration-reference.md`, `docs/21_rag/rag_05_07-rag-index-consistency-checks.md`, `docs/21_rag/rag_00_document-guide.md`, `docs/21_rag/rag_01_system_overview.md`, `docs/21_rag/rag_03_01_query_pipeline-overview.md`, `docs/21_rag/rag_03_02_query_pipeline-rag-pipeline-class.md`, `docs/21_rag/rag_03_03_query_pipeline-context-and-diagnostics.md`, `docs/21_rag/rag_03_05_query_pipeline-augment-stages.md`, `docs/21_rag/rag_03_06_query_pipeline-helpers-and-cache.md`, `docs/21_rag/rag_04_dto-models-types.md`, `docs/21_rag/rag_05_04-error-handling-reference.md`, `docs/22_mcp/mcp_04_03_rag-pipeline-and-cicd.md`, `docs/23_agent/agent_10_06_operations-and-observability-rag-diagnostics-and-memory.md`, `docs/23_agent/agent_09_02_data-layer-access-patterns.md`

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes / repository evidence | `scripts/rag/http_augment.py` | 1 | AC-01 | `tests/rag/test_rag_http_mode.py` (deleted) | Confirmed by repository evidence |
| REQ-001 | Required Changes / repository evidence | `scripts/rag/pipeline_service.py` | 1 | AC-01 | `tests/rag/test_rag_pipeline_service.py` (deleted) | Confirmed by repository evidence |
| REQ-001 | Required Changes / repository evidence | `scripts/rag/augment.py` | 1 | AC-01 | `tests/rag/test_augment_refiner.py`, `tests/rag/test_augment_integration.py` | Confirmed by repository evidence |
| REQ-002 | Required Changes / repository evidence | `scripts/rag/augment.py` | 1 | AC-02 | `tests/rag/test_augment_refiner.py`, `tests/rag/test_augment_integration.py` | Confirmed by repository evidence |
| REQ-001 | Required Changes / repository evidence | `scripts/rag/pipeline.py` | 1, 2 | AC-01 | `tests/rag/test_rag_pipeline.py`, `tests/rag/test_rag_pipeline_no_cache_freshness.py` | Confirmed by repository evidence |
| REQ-002 | Required Changes / repository evidence | `scripts/rag/pipeline.py` | 1, 2 | AC-02 | `tests/rag/test_rag_pipeline.py`, `tests/rag/test_rag_pipeline_no_cache_freshness.py` | Confirmed by repository evidence |
| REQ-002 | Required Changes / repository evidence | `scripts/rag/identity_gate.py` | 2 | AC-02 | `tests/rag/test_identity_gate.py` | Confirmed by repository evidence |
| REQ-002 | Required Changes / repository evidence | `scripts/rag/corpus_identity.py` | 2 | AC-02 | `tests/rag/test_identity_gate.py` | Confirmed by repository evidence |
| REQ-001 | Required Changes / repository evidence | `scripts/rag/diagnostics.py` | 1 | AC-01 | `tests/rag/test_diagnostics.py` | Confirmed by repository evidence |
| REQ-001 | Required Changes / repository evidence | `scripts/rag/models_result.py` | 1, 2 | AC-01 | `tests/rag/test_diagnostics.py` | Confirmed by repository evidence |
| REQ-002 | Required Changes / repository evidence | `scripts/rag/models_result.py` | 1, 2 | AC-02 | `tests/rag/test_diagnostics.py` | Confirmed by repository evidence |
| REQ-003 | Required Changes / repository evidence | `scripts/rag/models_config.py` | 3 | AC-03 | `tests/rag/test_config_resolution.py` | Confirmed by repository evidence |
| REQ-003 | Required Changes / repository evidence | `scripts/rag/config_resolution.py` | 3 | AC-03 | `tests/rag/test_config_resolution.py` | Confirmed by repository evidence |
| REQ-001 | Required Changes / repository evidence | `scripts/rag/llm_client.py` | 1 | AC-01 | `tests/rag/test_llm_client_timeout.py` | Confirmed by repository evidence |
| REQ-003 | Required Changes / repository evidence | `scripts/shared/types.py` | 3 | AC-03 | `tests/agent/test_rag_get_cfg.py` | Confirmed by repository evidence |
| REQ-003 | Required Changes / repository evidence | `scripts/agent/production_config_validator.py` | 3 | AC-03 | `tests/agent/test_production_config_validator.py` | Confirmed by repository evidence |
| REQ-003 | Required Changes / repository evidence | `scripts/mcp_servers/rag_pipeline/rag_pipeline_models.py` | 3 | AC-03 | `tests/mcp_servers/rag_pipeline/test_rag_pipeline_models.py` | Confirmed by repository evidence |
| REQ-001 | Required Changes / repository evidence | `scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py` | 3 | AC-01 | `tests/mcp_servers/rag_pipeline/test_rag_pipeline_mcp_service.py` | Confirmed by repository evidence |
| REQ-003 | Required Changes / repository evidence | `config/agent.toml` | 3 | AC-03 | `tests/agent/test_production_config_validator.py` | Confirmed by repository evidence |
| REQ-003 | Required Changes / repository evidence | `config/rag_pipeline_mcp_server.toml` | 3 | AC-03 | `tests/mcp_servers/rag_pipeline/test_rag_pipeline_models.py` | Confirmed by repository evidence |
| REQ-005 | Required Changes / repository evidence | `config/adr_authority.toml` | 4 | AC-05 | `uv run python tools/check_adr_authority.py` | Confirmed by repository evidence |
| REQ-005 | Required Changes / repository evidence | `registry/manifests/invariant_coverage.yaml` | 4 | AC-05 | `uv run python tools/check_adr_invariant_matrix.py` | Confirmed by repository evidence |
| REQ-001 | Required Changes / repository evidence | `tests/rag/test_rag_http_mode.py` | 1 | AC-01 | N/A: deleted with its subject | Confirmed by repository evidence |
| REQ-001 | Required Changes / repository evidence | `tests/rag/test_pipeline_http_result_kind.py` | 1 | AC-01 | N/A: deleted with its subject | Confirmed by repository evidence |
| REQ-001 | Required Changes / repository evidence | `tests/rag/test_rag_pipeline_service.py` | 1 | AC-01 | N/A: deleted with its subject | Confirmed by repository evidence |
| REQ-001 | Required Changes / repository evidence | `tests/rag/test_augment_refiner.py` | 1 | AC-01 | `uv run pytest tests/rag/test_augment_refiner.py -v` | Confirmed by repository evidence |
| REQ-001 | Required Changes / repository evidence | `tests/rag/test_augment_integration.py` | 1 | AC-01 | `uv run pytest tests/rag/test_augment_integration.py -v` | Confirmed by repository evidence |
| REQ-002 | Required Changes / repository evidence | `tests/rag/test_identity_gate.py` | 2 | AC-02 | `uv run pytest tests/rag/test_identity_gate.py -v` | Confirmed by repository evidence |
| REQ-003 | Required Changes / repository evidence | `tests/rag/test_config_resolution.py` | 3 | AC-03 | `uv run pytest tests/rag/test_config_resolution.py -v` | Confirmed by repository evidence |
| REQ-001 | Required Changes / repository evidence | `tests/rag/test_diagnostics.py` | 1 | AC-01 | `uv run pytest tests/rag/test_diagnostics.py -v` | Confirmed by repository evidence |
| REQ-003 | Required Changes / repository evidence | `tests/rag/test_rag_pipeline.py` | 1, 3 | AC-03 | `uv run pytest tests/rag/test_rag_pipeline.py -v` | Confirmed by repository evidence |
| REQ-003 | Required Changes / repository evidence | `tests/rag/test_rag_pipeline_no_cache_freshness.py` | 1, 3 | AC-03 | `uv run pytest tests/rag/test_rag_pipeline_no_cache_freshness.py -v` | Confirmed by repository evidence |
| REQ-003 | Required Changes / repository evidence | `tests/rag/test_rag_pipeline_stage.py` | 1, 3 | AC-03 | `uv run pytest tests/rag/test_rag_pipeline_stage.py -v` | Confirmed by repository evidence |
| REQ-003 | Required Changes / repository evidence | `tests/rag/test_rag_quality_regression.py` | 1, 3 | AC-03 | `uv run pytest tests/rag/test_rag_quality_regression.py -v` | Confirmed by repository evidence |
| REQ-003 | Required Changes / repository evidence | `tests/rag/test_stage_lifecycle.py` | 1, 3 | AC-03 | `uv run pytest tests/rag/test_stage_lifecycle.py -v` | Confirmed by repository evidence |
| REQ-003 | Required Changes / repository evidence | `tests/rag/test_stage_observability.py` | 1, 3 | AC-03 | `uv run pytest tests/rag/test_stage_observability.py -v` | Confirmed by repository evidence |
| REQ-003 | Required Changes / repository evidence | `tests/rag/test_llm_client_timeout.py` | 1, 3 | AC-03 | `uv run pytest tests/rag/test_llm_client_timeout.py -v` | Confirmed by repository evidence |
| REQ-003 | Required Changes / repository evidence | `tests/agent/commands/test_agent_rag.py` | 3 | AC-03 | `uv run pytest tests/agent/commands/test_agent_rag.py -v` | Confirmed by repository evidence |
| REQ-003 | Required Changes / repository evidence | `tests/agent/test_rag_get_cfg.py` | 3 | AC-03 | `uv run pytest tests/agent/test_rag_get_cfg.py -v` | Confirmed by repository evidence |
| REQ-003 | Required Changes / repository evidence | `tests/agent/test_production_config_validator.py` | 3 | AC-03 | `uv run pytest tests/agent/test_production_config_validator.py -v` | Confirmed by repository evidence |
| REQ-003 | Required Changes / repository evidence | `tests/mcp_servers/rag_pipeline/test_rag_pipeline_models.py` | 3 | AC-03 | `uv run pytest tests/mcp_servers/rag_pipeline/test_rag_pipeline_models.py -v` | Confirmed by repository evidence |
| REQ-003 | Required Changes / repository evidence | `tests/mcp_servers/rag_pipeline/test_rag_pipeline_mcp_service.py` | 3 | AC-03 | `uv run pytest tests/mcp_servers/rag_pipeline/test_rag_pipeline_mcp_service.py -v` | Confirmed by repository evidence |
| REQ-003 | Required Changes / repository evidence | `tests/mcp_servers/rag_pipeline/test_rag_security_validation.py` | 3 | AC-03 | `uv run pytest tests/mcp_servers/rag_pipeline/test_rag_security_validation.py -v` | Confirmed by repository evidence |
| REQ-004 | Required Changes / repository evidence | `docs/10_adr/adr_02_06_010_rag-fallback.md` | 4 | AC-04 | `check_adr_structure.py`, `check_adr_authority.py` | Confirmed by repository evidence |
| REQ-004 | Required Changes / repository evidence | `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md` | 4 | AC-04 | `check_adr_preservation.py` (expected ERROR on the amended decision; the maintainer-approved amendment is the intended change) | Confirmed by repository evidence |
| REQ-005 | Required Changes / repository evidence | `docs/10_adr/adr_01_index.md` | 4 | AC-05 | `uv run python tools/generate_adr_authority.py --check` | Confirmed by repository evidence |
| REQ-005 | Required Changes / repository evidence | `docs/10_adr/adr_00_document-guide.md` | 4 | AC-05 | `uv run python tools/check_docs_structure.py` | Confirmed by repository evidence |
| REQ-005 | Required Changes / repository evidence | `docs/10_adr/adr_02_07_016_adr-authority-model.md` | 4 | AC-05 | `uv run python tools/check_adr_authority.py` | Confirmed by repository evidence |
| REQ-005 | Required Changes / repository evidence | `docs/00_governance/governance_03_issue-and-uncertainty-management.md` | 4 | AC-05 | `uv run python tools/check_needs_confirmation_inventory.py` | Confirmed by repository evidence |
| REQ-005 | Required Changes / repository evidence | `docs/00_governance/governance_05_change-impact-and-dependency-graphs.md` | 4 | AC-05 | `uv run python tools/check_docs_quality.py` | Confirmed by repository evidence |
| REQ-005 | Required Changes / repository evidence | `docs/21_rag/rag_05_01-configuration-reference.md` | 4 | AC-05 | `uv run python tools/check_docs_consistency.py --domain rag` | Confirmed by repository evidence |
| REQ-005 | Required Changes / repository evidence | `docs/21_rag/rag_05_07-rag-index-consistency-checks.md` | 4 | AC-05 | `uv run python tools/check_docs_consistency.py --domain rag` | Confirmed by repository evidence |
| REQ-005 | Required Changes / repository evidence | `docs/21_rag/rag_00_document-guide.md` | 4 | AC-05 | `uv run python tools/check_docs_consistency.py --domain rag` | Confirmed by repository evidence |
| REQ-005 | Required Changes / repository evidence | `docs/21_rag/rag_01_system_overview.md` | 4 | AC-05 | `uv run python tools/check_docs_consistency.py --domain rag` | Confirmed by repository evidence |
| REQ-005 | Required Changes / repository evidence | `docs/21_rag/rag_03_01_query_pipeline-overview.md` | 4 | AC-05 | `uv run python tools/check_docs_consistency.py --domain rag` | Confirmed by repository evidence |
| REQ-005 | Required Changes / repository evidence | `docs/21_rag/rag_03_02_query_pipeline-rag-pipeline-class.md` | 4 | AC-05 | `uv run python tools/check_docs_consistency.py --domain rag` | Confirmed by repository evidence |
| REQ-005 | Required Changes / repository evidence | `docs/21_rag/rag_03_03_query_pipeline-context-and-diagnostics.md` | 4 | AC-05 | `uv run python tools/check_docs_consistency.py --domain rag` | Confirmed by repository evidence |
| REQ-005 | Required Changes / repository evidence | `docs/21_rag/rag_03_05_query_pipeline-augment-stages.md` | 4 | AC-05 | `uv run python tools/check_docs_consistency.py --domain rag` | Confirmed by repository evidence |
| REQ-005 | Required Changes / repository evidence | `docs/21_rag/rag_03_06_query_pipeline-helpers-and-cache.md` | 4 | AC-05 | `uv run python tools/check_docs_consistency.py --domain rag` | Confirmed by repository evidence |
| REQ-005 | Required Changes / repository evidence | `docs/21_rag/rag_04_dto-models-types.md` | 4 | AC-05 | `uv run python tools/check_docs_consistency.py --domain rag` | Confirmed by repository evidence |
| REQ-005 | Required Changes / repository evidence | `docs/21_rag/rag_05_04-error-handling-reference.md` | 4 | AC-05 | `uv run python tools/check_docs_consistency.py --domain rag` | Confirmed by repository evidence |
| REQ-005 | Required Changes / repository evidence | `docs/22_mcp/mcp_04_03_rag-pipeline-and-cicd.md` | 4 | AC-05 | `uv run python tools/check_docs_consistency.py --domain mcp` | Confirmed by repository evidence |
| REQ-005 | Required Changes / repository evidence | `docs/23_agent/agent_10_06_operations-and-observability-rag-diagnostics-and-memory.md` | 4 | AC-05 | `uv run python tools/check_docs_consistency.py --domain agent` | Confirmed by repository evidence |
| REQ-005 | Required Changes / repository evidence | `docs/23_agent/agent_09_02_data-layer-access-patterns.md` | 4 | AC-05 | `uv run python tools/check_docs_consistency.py --domain agent` | Confirmed by repository evidence |
