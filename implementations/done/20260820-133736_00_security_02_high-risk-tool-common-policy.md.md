# Implementation Procedure: Create High-Risk Tool Common Policy Document

## Goal
Create `docs/00_security_02_high-risk-tool-common-policy.md` as a new cross-cutting common policy document for file-write, file-delete, shell, git, github, cicd, and DB-maintenance-class MCP tools, consolidating allowed paths/repos, command allowlists, argument validation, path-traversal prevention, symlink-traversal prevention, approval requirements mapped to risk tiers, audit fields, production restrictions, and failure behavior.

## Scope
- Target file: `docs/00_security_02_high-risk-tool-common-policy.md` (new file)
- Create document with 11 sections per plan Design §00_security_02 structure
- YAML front matter matching project convention
- Generalize mdq-only traversal prevention language to all filesystem-touching high-risk tools
- Tool-specific exceptions documented separately in each tool's own doc

## Assumptions
- File-write/delete MCP tools already perform `Path.resolve()`-based path jailing (confirmed in `scripts/mcp_servers/file/write_service.py`, `delete_service.py`, `common.py`, `read_security.py`)
- mdq docs already use "path-traversal"/"symlink-traversal" terminology; this doc generalizes it
- Git/GitHub/CI/CD/DB-maintenance tool docs are out of scope for cross-references in this plan (requirement's Target files list omits them)

## Design decisions
- Follow `00_governance_NN_*` cross-cutting precedent (`00_security_02_*`)
- Explicit statement that exceptions live in each tool's own doc (not merged into common policy)
- Common policy references `agent/tool_arg_validator.py::validate_tool_arguments()` for argument validation
- Path/symlink-traversal prevention generalized from mdq-only language

## Alternatives considered
- Merge exceptions into common policy body: Rejected — per requirement's "documented separately from the common policy body, with clear references"
- Domain-scoped numbering: Rejected — content spans multiple domains

## Implementation
### Target file
`docs/00_security_02_high-risk-tool-common-policy.md`

### Procedure
1. Create new file with YAML front matter
2. Write 11 sections per Design §00_security_02 structure
3. Add `Related Documents` and `Keywords` footer sections

### Method
New Markdown file creation with exact structure

### Details
**YAML Front Matter:**
```yaml
---
title: "High-Risk MCP Tool Common Policy"
category: security
tags:
  - security
  - policy
  - high-risk-tools
  - path-traversal
  - approval
  - audit
related:
  - 00_security_01_architecture-and-trust-boundaries.md
  - 00_governance_01_documentation-governance.md
  - 00_governance_02_canonical-source-rule.md
  - 04_mcp_05_01_access-control-and-allowlists.md
  - 04_mcp_05_03_fail-open-fail-closed-and-risk-tiers.md
  - 05_agent_06_01_tool-execution-and-approval-execution.md
  - 04_mcp_04_02_file-write-file-delete-shell.md
  - 04_mcp_04_04_mdq.md
  - 04_mcp_05_05_mdq-enforcement-and-lockdown.md
  - 05_agent_06_01_tool-execution-and-approval-execution.md
  - 05_agent_06_02_tool-execution-and-approval-approval.md
  - 04_mcp_06_16_pre-production-fail-open-checklist.md
  - 04_mcp_02_03_audit-logging-and-errors.md
source:
  - 00_security_02_high-risk-tool-common-policy.md
---
```

**Section Structure (11 sections):**

1. **Purpose / scope** — Which tools this policy governs: file-write, file-delete, shell, git, github, cicd, DB maintenance — mdq included as reference implementation of traversal prevention.

2. **Allowed paths/repos** — Common shape (`allowed_dirs`/`allowed_repo_paths`/`allowed_repos`, all fail-closed on empty) — sourced from `04_mcp_05_01`.

3. **Command allowlists** — Sourced from `04_mcp_05_01` §コマンドAllowlist.

4. **Argument validation** — Pointer to `agent/tool_arg_validator.py::validate_tool_arguments()` per `05_agent_06_01`.

5. **Path-traversal prevention** — Common statement: all filesystem-touching tools resolve paths via `Path.resolve()` before comparison against the allowlist root — generalizes language currently found only in `04_mcp_04_04_mdq.md` / `04_mcp_05_05_mdq-enforcement-and-lockdown.md`.

6. **Symlink-traversal prevention** — Same generalization — `Path.resolve()` follows and normalizes symlinks before the allowlist check.

7. **Approval requirements mapped explicitly to risk tiers** — Reproduces the `READ_ONLY` / `WRITE_SAFE` / `WRITE_DANGEROUS` / `ADMIN` table from `04_mcp_05_03` §リスクティア分類 as the authoritative approval-to-tier mapping, cross-linked with `05_agent_06_01`/`05_agent_06_02` for the approval-execution flow.

8. **Audit fields** — Sourced from `04_mcp_02_03`.

9. **Production restrictions** — Sourced from `04_mcp_06_16`.

10. **Failure behavior** — Fail-closed-by-default statement, cross-linked to `00_security_01` §Fail-open-vs-fail-closed.

11. **Tool-specific exceptions** — Explicit statement that exceptions live in each tool's own doc (e.g., github's `protected_branches`/`path_denylist` are fail-open by design, documented in `04_mcp_05_01`), not merged into this policy body.

**Footer Sections:**
- `Related Documents` — list of cross-referenced docs
- `Keywords` — security, policy, high-risk-tools, path-traversal, approval, audit, symlink-traversal

## Compatibility considerations
- New document only; no existing content modified
- Bidirectional cross-references with `00_security_01` doc

## Security considerations
- Documents common security policy; no implementation details exposed
- Fail-closed-by-default is a security posture statement

## Rollback considerations
- Git revert (delete file) if issues arise

## Validation plan
- Cross-check policy vs actual enforcement code: `rg -n "resolve\(\)|allowed_dirs|allowed_repos|command_allowlist" scripts/mcp_servers/`
- No discrepancy between documented common policy and actual code paths for file-write, file-delete, shell, git, github, mdq
- `uv run check-mcp-docs` — no new broken internal links

## Out of scope
- No code changes
- No changes to existing docs' technical content (cross-refs added in separate procedure)
- Git/github/cicd/db-maintenance tool docs cross-references (out of scope per requirement's Target files list)

## Traceability
- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: requires/done/20260818-221156_require.md
- Source plan: plans/20260819-174040_plan.md
- Source implementation procedure: N/A
- Generated at: 20260820-133736
- Related target files: docs/00_security_02_high-risk-tool-common-policy.md