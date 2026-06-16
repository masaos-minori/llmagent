# Implementation: docs/06_shared_02_types_and_protocols.md

## Goal

Create the canonical reference for all shared type definitions and protocol interfaces:
LLMMessage, RagConfig, RagHit, LLMUsage/LLMResponse, ActionResult, ArtifactEvent,
ShellPolicy, and tool_constants.

## Scope

- Content from: `06_shared.md` §共通型定義 (LLMMessage, RagConfig, RagHit)
- Content from: `06_spec_shared.md` §9.1-9.7 (data specs) + §6.3-6.4-6.9-6.10-6.11-6.12
- Output: `docs/06_shared_02_types_and_protocols.md`
- Not covered: runtime behavior / execution flow (→ 03)

## Assumptions

- LLMMessage canonical definition is spec §9.1 (7 fields incl. importance/pinned)
- RagHit canonical definition is 06_shared.md (8 fields, total=False TypedDict)
- RagConfig canonical definition is 06_shared.md (15 fields Protocol, runtime_checkable)
- tool_constants are frozensets defined in shared/tool_constants.py

## Implementation

### Target file

`docs/06_shared_02_types_and_protocols.md`

### Procedure

1. LLMMessage (shared/types.py): field table with all 7 fields including importance/pinned;
   note total=False; note re-export from rag.types; note role is practically required
2. RagHit (rag/types.py): 8-field table with stage column (vector/fts/rrf/rerank);
   note total=False; note progressive field population across pipeline stages
3. RagConfig (shared/types.py): 15-field Protocol table; note @runtime_checkable;
   note SimpleNamespace adapter pattern; note used only in rag/mcp layer
4. LLMUsage / LLMResponse (shared/llm_types.py): frozen dataclass fields;
   note split from llm_client.py so callers can import without LLMClient
5. ActionResult (shared/action_result.py): ActionType Literal + frozen dataclass fields
6. ArtifactEvent (shared/events.py): TypedDict fields table; note event bus unimplemented
7. ShellPolicy (shared/protocols/shell.py): note pure dataclass, no fastapi/mcp/agent deps
8. tool_constants (shared/tool_constants.py): frozenset table with member counts per set

### Method

- Each type gets its own subsection with: import path, field table, key notes
- Preserve exact field names and types from source files
- Flag LLMMessage importance/pinned as not present in 06_shared.md (spec-only)

### Details

- LLMMessage.importance: float — compression prioritization score
- LLMMessage.pinned: bool — preserved during compression
- RagConfig.use_rrf, use_search, use_refiner fields are bool feature flags
- ActionType values: continue/call_tool/retrieve_more_context/ask_user/fail/retry

## Validation plan

- File exists at `docs/06_shared_02_types_and_protocols.md`
- All 7 types/protocols documented with field tables
- LLMMessage shows all 7 fields (including importance, pinned)
- RagHit shows all 8 fields with stage column
- tool_constants shows all 7 frozensets with member lists
