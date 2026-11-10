## Goal
- Delete the HTTP augment stage (REQ-001: a private client of the rag-pipeline MCP server that bypasses the common transport).

## Scope
**Release unit**: http-path-and-gate

- In scope: this one file, Phase 1 of the Plan.
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
`scripts/rag/http_augment.py`

### Procedure
1. Re-run `rg -n "http_augment|HttpAugment" scripts` and confirm the only importer is `scripts/rag/augment.py` (stop and report if a production caller exists).
2. Delete `scripts/rag/http_augment.py` together with its companion test (below), after document 03 stops importing it.
3. Remove its entry `rag/http_augment.py` from `tools/check_docstrings_baseline.txt` (document 59).

### Method
- Targeted edits; remove imports left unused as `ruff` reports them.

### Details
- `HttpAugment` (line 76 of the module) and `_map_http_result_kind` are used only by `augment.py` and `pipeline.py` (checked in Step 3a).

### Companion test files
- `tests/rag/test_rag_http_mode.py`
  - Procedure: Delete the file (it tests only the HTTP delegation mode).
  - Validation: `uv run pytest tests/rag -v` passes and `rg -n "test_rag_http_mode" tests` is empty.

## Compatibility considerations
- The removal is intentional and has no shim (`tools/check_compat_shims.py`).

## Security considerations
- Removes an outbound-token path and an empty-token default; no authentication or authorization behavior of the MCP server changes.

## Rollback considerations
- Revert the phase's commit; Phases 1 and 2 are one release unit and revert together.

## Validation plan
- `rg -n "HttpAugment|http_augment" scripts tests` returns nothing after documents 03, 04, 20, 24, 59.
- `uv run ruff check scripts/ tests/ tools/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`, `PYTHONPATH=scripts uv run lint-imports`.

## Completion criteria
- The module and its test are gone and nothing imports them.

## Out of Scope
- Editing any other file.
- Adding any new fallback or remote-delegation mechanism.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Delete `scripts/rag/http_augment.py` and `tests/rag/test_rag_http_mode.py` after documents 03 and 04 drop their imports | Completed | 20261110-151959 | 20261110-151959 | — |
| 2 | Run `uv run pytest tests/rag -v` | Completed | 20261110-151959 | 20261110-151959 | — |
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
- **Requirement ID**: REQ-001
- **Source issue**: issues/20261109-112608_adrrev003_rag-http-delegation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261110-092546_adrrev003_rag-http-delegation.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261110-143149
- **Related target files**: `scripts/rag/http_augment.py`, `tests/rag/test_rag_http_mode.py`
