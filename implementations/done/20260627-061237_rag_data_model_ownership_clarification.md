## Goal

Remove Agent session tables (sessions, messages) from the RAG data model documentation so it only describes RAG-owned tables and does not present Agent session tables as part of rag.sqlite.

## Scope

**In-Scope**:
- Remove `sessions` and `messages` from the table list in section 2.0 of `03_rag_04_data_model_and_interfaces.md`
- Add cross-reference to Agent/session DB schema documentation
- Clarify that the RAG layer does not own Agent conversation history

**Out-of-Scope**:
- Changing the actual Agent session schema
- Changing MCP access behavior
- Adding/removing RAG-owned tables

## Assumptions

1. Agent session DB schema is documented elsewhere (in agent docs) — needs cross-reference
2. `sessions` and `messages` are exclusively owned by the Agent REPL layer

## Implementation

### Target file: docs/03_rag_04_data_model_and_interfaces.md

**Procedure**: Remove sessions and messages from table list, add cross-reference to Agent/session DB schema, clarify RAG/Agent ownership boundary.

**Method**: Modify section 2.0 of the RAG data model documentation.

**Details**:
1. Remove `sessions` row from section 2.0 table (line 81)
2. Remove `messages` row from section 2.0 table (line 82)
3. After the RAG table list, add a note about Agent-owned tables with reference to agent session docs
4. Remove or rephrase the paragraph below section 2.0 that describes sessions/messages as REPL agent tables (line 86)

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| 03_rag_04_data_model_and_interfaces.md | Verify sessions and messages removed from RAG table list | Check section 2.0 | Only RAG tables (documents, chunks, chunks_fts, chunks_vec) remain |
| 03_rag_04_data_model_and_interfaces.md | Verify cross-reference to Agent/session DB exists | Check section 2.0 | Note about Agent-owned tables present with reference |
| 03_rag_01_system_overview.md | Verify consistency — no conflicting ownership claims | Check out-of-scope section | Already correct: "Agent REPL — calls the pipeline via MCP; does not own RAG logic" |

## Risks

- **Risk**: Cross-reference to Agent/session DB schema may be broken if agent docs are moved | **Likelihood**: Low | **Mitigation**: Verify agent session docs location before adding reference; add placeholder if needed | False
