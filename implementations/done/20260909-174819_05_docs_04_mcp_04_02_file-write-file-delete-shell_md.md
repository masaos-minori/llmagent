# Implementation Procedure: Remove hand-written port numbers from docs/04_mcp_04_02_file-write-file-delete-shell.md

## Plan Reference
- Plan: `plans/20260908-211017_plan.md`
- Row: #5 — `docs/04_mcp_04_02_file-write-file-delete-shell.md`
- Requirement: REQ-001
- Freeze Status: Frozen

## Goal
Remove all hand-written literal port numbers from this file while preserving server names and responsibility content intact.

## Scope
**In-Scope**: Remove `(Port NNNN)` annotations from heading names and prose text that contains port numbers.

**Out-of-Scope**: Configuration parameter defaults (e.g., `HARD_MAX_RESULTS_LIMIT=100`), file paths, and other non-port-number literals.

## Current Violations
This file has 4 literal-port-number findings per `check_docs_content_policy.py`. Concretely:

### Headings (lines 13, 47, 81)
```
## file-write-mcp (Port 8007)
## file-delete-mcp (Port 8008)
## shell-mcp (Port 8009)
```

### Prose (line 135)
```
file-write-mcp, file-delete-mcp, shell-mcp, port 8007, port 8008, port 8009
```

## Implementation Steps

### Step 1: Preparation
1. Read `skills/DESIGN.md` Docs content policy — remove/retain definitions.
2. Verify `config/agent.toml` authoritative port assignments for cross-reference.
3. Check `docs/00_governance_03_issue-and-uncertainty-management.md` for Needs Confirmation markers anchored to headings being edited.

### Step 2: Remove port numbers from headings
For each subsection heading, remove the `(Port NNNN)` annotation:
- Before: `## file-write-mcp (Port 8007)` → After: `## file-write-mcp`
- Before: `## file-delete-mcp (Port 8008)` → After: `## file-delete-mcp`
- Before: `## shell-mcp (Port 8009)` → After: `## shell-mcp`

### Step 3: Remove port numbers from prose
Edit line 135 (Keywords section):
- Before: `file-write-mcp, file-delete-mcp, shell-mcp, port 8007, port 8008, port 8009`
- After: `file-write-mcp, file-delete-mcp, shell-mcp`

### Step 4: Verification
1. Run `uv run python tools/check_docs_content_policy.py docs/04_mcp_04_02_file-write-file-delete-shell.md` — expect zero findings.
2. Run `uv run python tools/check_docs_structure.py docs/04_mcp_04_02_file-write-file-delete-shell.md` — expect structure check passes.
3. Run `uv run python tools/check_docs_consistency.py --domain mcp` — expect no broken cross-references or drift.
4. Manual review: confirm every Responsibilities / Explicit non-responsibilities section remains coherent after port-number removal.

## Acceptance Criteria
- Zero literal-port-number findings from `check_docs_content_policy.py` on this file [REQ-001]
- No broken cross-references confirmed by `check_docs_consistency.py` [REQ-003]
- Every Responsibilities / Explicit non-responsibilities section reads coherently without port numbers [REQ-003]

## Risks
- **Risk**: Removing port numbers breaks cross-references → **Mitigation**: Run `check_docs_consistency.py` after edits
- **Risk**: Server names become ambiguous without port numbers → **Mitigation**: Each server has one unique name; verify during implementation

## Execution Status

| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Identify the target implementation procedure file(s) | Completed | — | — | |
| 2 | Read the current implementation procedure file | Completed | — | — | |
| 3 | Implement the feature and pass code validation | Completed | — | — | Removed all `(Port NNNN)` from headings and prose |
| 4 | Test the feature and pass required tests/coverage | Completed | — | — | No test changes required |
| 5 | Update documentation per `docs/00_index.md` task-scope mapping | Completed | — | — | No docs/00_index.md task-scope row matched |
| 6 | Validate documentation updates | Completed | — | — | check_docs_content_policy.py: 0 findings |
| 7 | Move the implementation procedure file to `implementations/done/` | Pending | — | — | |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Source plan**: plans/20260908-211017_plan.md
- **Source requirement**: REQ-001
- **Generated at**: 20260909-174819
