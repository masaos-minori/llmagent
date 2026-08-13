# Implementation Procedure: Shared — Types & Protocols Documentation Restructuring

## Goal

Restructure shared design documentation chapter to remove overly detailed field definitions while preserving critical operational guidance on why common types exist in shared/, LLM DTO being separated so it can be imported without LLMClient, Protocol/TypedDict/dataclass usage policy, RagConfig being structural Protocol (not AgentConfig), ArtifactEvent being data definition only (not event bus), ShellPolicy separating policy value from shell MCP implementation, RuntimeTool/RuntimeToolRegistry moving toward canonical runtime metadata source, and shared having leaf constraint (shared/ does NOT import agent enumeration/configuration classes).

## Scope

**In-Scope:**
- `docs/90_shared_02_01_types_and_protocols-core-types.md` — compress LLMMessage full field definition; preserve design rationales
- `docs/90_shared_02_02_types_and_protocols-tool-and-execution-dto-part1.md` — compress ToolCallResult etc. DTO full field list, ActionResult/ToolSpec/CacheEntry signatures; preserve design rationales
- `docs/90_shared_02_02_types_and_protocols-tool-and-execution-dto-part2.md` — compress RawHit/MergedHit/RankedHit dataclass definitions, ToolCallFunction-family TypedDict list, ShellPolicy full field list, tool frozenset column enumeration; preserve design rationales
- `docs/90_shared_02_03_types_and_protocols-reference.md` — compress Pydantic definitions, text-book style Protocol/TypedDict/dataclass comparison table; preserve design rationales

**Out-of-Scope:**
- Other shared-related chapters (`docs/90_shared_*.md`)
- Source code changes to `scripts/shared/types.py` or other type-defining modules
- Test modifications

## Assumptions

- `memo-doc-shared-review.md` is valid and this chapter should be the authoritative reference for common type and Protocol design intent decisions
- What matters is not the shape of the type but WHY it exists in shared/ and WHICH boundary it protects
- Existing internal links and cross-references must remain valid after edits
- Compression preserves the "why" behind each design decision

## Design Decisions

- **Compress over delete**: Remove full field definitions, DTO lists, and verbose processing explanations but keep references to where they live (`scripts/shared/types.py`, other type-defining modules)
- **Preserve common type rationale**: Keep explanation of why common types exist in shared/
- **Preserve LLM DTO separation**: Keep explicit note that LLM DTO is separated so it can be imported without LLMClient
- **Preserve Protocol/TypedDict/dataclass usage policy**: Keep explicit statement of Protocol/TypedDict/dataclass usage policy
- **Preserve RagConfig structural Protocol**: Keep explicit note that RagConfig is structural Protocol (NOT AgentConfig)
- **Preserve ArtifactEvent purpose**: Keep explicit note that ArtifactEvent is data definition only (NOT event bus)
- **Preserve ShellPolicy separation**: Keep explicit note that ShellPolicy separates policy value from shell MCP implementation
- **Preserve RuntimeTool/RuntimeToolRegistry direction**: Keep explicit note that RuntimeTool/RuntimeToolRegistry is moving toward canonical runtime metadata source
- **Preserve shared leaf constraint**: Keep explicit note that shared has leaf constraint (shared/ does NOT import agent enumeration/configuration classes)

## Alternatives Considered

1. **Full deletion of field definitions** — Rejected: loses traceability to source implementations
2. **Move to appendix** — Rejected: fragments the document unnecessarily
3. **Inline cross-references only** — Chosen: balances brevity with traceability

## Implementation

### Target Files

| File | Action |
|------|--------|
| `docs/90_shared_02_01_types_and_protocols-core-types.md` | Compress LLMMessage fields; preserve design rationales |
| `docs/90_shared_02_02_types_and_protocols-tool-and-execution-dto-part1.md` | Compress ToolCallResult DTO fields, ActionResult/ToolSpec/CacheEntry signatures; preserve design rationales |
| `docs/90_shared_02_02_types_and_protocols-tool-and-execution-dto-part2.md` | Compress RawHit/MergedHit/RankedHit dataclasses, ToolCallFunction-family TypedDicts, ShellPolicy fields, tool frozenset columns; preserve design rationales |
| `docs/90_shared_02_03_types_and_protocols-reference.md` | Compress Pydantic definitions, Protocol/TypedDict/dataclass comparison table; preserve design rationales |

