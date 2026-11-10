# Remove the RAG HTTP delegation path and retire ADR-010

## Priority
High

## Summary
Remove the RAG remote-delegation path (`HttpAugment`, `call_rag_service()`, and their configuration keys) so RAG is reached only through rag-pipeline-mcp over the common MCP transport, and withdraw ADR-010 with an approval record.

## Background
- Source: `memo-issue.md` item H-03, re-checked against current source on 2026-11-09. The memo states that production has zero callers; that statement is only partly confirmed (see below).
- `Explicit in code`: `scripts/rag/http_augment.py` defines `HttpAugment`; `scripts/rag/pipeline_service.py` defines `call_rag_service()` with its own request timeout constant and retry logic; `scripts/rag/augment.py` (`run_http_augment`) and `scripts/rag/pipeline.py` call them when `rag_query_service_url` is non-empty. `scripts/mcp_servers/rag_pipeline/rag_pipeline_models.py` sets the URL to an empty string for in-process use.
- `Explicit in config`: no `config/*.toml` sets `rag_query_service_url`; `config/agent.toml` sets `rag_identity_mismatch_policy`; `scripts/agent/production_config_validator.py` and `scripts/shared/types.py` reference it. `auth_token` defaults to an empty string in `call_rag_service()` and no header is sent when it is empty.
- `Explicit in code`: the Agent imports `rag.corpus_identity` (`rag_maintenance_service.py`), so the memo's "the Agent never imports `scripts/rag/`" is refuted; what remains to confirm is that the identity-mismatch gate runs only inside rag-pipeline-mcp.
- `Documentation only` (not verified against code in this review): ADR-010 defines a fallback policy and an identity-mismatch gate and still lists open "Needs confirmation" items (NC-42..NC-44); the two readings of "unverifiable" in `rag_05_01` and `rag_05_07` conflict; ADR-007 INV-02/07 say requests use the common transport and timeouts are not retried.
- Related archived issue: `rag002_rag-augment-treats-an-empty-remote-result-as-terminal-which-contradicts-the-httpaugment-docstring` under `issues/done/`. Re-verify this issue against current source.

## Problem
- A feature with no configured user (the delegation URL is unset in every shipped configuration) keeps code, tests, configuration keys, and an ADR alive.
- The identity-mismatch gate cannot be both effective and usable: a fallback happens exactly when no usable remote response exists, so the remote identity is absent; under one reading the gate never fires, under the other every fallback is rejected (`Documentation only`; `Needs confirmation` against code).
- The path bypasses the common MCP transport with its own retry logic, a hard-coded timeout, and an empty-token default, which contradicts ADR-007 and ADR-004.
- ADR-010 is Accepted but carries unresolved items and internal contradictions.

## Reason for Change
- Repairing a feature that nothing uses costs more than removing it, and removal closes a group of open review items at once.
- Timing: no external deadline; removal is a prerequisite for the RAG consistency-policy alignment issue in this batch.

## Implementation Intent
- RAG is reached only through rag-pipeline-mcp over the common MCP transport. No remote-delegation or fallback path remains.
- Remove only what the delegation path alone uses; keep `corpus_identity` and any code that rag-pipeline-mcp or the Agent's maintenance service needs.
- ADR-004 states without exception that fallback is prohibited. ADR-010 is withdrawn following the ADR process, each with an approval record.

## Target Files or Areas
- `scripts/rag/http_augment.py`, `scripts/rag/pipeline_service.py` (`call_rag_service` and its result types), `scripts/rag/augment.py`, `scripts/rag/pipeline.py`, `scripts/rag/llm_client.py` (docstring references), `scripts/rag/corpus_identity.py` (docstring), `scripts/rag/config_resolution.py`, `scripts/rag/models_config.py`
- `scripts/shared/types.py`, `scripts/agent/production_config_validator.py`, `scripts/mcp_servers/rag_pipeline/rag_pipeline_models.py`, `scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py`
- `config/agent.toml`, `config/rag_pipeline_mcp_server.toml`
- Tests: `tests/rag/test_rag_http_mode.py`, `tests/rag/test_augment_integration.py`, `tests/rag/test_pipeline_http_result_kind.py`, `tests/rag/test_rag_pipeline_service.py`, `tests/rag/test_augment_refiner.py`, `tests/mcp_servers/rag_pipeline/test_rag_pipeline_models.py`
- Docs: ADR-010 (`docs/10_adr/adr_02_06_010_rag-fallback.md`), ADR-004 (`docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md`), `docs/10_adr/adr_01_index.md`, `docs/21_rag/rag_05_01-configuration-reference.md`, `docs/21_rag/rag_05_07-rag-index-consistency-checks.md`, `docs/00_governance/governance_03_issue-and-uncertainty-management.md`

