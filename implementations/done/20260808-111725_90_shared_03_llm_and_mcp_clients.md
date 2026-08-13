# Implementation Procedure: Shared — Runtime LLM and MCP Clients Documentation Restructuring

## Goal

Restructure shared design documentation chapter to remove overly detailed constructor signatures, error enumerations, and other implementation specifics while preserving critical operational guidance on LLMClient's HTTP/retry/SSE/error classification responsibility, why SSE design is delegated to Agent design docs, operational meaning of LLMTransportError, criteria for retryable vs fatal, that handling errors with partial_text is the agent's responsibility, McpServerConfig's role as shared contract, HealthRegistry's support for MCP transport availability determination, and load_all() configuration boundary that reads only agent.toml.

## Scope

**In-Scope:**
- `docs/90_shared_03_03_runtime_and_execution-llm-and-mcp-clients-part1.md` — compress full LLMClient constructor signatures, mechanical error type enumerations, complete list of statistics attributes, complete list of apply_config target fields, McpServerConfig field explanations, exhaustive enum value tables, execution flow pseudocode; preserve design rationales
- `docs/90_shared_03_03_runtime_and_execution-llm-and-mcp-clients-part2.md` — same compression targets

**Out-of-Scope:**
- Other shared-related chapters (`docs/90_shared_*.md`)
- Source code changes to `scripts/shared/` or `scripts/db/`
- Test modifications

## Assumptions

- `memo-doc-shared-review.md` is valid and this chapter should be the authoritative reference for LLM/MCP common client boundary decisions
- Both files cover the same conceptual area and must be treated together
- Existing internal links and cross-references must remain valid after edits
- Compression preserves the "why" behind each design decision

## Design Decisions

- **Compress over delete**: Remove full signatures, error lists, and verbose processing explanations but keep references to where they live (`scripts/shared/llm_client.py`, `scripts/shared/mcp_config.py`, `scripts/shared/mcp_health.py`, etc.)
- **Preserve LLMClient HTTP communication/retry/SSE/error classification**: Keep explicit note of LLMClient's responsibilities
- **Preserve SSE design delegated to Agent design docs**: Keep explicit note that SSE design is delegated
- **Preserve LLMTransportError operational meaning**: Keep explicit statement of LLMTransportError's operational meaning
- **Preserve retryable vs fatal criteria**: Keep explicit note of criteria for retryable vs fatal
- **Preserve partial_text error handling agent-side responsibility**: Keep explicit note that handling errors with partial_text is the agent's responsibility
- **Preserve McpServerConfig shared contract role**: Keep explicit note of McpServerConfig's role as shared contract
- **Preserve HealthRegistry MCP transport availability determination support**: Keep explicit note of HealthRegistry's support for MCP transport availability
- **Preserve load_all() reads only agent.toml**: Keep explicit note of load_all() configuration boundary

## Alternatives Considered

1. **Full deletion of constructor signatures** — Rejected: loses traceability to source implementations
2. **Move to appendix** — Rejected: fragments the document unnecessarily
3. **Inline cross-references only** — Chosen: balances brevity with traceability

## Implementation

### Target Files

| File | Action |
|------|--------|
| `docs/90_shared_03_03_runtime_and_execution-llm-and-mcp-clients-part1.md` | Compress LLMClient constructors, error enumerations, stats attributes, apply_config fields, McpServerConfig fields, enum tables, execution pseudocode; preserve design rationales |
| `docs/90_shared_03_03_runtime_and_execution-llm-and-mcp-clients-part2.md` | Same compression targets |

### Procedure

1. Read both target files to understand current structure
2. For each section containing overly detailed definitions, replace with prose summary that references source files
3. Preserve all design rationale paragraphs (LLMClient HTTP/retry/SSE/error classification, SSE design delegation, LLMTransportError operational meaning, retryable vs fatal criteria, partial_text error handling agent-side responsibility, McpServerConfig shared contract role, HealthRegistry MCP transport availability support, load_all() reads only agent.toml)
4. Verify all internal Markdown links remain valid after edits
5. Confirm each design decision's "why" is explicitly stated

### Method

For each target section:
1. Locate the section containing the full definition (grep for key identifiers like `LLMClient`, `LLMTransportError`, `McpServerConfig`, etc.)
2. Read the surrounding context (5-10 lines before/after) to preserve relationships
3. Replace the definition block with a summary paragraph:
   - State what the component represents (1 sentence)
   - Note its purpose in the DB architecture
   - Reference where the full definition lives (e.g., `scripts/shared/llm_client.py`)
4. Leave any design rationale paragraphs untouched

### Details

**File: `90_shared_03_03_runtime_and_execution-llm-and-mcp-clients-part1.md`**
- Full LLMClient constructor signatures: Replace with prose summary referencing `scripts/shared/llm_client.py`
- Mechanical error type enumerations: Replace with prose summary
- Complete list of statistics attributes: Replace with prose summary
- Complete list of apply_config target fields: Replace with prose summary
- McpServerConfig field explanations: Replace with prose summary referencing `scripts/shared/mcp_config.py`
- Exhaustive enum value tables: Replace with prose summary
- Execution flow pseudocode: Replace with prose summary

**File: `90_shared_03_03_runtime_and_execution-llm-and-mcp-clients-part2.md`**
- Same compression targets as part1

## Compatibility Considerations

- All compression targets are documentation-only; no API contract changes
- Internal cross-references to `scripts/shared/llm_client.py`, `scripts/shared/mcp_config.py`, and `scripts/shared/mcp_health.py` must remain accurate
- Any downstream consumers of these docs (e.g., AI agent prompts) should still receive sufficient information about retryable/fatal criteria and partial_text handling statements
- Known issue note about caching duplication must be preserved
- retryable/fatal criteria must be verified as clear
- partial_text handling statement must be verified as clear

## Security Considerations

N/A — documentation restructuring only; no security-sensitive content involved.

## Rollback Considerations

- Before making changes, commit current state: `git add docs/ && git commit -m "pre-restructure snapshot"`
- After edits, verify with `git diff --stat` to confirm only documentation changed
- If internal links break, revert to pre-change state and adjust compression strategy

## Validation Plan

| Check | Tool | Target |
|-------|------|--------|
| retryable/fatal criteria preserved | Manual | Explicitly stated |
| partial_text handling statement preserved | Manual | Explicitly stated |
| Cross-references valid | Manual | All removed details point to `scripts/shared/llm_client.py` / `mcp_config.py` / `mcp_health.py` |
| Internal links valid | Manual | All Markdown links resolve correctly |
| Template compliance | Manual | Follows `memo-doc-shared-review.md` §「修正後の章構成テンプレート」 |
| No full constructor signatures/error enumerations remain | Manual | Scanning for remaining verbose definitions |

## Out of Scope

- Modifying source type definitions in `scripts/shared/` or `scripts/db/`
- Adding new types or changing existing ones
- Updating test coverage for type definitions
- Changes to other shared chapters beyond the two target files

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260807-215545_plan.md
- Source implementation procedure: N/A
- Generated at: 20260808-111725
- Related target files: docs/90_shared_03_03_runtime_and_execution-llm-and-mcp-clients-part1.md, docs/90_shared_03_03_runtime_and_execution-llm-and-mcp-clients-part2.md
