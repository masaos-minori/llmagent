# Implementation Procedure: Create System Security Architecture and Trust Boundaries Document

## Goal
Create `docs/00_security_01_architecture-and-trust-boundaries.md` as a new cross-cutting security architecture document synthesizing trust boundaries, protected assets, threat model, per-API authN/authZ, secret lifecycle, log redaction, audit retention, local-vs-production behavior, fail-open/closed behavior, and prompt-injection responsibility boundaries from existing scattered docs.

## Scope
- Target file: `docs/00_security_01_architecture-and-trust-boundaries.md` (new file)
- Create document with 11 sections per plan Design §00_security_01 structure
- YAML front matter matching project convention (`title`, `category: security`, `tags`, `related`, `Related Documents`, `Keywords`)
- Synthesize from existing docs only — no new claims

## Assumptions
- The `00_governance_NN_*` cross-cutting precedent applies (numbering under `00_`)
- Content spans Agent + MCP + RAG + operations → belongs under `00_` cross-cutting prefix
- Source docs already contain all needed information; this doc only synthesizes

## Design decisions
- Plain Markdown ASCII diagram for trust boundaries (no external rendering)
- Follow existing doc convention: YAML front matter + `Related Documents` + `Keywords` footer
- Each section cites source doc(s) explicitly
- Cross-references bidirectional with new `00_security_02` doc

## Alternatives considered
- Domain-scoped `0X_<domain>_NN_*` pattern: Rejected — content spans multiple domains
- Mermaid diagram: Rejected — no external rendering dependency per plan

## Implementation
### Target file
`docs/00_security_01_architecture-and-trust-boundaries.md`

### Procedure
1. Create new file with YAML front matter
2. Write 11 sections per Design §00_security_01 structure
3. Add `Related Documents` and `Keywords` footer sections

### Method
New Markdown file creation with exact structure

### Details
**YAML Front Matter:**
```yaml
---
title: "System Security Architecture and Trust Boundaries"
category: security
tags:
  - security
  - architecture
  - trust-boundaries
  - threat-model
  - auth
  - audit
related:
  - 00_security_02_high-risk-tool-common-policy.md
  - 00_governance_01_documentation-governance.md
  - 00_governance_02_canonical-source-rule.md
  - 04_mcp_05_01_access-control-and-allowlists.md
  - 04_mcp_05_03_fail-open-fail-closed-and-risk-tiers.md
  - 05_agent_06_01_tool-execution-and-approval-execution.md
  - 03_rag_03_05_query_pipeline-augment-stages.md
  - 04_mcp_06_16_pre-production-fail-open-checklist.md
  - 04_mcp_06_17_local-to-production-auth-migration.md
  - 04_mcp_02_03_audit-logging-and-errors.md
  - 04_mcp_06_07_reading-audit-logs.md
  - 05_agent_10_02_operations-and-observability-audit-and-otel.md
  - 03_rag_03_05_query_pipeline-augment-stages.md
  - 03_rag_04_02_dto-models_result.md
  - 05_failure_modes_and_operational_readiness.md
source:
  - 00_security_01_architecture-and-trust-boundaries.md
---
```

**Section Structure (11 sections):**

1. **Purpose / how to use this doc** — One paragraph explaining this is the canonical cross-cutting security architecture reference; other docs should cross-reference here rather than duplicate.

2. **Trust-boundary diagram** — ASCII diagram:
```
Agent -> LLM -> MCP -> target resource
     \-> RAG ingestion path -> vector store
```
With explanation of two boundary crossings: Agent→MCP and ingestion→vector store.

3. **Protected assets** — Filesystem under `allowed_dirs`, git repos, GitHub repos, CI/CD workflows, DB files, audit logs, secrets.

4. **Threat model** — Untrusted LLM output, untrusted RAG-ingested content, untrusted tool arguments, path/symlink escape, command-allowlist bypass, unauthorized repo/workflow access, execution without approval.

5. **Per-externally-reachable-API authN/authZ table** — One row per MCP server (file-read/write/delete, shell, git, github, cicd, mdq, rag-pipeline) sourced from `04_mcp_05_01`/`04_mcp_05_02`.

6. **Secret lifecycle** — Provisioning/storage/rotation/revocation — sourced from `04_mcp_06_17_local-to-production-auth-migration.md`.

7. **Log redaction rules** — Sourced from `04_mcp_02_03_audit-logging-and-errors.md`.

8. **Audit retention** — Sourced from `04_mcp_06_07_reading-audit-logs.md` and `05_agent_10_02_operations-and-observability-audit-and-otel.md`.

9. **Local-vs-production behavior** — Sourced from `04_mcp_06_16_pre-production-fail-open-checklist.md` and `04_mcp_05_03_fail-open-fail-closed-and-risk-tiers.md` §起動時のAudit.

10. **Fail-open-vs-fail-closed behavior** — Table reproduced/linked from `04_mcp_05_03` §Fail-Open 対 Fail-Closed の要約, cross-referenced with `05_failure_modes_and_operational_readiness.md`.

11. **Prompt-injection responsibility boundaries** — Sourced from `03_rag_03_05` (`sanitize_document()`) and `03_rag_04_02` (`was_sanitized`, `patterns_detected`), stating which layer (RAG ingestion vs Agent vs MCP) is responsible at each boundary crossing.

**Footer Sections:**
- `Related Documents` — list of cross-referenced docs
- `Keywords` — security, architecture, trust-boundaries, threat-model, auth, audit, prompt-injection

## Compatibility considerations
- New document only; no existing content modified
- Bidirectional cross-references with `00_security_02` doc

## Security considerations
- Documents security posture; no secrets or implementation details exposed
- Threat model is defensive documentation

## Rollback considerations
- Git revert (delete file) if issues arise

## Validation plan
- Manual trace: every trust-boundary transition named has corresponding control in existing source doc
- `uv run check-mcp-docs` — no new broken internal links
- `git diff` confirms only new file added under `docs/`

## Out of scope
- No code changes
- No changes to existing docs' technical content (only cross-refs added in separate procedure)
- No diagram rendering pipeline

## Traceability
- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: requires/done/20260818-221156_require.md
- Source plan: plans/20260819-174040_plan.md
- Source implementation procedure: N/A
- Generated at: 20260820-133705
- Related target files: docs/00_security_01_architecture-and-trust-boundaries.md