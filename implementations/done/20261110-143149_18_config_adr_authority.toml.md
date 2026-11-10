## Goal
- Remove ADR-010 from the ADR authority model (REQ-005).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: this one file, Phase 4 of the Plan.
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
`config/adr_authority.toml`

### Procedure
1. Remove the ADR-010 node and every edge whose `from` or `to` is ADR-010, and change the ADR-004 note that calls ADR-010 the sole Fallback it permits to say fallback is prohibited without exception; remove the `rag.fallback` primary-ADR entry (lines named in the Plan row).
2. Run `uv run python tools/check_adr_authority.py` after each group of edits and `uv run python tools/generate_adr_authority.py` (document 43) afterwards.

### Method
- Documentation edit in place; English only; state intent, boundaries, and failure behavior ("no fallback"); no implementation-location mappings or config values (docs content policy).

### Details
- Phase 4 starts only after the maintainer's statement for the ADR rows (Plan UNK-02); this file follows the withdrawal.

## Compatibility considerations
N/A: documentation only.

## Security considerations
N/A: documentation only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_adr_authority.py`, `uv run python tools/generate_adr_authority.py --check`.

## Completion criteria
- The authority model has no ADR-010 node or edge and the checkers pass.

## Out of Scope
- Editing any other file.
- Adding any new fallback or remote-delegation mechanism.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit `config/adr_authority.toml` as described in Procedure | Completed | 20261110-151959 | 20261110-151959 | — |
| 2 | Run the checkers listed in Validation plan | Completed | 20261110-151959 | 20261110-151959 | — |

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
- **Requirement ID**: REQ-005
- **Source issue**: issues/20261109-112608_adrrev003_rag-http-delegation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261110-092546_adrrev003_rag-http-delegation.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261110-143149
- **Related target files**: `config/adr_authority.toml`
