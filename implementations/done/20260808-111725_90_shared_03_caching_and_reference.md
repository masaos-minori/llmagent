# Implementation Procedure: Shared — Runtime Caching and Reference Documentation Restructuring

## Goal

Restructure shared design documentation chapter to remove overly detailed signatures, method lists, and other implementation specifics while preserving critical operational guidance on why retries are limited to transient failures, that ToolResultCache is currently not used by ToolExecutor, known caching duplication/disorganization issues, ToolSpec's role as DAG scheduling metadata, HealthRegistry's circuit-breaker-like meaning, and hot-reloadable LLM configuration.

## Scope

**In-Scope:**
- `docs/90_shared_03_04_runtime_and_execution-caching-and-reference-part1.md` — compress LlmRetryHandler signatures, ToolResultCache method lists, ToolSpec dataclass definitions, HealthRegistry full method lists, LlmPayloadHandler/LlmHotConfigHandler method lists, AI reference tables; preserve design rationales
- `docs/90_shared_03_04_runtime_and_execution-caching-and-reference-part2.md` — same compression targets

**Out-of-Scope:**
- Other shared-related chapters (`docs/90_shared_*.md`)
- Source code changes to `scripts/shared/` or `scripts/db/`
- Test modifications

## Assumptions

- `memo-doc-shared-review.md` is valid and this chapter should be the authoritative reference for caching/retry/health auxiliary decisions
- Known caching duplication/disorganization issues must be kept as Known Issues
- Existing internal links and cross-references must remain valid after edits
- Compression preserves the "why" behind each design decision

## Design Decisions

- **Compress over delete**: Remove full signatures, method lists, and verbose processing explanations but keep references to where they live (`scripts/shared/`, etc.)
- **Preserve retry limited to transient failures**: Keep explicit note of why retries are limited to transient failures
- **Preserve ToolResultCache unused by ToolExecutor**: Keep explicit note that ToolResultCache is currently not used by ToolExecutor
- **Preserve known caching duplication/disorganization issues**: Keep explicit note of known caching issues
- **Preserve ToolSpec DAG scheduling metadata role**: Keep explicit statement of ToolSpec's role as DAG scheduling metadata
- **Preserve HealthRegistry circuit-breaker-like meaning**: Keep explicit note of HealthRegistry's circuit-breaker-like semantics
- **Preserve hot-reloadable LLM configuration**: Keep explicit note of hot-reloadable LLM configuration

## Alternatives Considered

1. **Full deletion of method lists** — Rejected: loses traceability to source implementations
2. **Move to appendix** — Rejected: fragments the document unnecessarily
3. **Inline cross-references only** — Chosen: balances brevity with traceability

## Implementation

### Target Files

| File | Action |
|------|--------|
| `docs/90_shared_03_04_runtime_and_execution-caching-and-reference-part1.md` | Compress LlmRetryHandler signatures, ToolResultCache methods, ToolSpec dataclass defs, HealthRegistry methods, LlmPayloadHandler/LlmHotConfigHandler methods, AI reference tables; preserve design rationales |
| `docs/90_shared_03_04_runtime_and_execution-caching-and-reference-part2.md` | Same compression targets |

### Procedure

1. Read both target files to understand current structure
2. For each section containing overly detailed definitions, replace with prose summary that references source files
3. Preserve all design rationale paragraphs (retry limited to transient failures, ToolResultCache unused by ToolExecutor, known caching duplication/disorganization issues, ToolSpec DAG scheduling metadata role, HealthRegistry circuit-breaker-like meaning, hot-reloadable LLM configuration)
4. Verify all internal Markdown links remain valid after edits
5. Confirm each design decision's "why" is explicitly stated

### Method

For each target section:
1. Locate the section containing the full definition (grep for key identifiers like `LlmRetryHandler`, `ToolResultCache`, `HealthRegistry`, etc.)
2. Read the surrounding context (5-10 lines before/after) to preserve relationships
3. Replace the definition block with a summary paragraph:
   - State what the component represents (1 sentence)
   - Note its purpose in the DB architecture
   - Reference where the full definition lives (e.g., `scripts/shared/`)
4. Leave any design rationale paragraphs untouched

### Details

**File: `90_shared_03_04_runtime_and_execution-caching-and-reference-part1.md`**
- LlmRetryHandler signatures: Replace with prose summary referencing `scripts/shared/`
- ToolResultCache method lists: Replace with prose summary
- ToolSpec dataclass definitions: Replace with prose summary
- HealthRegistry full method list: Replace with prose summary
- LlmPayloadHandler/LlmHotConfigHandler method lists: Replace with prose summary
- AI reference tables: Replace with prose summary

**File: `90_shared_03_04_runtime_and_execution-caching-and-reference-part2.md`**
- Same compression targets as part1

## Compatibility Considerations

- All compression targets are documentation-only; no API contract changes
- Internal cross-references to `scripts/shared/` cache/retry/health infrastructure modules must remain accurate
- Any downstream consumers of these docs (e.g., AI agent prompts) should still receive sufficient information about ToolResultCache unused note and cache duplication known issue
- Known issue note about caching duplication must be preserved
- ToolResultCache unused note must be verified as clear
- Cache duplication known issue flag must be verified as clear

## Security Considerations

N/A — documentation restructuring only; no security-sensitive content involved.

## Rollback Considerations

- Before making changes, commit current state: `git add docs/ && git commit -m "pre-restructure snapshot"`
- After edits, verify with `git diff --stat` to confirm only documentation changed
- If internal links break, revert to pre-change state and adjust compression strategy

## Validation Plan

| Check | Tool | Target |
|-------|------|--------|
| ToolResultCache unused note preserved | Manual | Explicitly stated |
| Cache duplication known issue preserved | Manual | Explicitly flagged as Known Issue |
| Cross-references valid | Manual | All removed details point to `scripts/shared/` cache/retry/health modules |
| Internal links valid | Manual | All Markdown links resolve correctly |
| Template compliance | Manual | Follows `memo-doc-shared-review.md` §「修正後の章構成テンプレート」 |
| No full signatures/method lists remain | Manual | Scanning for remaining verbose definitions |

## Out of Scope

- Modifying source type definitions in `scripts/shared/` or `scripts/db/`
- Adding new types or changing existing ones
- Updating test coverage for type definitions
- Changes to other shared chapters beyond the two target files

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260807-215432_plan.md
- Source implementation procedure: N/A
- Generated at: 20260808-111725
- Related target files: docs/90_shared_03_04_runtime_and_execution-caching-and-reference-part1.md, docs/90_shared_03_04_runtime_and_execution-caching-and-reference-part2.md