## Required Changes
- Delete `HttpAugment`, `call_rag_service()`, and the HTTP branch of the pipeline and augment refiner, together with their tests.
- Remove `rag_query_service_url`, `rag_identity_mismatch_policy`, `rag_auth_token`, and any other key used only by this path from code, configs, validators, and `rag_05_01`.
- Mark ADR-010 Withdrawn following the ADR process and add an approval record.
- Amend ADR-004 Decision Group 10 to "fallback is prohibited without exception" and add an approval record.
- Remove the identity gate and the "unverifiable" state from `rag_05_07`.
- Close NC-42, NC-43, and NC-44 in `governance_03`, citing this issue.
- Update `adr_01_index.md` (status, verification matrix, reference graph) and remove ADR-010 edges from other ADRs.

## Constraints
- Config load must reject the removed keys as unknown (no compatibility shim; see `tools/check_compat_shims.py`).
- The ADR approval process and `docs/10_adr` checkers apply; the approval record is a maintainer statement and must not be fabricated by the implementer (see `Unresolved Questions`).
- Run the impact-radius check from `rules/toolchain.md` for `HttpAugment`, `call_rag_service`, and the config keys before deleting.
- `scripts/rag/` and `scripts/agent/` import-layer rules (`.importlinter`) must stay satisfied.

## Acceptance Criteria
- No code, config, or document references the removed symbols, keys, or ADR-010 invariants (`rg` over `scripts/ tests/ config/ docs/` returns none, apart from the Withdrawn ADR-010 record itself).
- Config load rejects the removed keys.
- The documentation checks pass with no dangling references: `check_adr_authority.py`, `check_adr_invariant_matrix.py`, `check_adr_structure.py`, `check_docs_consistency.py --domain rag`, `check_needs_confirmation_inventory.py`.
- The RAG in-process pipeline and rag-pipeline-mcp tests still pass.

## Testing Expectations
- `uv run pytest tests/rag tests/mcp_servers/rag_pipeline tests/agent -v`, then the standard validation sequence including `tests/mcp_servers/mdq/test_mdq_rag_boundary.py`.
- Add a test that the removed keys are rejected at config load.
- Documentation checkers listed above.

## Documentation Impact
- ADR-010 status, ADR-004 Decision Group 10, the ADR index, `rag_05_01`, `rag_05_07`, and `governance_03` must change; state intent, failure behavior ("no fallback"), and the closed Needs Confirmation items. Do not add implementation-location mappings or config values.

## Out of Scope
- Aligning the consistency-check severity policy across ADR-005, ADR-009, `db_07`, and `security_01` (separate issue in this batch).
- Adding any new fallback or remote-delegation mechanism.

## Dependencies
- Depends on: none.
- Blocks: `issues/20261109-113123_adrrev013_rag-consistency-policy.md` (RAG consistency-policy alignment).
- Related, recently archived: `rag002_rag-augment-treats-an-empty-remote-result-as-terminal-which-contradicts-the-httpaugment-docstring` under `issues/done/`.

## Unresolved Questions
- `Needs confirmation`: does any deployment (including `/opt/llm` configuration outside the repository) set `rag_query_service_url`? Repository configs do not. If one does, stop and report.
- `Needs confirmation`: does anything outside `scripts/rag/` use `rag_identity_mismatch_policy` at runtime (it is validated in `production_config_validator.py`)?
- The approval record for withdrawing ADR-010 and amending ADR-004 requires a maintainer; the implementer records the decision only after the maintainer states it.

## AI Implementation Instruction
- Keep changes limited to the delegation path; do not remove `corpus_identity` or code used by rag-pipeline-mcp.
- Verify each symbol's callers with `rg` before deleting; stop and report if a production caller is found.
- Do not write an approval record on a maintainer's behalf; leave a clearly marked pending record and report it.
- Write documentation in English, follow the docs content policy, and do not commit.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261109-112608
- **Related target files**: `scripts/rag/http_augment.py`, `scripts/rag/pipeline_service.py`, `scripts/rag/augment.py`, `scripts/rag/pipeline.py`, `scripts/shared/types.py`, `scripts/agent/production_config_validator.py`, `config/agent.toml`, `config/rag_pipeline_mcp_server.toml`, `docs/10_adr/adr_02_06_010_rag-fallback.md`, `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md`, `docs/10_adr/adr_01_index.md`, `docs/21_rag/rag_05_01-configuration-reference.md`, `docs/21_rag/rag_05_07-rag-index-consistency-checks.md`, `docs/00_governance/governance_03_issue-and-uncertainty-management.md`
