## Goal
- Remove `rag_auth_token` and the loop guard `rag_query_service_url` from the rag-pipeline-mcp config (REQ-003).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: this one file, Phase 3 of the Plan.
- Not in scope: any other file; a second file needed here is an additional-target discovery.
- Execution order follows the Plan's phases, not `seq`: Phases 1 and 2 are one release unit (HTTP path and identity gate: documents 01-08, 11, 15, 21, 25, 27, 59 with their companions); Phase 3 (configuration keys: documents 09, 10, 12, 13, 14, 16, 17, 61 and the fixture tests 26, 30-33, 35, 37, 38, 40); Phase 4 (ADRs and documents: 18, 19, 41-58, 60).

## Assumptions
- Overlap with plan 004 (`config/agent.toml`, `scripts/agent/production_config_validator.py`, `tests/agent/test_production_config_validator.py`, ADR-004) and plan 006 (`adr_01_index.md`): different keys or sections (judged in the Plan); no contradiction on this file.
- The Plan's Step 3a corrections apply (removed-key rejection is implemented once in `RagConfigValidator`; the gate block of `RagPipeline.augment()` keeps recording `_last_corpus_generation`; `rag_pipeline_service_url` belongs to the ingester and stays).

## Design decisions
- Remove only what the delegation path alone uses; keep `compute_local_identity`, `CorpusIdentity`, `ensure_corpus_meta`, `compute_identity`, and the refiner.

## Alternatives considered
N/A: RAG is reached only through rag-pipeline-mcp over the common MCP transport (Issue Implementation Intent); no remote-delegation or fallback path remains.

## Implementation
### Target file
`scripts/mcp_servers/rag_pipeline/rag_pipeline_models.py`

### Procedure
1. Delete the `rag_auth_token` field and its `from_dict` read, the `rag_auth_token_present` entry and the sentence about both tokens in `non_secret_view`, and the `rag_query_service_url` and `rag_auth_token` lines of `build_rag_cfg_adapter`; keep `auth_token` (the server's inbound token).
2. Do not add key rejection here: `RagPipelineConfig.load()` already runs `RagConfigValidator` on the raw config (document 61).

### Method
- Targeted edits; remove imports left unused as `ruff` reports them.

### Details
- The posture fingerprint view (`non_secret_view`) loses one presence boolean; `tests/mcp_servers/rag_pipeline/test_rag_security_validation.py` asserts on it (document 40).
- `scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py` computes the posture from this view; no other consumer reads `rag_auth_token_present`.

## Compatibility considerations
- The posture fingerprint of rag-pipeline-mcp changes once (one presence key fewer), which is expected after deploy.

## Security considerations
- Removes an outbound-token path and an empty-token default; no authentication or authorization behavior of the MCP server changes.

## Rollback considerations
- Revert the phase's commit; Phases 1 and 2 are one release unit and revert together.

## Validation plan
- `uv run pytest tests/mcp_servers/rag_pipeline -v`.
- `uv run ruff check scripts/ tests/ tools/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`, `PYTHONPATH=scripts uv run lint-imports`.

## Completion criteria
- No `rag_auth_token` or `rag_query_service_url` remains in the module.

## Out of Scope
- Editing any other file.
- Adding any new fallback or remote-delegation mechanism.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change in `scripts/mcp_servers/rag_pipeline/rag_pipeline_models.py` | Completed | 20261110-151959 | 20261110-151959 | — |
| 2 | Add or update tests per Validation plan | Completed | 20261110-151959 | 20261110-151959 | — |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261110-151959 | 20261110-151959 | — |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-003
- **Source issue**: issues/20261109-112608_adrrev003_rag-http-delegation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261110-092546_adrrev003_rag-http-delegation.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261110-143149
- **Related target files**: `scripts/mcp_servers/rag_pipeline/rag_pipeline_models.py`
