## Goal
- Restructure `docs/90_shared_02_02_types_and_protocols-tool-and-execution-dto-part2.md` to remove overly detailed field definitions and type comparison tables while explicitly preserving why common types belong in shared/, why LLM DTOs can be imported without LLMClient, Protocol/TypedDict/dataclass usage policy, RagConfig structural protocol justification, ArtifactEvent data-only nature, ShellPolicy separation rationale, RuntimeTool/RuntimeToolRegistry design intent, and shared-is-leaf constraint.

## Scope
- **In-Scope**: `docs/90_shared_02_02_types_and_protocols-tool-and-execution-dto-part2.md` — restructure to reduce implementation detail while preserving design-intent-critical facts
- **Out-of-Scope**: Other shared/DB chapters (`docs/90_shared_*.md`), source code changes, tests

## Assumptions
- `memo-doc-shared-review.md` is valid and this chapter should describe "why types are in shared/, which boundaries they protect"
- Existing internal links and cross-references must remain valid after editing

## Design decisions
- Compress Section 7c ToolDefinition full field listing: replace with prose describing purpose (immutable tool definition owned by single server)
- Compress Section 8 ArtifactEvent/RetryEvent full TypedDict listings: replace with prose describing event structure categories
- Compress Section 8 future event envelope table: remove entirely — unimplemented feature specification is not current documentation value
- Compress Section 9 ShellPolicy full field listing: replace with prose describing policy categories (commands, paths, timeouts, memory, kill, user, shell, audit, sandbox, env)
- Keep: shared-is-leaf constraint rationale, Protocol vs TypedDict vs dataclass usage policy, RagConfig structural protocol justification, ArtifactEvent data-only nature, ShellPolicy separation rationale, RuntimeTool/RuntimeToolRegistry design intent

## Alternatives considered
- Remove Section 2 entirely: rejected — type overview provides quick lookup that prose does not
- Replace all tables with prose: rejected — tabular format for type overview is efficient for reference
- Merge Sections 4 and 5 into one: rejected — different conceptual domains (config protocol vs search results)

## Implementation
### Target file
`docs/90_shared_02_02_types_and_protocols-tool-and-execution-dto-part2.md`

### Procedure
1. **Phase 1: Preparation**
   - Analyze current document structure and identify which type design judgments are scattered across sections

2. **Phase 2: Core Logic Implementation**
   - Compress or remove Section 7c ToolDefinition full field listing (lines 27-34)
   - Compress or remove Section 8 ArtifactEvent/RetryEvent full TypedDict listings (lines 47-69)
   - Compress or remove Section 8 future event envelope table (lines 79-87)
   - Compress or remove Section 9 ShellPolicy full field listing (lines 94-110)
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
- Section 7c (ToolDefinition): replace field listing with prose: "Immutable tool definition owned by a single server. description and input_schema are reserved fields not yet set by default registry initializer. ToolRegistry handles ownership/routing only; live /v1/tools response used only at startup drift validation, not routing decisions"
- Section 8 (ArtifactEvent/RetryEvent): replace TypedDict listings with prose: "ArtifactEvent (event_type, repo, branch, commit, path, pr_number, session_id, timestamp) — emitted when repo artifact created/updated; RetryEvent (event_type, workflow_id, task_id, attempt_number, max_attempts, error_type, backoff_sec, session_id, timestamp) — emitted on workflow stage retry". Drop future event envelope table — unimplemented feature spec not current documentation value
- Section 9 (ShellPolicy): replace field listing with prose: "Frozen dataclass holding shell execution policy values separated from MCP server implementation. Categories: allowed commands, working directory constraints, timeout/memory limits, kill policy, execution user, shell path, audit log path, sandbox backend, environment allow/denylists. __post_init__ validates kill_policy/sandbox_backend enum values and numeric bounds"
- Remove Related Documents and Keywords sections — content duplicated in frontmatter

## Compatibility considerations
- Cross-references to `scripts/shared/tool_registry.py`, `scripts/shared/events.py`, `scripts/shared/protocols/shell.py` must remain valid after restructuring
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
- Generated at: 20260808-093015
- Related target files: 90_shared_02_02_types_and_protocols-tool-and-execution-dto-part2.md
