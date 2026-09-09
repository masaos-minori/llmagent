# Implementation Procedure: Remove hand-written port numbers from docs/04_mcp_01_tool_ownership_matrix.md

## Plan Reference
- Plan: `plans/20260908-211017_plan.md`
- Row: #1 — `docs/04_mcp_01_tool_ownership_matrix.md`
- Requirement: REQ-001
- Freeze Status: Frozen

## Goal
Remove all hand-written literal port numbers from this file while preserving server names and responsibility content intact. Leave the `<!-- AUTO-GENERATED -->` block untouched.

## Scope
**In-Scope**: Remove `(port NNNN)` annotations from table cells in the Tool-to-MCP Server Mapping table, and from heading names in the Responsibility Boundaries section. Update the note text that references port numbers.

**Out-of-Scope**: The `<!-- AUTO-GENERATED -->` / `<!-- END AUTO-GENERATED -->` block at the end of the file (disposition is `dcp001`).

## Current Violations
This file has 26 literal-port-number findings per `check_docs_content_policy.py`. Concretely:

### Table cells (Tool-to-MCP Server Mapping table, rows 22–36)
Each row in the second column ("Owning MCP Server") embeds a port number inline:
```
file-read-mcp (port 8005)
file-write-mcp (port 8007)
file-delete-mcp (port 8008)
rag-pipeline-mcp (port 8010)
cicd-mcp (port 8012)
mdq-mcp (port 8013)
git-mcp (port 8014)
shell-mcp (port 8009)
web-search-mcp (port 8004)
github-mcp (port 8006)
```

### Headings (Responsibility Boundaries section, lines 64–161)
Each subsection heading repeats the same pattern:
```
### file-read-mcp (port 8005)
### file-write-mcp (port 8007)
### file-delete-mcp (port 8008)
### rag-pipeline-mcp (port 8010)
### cicd-mcp (port 8012)
### mdq-mcp (port 8013)
### git-mcp (port 8014)
### shell-mcp (port 8009)
### web-search-mcp (port 8004)
### github-mcp (port 8006)
```

### Prose (lines 41–43)
The note paragraph contains:
```
Port numbers and tool membership above are kept in sync with the auto-generated reference table below — see `tools/gen_mcp_reference.py`.
```

## Implementation Steps

### Step 1: Preparation
1. Read `skills/DESIGN.md` Docs content policy — remove/retain definitions.
2. Verify `config/agent.toml` authoritative port assignments for cross-reference.
3. Check `docs/00_governance_03_issue-and-uncertainty-management.md` for Needs Confirmation markers anchored to headings being edited.

### Step 2: Remove port numbers from table cells
For each row in the Tool-to-MCP Server Mapping table (rows 22–36), replace the second column value:
- Before: `file-read-mcp (port 8005)` → After: `file-read-mcp`
- Before: `file-write-mcp (port 8007)` → After: `file-write-mcp`
- Before: `file-delete-mcp (port 8008)` → After: `file-delete-mcp`
- Before: `rag-pipeline-mcp (port 8010)` → After: `rag-pipeline-mcp`
- Before: `cicd-mcp (port 8012)` → After: `cicd-mcp`
- Before: `mdq-mcp (port 8013)` → After: `mdq-mcp`
- Before: `git-mcp (port 8014)` → After: `git-mcp`
- Before: `shell-mcp (port 8009)` → After: `shell-mcp`
- Before: `web-search-mcp (port 8004)` → After: `web-search-mcp`
- Before: `github-mcp (port 8006)` → After: `github-mcp`

### Step 3: Remove port numbers from headings
For each subsection heading under "Responsibility Boundaries", remove the `(port NNNN)` annotation:
- Before: `### file-read-mcp (port 8005)` → After: `### file-read-mcp`
- Before: `### file-write-mcp (port 8007)` → After: `### file-write-mcp`
- Before: `### file-delete-mcp (port 8008)` → After: `### file-delete-mcp`
- Before: `### rag-pipeline-mcp (port 8010)` → After: `### rag-pipeline-mcp`
- Before: `### cicd-mcp (port 8012)` → After: `### cicd-mcp`
- Before: `### mdq-mcp (port 8013)` → After: `### mdq-mcp`
- Before: `### git-mcp (port 8014)` → After: `### git-mcp`
- Before: `### shell-mcp (port 8009)` → After: `### shell-mcp`
- Before: `### web-search-mcp (port 8004)` → After: `### web-search-mcp`
- Before: `### github-mcp (port 8006)` → After: `### github-mcp`

### Step 4: Update prose referencing port numbers
Edit the note paragraph (lines 41–43):
- Before: `Port numbers and tool membership above are kept in sync with the auto-generated reference table below — see \`tools/gen_mcp_reference.py\`.`
- After: `Tool membership above is kept in sync with the auto-generated reference table below — see \`tools/gen_mcp_reference.py\`.`

### Step 5: Verification
1. Run `uv run python tools/check_docs_content_policy.py docs/04_mcp_01_tool_ownership_matrix.md` — expect zero findings.
2. Run `uv run python tools/check_docs_structure.py docs/04_mcp_01_tool_ownership_matrix.md` — expect structure check passes.
3. Run `uv run python tools/check_docs_consistency.py --domain mcp` — expect no broken cross-references or drift.
4. Manual review: confirm every Responsibilities / Explicit non-responsibilities section remains coherent after port-number removal.

## Acceptance Criteria
- Zero literal-port-number findings from `check_docs_content_policy.py` on this file [REQ-001]
- No broken cross-references confirmed by `check_docs_consistency.py` [REQ-003]
- Every Responsibilities / Explicit non-responsibilities section reads coherently without port numbers [REQ-003]
- The `<!-- AUTO-GENERATED -->` block is untouched [REQ-002]

## Risks
- **Risk**: Removing port numbers breaks cross-references → **Mitigation**: Run `check_docs_consistency.py` after edits
- **Risk**: Server names become ambiguous without port numbers → **Mitigation**: Each server has one unique name; verify during implementation
- **Risk**: Auto-generated block accidentally modified → **Mitigation**: Explicitly skip `<!-- AUTO-GENERATED -->` section

## Execution Status

| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Identify the target implementation procedure file(s) | Completed | — | — | |
| 2 | Read the current implementation procedure file | Completed | — | — | |
| 3 | Implement the feature and pass code validation | Completed | — | — | Removed all `(port NNNN)` from table cells and headings; updated prose |
| 4 | Test the feature and pass required tests/coverage | Completed | — | — | No test changes required |
| 5 | Update documentation per `docs/00_index.md` task-scope mapping | Completed | — | — | No docs/00_index.md task-scope row matched |
| 6 | Validate documentation updates | Completed | — | — | check_docs_content_policy.py: 0 findings; check_docs_structure.py: 1 pre-existing issue (source ref); check_docs_consistency.py: 0 findings for this file |
| 7 | Move the implementation procedure file to `implementations/done/` | Pending | — | — | |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Source plan**: plans/20260908-211017_plan.md
- **Source requirement**: REQ-001
- **Generated at**: 20260909-174819
