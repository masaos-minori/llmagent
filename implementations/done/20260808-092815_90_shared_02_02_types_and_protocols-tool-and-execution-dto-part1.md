## Goal
- Restructure `docs/90_shared_02_02_types_and_protocols-tool-and-execution-dto-part1.md` to remove overly detailed field definitions and type comparison tables while explicitly preserving why common types belong in shared/, why LLM DTOs can be imported without LLMClient, Protocol/TypedDict/dataclass usage policy, RagConfig structural protocol justification, ArtifactEvent data-only nature, ShellPolicy separation rationale, RuntimeTool/RuntimeToolRegistry design intent, and shared-is-leaf constraint.

## Scope
- **In-Scope**: `docs/90_shared_02_02_types_and_protocols-tool-and-execution-dto-part1.md` — restructure to reduce implementation detail while preserving design-intent-critical facts
- **Out-of-Scope**: Other shared/DB chapters (`docs/90_shared_*.md`), source code changes, tests

## Assumptions
- `memo-doc-shared-review.md` is valid and this chapter should describe "why types are in shared/, which boundaries they protect"
- Existing internal links and cross-references must remain valid after editing

## Design decisions
- Compress Section 6 LLMUsage/LLMResponse full dataclass definitions: replace with prose description of purpose (token counting + response envelope)
- Compress Section 6a ToolCallResult/TransportErrorInfo full field listings: replace with prose describing result contract categories (output/error metadata, transport info, audit info)
- Compress Section 7 ActionResult full field listing: replace with prose describing action routing schema categories
- Compress Section 7a ToolSpec full field listing: replace with prose describing execution metadata categories (identity, scheduling, side-effect detection)
- Compress Section 7b CacheEntry full field listing: replace with prose describing cache entry structure
- Compress Section 7c RuntimeTool full field listing and build_runtime_tool() function signature: replace with prose describing normalization categories (routing, schema, scheduler metadata, side-effect detection, safety tier, approval, arg validation)
- Compress Section 7d RuntimeToolRegistry method listing: replace with prose describing registry responsibilities (resolution, classification, policy application)
- Keep: shared-is-leaf constraint rationale, Protocol vs TypedDict vs dataclass usage policy, RagConfig structural protocol justification, ArtifactEvent data-only nature, ShellPolicy separation rationale, RuntimeTool/RuntimeToolRegistry design intent

## Alternatives considered
- Remove Section 2 entirely: rejected — type overview provides quick lookup that prose does not
- Replace all tables with prose: rejected — tabular format for type overview is efficient for reference
- Merge Sections 4 and 5 into one: rejected — different conceptual domains (config protocol vs search results)

## Implementation
### Target file
`docs/90_shared_02_02_types_and_protocols-tool-and-execution-dto-part1.md`

### Procedure
1. **Phase 1: Preparation**
   - Analyze current document structure and identify which type design judgments are scattered across sections

2. **Phase 2: Core Logic Implementation**
   - Compress or remove Section 6 LLMUsage/LLMResponse full dataclass definitions (lines 27-37)
   - Compress or remove Section 6a ToolCallResult/TransportErrorInfo full field listings (lines 47-63)
   - Compress or remove Section 7 ActionResult full field listing (lines 76-86)
   - Compress or remove Section 7a ToolSpec full field listing (lines 96-105)
   - Compress or remove Section 7b CacheEntry full field listing (lines 116-129)
   - Compress or remove Section 7c RuntimeTool full field listing and build_runtime_tool() signature (lines 138-176)
   - Compress or remove Section 7d RuntimeToolRegistry method listing (lines 190-205)
   - Preserve: why common types belong in shared/, why LLM DTOs can be imported without LLMClient, Protocol/TypedDict/dataclass usage policy, RagConfig structural protocol justification, ArtifactEvent data-only nature, ShellPolicy separation rationale, RuntimeTool/RuntimeToolRegistry design intent, shared-is-leaf constraint

3. **Phase 3: Deployment & Verification**
   - Confirm all 4 files follow standard template
   - Confirm no complete DTO/dataclass/Protocol field lists remain
   - Confirm each type's "why in shared/, which boundary protected" rationale is explicit
   - Confirm cross-references to `scripts/shared/types.py` and other type-defining modules exist
   - Validate internal Markdown links and cross-references
   - Confirm compliance with post-edit chapter structure template from `memo-doc-shared-review.md`

