# Implementation Procedure: Shared — Overview Layer Responsibilities Documentation Restructuring

## Goal

Restructure shared design documentation chapter to remove overly detailed module-by-module responsibility tables while preserving critical operational guidance on "which layer owns what" decision criteria. Keep clear boundaries between shared-vs-db-vs-agent-vs-rag-vs-mcp_servers.

## Scope

**In-Scope:**
- `docs/90_shared_01_02_overview-layer-responsibilities.md` — compress shared/ module-by-module responsibility table, db/ module-by-module responsibility table, per-file function/DTO descriptions, fine-grained file-level explanations (e.g., mcp_config.py), individual responsibility enumerations for tool_constants and llm_sse_stream; preserve design rationales

**Out-of-Scope:**
- Other shared/overview-related chapters (`docs/90_shared_*.md`)
- Source code changes to `scripts/shared/` or `scripts/db/`
- Test modifications

## Assumptions

- `memo-doc-shared-review.md` is valid and this chapter should be the authoritative reference for layer responsibility boundary decisions
- What belongs in shared/ vs db/ vs agent/ is an architecture boundary enforced elsewhere (lint-imports)
- This boundary must NOT be weakened while trimming file-level details
- Existing internal links and cross-references must remain valid after edits
- Compression preserves the "why" behind each design decision

## Design Decisions

- **Compress over delete**: Remove full module-by-module responsibility tables, per-file descriptions, and verbose processing explanations but keep references to where they live (`scripts/shared/`, `scripts/db/`)
- **Preserve layer structure**: Keep explanation of layer structure
- **Preserve import direction concept**: Keep explicit note of import direction concept
- **Preserve shared-vs-db responsibility boundary**: Keep explicit statement of shared-vs-db responsibility boundary
- **Preserve relationship with agent/rag/mcp_servers**: Keep explicit note of relationship with agent/rag/mcp_servers
- **Preserve what should/shouldn't be in shared/**: Keep explicit note of what should/shouldn't be in shared/
- **Preserve what should be in db/ vs agent-side**: Keep explicit note of what should be in db/ vs agent-side

## Alternatives Considered

1. **Full deletion of responsibility tables** — Rejected: loses traceability to source implementations
2. **Move to appendix** — Rejected: fragments the document unnecessarily
3. **Inline cross-references only** — Chosen: balances brevity with traceability

## Implementation

### Target File

| File | Action |
|------|--------|
| `docs/90_shared_01_02_overview-layer-responsibilities.md` | Compress shared/ module responsibilities, db/ module responsibilities, per-file descriptions, fine-grained file explanations, individual responsibility enumerations; preserve design rationales |

### Procedure

1. Read target file to understand current structure
2. For each section containing overly detailed definitions, replace with prose summary that references source files
3. Preserve all design rationale paragraphs (layer structure, import direction concept, shared-vs-db responsibility boundary, relationship with agent/rag/mcp_servers, what should/shouldn't be in shared/, what should be in db/ vs agent-side)
4. Verify all internal Markdown links remain valid after edits
5. Confirm each design decision's "why" is explicitly stated

### Method

For each target section:
1. Locate the section containing the full definition (grep for key identifiers like `shared/`, `db/`, etc.)
2. Read the surrounding context (5-10 lines before/after) to preserve relationships
3. Replace the definition block with a summary paragraph:
   - State what the component represents (1 sentence)
   - Note its purpose in the DB architecture
   - Reference where the full definition lives (e.g., `scripts/shared/`)
4. Leave any design rationale paragraphs untouched

### Details

**File: `90_shared_01_02_overview-layer-responsibilities.md`**
- shared/ module-by-module responsibility table: Replace table with prose summary referencing `scripts/shared/`
- db/ module-by-module responsibility table: Replace table with prose summary referencing `scripts/db/`
- Per-file function/DTO descriptions: Replace descriptions with prose summaries
- Fine-grained file-level explanations (e.g., mcp_config.py): Replace explanations with prose summaries
- Individual responsibility enumerations for tool_constants and llm_sse_stream: Replace enumerations with prose summaries

## Compatibility Considerations

- All compression targets are documentation-only; no API contract changes
- Internal cross-references to `scripts/shared/` and `scripts/db/` must remain accurate
- Any downstream consumers of these docs (e.g., AI agent prompts) should still receive sufficient information about layer-boundary statements and shared-vs-db-vs-agent-vs-rag-vs-mcp_servers boundaries
- Known issue note about caching duplication must be preserved
- Layer-boundary statements must be verified as clear
- shared-vs-db-vs-agent-vs-rag-vs-mcp_servers boundaries must be verified as clear

## Security Considerations

N/A — documentation restructuring only; no security-sensitive content involved.

## Rollback Considerations

- Before making changes, commit current state: `git add docs/ && git commit -m "pre-restructure snapshot"`
- After edits, verify with `git diff --stat` to confirm only documentation changed
- If internal links break, revert to pre-change state and adjust compression strategy

## Validation Plan

| Check | Tool | Target |
|-------|------|--------|
| Layer-boundary statements preserved | Manual | Explicitly stated |
| shared-vs-db-vs-agent-vs-rag-vs-mcp_servers boundaries preserved | Manual | Explicitly stated |
| Cross-references valid | Manual | All removed details point to `scripts/shared/` / `scripts/db/` |
| Internal links valid | Manual | All Markdown links resolve correctly |
| Template compliance | Manual | Follows `memo-doc-shared-review.md` §「修正後の章構成テンプレート」 |
| No full module-by-module responsibility tables remain | Manual | Scanning for remaining verbose definitions |

## Out of Scope

- Modifying source type definitions in `scripts/shared/` or `scripts/db/`
- Adding new types or changing existing ones
- Updating test coverage for type definitions
- Changes to other shared/overview chapters beyond the one target file

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260807-214132_plan.md
- Source implementation procedure: N/A
- Generated at: 20260808-111725
- Related target files: docs/90_shared_01_02_overview-layer-responsibilities.md
