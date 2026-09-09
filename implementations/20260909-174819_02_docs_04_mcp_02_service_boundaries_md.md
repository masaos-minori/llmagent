# Implementation Procedure: Remove hand-written port numbers from docs/04_mcp_02_service_boundaries.md

## Plan Reference
- Plan: `plans/20260908-211017_plan.md`
- Row: #2 — `docs/04_mcp_02_service_boundaries.md`
- Requirement: REQ-001
- Freeze Status: Frozen

## Goal
Remove all hand-written literal port numbers from this file while preserving server names and responsibility content intact.

## Scope
**In-Scope**: Remove `(port NNNN)` annotations from heading names in the Per-Server Responsibility Definitions section.

**Out-of-Scope**: The cross-reference link at line 161 ("For authoritative tool-to-server and risk-tier mapping...") — it does not contain port numbers.

## Current Violations
This file has 10 literal-port-number findings per `check_docs_content_policy.py`. Concretely:

### Headings (Per-Server Responsibility Definitions section, lines 19–159)
Each subsection heading embeds a port number inline:
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

## Implementation Steps

### Step 1: Preparation
1. Read `skills/DESIGN.md` Docs content policy — remove/retain definitions.
2. Verify `config/agent.toml` authoritative port assignments for cross-reference.
3. Check `docs/00_governance_03_issue-and-uncertainty-management.md` for Needs Confirmation markers anchored to headings being edited.

### Step 2: Remove port numbers from headings
For each subsection heading under "Per-Server Responsibility Definitions", remove the `(port NNNN)` annotation:
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

### Step 3: Verification
1. Run `uv run python tools/check_docs_content_policy.py docs/04_mcp_02_service_boundaries.md` — expect zero findings.
2. Run `uv run python tools/check_docs_structure.py docs/04_mcp_02_service_boundaries.md` — expect structure check passes.
3. Run `uv run python tools/check_docs_consistency.py --domain mcp` — expect no broken cross-references or drift.
4. Manual review: confirm every Responsibilities / Explicit non-responsibilities section remains coherent after port-number removal.

## Acceptance Criteria
- Zero literal-port-number findings from `check_docs_content_policy.py` on this file [REQ-001]
- No broken cross-references confirmed by `check_docs_consistency.py` [REQ-003]
- Every Responsibilities / Explicit non-responsibilities section reads coherently without port numbers [REQ-003]

## Risks
- **Risk**: Removing port numbers breaks cross-references → **Mitigation**: Run `check_docs_consistency.py` after edits
- **Risk**: Server names become ambiguous without port numbers → **Mitigation**: Each server has one unique name; verify during implementation

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Source plan**: plans/20260908-211017_plan.md
- **Source requirement**: REQ-001
- **Generated at**: 20260909-174819
