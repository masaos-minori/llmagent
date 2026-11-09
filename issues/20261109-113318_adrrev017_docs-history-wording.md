# Remove change-history wording and correct runtime-behavior statements in current specifications

## Priority
Medium

## Summary
Remove history passages (amendment narratives, "replaces the previous", renamed-field notes, plan and issue IDs) from current-specification documents, register or remove the `/reload` exception for `diagnostics` (current code reloads diagnostics fields live and ADR-002 mentions no exception), and state the reload scope, the retry count, and the meaning of FATAL once and identically across documents.

## Background
- Source: `memo-issue.md` items M-11 (wording part) and M-09 (remaining parts), re-checked against current source on 2026-11-09. The memo's passage list is only partly current.
- `Explicit in documentation`, history wording found by search on 2026-11-09:
  - `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md`: an "Amendment (dbmig001, 2026-10-30)" section, a "Historical, superseded 2026-11-07 (source compatrm001)" paragraph, a Review Trigger mentioning "removed by compatrm001", and the Amendment Approval Mapping text (the approval mapping belongs to the governance-ledger issue).
  - `docs/10_adr/adr_01_index.md`: a line describing ADR-008 as "amended ... superseded ..." with plan sources.
  - `docs/41_db/db_07_api_and_operations-recovery-and-reference.md`: a note that a drill artifact field was renamed (the old field name `rpo_window_seconds` is mentioned).
  - `docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md`: several passages saying migration machinery "was removed by the compatrm001 plan" or was "established by dbmig001".
  - `docs/22_mcp/mcp_03_03_transport-and-health.md`: "This replaces the previous per-call random key: before this change ...".
