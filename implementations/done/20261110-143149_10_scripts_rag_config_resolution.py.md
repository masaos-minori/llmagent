## Goal
- Remove the three keys from the RAG config schema (REQ-003).

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
`scripts/rag/config_resolution.py`

### Procedure
1. Delete the three names from the known-field set and from `_DEFAULTS_FOR_ALL`; do not touch `rag_pipeline_service_url`.
2. Step 3a correction: `resolve_rag_config` validated the dict that `_apply_defaults` had already filtered, so a removed key never reached `RagConfigValidator`. Validate the raw layered dict (`raw_cfg`) instead, so document 61's rejection applies on this load path too.

### Method
- Targeted edits; remove imports left unused as `ruff` reports them.

### Details
- Step 3a found that `resolve_rag_config` ran `RagConfigValidator().validate(filtered_cfg)` after `_apply_defaults` (corrected in this document; the Agent and rag-pipeline-mcp paths already validate the raw dict).

## Compatibility considerations
- The removal is intentional and has no shim (`tools/check_compat_shims.py`).

## Security considerations
- Removes an outbound-token path and an empty-token default; no authentication or authorization behavior of the MCP server changes.

## Rollback considerations
- Revert the phase's commit; Phases 1 and 2 are one release unit and revert together.

## Validation plan
- `uv run pytest tests/rag/test_config_resolution.py -v` (document 26).
- `uv run ruff check scripts/ tests/ tools/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`, `PYTHONPATH=scripts uv run lint-imports`.

## Completion criteria
- The schema and defaults carry none of the three keys.

## Out of Scope
- Editing any other file.
- Adding any new fallback or remote-delegation mechanism.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change in `scripts/rag/config_resolution.py` | Completed | 20261110-151959 | 20261110-151959 | Step 3a correction: validate raw cfg in resolve_rag_config (see Details) |
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
- **Related target files**: `scripts/rag/config_resolution.py`
