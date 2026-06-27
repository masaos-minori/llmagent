## Goal

Standardize terminology across RAG docs so "3 scripts" and "4 processing phases" are consistently distinguished — use "script" for executable files, "processing phase" for logical steps, and avoid using "stage" for ingestion unless explicitly contrasted with query pipeline stages.

## Scope

**In-Scope**:
- Use "script" for executable files: `crawler.py`, `chunk_splitter.py`, `ingester.py`
- Use "processing phase" for: crawl, chunk, embed, store
- Avoid using "stage" for ingestion unless explicitly contrasted with query pipeline stages
- Update ingestion, overview, and operations docs

**Out-of-Scope**:
- Runtime behavior changes
- Query pipeline stage redesign

## Assumptions

1. The existing 3-script / 4-phase explanation should be preserved — only terminology needs standardization
2. "Stage" is reserved for query pipeline stages (MQE, Search, Fusion, Rerank, PluginHooks, Augment)

## Implementation

### Target file: docs/03_rag_01_system_overview.md

**Procedure**: Fix conflation of "stage" with "script" for ingestion.

**Method**: Modify terminology in the system overview document.

**Details**:
1. Line 79: Change "3 stages (3 scripts)" to "3 scripts" and clarify that "3 scripts ≠ 4 phases"
2. Add a brief terminology note explaining the distinction between scripts, processing phases, and query pipeline stages

### Target file: docs/03_rag_02_ingestion_pipeline.md

**Procedure**: Audit ingestion pipeline doc for ambiguous stage references.

**Method**: Search for "stage" in context of ingestion and replace with appropriate terms.

**Details**:
1. Search for any "stage" references that could be confused with query pipeline stages
2. Replace with "script" or "processing phase" as appropriate

### Target file: docs/03_rag_05_configuration_and_operations.md

**Procedure**: Audit operations doc for ambiguous stage references.

**Method**: Search for "stage" in context of ingestion and replace with appropriate terms.

**Details**:
1. Search for any "stage" references related to ingestion
2. Replace with "script" or "processing phase" as appropriate

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| 03_rag_01_system_overview.md | Verify no conflation of "stage" with "script" for ingestion | Check section 2 (Ingestion Pipeline) | Clear distinction between scripts and phases |
| 03_rag_02_ingestion_pipeline.md | Verify no ambiguous stage references for ingestion | Search for "stage" in context of ingestion | Zero ambiguous "stage" references for ingestion |
| 03_rag_05_configuration_and_operations.md | Verify no ambiguous stage references for ingestion | Search for "stage" in context of ingestion | Zero ambiguous "stage" references for ingestion |

## Risks

- **Risk**: No risks identified — this is a straightforward terminology cleanup | **Likelihood**: N/A | **Mitigation**: N/A | False
