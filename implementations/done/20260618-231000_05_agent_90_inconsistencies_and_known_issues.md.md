# Design: Remove resolved OQ-01 from agent inconsistencies doc

## Goal
Remove the `AgentSession` RAG boundary open question (OQ-01) from `docs/05_agent_90_inconsistencies_and_known_issues.md` since it is now resolved by moving document operations to rag-pipeline-mcp.

## Target File
- `docs/05_agent_90_inconsistencies_and_known_issues.md`

## Current State (lines 18-26)
```markdown
### OQ-01: `AgentSession` owns RAG-layer table access — responsibility boundary unclear

- **Type:** Open Question / Needs confirmation
- **Impact scope:** `agent/session.py AgentSession`, `/db clean`, `/db stats` commands, `RAG` layer
- **Description:** `AgentSession` (`agent/session.py`) implements `delete_document(url)` and `list_documents()`, which directly access the RAG layer tables (`documents`, `chunks`, `chunks_vec`) in `rag.sqlite`. This makes the agent layer depend on the RAG schema.
- **Current safe interpretation:** The current implementation works. `AgentSession` accesses RAG tables for `/db clean` and `/db stats` as a convenience. This is a known responsibility boundary violation.
- **Recommended action:** Consider moving RAG document management to `rag-pipeline-mcp` and having agent commands call it via MCP. Track before any RAG layer schema refactoring.
- **Notes for AI reference:** When modifying `AgentSession`, be aware it contains both session-layer and RAG-layer operations. Do not assume `agent/session.py` touches only `session.sqlite`.
```

## Implementation Steps

### Step 1: Delete the OQ-01 entry
Delete lines 18-26 (the entire OQ-01 section including the `###` heading).

### Step 2: Verify no other references to OQ-01
- Grep for `OQ-01` in `docs/` — should return only this section
- Grep for `AgentSession.*RAG` in `docs/` — should find references in other docs that are now updated (covered by separate impl docs)

## Completion Criteria
- OQ-01 entry removed from inconsistencies doc
- No orphaned references to "OQ-01" remain
- The open question about AgentSession RAG boundary is resolved and documented elsewhere