- `Needs confirmation` (the same searches found no match, so these may already be fixed): ADR-013 "breaking change (2026-10-30)", `db_01` "facade deleted (2026-11-07)", `eventbus_06` "removed in version 6" and "duplicates before the constraint", `eventbus_03` plan IDs "H-01/H-03", and ADR-003 leftover terms ("Profile" in #7, "Across Environments", and Out of Scope "changes to runtime behavior").
- Runtime statements (`Needs confirmation`, not re-read in this review): `diagnostics` settings change through `/reload` while ADR-002 says configuration changes need a restart; `security_01` says subprocess servers are "retried automatically" and mentions a "schema version mismatch" while ADR-004 allows exactly one retry and the workflow has no schema version. `Explicit in documentation`: FATAL in `docs/22_mcp/mcp_06_09_startup-validation-behavior-tool_definitions_strict.md` is described as a startup-blocking outcome for required cases; the memo says `mcp_06_09` says "may be partially functional" (not confirmed in the quoted lines) while `agent_10_01` says "startup is aborted".
- The Current-Specification-Only Policy is in `docs/00_governance/governance_01_documentation-policy.md` (`Needs confirmation` of the exact heading and forbidden patterns).

## Problem
- History in current documents makes readers work out which parts are current; git and the issues already keep the history.
- A retracted or superseded amendment that is still present can be mistaken for a valid decision.
- Inconsistent runtime statements mislead operators (waiting for an automatic retry that does not happen; an undocumented `/reload` exception that breaks ADR-002 without an approval; two definitions of FATAL make startup logs ambiguous).

## Reason for Change
- The forbidden-pattern checks from the checker issue in this batch should start green, so the corpus must be clean first. Timing: before the checker hardening issue.

## Implementation Intent
- Every document describes only current behavior; each runtime behavior (reload scope, retry count, the meaning of FATAL) is stated once and identically, with other documents referencing the owning ADR.
- Removing history must not change any normative decision; when a decision hides inside a history passage, keep the decision as current-tense text.

## Target Files or Areas
- `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md`, `docs/10_adr/adr_01_index.md`, `docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md`, `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`
- `docs/41_db/db_01_architecture_and_schema-overview-and-config.md`, `docs/41_db/db_07_api_and_operations-recovery-and-reference.md`, `docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md`
- `docs/24_eventbus/eventbus_03_dlq_operations.md`, `docs/24_eventbus/eventbus_06_persistence_schema_and_replay.md`
- `docs/22_mcp/mcp_03_03_transport-and-health.md`, `docs/22_mcp/mcp_06_09_startup-validation-behavior-tool_definitions_strict.md`, `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md`
- `docs/91_security/security_01_architecture-and-trust-boundaries.md`, `docs/10_adr/adr_02_01_002_platform-config-isolation.md`

## Required Changes
- Re-run the search for history wording (amendment, superseded, "replaces", "was removed", "renamed", plan and issue IDs, dates in parentheses) across `docs/` and remove or rewrite every current-specification passage found, including the passages listed above.
- Register `/reload` for `diagnostics` as an explicit ADR-002 exception, or require a restart (maintainer decision).
- Correct the retry and schema-version wording in `security_01` to match ADR-004 and the workflow.
- Define FATAL as "startup is aborted" in both `mcp_06_09` and `agent_10_01`, or document why they differ.

## Constraints
- Maintainer decision of 2026-11-09: ADR amendment history is not needed in the ADRs. Remove amendment sections and amendment narratives (including the ADR-008 Amendment section and the Amendment Approval Mapping paragraph) and keep only the current decision text; the approval of the current decision text stays. Run `tools/check_adr_preservation.py` and justify each reported change; keep Review Triggers that describe current conditions, invariants, and the current approval record intact.
- Reconcile with the governance-ledger issue: it must not add per-amendment approval records for amendments removed here.
- Docs content policy and English-only rule apply.

## Acceptance Criteria
- No history passage remains in the listed documents, and the forbidden-pattern checks from the checker issue pass.
- The reload, retry, and FATAL definitions are identical across all documents that mention them.
- `check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py --strict`, `check_adr_preservation.py` (all reported changes justified), `check_adr_authority.py`, and `check_docs_consistency.py` for each touched domain pass.

## Testing Expectations
- Documentation-only; run the checkers above. No code change is expected.

## Documentation Impact
- All documents listed above change. State current behavior and failure behavior only; no change narratives.

## Out of Scope
- Hardening the checkers (separate issue in this batch).
- Adding approval records (governance-ledger issue).
- Changing runtime behavior of reload or retry (only the statements and, if chosen, the ADR-002 exception).

## Dependencies
- Depends on: none.
- Blocks: `issues/20261109-113351_adrrev018_docs-checker-harden.md` (documentation checker hardening).
- Related: `issues/20261109-113054_adrrev012_adr-approval-ledger.md`.

## Unresolved Questions
- Maintainer decision: register the `/reload` exception for `diagnostics` or require a restart.
- `Needs confirmation`: which of the memo's passage list is already fixed; the `security_01` and `mcp_06_09` wording on retries and FATAL.

## AI Implementation Instruction
- Search first and edit only passages that still exist.
- Do not delete a normative decision while removing history; rewrite it in current tense.
- Do not touch approval records or invariants.
- Write documentation in English and follow the docs content policy; do not commit.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261109-113318
- **Related target files**: `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md`, `docs/10_adr/adr_01_index.md`, `docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md`, `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`, `docs/10_adr/adr_02_01_002_platform-config-isolation.md`, `docs/41_db/db_01_architecture_and_schema-overview-and-config.md`, `docs/41_db/db_07_api_and_operations-recovery-and-reference.md`, `docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md`, `docs/24_eventbus/eventbus_03_dlq_operations.md`, `docs/24_eventbus/eventbus_06_persistence_schema_and_replay.md`, `docs/22_mcp/mcp_03_03_transport-and-health.md`, `docs/22_mcp/mcp_06_09_startup-validation-behavior-tool_definitions_strict.md`, `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md`, `docs/91_security/security_01_architecture-and-trust-boundaries.md`
