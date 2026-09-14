## Goal

Add a note to `docs/03_rag_01_system_overview.md` stating that external (HTTP-delegated) and local (in-process) RAG execution modes currently read the same `rag_db_path` by configuration convention — not architectural guarantee — citing both config files' `rag_db_path` values as evidence. Per REQ-001.

## Scope

- Add exactly one note (a few sentences) to the "MCP Server Responsibility Division" section of `docs/03_rag_01_system_overview.md`
- State the shared-corpus fact, cite both config files, and explicitly label it a convention rather than an enforced invariant
- Out-of-scope: adding automated divergence checks; changing any other doc

## Assumptions

- The "MCP Server Responsibility Division" section exists at line 186 of `docs/03_rag_01_system_overview.md` — confirmed via grep
- Both `config/agent.toml` (line 7) and `config/rag_pipeline_mcp_server.toml` (line 13) set `rag_db_path = "/opt/llm/db/rag.sqlite"` — confirmed via grep
- No existing mention of `rag_db_path`, corpus, or execution-mode distinction in `docs/03_rag_01_system_overview.md` — confirmed via grep returning no matches
- The note should be placed after the existing bullet-point list (lines 190-196) and before the closing paragraph (line 198)

## Design decisions

1. Place the note after the existing bullet-point list (lines 190-196) and before the closing paragraph (line 198) — this keeps it adjacent to the component responsibility descriptions it complements
2. Explicitly state this is a configuration convention, not an enforced invariant — per the source Issue's own Constraints
3. Cite both config files by name and path — provides traceability for operators verifying the claim

## Alternatives considered

1. Creating a new top-level section for the note: rejected — the source Issue's Implementation Intent specifies placing it in the most appropriate existing section ("MCP Server Responsibility Division") rather than creating a new section for a two-sentence note
2. Placing the note under "Query Pipeline" instead: rejected — the "MCP Server Responsibility Division" section already describes the HTTP-routing-vs-in-process-pipeline-execution split that this note's "same corpus, different execution path" point directly extends

## Implementation

### Target file

`docs/03_rag_01_system_overview.md`

### Procedure

1. Read the current "MCP Server Responsibility Division" section (lines 186-198) to confirm current content
2. Insert the new note between the existing bullet-point list and the closing paragraph
3. Verify the inserted text follows the document's existing formatting conventions

### Method

1. Read `docs/03_rag_01_system_overview.md` lines 186-198 to confirm the exact current content
2. Apply edits using the Edit tool to insert the new note
3. Verify the inserted text maintains consistency with the document's existing style

### Details

**Step 1 — Read current section:**

Current "MCP Server Responsibility Division" section (lines 186-198):

```markdown
## MCP Server Responsibility Division

For operators who prefer a quick reference without navigating away from this document, here is a concise summary of each component's role:

- **`rag_pipeline_server.py`**: HTTP route handling and request/response formatting. This FastAPI application exposes MCP endpoints (`/v1/call_tool`, `/health`, `/rag_run_pipeline`, etc.), builds the tool list, and handles exceptions for `RagPipelineServiceError`.

- **`rag_pipeline_service.py`**: Pipeline orchestration and error handling. The `RagPipelineMCPService` class wraps `RagPipeline`, manages lifecycle (start/stop), formats results for MCP tool responses, and maintains the dispatch table mapping tool names to service methods.

- **`scripts/rag/pipeline.py`**: Core search logic and stage execution. The `RagPipeline` class orchestrates the MQE → Search → RRF → Rerank pipeline stages, implements the `augment()` method with its fallback chain (HTTP → cache → search → refiner → raw chunks), and collects diagnostics.

The interaction flow is: MCP client → `rag_pipeline_server.py` (HTTP routing) → `rag_pipeline_service.py` (orchestration) → `scripts/rag/pipeline.py` (search execution).

For details on responsibilities of these components, please refer to `docs/03_rag_03_01_query_pipeline-overview.md`.
```

**Step 2 — Insert new note between the interaction-flow paragraph and the closing paragraph:**

After line 197 (`The interaction flow is...`) and before line 198 (`For details on responsibilities...`), insert:

```markdown
Note: External (HTTP-delegated) and local (in-process) RAG execution modes currently read the same corpus database (`rag_db_path`). Both `config/agent.toml` (line 7: `rag_db_path = "/opt/llm/db/rag.sqlite"`) and `config/rag_pipeline_mcp_server.toml` (line 13: `rag_db_path = "/opt/llm/db/rag.sqlite"`) are configured identically. This is a configuration convention, not an enforced invariant — a misconfigured `rag_pipeline_mcp_server.toml` pointing at a different `rag_db_path` would silently diverge, undetected by any current automated check.
```

Reference files read (must NOT be modified):
- `config/agent.toml:7` — confirms `rag_db_path = "/opt/llm/db/rag.sqlite"`
- `config/rag_pipeline_mcp_server.toml:13` — confirms `rag_db_path = "/opt/llm/db/rag.sqlite"`
- `docs/03_rag_01_system_overview.md:186-198` — confirms current section content

## Compatibility considerations

- No public API changes; only documentation addition
- Document structure preserved — only adds a new paragraph within an existing section
- Existing content unaffected by the insertion

## Security considerations

N/A — documentation-only change, no security-sensitive operations introduced.

## Rollback considerations

- Revert the inserted paragraph to restore original state
- No data loss risk — only documentation changes

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| docs/03_rag_01_system_overview.md | Documentation quality/consistency check | `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_consistency.py --domain rag` | No new findings introduced by this Plan's edit (pre-existing 21 warnings in the `rag` domain remain, none newly caused by this change) |

## Completion criteria

- [ ] Note added to "MCP Server Responsibility Division" section
- [ ] Note states that external/local RAG modes share one corpus
- [ ] Note cites both config files' `rag_db_path` keys as evidence
- [ ] Note explicitly labels this a configuration convention, not an enforced invariant
- [ ] Note mentions no automated check detects `rag_db_path` divergence
- [ ] Doc-quality tools pass without new findings

## Out of scope

- Adding automated divergence checks between config files
- Changing the placement of the note (unless a reviewer disagrees at implementation time)
- Modifying any other documentation file

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260914-220137 | 20260914-220137 |  |
| 2 | Add or update tests per Validation plan | Completed | 20260914-220137 | 20260914-220137 | N/A: documentation-only change |
| 3 | Run the validation sequence (rules/toolchain.md) | Completed | 20260914-220138 | 20260914-220138 | N/A: documentation-only change |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260914-220138 | 20260914-220138 | N/A: docstring already describes delegation |

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
- **Source issue**: issues/20260914-112416_ragsvc04_execution-mode-shared-corpus-doc.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260914-151434_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260914-170933
- **Related target files**: docs/03_rag_01_system_overview.md