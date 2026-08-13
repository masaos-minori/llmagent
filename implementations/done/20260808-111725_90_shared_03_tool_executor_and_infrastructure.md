# Implementation Procedure: Shared — Runtime Tool Executor and Infrastructure Documentation Restructuring

## Goal

Restructure shared design documentation chapter to remove overly detailed constructor signatures, method lists, and other implementation specifics while preserving critical operational guidance on why RuntimeToolRegistry is the only execution-time routing source of truth, why ToolRegistry exists only as drift validation seed, why cache holds successful results only, why tools with side effects require caution in caching/parallelization, that ToolExecutor's responsibility boundary is single tool call execution foundation (approval/round control is agent-side), HealthRegistry's purpose as dispatch gate, HALF_OPEN experimental recovery concept, OTel tracer private provider rationale, and design intent of exact vs estimate fallback token counting.

## Scope

**In-Scope:**
- `docs/90_shared_03_02_runtime_and_execution-tool-executor-and-infrastructure.md` — compress ToolExecutor constructor signatures, sequential internal processing steps of execute(), helper function lists, ToolRegistry method lists, ToolRouteResolver method lists, validation function lists, function signatures of token_counter/git_helper/formatters; preserve design rationales

**Out-of-Scope:**
- Other shared-related chapters (`docs/90_shared_*.md`)
- Source code changes to `scripts/shared/` or `scripts/db/`
- Test modifications

## Assumptions

- `memo-doc-shared-review.md` is valid and this chapter should be the authoritative reference for ToolExecutor/RuntimeToolRegistry/ToolRegistry boundary decisions
- This boundary is important and must be expressed as source-of-truth/boundary/operational-meaning
- Existing internal links and cross-references must remain valid after edits
- Compression preserves the "why" behind each design decision

## Design Decisions

- **Compress over delete**: Remove full signatures, method lists, and verbose processing explanations but keep references to where they live (`scripts/shared/tool_executor.py`, `scripts/shared/runtime_tool_registry.py`, `scripts/shared/tool_registry.py`, etc.)
- **Preserve ToolExecutor responsibility boundary**: Keep explicit note that ToolExecutor is single tool call execution foundation (approval/round control is agent-side)
- **Preserve RuntimeToolRegistry as only execution-time routing source of truth**: Keep explicit statement of RuntimeToolRegistry's role
- **Preserve ToolRegistry as drift validation seed only**: Keep explicit note that ToolRegistry is not used for execution-time routing
- **Preserve tool result cache design intent**: Keep explicit note of cache design intent
- **Preserve success-only caching rationale**: Keep explicit note of why only successful results are cached
- **Preserve side-effect tool caution**: Keep explicit note of caution for tools with side effects in caching/parallelization
- **Preserve HealthRegistry dispatch gate purpose**: Keep explicit note of HealthRegistry's purpose as dispatch gate
- **Preserve HALF_OPEN experimental recovery concept**: Keep explicit note of HALF_OPEN experimental recovery
- **Preserve OTel tracer private provider rationale**: Keep explicit note of why OTel tracer uses private provider
- **Preserve exact vs estimate fallback token count design intent**: Keep explicit note of token count strategy

## Alternatives Considered

1. **Full deletion of constructor signatures** — Rejected: loses traceability to source implementations
2. **Move to appendix** — Rejected: fragments the document unnecessarily
3. **Inline cross-references only** — Chosen: balances brevity with traceability

## Implementation

### Target File

| File | Action |
|------|--------|
| `docs/90_shared_03_02_runtime_and_execution-tool-executor-and-infrastructure.md` | Compress ToolExecutor constructors, execute() steps, helper functions, ToolRegistry methods, ToolRouteResolver methods, validation functions, token_counter/git_helper/formatters signatures; preserve design rationales |

### Procedure

1. Read target file to understand current structure
2. For each section containing overly detailed definitions, replace with prose summary that references source files
3. Preserve all design rationale paragraphs (ToolExecutor responsibility boundary, RuntimeToolRegistry as only execution-time routing source of truth, ToolRegistry as drift validation seed only, tool result cache design intent, success-only caching rationale, side-effect tool caution, HealthRegistry dispatch gate purpose, HALF_OPEN experimental recovery concept, OTel tracer private provider rationale, exact vs estimate fallback token count design intent)
4. Verify all internal Markdown links remain valid after edits
5. Confirm each design decision's "why" is explicitly stated

### Method

For each target section:
1. Locate the section containing the full definition (grep for key identifiers like `ToolExecutor`, `RuntimeToolRegistry`, `ToolRegistry`, etc.)
2. Read the surrounding context (5-10 lines before/after) to preserve relationships
3. Replace the definition block with a summary paragraph:
   - State what the component represents (1 sentence)
   - Note its purpose in the DB architecture
   - Reference where the full definition lives (e.g., `scripts/shared/tool_executor.py`)
4. Leave any design rationale paragraphs untouched

### Details

**File: `90_shared_03_02_runtime_and_execution-tool-executor-and-infrastructure.md`**
- ToolExecutor constructor signatures: Replace with prose summary referencing `scripts/shared/tool_executor.py`
- Sequential internal processing steps of execute(): Replace with prose summary
- Helper function lists: Replace with prose summary
- ToolRegistry method lists: Replace with prose summary referencing `scripts/shared/tool_registry.py`
- ToolRouteResolver method lists: Replace with prose summary
- Validation function lists: Replace with prose summary
- Function signatures of token_counter/git_helper/formatters: Replace with prose summary

## Compatibility Considerations

- All compression targets are documentation-only; no API contract changes
- Internal cross-references to `scripts/shared/tool_executor.py`, `scripts/shared/runtime_tool_registry.py`, and `scripts/shared/tool_registry.py` must remain accurate
- Any downstream consumers of these docs (e.g., AI agent prompts) should still receive sufficient information about routing source of truth distinction
- Known issue note about caching duplication must be preserved
- Routing source of truth distinction must be verified as clear
- ToolRegistry seed-only status must be verified as clear

## Security Considerations

N/A — documentation restructuring only; no security-sensitive content involved.

## Rollback Considerations

- Before making changes, commit current state: `git add docs/ && git commit -m "pre-restructure snapshot"`
- After edits, verify with `git diff --stat` to confirm only documentation changed
- If internal links break, revert to pre-change state and adjust compression strategy

## Validation Plan

| Check | Tool | Target |
|-------|------|--------|
| Routing source of truth distinction preserved | Manual | Explicitly stated |
| ToolRegistry seed-only status preserved | Manual | Explicitly stated |
| Cross-references valid | Manual | All removed details point to `scripts/shared/tool_executor.py` / `runtime_tool_registry.py` / `tool_registry.py` |
| Internal links valid | Manual | All Markdown links resolve correctly |
| Template compliance | Manual | Follows `memo-doc-shared-review.md` §「修正後の章構成テンプレート」 |
| No full constructor signatures/method lists remain | Manual | Scanning for remaining verbose definitions |

## Out of Scope

- Modifying source type definitions in `scripts/shared/` or `scripts/db/`
- Adding new types or changing existing ones
- Updating test coverage for type definitions
- Changes to other shared chapters beyond the one target file

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260807-215706_plan.md
- Source implementation procedure: N/A
- Generated at: 20260808-111725
- Related target files: docs/90_shared_03_02_runtime_and_execution-tool-executor-and-infrastructure.md
