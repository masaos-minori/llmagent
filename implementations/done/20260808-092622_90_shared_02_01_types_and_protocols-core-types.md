## Goal
- Restructure `docs/90_shared_02_01_types_and_protocols-core-types.md` to remove overly detailed field definitions and type comparison tables while explicitly preserving why common types belong in shared/, why LLM DTOs can be imported without LLMClient, Protocol/TypedDict/dataclass usage policy, why RagConfig is a structural protocol, that ArtifactEvent is data-only, ShellPolicy separates policy values from shell MCP implementations, RuntimeTool/RuntimeToolRegistry design intent, and shared-is-leaf constraint.

## Scope
- **In-Scope**: `docs/90_shared_02_01_types_and_protocols-core-types.md` — restructure to reduce implementation detail while preserving design-intent-critical facts
- **Out-of-Scope**: Other shared/DB chapters (`docs/90_shared_*.md`), source code changes, tests

## Assumptions
- `memo-doc-shared-review.md` is valid and this chapter should describe "why types are in shared/, which boundaries they protect"
- Existing internal links and cross-references must remain valid after editing

## Design decisions
- Compress Section 2 type overview table: keep type name + category columns, drop file path column (deferred to source code), drop layer utilization column (redundant with section headers)
- Compress Section 3 LLMMessage full field definition (lines 61-73): replace with prose description of field categories (required role, optional content/tool_calls, ephemeral markers, source validation)
- Compress Section 3 related TypedDict table: replace with prose list of streaming-related auxiliary types
- Compress Section 4 RagConfig Protocol fields: replace full field listing with prose summary of configuration categories (cache, search, rerank, refiner, semantic cache)
- Compress Section 5 hit-type dataclass definitions (lines 133-167): replace with prose describing the progression chain (RawHit → MergedHit adds rrf_score → RankedHit adds rerank_score)
- Keep: shared-is-leaf constraint rationale, Protocol vs TypedDict vs dataclass usage policy, RagConfig structural protocol justification, ArtifactEvent data-only nature, ShellPolicy separation rationale, RuntimeTool/RuntimeToolRegistry design intent

## Alternatives considered
- Remove Section 2 entirely: rejected — type overview provides quick lookup that prose does not
- Replace all tables with prose: rejected — tabular format for type overview is efficient for reference
- Merge Sections 4 and 5 into one: rejected — different conceptual domains (config protocol vs search results)

## Implementation
### Target file
`docs/90_shared_02_01_types_and_protocols-core-types.md`

### Procedure
1. **Phase 1: Preparation**
   - Analyze current document structure and identify which type design judgments are scattered across sections

2. **Phase 2: Core Logic Implementation**
   - Compress or remove Section 2 type overview table's file path and layer utilization columns
   - Compress or remove Section 3 LLMMessage full field definition (lines 61-73)
   - Compress or remove Section 3 related TypedDict table (ToolCallFunction-family enumeration)
   - Compress or remove Section 4 RagConfig Protocol field listing (19 fields)
   - Compress or remove Section 5 RawHit/MergedHit/RankedHit dataclass definitions (lines 133-167)
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
- Section 2 (type overview): reduce from 4-column table to 2-column (type name | category). File path deferred to source code, layer utilization redundant with section headers
- Section 3 (LLMMessage): replace full field listing with prose: "role (required), content/tool_calls (conditional on role), importance/pinned (compression), _ephemeral/_skill_ephemeral/_memory_injected (lifecycle), source (validation)". Drop ToolCallFunction-family TypedDict table — streaming types are implementation detail
- Section 4 (RagConfig): replace 19-field Protocol listing with prose: "semantic cache config, search parameters (top_k, rag_top_k), rerank params (use_rerank, top_k_rerank, rag_min_score, use_rrf, rrf_k), refiner config (max_tokens, max_chars_per_chunk, timeout), service URL/auth". Keep @runtime_checkable note
- Section 5 (hit types): replace 3 dataclass listings with prose: "RawHit (base: chunk_id, content, url, title, distance, bm25_score) → MergedHit adds rrf_score → RankedHit adds rerank_score | None". Keep RagHit Union alias note
- Remove Related Documents and Keywords sections — content duplicated in frontmatter

## Compatibility considerations
- Cross-references to `scripts/shared/types.py` and other type-defining modules must remain valid after restructuring
- Internal Markdown links must be verified against actual file paths in `docs/90_shared_*` directory
- No change to source code contracts — document-only modification

## Security considerations
- N/A — document-only modification, no security-sensitive content affected

## Rollback considerations
- If restructuring causes link breakage, revert to original structure and apply targeted compression instead of full rewrite
- All removed details point to source files (`scripts/shared/types.py`, `scripts/shared/llm_types.py`, etc.) for verification

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
- Generated at: 20260808-092622
- Related target files: 90_shared_02_01_types_and_protocols-core-types.md
