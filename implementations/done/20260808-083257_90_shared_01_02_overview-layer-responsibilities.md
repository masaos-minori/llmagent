## Goal
- Restructure `docs/90_shared_01_02_overview-layer-responsibilities.md` to remove overly detailed per-module responsibility tables and function/DTO explanations while explicitly preserving layer structure, import direction concept, shared-vs-db responsibility boundary, and relationship with agent/rag/mcp_servers.

## Scope
- **In-Scope**: `docs/90_shared_01_02_overview-layer-responsibilities.md` — restructure to reduce implementation detail while preserving design-intent-critical facts
- **Out-of-Scope**: Other shared/db chapters (`docs/90_shared_*.md`), source code changes, tests

## Assumptions
- `memo-doc-shared-review.md` is valid and this chapter should describe "which layer owns what"
- "Which file has which function" belongs in Reference
- Existing internal links and cross-references must remain valid after editing

## Design decisions
- Compress or remove overly detailed per-module responsibility table (~44 modules)
- Compress or remove overly detailed function/DTO explanation (e.g., `LlmSseStreamHandler — read_next_chunk, stream_once`)
- Compress or remove overly detailed function/DTO explanation (e.g., `ToolRouteResolver — tool name → server key`)
- Compress or remove overly detailed function/DTO explanation (e.g., `ProductionConfigValidator, ConfigValidationResult — validate strict key unset, tool_safety_tiers over/under-specification, allowed_tools=[] in production security profile`)
- Compress or remove overly detailed individual file descriptions (e.g., `mcp_config.py`)
- Compress or remove overly detailed individual responsibility enumeration (e.g., `tool_constants`, `llm_sse_stream`)
- Preserve: layer structure, import direction concept, shared-vs-db responsibility boundary, relationship with agent/rag/mcp_servers, what does not belong to shared/, what belongs to db/, what belongs to agent side

## Alternatives considered
- Keeping complete per-module table but adding a note pointing to scripts/shared/ as canonical
- Converting edge case descriptions to prose instead of removing them
- Moving detailed validation specifications to an appendix rather than removing them

## Implementation
### Target file
- `docs/90_shared_01_02_overview-layer-responsibilities.md`

### Procedure
#### Phase 1: Preparation
1. Analyze current document structure to identify where layer responsibility design judgments are distributed

#### Phase 2: Core Logic Implementation
1. Compress or remove overly detailed per-module responsibility table
   - Replace with brief description of expected payload shape
2. Compress or remove overly detailed function/DTO explanation
   - Delete function-level naming rationale
3. Compress or remove overly detailed function/DTO explanation
   - Delete invocation chain details
4. Compress or remove overly detailed function/DTO explanation
   - Delete parameter-by-parameter constraint descriptions
5. Compress or remove overly detailed individual file descriptions
   - Delete specific filename references
6. Compress or remove overly detailed individual responsibility enumeration
   - Delete exhaustive responsibility mappings
7. Preserve design-critical information:
   - Layer structure
   - Import direction concept
   - Shared-vs-db responsibility boundary
   - Relationship with agent/rag/mcp_servers
   - What does not belong to shared/
   - What belongs to db/
   - What belongs to agent side

#### Phase 3: Deployment & Verification
1. Confirm layer boundary descriptions were not silently dropped or weakened
2. Confirm cross-reference to `scripts/shared/` and `scripts/db/` exists
3. Validate internal Markdown links and cross-references
4. Confirm chapter follows standard template from `memo-doc-shared-review.md` §「修正後の章構成テンプレート」

### Method
- Document restructuring only; no source code changes
- Use grep to verify link integrity before and after editing
- Manual verification of cross-references post-edit
- Explicitly preserve layer boundaries and import direction concept during trimming

### Details
- Focus on reducing implementation-derived detail while preserving design intent
- Layer boundaries are critical — must survive unchanged
- Import direction concept is critical — must survive unchanged
- Ensure navigation remains functional for both human and AI consumers

## Compatibility considerations
- No API changes — documentation-only update
- Internal cross-references must remain valid after restructuring
- Layer boundaries and import direction concept must survive unchanged

## Security considerations
- N/A — documentation-only change

## Rollback considerations
- Preserve pre-edit backup of layer boundaries and import direction sections
- If these statements are accidentally weakened, revert immediately

## Validation plan
| Check | Tool | Target |
|---|---|---|
| Layer Responsibility Boundaries | Manual | Explicitly preserved |
| Import Direction Concept | Manual | Explicitly preserved |
| Cross-references | Manual | All removed details point to scripts/shared/ / scripts/db/ |
| Internal Links | Manual | All cross-references valid |
| Template Compliance | Manual | Follows `memo-doc-shared-review.md` §「修正後の章構成テンプレート」 |

## Out of scope
- Other shared/db chapters (`docs/90_shared_*.md`)
- Source code changes
- Test updates

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: requires/20260807-181448_require.md
- Source plan: plans/20260807-210635_plan.md
- Source implementation procedure: N/A
- Generated at: 20260808-083257
- Related target files: docs/90_shared_01_02_overview-layer-responsibilities.md
