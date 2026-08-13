# Implementation Procedure: Shared DB — Protocol & Backend Documentation Restructuring

## Goal

Restructure shared/DB design documentation chapter to remove overly detailed protocol method lists, embedding helper function lists, and backend class enumerations while preserving critical operational guidance on why Protocol is used, abstracting SQLite implementation for future alternative backends, SQLiteSessionStore as thin DB adapter, SessionMessageRepository retaining semantics, message role validation/content normalization/JSON encode-decode as agent responsibility, MemoryDeleteStore as safe cross-table deletion boundary, and MemoryStore being on agent/memory side (not db/).

## Scope

**In-Scope:**
- `docs/90_shared_05_02_db_api_and_operations-protocol-and-backend.md` — compress complete protocol method list, embedding helper function list, SQLite backend class list, MemoryStore method table, detailed SQL operation explanations; preserve design rationales

**Out-of-Scope:**
- Other shared/DB-related chapters (`docs/90_shared_*.md`)
- Source code changes to `scripts/db/store_protocols.py` or related modules
- Test modifications

## Assumptions

- `memo-doc-shared-review.md` is valid and this chapter should be the authoritative reference for store Protocol/backend boundary decisions
- Existing internal links and cross-references must remain valid after edits
- Compression preserves the "why" behind each design decision

## Design Decisions

- **Compress over delete**: Remove full protocol method lists, embedding helper lists, and backend class enumerations but keep references to where they live (`scripts/db/store_protocols.py`, related modules)
- **Preserve Protocol rationale**: Keep explanation of why Protocol is used (interface abstraction, not implementation detail)
- **Preserve SQLite abstraction intent**: Keep explanation that SQLite implementation is abstracted to leave room for future alternative backends
- **Preserve SQLiteSessionStore role**: Keep note that SQLiteSessionStore is a thin DB adapter
- **Preserve SessionMessageRepository ownership**: Keep note that SessionMessageRepository retains semantics
- **Preserve agent-side responsibilities**: Keep explicit statement that message role validation/content normalization/JSON encode-decode are agent-side responsibilities
- **Preserve MemoryDeleteStore boundary**: Keep note that MemoryDeleteStore is the boundary for safe cross-table deletion
- **Preserve MemoryStore location**: Keep explicit note that MemoryStore is on agent/memory side, NOT in db/

## Alternatives Considered

1. **Full deletion of protocol method lists** — Rejected: loses traceability to source implementations
2. **Move to appendix** — Rejected: fragments the document unnecessarily
3. **Inline cross-references only** — Chosen: balances brevity with traceability

## Implementation

### Target File

| File | Action |
|------|--------|
| `docs/90_shared_05_02_db_api_and_operations-protocol-and-backend.md` | Compress protocol methods, embedding helpers, SQLite backends, MemoryStore methods, SQL operations; preserve design rationales |

### Procedure

1. Read target file to understand current structure
2. For each section containing overly detailed definitions, replace with prose summary that references source files
3. Preserve all design rationale paragraphs (Protocol rationale, SQLite abstraction, SQLiteSessionStore role, SessionMessageRepository ownership, agent-side responsibilities, MemoryDeleteStore boundary, MemoryStore location)
4. Verify all internal Markdown links remain valid after edits
5. Confirm each design decision's "why" is explicitly stated

### Method

For each target section:
1. Locate the section containing the full definition (grep for key identifiers like `Protocol`, `SQLiteSessionStore`, `SessionMessageRepository`, etc.)
2. Read the surrounding context (5-10 lines before/after) to preserve relationships
3. Replace the definition block with a summary paragraph:
   - State what the component represents (1 sentence)
   - Note its purpose in the DB architecture
   - Reference where the full definition lives (e.g., `scripts/db/store_protocols.py`)
4. Leave any design rationale paragraphs untouched

### Details

**File: `90_shared_05_02_db_api_and_operations-protocol-and-backend.md`**
- Complete protocol method list: Replace full method list with prose summary referencing `scripts/db/store_protocols.py`
- Embedding helper function list: Replace embedding helper enumeration with prose summary
- SQLite backend class list: Replace backend class enumeration with prose summary
- MemoryStore method table: Replace MemoryStore method table with prose summary
- Detailed SQL operation explanations: Replace SQL operation descriptions with prose summaries

## Compatibility Considerations

- All compression targets are documentation-only; no API contract changes
- Internal cross-references to `scripts/db/store_protocols.py` and related modules must remain accurate
- Any downstream consumers of these docs (e.g., AI agent prompts) should still receive sufficient information about thin-adapter vs semantics owner split and MemoryStore location
- Known issue note about caching duplication must be preserved

## Security Considerations

N/A — documentation restructuring only; no security-sensitive content involved.

## Rollback Considerations

- Before making changes, commit current state: `git add docs/ && git commit -m "pre-restructure snapshot"`
- After edits, verify with `git diff --stat` to confirm only documentation changed
- If internal links break, revert to pre-change state and adjust compression strategy

## Validation Plan

| Check | Tool | Target |
|-------|------|--------|
| Thin-adapter vs semantics owner split preserved | Manual | Explicitly stated |
| MemoryStore location preserved | Manual | Explicitly stated as agent/memory side, not db/ |
| Cross-references valid | Manual | All removed details point to `scripts/db/store_protocols.py` / related modules |
| Internal links valid | Manual | All Markdown links resolve correctly |
| Template compliance | Manual | Follows `memo-doc-shared-review.md` §「修正後の章構成テンプレート」 |
| No full protocol method lists/backend class lists remain | Manual | Scanning for remaining verbose definitions |

## Out of Scope

- Modifying source type definitions in `scripts/db/store_protocols.py` or related modules
- Adding new types or changing existing ones
- Updating test coverage for type definitions
- Changes to other shared/DB chapters beyond the one target file

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260807-211857_plan.md
- Source implementation procedure: N/A
- Generated at: 20260808-111725
- Related target files: docs/90_shared_05_02_db_api_and_operations-protocol-and-backend.md
