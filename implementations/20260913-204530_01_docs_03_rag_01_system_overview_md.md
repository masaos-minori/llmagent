## Goal

Add a concise inline summary of `rag_pipeline_server.py`, `rag_pipeline_service.py`, and `scripts/rag/pipeline.py` responsibilities to the MCP Server Responsibility Division section of `docs/03_rag_01_system_overview.md`, per REQ-001 through REQ-005.

## Scope

- In-Scope: Adding a brief responsibility summary to `docs/03_rag_01_system_overview.md`; preserving the existing cross-reference as supplementary detail
- Out-of-Scope: Modifying any source code files; modifying `docs/03_rag_03_01_query_pipeline-overview.md`; changing the existing cross-reference link

## Assumptions

- The existing cross-reference to `docs/03_rag_03_01_query_pipeline-overview.md` is accurate and should be preserved as supplementary detail
- The three components listed in the issue (`rag_pipeline_server.py`, `rag_pipeline_service.py`, `scripts/rag/pipeline.py`) remain the correct set of components to summarize
- A concise inline summary (approximately 3-5 sentences total) is sufficient — exhaustive detail belongs in the referenced document

## Design decisions

1. Extract responsibility summaries directly from source code evidence, not from the existing cross-referenced document.
2. Keep the summary concise — approximately 3-5 sentences total — since the detailed breakdown already exists in `docs/03_rag_03_01_query_pipeline-overview.md`.
3. Preserve the existing cross-reference as supplementary detail rather than replacing it.
4. Use the same terminology as the source code (e.g., "HTTP route handling" for `rag_pipeline_server.py`, not "MCP endpoint management").

Evidence grounding:
- `rag_pipeline_server.py`: FastAPI app with HTTP endpoints (`/v1/call_tool`, `/health`, `/rag_run_pipeline`, etc.), tool list building, exception handling for `RagPipelineServiceError`
- `rag_pipeline_service.py`: `RagPipelineMCPService` class wrapping `RagPipeline`, lifecycle management (start/stop), result formatting for MCP tool responses, dispatch table
- `pipeline.py`: `RagPipeline` class orchestrating MQE → Search → RRF → Rerank stages, `augment()` method with fallback chain, diagnostics collection

## Alternatives considered

- **Replace cross-reference entirely**: Rejected because the existing cross-reference provides access to detailed breakdowns that would be too verbose for an overview document.
- **Expand into a separate subsection**: Rejected because the Plan scope limits changes to adding inline text within the existing section.

## Implementation
### Target file
`docs/03_rag_01_system_overview.md`

### Procedure
1. Verify the exact wording of the existing cross-reference in line 136
2. Write concise responsibility summary for each of the three components
3. Add caller → callee flow description between the three components
4. Preserve the existing cross-reference as supplementary detail after the inline summary

### Method
Inline text addition within the existing MCP Server Responsibility Division section.

### Details
1. **Phase 1: Preparation — Confirm current state**
   a. Locate the MCP Server Responsibility Division section at line 134-136 in `docs/03_rag_01_system_overview.md`
   b. Record the exact wording of the existing cross-reference sentence
   
2. **Phase 2: Core Implementation**
   a. After the existing cross-reference sentence, add a paragraph summarizing each component's responsibility:
      ```markdown
      ### MCP Server Responsibility Division
      
      [Existing cross-reference sentence]
      
      For operators who prefer a quick reference without navigating away from this document, here is a concise summary of each component's role:
      
      - **`rag_pipeline_server.py`**: HTTP route handling and request/response formatting. This FastAPI application exposes MCP endpoints (`/v1/call_tool`, `/health`, `/rag_run_pipeline`, etc.), builds the tool list, and handles exceptions for `RagPipelineServiceError`.
      
      - **`rag_pipeline_service.py`**: Pipeline orchestration and error handling. The `RagPipelineMCPService` class wraps `RagPipeline`, manages lifecycle (start/stop), formats results for MCP tool responses, and maintains the dispatch table mapping tool names to service methods.
      
      - **`scripts/rag/pipeline.py`**: Core search logic and stage execution. The `RagPipeline` class orchestrates the MQE → Search → RRF → Rerank pipeline stages, implements the `augment()` method with its fallback chain (HTTP → cache → search → refiner → raw chunks), and collects diagnostics.
      
      The interaction flow is: MCP client → `rag_pipeline_server.py` (HTTP routing) → `rag_pipeline_service.py` (orchestration) → `scripts/rag/pipeline.py` (search execution).
      
      For details on responsibilities of these components, please refer to [docs/03_rag_03_01_query_pipeline-overview.md].
      ```
   
   b. Ensure the inline summary uses terminology consistent with both the source code and the existing cross-referenced document

3. **Phase 3: Verification**
   a. Confirm the summary accurately reflects the source code evidence
   b. Confirm no unintended modifications were made to other files

## Compatibility considerations

- The inline summary supplements, not replaces, the existing cross-reference — operators can still navigate to the detailed document for deeper understanding
- Terminology choices ("HTTP route handling", "pipeline orchestration", "core search logic") align with the source code's own descriptions and the existing cross-referenced document
- No behavioral change — this is documentation-only

## Security considerations

N/A: Documentation update only, no security impact.

## Rollback considerations

Simple revert of the added text — no data migration or state rollback needed.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| docs/03_rag_01_system_overview.md | Manual review against source code evidence | Read target files + compare | Summary matches actual responsibilities |

## Completion criteria

- [ ] `docs/03_rag_01_system_overview.md` MCP Server Responsibility Division section includes a concise summary of each component's responsibilities
- [ ] The caller → callee interaction flow between the three components is described
- [ ] The existing cross-reference to `docs/03_rag_03_01_query_pipeline-overview.md` is preserved
- [ ] No source code files are modified
- [ ] No other documentation files are modified except `docs/03_rag_01_system_overview.md`

## Out of scope

- Modifying `scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py` (reference file only)
- Modifying `scripts/mcp_servers/rag_pipeline/rag_pipeline_service.py` (reference file only)
- Modifying `scripts/rag/pipeline.py` (reference file only)
- Modifying `docs/03_rag_03_01_query_pipeline-overview.md` (reference file only)
- Changing the existing cross-reference link
- Exhaustive detail about each component (belongs in the referenced document)

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Verify existing cross-reference wording | Pending | — | — | Line 136 |
| 2 | Write responsibility summary for rag_pipeline_server.py | Pending | — | — | HTTP route handling |
| 3 | Write responsibility summary for rag_pipeline_service.py | Pending | — | — | Pipeline orchestration |
| 4 | Write responsibility summary for scripts/rag/pipeline.py | Pending | — | — | Core search logic |
| 5 | Add caller → callee flow description | Pending | — | — | MCP client → server → service → pipeline |
| 6 | Preserve existing cross-reference as supplementary detail | Pending | — | — | After inline summary |
| 7 | Manual review of accuracy against source code | Pending | — | — | Verify all claims |

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
- **Requirement ID**: REQ-001 through REQ-005 — add MCP Server Responsibility Division summary to RAG System Overview
- **Source issue**: issues/20260913-183046_missing_system_overview_mcp_responsibility_division.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260913-193350_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260913-204530
- **Related target files**: docs/03_rag_01_system_overview.md