### Procedure

1. Read all target files to understand current structure
2. For each section containing overly detailed definitions, replace with prose summary that references source files
3. Preserve all design rationale paragraphs (common type rationale, LLM DTO separation, Protocol/TypedDict/dataclass usage policy, RagConfig structural Protocol, ArtifactEvent purpose, ShellPolicy separation, RuntimeTool/RuntimeToolRegistry direction, shared leaf constraint)
4. Verify all internal Markdown links remain valid after edits
5. Confirm each design decision's "why" is explicitly stated

### Method

For each target section:
1. Locate the section containing the full definition (grep for key identifiers like `LLMMessage`, `ToolCallResult`, etc.)
2. Read the surrounding context (5-10 lines before/after) to preserve relationships
3. Replace the definition block with a summary paragraph:
   - State what the component represents (1 sentence)
   - Note its purpose in the DB architecture
   - Reference where the full definition lives (e.g., `scripts/shared/types.py`)
4. Leave any design rationale paragraphs untouched

### Details

**File: `90_shared_02_01_types_and_protocols-core-types.md`**
- LLMMessage full field definition: Replace full field definition with prose summary referencing `scripts/shared/types.py`

**File: `90_shared_02_02_types_and_protocols-tool-and-execution-dto-part1.md`**
- ToolCallResult etc. DTO full field list: Replace field enumeration with prose summary
- ActionResult/ToolSpec/CacheEntry signatures: Replace signature enumeration with prose summary

**File: `90_shared_02_02_types_and_protocols-tool-and-execution-dto-part2.md`**
- RawHit/MergedHit/RankedHit dataclass definitions: Replace dataclass definitions with prose summaries
- ToolCallFunction-family TypedDict list: Replace TypedDict enumeration with prose summary
- ShellPolicy full field list: Replace field enumeration with prose summary noting ShellPolicy separates policy value from shell MCP implementation
- Tool frozenset column enumeration: Replace column enumeration with prose summary

**File: `90_shared_02_03_types_and_protocols-reference.md`**
- Pydantic definitions: Replace Pydantic definitions with prose summary
- Text-book style Protocol/TypedDict/dataclass comparison table: Replace table with prose summary

## Compatibility Considerations

- All compression targets are documentation-only; no API contract changes
- Internal cross-references to `scripts/shared/types.py` and other type-defining modules must remain accurate
- Any downstream consumers of these docs (e.g., AI agent prompts) should still receive sufficient information about type rationale and shared leaf constraint
- Known issue note about caching duplication must be preserved
- Each type's "why shared/ exists, which boundary it protects" rationale must be verified as clear

## Security Considerations

N/A — documentation restructuring only; no security-sensitive content involved.

## Rollback Considerations

- Before making changes, commit current state: `git add docs/ && git commit -m "pre-restructure snapshot"`
- After edits, verify with `git diff --stat` to confirm only documentation changed
- If internal links break, revert to pre-change state and adjust compression strategy

## Validation Plan

| Check | Tool | Target |
|-------|------|--------|
| Type rationale preserved | Manual | Explicitly stated |
| Cross-references valid | Manual | All removed details point to `scripts/shared/types.py` / other type-defining modules |
| Internal links valid | Manual | All Markdown links resolve correctly |
| Template compliance | Manual | Follows `memo-doc-shared-review.md` §「修正後の章構成テンプレート」 |
| No full field definitions remain | Manual | Scanning for remaining verbose definitions |

## Out of Scope

- Modifying source type definitions in `scripts/shared/types.py` or other type-defining modules
- Adding new types or changing existing ones
- Updating test coverage for type definitions
- Changes to other shared chapters beyond the four target files

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260807-213900_plan.md
- Source implementation procedure: N/A
- Generated at: 20260808-111725
- Related target files: docs/90_shared_02_01_types_and_protocols-core-types.md, docs/90_shared_02_02_types_and_protocols-tool-and-execution-dto-part1.md, docs/90_shared_02_02_types_and_protocols-tool-and-execution-dto-part2.md, docs/90_shared_02_03_types_and_protocols-reference.md