### Method
- Table reduction: convert full-field tables to category-level descriptions
- Code block removal: replace inline Python definitions with prose summaries of field semantics
- Prose compression: convert field-by-field enumeration to grouped descriptions by purpose

### Details
- Section 6 (LLMUsage/LLMResponse): replace dataclass listings with prose: "LLMUsage (prompt_tokens, completion_tokens for token accounting); LLMResponse (message, finish_reason, usage). Separated from llm_client.py so callers can import DTOs without importing LLMClient"
- Section 6a (ToolCallResult/TransportErrorInfo): replace full field listings with prose: "ToolCallResult (output, is_error, request_id, server_key, source, error_type) — canonical result contract for all tool call executions; TransportErrorInfo (summary, detail) — structured error info for audit logs". Drop from_transport() classmethod detail
- Section 7 (ActionResult): replace field listing with prose: "ActionType enum (continue/call_tool/retrieve_more_context/ask_user/fail/retry); frozen dataclass with reason, required_context, payload, errors, confidence — generic machine-decision schema for agent action routing"
- Section 7a (ToolSpec): replace field listing with prose: "Execution metadata for a single approved tool call (call_id, name, args, resource_scope, requires_serial, is_write). Used unconditionally in DAG scheduling; serial grouping logic deferred to tool_scheduler.py"
- Section 7b (CacheEntry/ToolResultCache): replace field/method listings with prose: "CacheEntry (output, is_error, cached_at) — LRU+TTL cache utility for tool results. Not currently used by ToolExecutor; kept for potential future use without stampede protection"
- Section 7c (RuntimeTool/build_runtime_tool): replace full field listings with prose: "RuntimeTool normalizes 15 fields of tool execution metadata (routing, LLM schema, scheduler metadata, side-effect detection, safety tier, approval, arg validation). build_runtime_tool() applies safe-side defaults for unspecified annotations. AgentSafetyTier Literal defined locally due to shared-is-leaf constraint. allow_extra_fields flag controls argument validation strictness per tool". Drop web_search-mcp browser_fetch detail
- Section 7d (RuntimeToolRegistry): replace method listing with prose: "In-memory {name: RuntimeTool} registry. Provides resolution (resolve/get), classification (classify_operation_type), policy application (apply_policy), and side-effect detection (is_side_effect). resolve() returns None for unknown names; get() raises KeyError — distinguishes 'registered but under-annotated' from 'not in registry'. classify_operation_type returns local Literal['read', 'write'] rather than OperationType enum due to shared-is-leaf constraint. apply_policy accepts plain tier_map/allowed_tools rather than ToolConfig/ApprovalConfig due to shared-is-leaf constraint. is_side_effect intentionally duplicated alongside shared.tool_executor_helpers.is_side_effect()". Drop MCP discovery integration detail
- Remove Related Documents and Keywords sections — content duplicated in frontmatter

## Compatibility considerations
- Cross-references to `scripts/shared/types.py`, `scripts/shared/llm_types.py`, `scripts/shared/transport_dto.py`, etc. must remain valid after restructuring
- Internal Markdown links must be verified against actual file paths in `docs/90_shared_*` directory
- No change to source code contracts — document-only modification

## Security considerations
- N/A — document-only modification, no security-sensitive content affected

## Rollback considerations
- If restructuring causes link breakage, revert to original structure and apply targeted compression instead of full rewrite
- All removed details point to source files for verification

## Validation plan
| Check | Tool | Target |
|---|---|---|
| Type Design Intent | Manual | Explicitly preserved |
| Cross-references | Manual | All removed details point to scripts/shared/types.py / other type-defining modules |
| Internal Links | Manual | All cross-references valid |
| Template Compliance | Manual | Follows `memo-doc-shared-review.md` §「修正後の章構成テンプレート」 |

## Out of scope
- Source code changes
- Test modifications
- Cross-chapter structural changes beyond this single file
- Auto-generation of documentation (future work)

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260807-210830_plan.md
- Source implementation procedure: N/A
- Generated at: 20260808-092815
- Related target files: 90_shared_02_02_types_and_protocols-tool-and-execution-dto-part1.md
