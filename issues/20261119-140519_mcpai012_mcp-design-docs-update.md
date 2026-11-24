# Update MCP design documentation after implementation contracts are finalized

## Priority
Low

## Summary
Remove obsolete design statements and document the final idempotency, replay, audit, file protection, Git postcondition, and GitHub security contracts after the implementation issues are complete.

## Background
Source: consolidated review backlog (`memo-issue.md`, Issue 12). The design document location is `Unknown` and must be identified when this issue is planned.

## Problem
The combined design document is said to contain pre-fix and post-fix descriptions that contradict each other, and comments describe the Agent logical key and the transport key as separate values and imply that the LLM controls replay identity (`Needs confirmation`).

## Reason for Change
Documenting before implementation is complete risks another round of drift, so this is last in order; no urgency otherwise.

## Implementation Intent
Produce one implementation-aligned description in which every security or reliability claim names the enforcement point, failure behavior, and proving test. Follow `skills/DESIGN.md` (no implementation-reference duplication, only unresolved limitations).

## Target Files or Areas
- MCP design documents under `docs/22_mcp/` (see the document map in Required Changes)
- Agent workflow and audit comments
- File write and delete, Git, and GitHub design sections
- `docs/10_adr/adr_02_01_002_platform-config-isolation.md`, `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md`, `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md`, deployment manifests, and the migration and operator runbooks (runbook locations `Unknown`)

## Required Changes
- Define workflow, task, turn, call, session, request ids and the idempotency key in one table; document Agent-managed replay and the final dedup ownership and lease state machine.
- Correct file-write and file-delete statements; name audit log types and authoritative locations consistently; describe Git postconditions per operation; describe GitHub read authorization, search scope, file-read controls, timeout outcomes, and retry policy.
- List only unresolved limitations; reference the proving test and verified revision for each claim.
- Document Agent ownership of intent, approval, workflow state, and retry orchestration; MCP ownership of final pre-handler enforcement, owner lease, and terminal evidence; and external-system reconciliation responsibility; align ADR-002, ADR-004, and ADR-008 with the implemented ownership and failure contracts.
- Remove `mcp_dedup.toml` from every reference and deployment mount once `issues/20261120-115842_mcpdl003_dedup-config-isolation.md` lands; document the store migration, store identity initialization, legacy handling, rollback, and operator resolution (`issues/20261120-115841_mcpdl002_store-identity-continuity.md`), and the retention and capacity runbooks (`issues/20261120-115844_mcpdl005_retention-capacity-monitoring.md`).
- Link every state and recovery invariant to its automated test from `issues/20261120-115845_mcpdl006_two-layer-failure-verification.md`; correct obsolete terminology, spelling, and contradictory ownership descriptions.
- Record the document map of the MCP design documents under `docs/22_mcp/` so that every server issue updates the right file and none decides a location: audit and errors in `mcp_02_03_audit-logging-and-errors.md`; Web Search, File read, and GitHub in `mcp_04_01_web-search-file-read-github.md`; File write and delete in `mcp_04_02_file-write-file-delete-shell.md`; CI/CD in `mcp_04_03_rag-pipeline-and-cicd.md`; MDQ in `mcp_04_04_mdq.md`, `mcp_05_04_mdq-rag-boundary.md`, and `mcp_05_05_mdq-enforcement-and-lockdown.md`; Git in `mcp_04_05_git.md`; fail-open, fail-closed, and risk tiers in `mcp_05_03_fail-open-fail-closed-and-risk-tiers.md` (assignment by file title, to be confirmed against content). The later Web Search, CI/CD, and MDQ issues cite this map for their documentation updates.

## Constraints
- Do not merge before the behavior it documents. ADR content changes need an approval record (governance_01, governance_05), never a simulated one.
- The alignment of ADR-004 and ADR-008 must account for the open governance items on them (`docs/00_governance/governance_03_issue-and-uncertainty-management.md`): Known Issues MCP-001 and MCP-002 (ADR-004 exceptions without approval), Needs Confirmation NC-001 and NC-002 (ADR-004 Group 1 and Group 2 item 7 rationale), and the pending ledger entries AAL-002, AAL-003, AAL-019 (ADR-004) and AAL-024, AAL-025, AAL-028, AAL-039 (ADR-008). The Known Issue SHARED-002 (`memories_vec` classified as both system of record and derived) no longer exists: the ADR-008 amendment of 2026-11-24 (adrdoc001) rewrote the Recovery Policy Matrix for Episodic Memory and removed it, withdrew AAL-026 and AAL-027, and added AAL-039; the remaining memory-model differences are tracked by SHARED-003 and SHARED-004. Describe the implemented behavior without resolving them, and do not write an approval for any of them.

## Acceptance Criteria
- [ ] No section contradicts the implementation, and no comment claims that session, tool, and arguments identify a logical call.
- [ ] Replay is described as Agent-managed; audit and recovery outcomes are defined consistently.
- [ ] Known limitations include only unresolved behavior.
- [ ] No document or deployment artifact requires `mcp_dedup.toml`.
- [ ] Every state and recovery invariant has a verification reference.

## Testing Expectations
- Documentation consistency checks used by the repository (docs checkers, reference table checks); run them on the changed files.

## Documentation Impact
This issue is the documentation change: intent, boundaries, failure behavior, and Known Issues.

## Out of Scope
- Any behavior change.

## Dependencies
- Depends on `issues/20261119-140508_mcpai001_atomic-dedup-state-machine.md`, `issues/20261119-140509_mcpai002_github-read-security-boundary.md`, `issues/20261119-140510_mcpai003_github-pydantic-schema-source.md`, `issues/20261119-140511_mcpai004_logical-idempotency-key-replay.md`, `issues/20261119-140512_mcpai005_structured-execution-context.md`, `issues/20261119-140513_mcpai006_github-write-retry-policy.md`, `issues/20261119-140514_mcpai007_dedup-audit-observability.md`, `issues/20261119-140515_mcpai008_git-postcondition-lifecycle.md`, `issues/20261119-140516_mcpai009_file-mcp-hardening.md`, `issues/20261119-140517_mcpai010_github-http-contract-tests.md`, and `issues/20261119-140518_mcpai011_round-recording-accuracy.md`; also on `issues/20261120-115840_mcpdl001_approval-grant-intent.md`, `issues/20261120-115841_mcpdl002_store-identity-continuity.md`, `issues/20261120-115842_mcpdl003_dedup-config-isolation.md`, `issues/20261120-115843_mcpdl004_call-state-control-api.md`, `issues/20261120-115844_mcpdl005_retention-capacity-monitoring.md`, and `issues/20261120-115845_mcpdl006_two-layer-failure-verification.md`.

## Unresolved Questions
- `不明`: whether the document map above is complete; the combined `22_mcp_all.md` named in the backlogs is not a tracked file (`ls docs/22_mcp` shows the split files).
- `不明`: the outcomes of MCP-001, MCP-002, NC-001, and NC-002; the ADR text this issue writes depends on them. (The earlier question about the `memories_vec` classification, SHARED-002, is closed by the ADR-008 amendment of 2026-11-24.)

## AI Implementation Instruction
Edit documentation and comments only; verify each claim against current source and the named test before writing it.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261119-140519
- **Related target files**: N/A: not yet confirmed
