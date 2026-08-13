## Goal

Rebuild the shared/db layer responsibility boundary chapter by compressing or removing exhaustive per-module responsibility tables while explicitly preserving "which layer owns what."

## Scope

**In-Scope**: `docs/90_shared_01_02_overview-layer-responsibilities.md` structure change only.

**Out-of-Scope**: Other shared/db related chapters (`docs/90_shared_*.md`), source code changes, tests.

## Assumptions

- `memo-doc-shared-review.md` is valid and this chapter should be maintained as the authoritative reference for layer responsibility boundaries.
- This chapter focuses on design intent, not implementation details.
- Existing internal links and cross-references must remain valid after editing.

## Design decisions

- Compress per-module responsibility tables into high-level ownership declarations.
- Preserve import direction concept (shared → db ← upper layers).
- Retain explicit shared-vs-db boundary statements.

## Alternatives considered

- Full removal of all module-level responsibilities: rejected because ownership becomes ambiguous without any concrete anchors.
- Keeping full per-module tables: rejected because they drift from reality as modules evolve and add noise to the overview.

## Implementation

### Target file

`docs/90_shared_01_02_overview-layer-responsibilities.md`

### Procedure

1. Read current chapter content.
2. Identify comprehensive shared/ per-module responsibility table and replace with high-level category ownership (e.g., "configuration types owned by shared", "schema definitions owned by db").
3. Identify comprehensive db/ per-module responsibility table and replace with high-level category ownership.
4. Compress per-file function/DTO descriptions — remove detailed per-function explanations; retain only ownership assertions.
5. Compress/remove fine-grained file explanations like `mcp_config.py` specifics.
6. Compress/remove individual responsibility enumerations like `tool_constants`, `llm_sse_stream` — replace with "constants owned by shared", "streaming protocol owned by shared".
7. Verify preservation of: layer structure, import direction concept, shared vs db responsibility boundary, relationships with agent/rag/mcp_servers, what should/should-not live in shared, what should live in db vs agent side.
8. Validate all internal Markdown links and cross-references.
9. Confirm compliance with `memo-doc-shared-review.md` §「修正後の章構成テンプレート」.

### Method

Document compression via selective deletion of exhaustive per-module/per-file enumerations while retaining structural ownership declarations that point to source modules.

### Details

- **Preserve**: layer structure (shared / db / upper layers), import direction concept (shared → db ← upper layers), shared vs db responsibility boundary, relationship-with-agent-rag-mcp_servers declarations, what-should-live-in-shared assertions, what-should-not-live-in-shared assertions, what-should-live-in-db-vs-agent-side assertions.
- **Compress/remove**: shared/ comprehensive per-module responsibility table → replace with "shared owns configuration types, DTOs, logging infrastructure, caching, client abstractions"; db/ comprehensive per-module responsibility table → replace with "db owns schema management, migration, store protocols, backend implementations, recovery"; per-file function/DTO descriptions → remove detailed explanations, keep ownership assertions only; mcp_config.py fine-grained file explanation → compress to "MCP config type owned by shared"; tool_constants/llm_sse_stream individual responsibility enumerations → compress to "constants owned by shared", "streaming protocol owned by shared".
- **Verify**: cross-references to `scripts/shared/` and `scripts/db/` exist; internal Markdown links valid; template compliance.

## Compatibility considerations

N/A — document-only phase.

## Security considerations

N/A — document-only phase.

## Rollback considerations

N/A — document-only phase.

## Validation plan

| Check | Tool | Target |
|---|---|---|
| Layer Structure | Manual | Explicitly preserved |
| Import Direction Concept | Manual | Explicitly preserved |
| Shared Vs Db Responsibility Boundary | Manual | Explicitly preserved |
| Relationship With Agent Rag Mcp Servers | Manual | Explicitly preserved |
| What Should And Should Not Live In Shared | Manual | Explicitly preserved |
| What Should Live In Db Vs Agent Side | Manual | Explicitly preserved |
| Internal Links | Manual | All cross-references valid |
| Template Compliance | Manual | Follows `memo-doc-shared-review.md` §「修正後の章構成テンプレート」 |

## Out of scope

Other shared/db related chapters, source code changes, tests.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260807-232321_plan.md
- Source implementation procedure: N/A
- Generated at: 20260808-131126
- Related target files: 90_shared_01_02_overview-layer-responsibilities.md
