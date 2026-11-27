## Goal
- Produce one implementation-aligned description of the MCP contracts: remove obsolete design statements, document the final idempotency, replay, audit, file protection, Git postcondition, and GitHub security contracts, record the document map, and align ADR-002, ADR-004, and ADR-008 with the implemented ownership and failure contracts without writing any approval.

## Priority
Low

## Scope
- **In-Scope**: the MCP design documents named by the Issue's document map plus `mcp_00_document-guide.md` (the map is recorded there), `mcp_06_06_end-to-end-tool-call-tracing.md` (the id table), and `docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md` (runbook consistency); the three ADRs; terminology, spelling, and ownership-description corrections; proving-test references for claims changed by this sweep; verification that no document or deployment artifact requires `mcp_dedup.toml`.
- **Out-of-Scope**: any behavior change; resolving the open governance items (MCP-001, MCP-002, NC-001, NC-002) or writing approvals for the pending AAL entries (AAL-003, AAL-019, AAL-028) — per the owner decision of 20261126, the ADR work describes implemented behavior only and references the open items; the agent code comments, which Step 2 found consistent; the documentation updates already landed by the dependency plans.
- **Dependencies**: all 17 dependency issues are closed (mcpai001–mcpai011 in `issues/done/` except mcpai012/mcpai013, mcpdl001–mcpdl006 in `issues/done/`). Three of their Plans have Pending implementation rows (mcpai008, mcpai009, mcpai010 — this Plan's siblings in the memo1 batch): the sweep must run after those implementations land, per the Issue's Constraint "do not merge before the behavior it documents".

## Background
Source: consolidated review backlog (`memo-issue.md`, Issue 12). Step 2 verification against current source: the document-map files all exist under `docs/22_mcp/` and the combined `22_mcp_all.md` is not a tracked file (the Issue's `不明` on map completeness is confirmed as a scope note, not a gap). The logical-key/transport-key separation claim is confirmed at `docs/22_mcp/mcp_03_01_dispatch-and-routing.md:61`; the second half of the claim — that comments imply the LLM controls replay identity — was not found in the agent code or docs and is recorded as unconfirmed (replay is documented as Agent-managed: `scripts/agent/tool_preparation.py` `ReplayDirective`, mcpai004). Re-verified 20261126 (Step 3a): the runbook link is at `docs/90_deployment/deployment_01_deployment.md:351`, not 345. The governance claims are confirmed in part: MCP-001, MCP-002, NC-001, NC-002 are all `open` in `docs/00_governance/governance_03_issue-and-uncertainty-management.md`; SHARED-002 no longer exists (confirmed); but the "pending ledger entries" claim is stale — AAL-002 is recorded in ADR-004's Approval Record, and AAL-024, AAL-025, AAL-039 are recorded in ADR-008's Approval Record (approved 2026-11-24); the pending entries are AAL-003, AAL-019 (ADR-004) and AAL-028 (ADR-008). `mcp_dedup.toml` appears only as a historical removal note in `docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md:88`; no deployment manifest requires it. The runbook locations the Issue lists as `Unknown` are tracked: `docs/90_deployment/deployment_01_deployment.md:345` links the Workflow Deployment Runbook in `docs/23_agent/agent_10_04_operations-and-observability-validation-and-troubleshooting.md`, and the dedup operator-runbook content lives in `docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md` (store migration, identity initialization, legacy handling, rollback, operator resolution already landed by mcpdl002/mcpdl005).

## Problem
The design documents contain pre-fix and post-fix descriptions that contradict each other (confirmed in part: the id table in `mcp_06_06` lacks the workflow, session, request, and call ids — the idempotency key, `turn_id`, `task_id`, and `task_linkage` are already in it as of 20261126; invariant-to-test references are missing in `db_03_07`, while `mcp_03_01` already cites the layer-consistency tests at line 141 but has no proving-test reference for its dedup ownership claims). Claims that name an enforcement point, failure behavior, and proving test are absent for the contracts the dependency issues landed, and the ADRs' ownership descriptions predate the implemented contracts.

## Reason for Change
Documenting before implementation is complete risks another round of drift, so this is last in order; no urgency otherwise.

## Implementation Intent
Produce one implementation-aligned description in which every security or reliability claim names the enforcement point, failure behavior, and proving test. Follow `skills/DESIGN.md` (no implementation-reference duplication, only unresolved limitations). Verify each claim against current source and the named test before writing it.

## Design decisions (Path B)
- **ADR alignment scope** (owner decision, 20261126): align ADR-002, ADR-004, ADR-008 with the implemented ownership and failure contracts by describing implemented behavior only; do not resolve MCP-001, MCP-002, NC-001, NC-002 and do not write approvals for AAL-003, AAL-019, AAL-028 — reference them as open items.
- **Document map location**: recorded in `docs/22_mcp/mcp_00_document-guide.md` (the MCP document guide, the file-index document); the Issue's map is taken as the assignment basis, confirmed against content during implementation.
- **Id table**: completed in `docs/22_mcp/mcp_06_06_end-to-end-tool-call-tracing.md`, which already holds the Identity Fields table; the single-table definition extends it with the workflow, session, request, and call ids (the idempotency key, `turn_id`, and `task_id` rows are already present — corrected in Step 3a on 20261126).
- **Size ceilings**: `check_docs_structure.py`'s `SIZE_EXCEPTIONS` pins ADR-004 at 36992 B (current size) and ADR-008 at 54865 B (current size), so ADR edits must be size-neutral replacements; if growth is unavoidable, the ceiling is re-recorded in the checker per its recorded convention.
- **Proving-test references**: required for claims this sweep changes, not retroactively for every claim in the tree.

## Requirements
- `REQ-001`: Define workflow, task, turn, call, session, request ids and the idempotency key in one table; document Agent-managed replay and the final dedup ownership and lease state machine.
- `REQ-002`: Correct the file-write and file-delete statements; name audit log types and authoritative locations consistently; describe Git postconditions per operation; describe GitHub read authorization, search scope, file-read controls, timeout outcomes, and retry policy.
- `REQ-003`: List only unresolved limitations; reference the proving test and verified revision for each claim this sweep changes.
- `REQ-004`: Document Agent ownership of intent, approval, workflow state, and retry orchestration; MCP ownership of final pre-handler enforcement, owner lease, and terminal evidence; and external-system reconciliation responsibility; align ADR-002, ADR-004, and ADR-008 with the implemented ownership and failure contracts without resolving open governance items or writing approvals.
- `REQ-005`: No document or deployment artifact requires `mcp_dedup.toml` (verified state; the historical removal note is the only occurrence).
- `REQ-006`: Link every state and recovery invariant to its automated test.
- `REQ-007`: Record the document map of the MCP design documents so that every server issue updates the right file.
- `REQ-008`: Correct obsolete terminology, spelling, and contradictory ownership descriptions.

## Implementation Target Files
**Freeze status**: Frozen — `issue-to-plan` Step 8's Implementation Target Files
Validation passed for every row on 20261126; see `rules/workflow-lifecycle.md`
Implementation Target Files Validation (Plan Freeze).

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `docs/22_mcp/mcp_00_document-guide.md` | Modify | Record the document map (assignment by file title, confirmed against content) | REQ-007, AC-5 | File exists (9179 B); contains a file index and related list, no document map (checked in Step 2) | `uv run python tools/check_docs_structure.py` | Verified |
| `docs/22_mcp/mcp_03_01_dispatch-and-routing.md` | Modify | Complete the single id-definition table; state Agent-managed replay; add proving-test references for the dedup ownership claims | REQ-001, REQ-003, AC-1, AC-2, AC-4 | Key-separation paragraph at line 61 confirmed; test citations exist at line 141 (layer-consistency tests), but no proving-test reference for the dedup ownership claims (re-verified 20261126, Step 3a) | `tests/mcp_servers/test_mcp_dispatch.py`, `tests/mcp_servers/test_mcp_dispatch_concurrency.py` | Verified |
| `docs/22_mcp/mcp_02_03_audit-logging-and-errors.md` | Modify | Name audit log types and authoritative locations consistently | REQ-002, AC-1 | Audit-log-types section at lines 20-48; consistency against the per-server audit code pending the mcpai009 audit-order landing | `tests/mcp_servers/file/test_file_server_audit_records.py` | Verified |
| `docs/22_mcp/mcp_04_01_web-search-file-read-github.md` | Modify | GitHub read authorization, search scope, file-read controls; symlink policy and traversal limits as failure behavior after mcpai009 lands | REQ-002, AC-1 | Timeout and retry-policy sections already landed (lines 39, 101, 111); symlink policy and traversal-limit reporting already present at lines 76-77 (re-verified 20261126, Step 3a — the Step 2 claim "no symlink/traversal-limit policy" is stale; the row's work is confirming these against current source, not adding them) | `tests/mcp_servers/github/test_github_security_compliance.py` (mcpai010), `tests/mcp_servers/file/test_read_service.py` | Verified |（re-verified 20261126, Step 3a: the mcpai010 test files do not exist yet — they are pending outputs of procedures `implementations/20261126-205430_03` and `_04`; the claim's proving test must cite them at execution time, after they land）
| `docs/22_mcp/mcp_04_02_file-write-file-delete-shell.md` | Modify | Correct file-write and file-delete statements; record dry-run parity and audit order after mcpai009 lands | REQ-002, AC-1 | Postcondition and root-protection sections at lines 28-32 without dry-run parity and audit order (checked in Step 2) | `tests/mcp_servers/file/test_delete_service.py` | Verified |
| `docs/22_mcp/mcp_04_03_rag-pipeline-and-cicd.md` | Modify | CI/CD section consistency sweep | REQ-002, REQ-008, AC-1, AC-5 | File exists (6610 B); sweep scope per the document map | `tests/mcp_servers/cicd/test_tool_server_layer_consistency.py` | Verified |
| `docs/22_mcp/mcp_04_04_mdq.md` | Modify | MDQ section consistency sweep | REQ-002, REQ-008, AC-1, AC-5 | File exists (10105 B); sweep scope per the document map | `tests/mcp_servers/mdq/test_mdq_tool_layer_consistency.py` | Verified |
| `docs/22_mcp/mcp_04_05_git.md` | Modify | Git postconditions per operation (final wording after mcpai008 lands) | REQ-002, AC-1 | Postcondition section at lines 57-115 already cites the pipeline; per-operation descriptions pending mcpai008 | `tests/mcp_servers/git/` postcondition tests (mcpai008 plan) | Verified |
| `docs/22_mcp/mcp_05_03_fail-open-fail-closed-and-risk-tiers.md` | Modify | Fail-open/fail-closed and risk-tier statements aligned to the implemented contracts; open exceptions referenced, not resolved | REQ-002, REQ-004, AC-1, AC-2 | File exists (11157 B); ADR-004 exceptions MCP-001/MCP-002 open in governance_03 (checked in Step 2) | `tests/mcp_servers/test_mcp_dispatch.py` (store_error overlay path) | Verified |
| `docs/22_mcp/mcp_05_04_mdq-rag-boundary.md` | Modify | Boundary section consistency sweep | REQ-002, REQ-008, AC-1, AC-5 | File exists (5508 B); sweep scope per the document map | `tests/mcp_servers/mdq/` boundary tests | Verified |
| `docs/22_mcp/mcp_05_05_mdq-enforcement-and-lockdown.md` | Modify | Enforcement section consistency sweep | REQ-002, REQ-008, AC-1, AC-5 | File exists (6128 B); sweep scope per the document map | `tests/mcp_servers/mdq/` enforcement tests | Verified |
| `docs/22_mcp/mcp_06_06_end-to-end-tool-call-tracing.md` | Modify | Extend the Identity Fields table to the single id-definition table (workflow, task, turn, call, session, request ids, idempotency key) | REQ-001, AC-1 | Identity Fields table at lines 60-65 lacks workflow, session, request, call ids and the key as one table (checked in Step 2) | `tests/mcp_servers/test_execution_context.py` | Verified |
| `docs/10_adr/adr_02_01_002_platform-config-isolation.md` | Modify | Align with the implemented config-isolation ownership contract | REQ-004, AC-2 | File exists (23084 B); churn 11 in 30d; alignment against `scripts/shared/mcp_dedup_config.py` boundaries | `tests/mcp_servers/test_config_isolation_import.py`, `tests/mcp_servers/test_config_isolation_fail_closed.py` | Verified |
| `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md` | Modify | Align ownership and failure-contract descriptions with the implementation; reference MCP-001, MCP-002, NC-001, NC-002 and pending AAL-003/AAL-019 as open; size-neutral edits (ceiling 36992 B equals current size) | REQ-003, REQ-004, REQ-008, AC-2, AC-3 | Current size 36992 B pinned as `SIZE_EXCEPTIONS` ceiling in `tools/check_docs_structure.py` (checked in Step 2); open items confirmed in governance_03 | `uv run python tools/check_adr_structure.py`, `uv run python tools/check_docs_structure.py` | Verified |
| `docs/10_adr/adr_02_05_008_db-six-sqlite-store-separation.md` | Modify | Align ownership descriptions with the implemented dedup contracts; reference pending AAL-028 as open; size-neutral edits (ceiling 54865 B equals current size) | REQ-003, REQ-004, REQ-008, AC-2, AC-3 | Current size 54865 B pinned as `SIZE_EXCEPTIONS` ceiling (checked in Step 2); AAL-024/025/039 already recorded as approved (issue claim corrected) | `uv run python tools/check_adr_structure.py`, `uv run python tools/check_docs_structure.py` | Verified |
| `docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md` | Modify | Link each state and recovery invariant to its automated test; runbook consistency check (store migration, identity initialization, legacy handling, rollback, operator resolution already landed by mcpdl002/mcpdl005) | REQ-006, REQ-008, AC-4 | No test citations in the file (checked in Step 2); runbook content present at lines 69, 280 | `tests/mcp_servers/test_mcp_dispatch_concurrency.py`, `tests/shared/test_mcp_dedup.py` | Verified |

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same
one-file-per-row discipline as `Implementation Target Files` above — no directories, glob
patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `docs/00_governance/governance_03_issue-and-uncertainty-management.md` | The open items (MCP-001, MCP-002, NC-001, NC-002) and pending AAL entries this Plan references but does not resolve | REQ-004, Constraint |
| `scripts/agent/tool_audit.py` | The audit comment baseline; Step 2 found it consistent with the logical-call-id contract, so no comment change is planned | REQ-001, REQ-008 |
| `scripts/agent/tool_call_identity.py` | The logical call id definition the id table must match | REQ-001 |
| `scripts/mcp_servers/dispatch.py` | The implemented dedup ownership and failure behavior the ADR alignment describes | REQ-004 |
| `scripts/shared/mcp_dedup.py` | The implemented lease and store-write behavior (lease state machine, warning-only write path recorded as an open exception) | REQ-001, REQ-004 |
| `tools/check_docs_structure.py` | The `SIZE_EXCEPTIONS` ceilings that constrain the ADR edits | REQ-003, Risks |

## Acceptance Criteria
- AC-1: No section contradicts the implementation, and no comment claims that session, tool, and arguments identify a logical call (REQ-001, REQ-002).
- AC-2: Replay is described as Agent-managed; audit and recovery outcomes are defined consistently (REQ-001, REQ-004).
- AC-3: Known limitations include only unresolved behavior (REQ-003).
- AC-4: Every state and recovery invariant has a verification reference (REQ-006).
- AC-5: No document or deployment artifact requires `mcp_dedup.toml`, and the document map is recorded (REQ-005, REQ-007).

## Tests
- Documentation consistency checks used by the repository, run on the changed files: `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py`, `uv run python tools/check_docs_content_policy.py`, `uv run python tools/check_docs_consistency.py --domain mcp`, `uv run python tools/check_adr_structure.py` (`rules/tool-gates.md`).
- Each claim cites a proving test that exists and passes; the named tests are executed once during the validation pass.

## Documentation Impact
This issue is the documentation change: intent, boundaries, failure behavior, and Known Issues. No `docs/` file outside the target table is modified; the governance file is referenced, not edited (no approvals are written).

## Assumptions
- Owner decision recorded on 20261126 for this cycle: ADR alignment describes implemented behavior only; open governance items and pending AAL entries are referenced, not resolved; no approval text is written.
- The Issue's "pending ledger entries" claim is stale for AAL-002, AAL-024, AAL-025, AAL-039 (recorded in the ADR Approval Records); the plan treats only AAL-003, AAL-019, AAL-028 as pending (corrected in Step 2).
- The claim that comments imply the LLM controls replay identity was not found in current source; no agent comment change is planned unless the implementation pass finds a contradiction (recorded as unconfirmed in Problem).
- The sweep runs after the mcpai008, mcpai009, mcpai010 implementations land (Constraint: do not merge before the behavior it documents).
- The document map is taken as complete for this Plan; its completeness remains the Issue's open note (AC-5 covers recording it, not proving completeness).

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Outcomes of MCP-001, MCP-002, NC-001, NC-002 (open governance items) | Maintainer approval/rationale text | Owner decision 20261126: describe implemented behavior only and reference the items as open; the items themselves remain open for the maintainer | False |
| UNK-02 | Whether the document map is complete | Content confirmation of each file against the map | Confirmed against content during implementation (the Issue states assignment by file title, to be confirmed against content) | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `docs/22_mcp/mcp_00_document-guide.md` | Modify | Low | 1 | High (single author) | not applicable (docs not deployed) |
| `docs/22_mcp/mcp_03_01_dispatch-and-routing.md` | Modify | Medium (referenced by the sibling server issues via the map) | 7 | High (single author) | not applicable (docs not deployed) |
| `docs/22_mcp/mcp_02_03_audit-logging-and-errors.md` | Modify | Medium | 3 | High (single author) | not applicable (docs not deployed) |
| `docs/22_mcp/mcp_04_01_web-search-file-read-github.md` | Modify | Medium (shared with mcpai009, judged compatible) | 3 | High (single author) | not applicable (docs not deployed) |
| `docs/22_mcp/mcp_04_02_file-write-file-delete-shell.md` | Modify | Medium (shared with mcpai009, judged compatible) | 1 | High (single author) | not applicable (docs not deployed) |
| `docs/22_mcp/mcp_04_03_rag-pipeline-and-cicd.md` | Modify | Low | 4 | High (single author) | not applicable (docs not deployed) |
| `docs/22_mcp/mcp_04_04_mdq.md` | Modify | Low | 1 | High (single author) | not applicable (docs not deployed) |
| `docs/22_mcp/mcp_04_05_git.md` | Modify | Low | 1 | High (single author) | not applicable (docs not deployed) |
| `docs/22_mcp/mcp_05_03_fail-open-fail-closed-and-risk-tiers.md` | Modify | Medium | 4 | High (single author) | not applicable (docs not deployed) |
| `docs/22_mcp/mcp_05_04_mdq-rag-boundary.md` | Modify | Low | 1 | High (single author) | not applicable (docs not deployed) |
| `docs/22_mcp/mcp_05_05_mdq-enforcement-and-lockdown.md` | Modify | Low | 1 | High (single author) | not applicable (docs not deployed) |
| `docs/22_mcp/mcp_06_06_end-to-end-tool-call-tracing.md` | Modify | Low | 3 | High (single author) | not applicable (docs not deployed) |
| `docs/10_adr/adr_02_01_002_platform-config-isolation.md` | Modify | Medium | 11 | High (single author) | not applicable (docs not deployed) |
| `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md` | Modify | High (governance-consumed ADR at its size ceiling) | 16 | High (single author) | not applicable (docs not deployed) |
| `docs/10_adr/adr_02_05_008_db-six-sqlite-store-separation.md` | Modify | High (governance-consumed ADR at its size ceiling) | 1 | High (single author) | not applicable (docs not deployed) |
| `docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md` | Modify | Medium | 15 | High (single author) | not applicable (docs not deployed) |

## Design
- **Claim format**: every security or reliability claim written by this sweep names the enforcement point (file and function), the failure behavior, and the proving test; claims already conforming are left untouched (no implementation-reference duplication per `skills/DESIGN.md`).
- **Ownership vocabulary**: Agent owns intent, approval, workflow state, retry orchestration; MCP owns final pre-handler enforcement, owner lease, terminal evidence; external systems own reconciliation. The ADR alignment rewrites descriptions to this vocabulary without touching exception rationales or approval sections.
- **Size-neutral ADR edits**: ADR-004 and ADR-008 sit at their `SIZE_EXCEPTIONS` ceilings; the plan designs replacement-style edits. If a required addition cannot be size-neutral, the ceiling is re-recorded in `tools/check_docs_structure.py` following its recorded convention (comment with the procedure id and size change).
- **Predictable fallout**: the two File MCP documents are shared with mcpai010's sibling mcpai009 — judged compatible (mcpai009 writes the facts it establishes; this Plan performs the final sweep afterward), recorded in Assumptions and Risks. No pinned counts change. No tool is added or removed, so `tools/TOOL_DESCRIPTIONS.md` is not affected. No generated-reference domain is touched. The consumer scan for the document map (Step 3) has no code consumers; the map is consumed by future server issues as documentation guidance only.
- **Validation quality baseline**: the docs checkers listed in `rules/tool-gates.md` plus `check_adr_structure.py` must report no findings on the changed files; the proving tests cited must pass in the full-suite run.

## Implementation steps
Each step description MUST cite the exact file path(s) it touches by referencing rows
of `Implementation Target Files` above — do not restate file-level detail
independently of that frozen table.

1. **Phase 1: Document map**
   - [ ] Record the document map in the MCP document guide, confirming each assignment against file content (REQ-007, AC-5; `docs/22_mcp/mcp_00_document-guide.md`)
2. **Phase 2: Identity, replay, and dedup ownership**
   - [ ] Complete the single id table and the Agent-managed replay description; add proving-test references (REQ-001, REQ-003, AC-1, AC-2; `docs/22_mcp/mcp_06_06_end-to-end-tool-call-tracing.md`, `docs/22_mcp/mcp_03_01_dispatch-and-routing.md`)
3. **Phase 3: Server-section corrections**
   - [ ] Correct audit log types and authoritative locations (REQ-002, AC-1; `docs/22_mcp/mcp_02_03_audit-logging-and-errors.md`)
   - [ ] Correct the GitHub, File write/delete, CI/CD, MDQ, and Git sections against current source, after mcpai008/mcpai009 implementations land (REQ-002, REQ-008, AC-1; `docs/22_mcp/mcp_04_01_web-search-file-read-github.md`, `docs/22_mcp/mcp_04_02_file-write-file-delete-shell.md`, `docs/22_mcp/mcp_04_03_rag-pipeline-and-cicd.md`, `docs/22_mcp/mcp_04_04_mdq.md`, `docs/22_mcp/mcp_04_05_git.md`, `docs/22_mcp/mcp_05_04_mdq-rag-boundary.md`, `docs/22_mcp/mcp_05_05_mdq-enforcement-and-lockdown.md`)
   - [ ] Align the fail-open/fail-closed and risk-tier statements; reference the open exceptions without resolving them (REQ-002, REQ-004, AC-1, AC-2; `docs/22_mcp/mcp_05_03_fail-open-fail-closed-and-risk-tiers.md`)
4. **Phase 4: ADR alignment**
   - [ ] Align ADR-002, ADR-004, ADR-008 with the implemented ownership and failure contracts; describe implemented behavior only, reference open items and pending AAL entries, write no approval, keep ADR edits size-neutral (REQ-003, REQ-004, REQ-008, AC-2, AC-3; `docs/10_adr/adr_02_01_002_platform-config-isolation.md`, `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md`, `docs/10_adr/adr_02_05_008_db-six-sqlite-store-separation.md`)
5. **Phase 5: Invariant links, mcp_dedup.toml sweep, terminology**
   - [ ] Link every state and recovery invariant to its automated test; verify the runbook content and the absence of `mcp_dedup.toml` requirements (REQ-005, REQ-006, AC-4, AC-5; `docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md`)
   - [ ] Correct obsolete terminology, spelling, and contradictory ownership descriptions across the target files (REQ-008, AC-1)
6. **Phase 6: Validation**
   - [ ] Run the docs gates (`check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py`, `check_docs_consistency.py --domain mcp`, `check_adr_structure.py`) and the proving tests cited by changed claims (REQ-003, REQ-006)

### Release units
N/A: no release unit — each phase can be validated alone.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| All `docs/22_mcp/` targets | Documentation consistency | `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py`, `uv run python tools/check_docs_content_policy.py`, `uv run python tools/check_docs_consistency.py --domain mcp` | No findings |
| ADR targets | ADR structure and size ceilings | `uv run python tools/check_adr_structure.py`, `uv run python tools/check_docs_structure.py` | No findings; ADR-004 and ADR-008 within their recorded ceilings |
| Proving tests cited by changed claims | Test execution | `uv run pytest tests/mcp_servers/test_mcp_dispatch.py tests/mcp_servers/test_mcp_dispatch_concurrency.py tests/mcp_servers/test_execution_context.py tests/shared/test_mcp_dedup.py tests/mcp_servers/test_config_isolation_import.py tests/mcp_servers/test_config_isolation_fail_closed.py -v` | All cited tests pass |
| `mcp_dedup.toml` sweep | Reference check | `grep -rn "mcp_dedup.toml" docs/ config/ deploy.sh` | Only the historical removal note remains |

## Risks
- **Risk**: ADR-004 and ADR-008 are at their `SIZE_EXCEPTIONS` ceilings, so any growth fails `check_docs_structure.py` → **Mitigation**: size-neutral replacement edits; if growth is unavoidable, re-record the ceiling in the checker per its recorded convention and report it.
- **Risk**: the sweep documents behavior whose implementation rows are still Pending (mcpai008, mcpai009, mcpai010) → **Mitigation**: the Constraint forbids merging before the behavior lands; Phase 3 runs after those implementations, and claims cite the proving tests at execution time.
- **Risk**: overlap with mcpai009 on the two File MCP documents → **Mitigation**: judged compatible (mcpai009 writes the facts it establishes; this Plan sweeps afterward), recorded in Assumptions.
- **Risk**: writing ADR text that implicitly resolves an open governance item → **Mitigation**: the owner decision limits the ADR work to implemented-behavior descriptions with open-item references; no approval text is written.
- **Risk**: `Bus Factor` is high for every target (single author) → **Mitigation**: keep each phase independently revertable.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`.

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Document map | Completed | 20261126-220000 | 20261126-234230 | — Procedures 01-16 executed; docs checkers pass for every changed doc; cited proving tests pass. |
| 2 | Identity, replay, and dedup ownership | Completed | 20261126-220000 | 20261126-234230 | — Procedures 01-16 executed; docs checkers pass for every changed doc; cited proving tests pass. |
| 3 | Server-section corrections | Completed | 20261126-220000 | 20261126-234230 | — Procedures 01-16 executed; docs checkers pass for every changed doc; cited proving tests pass. |
| 4 | ADR alignment | Completed | 20261126-220000 | 20261126-234230 | — Procedures 01-16 executed; docs checkers pass for every changed doc; cited proving tests pass. |
| 5 | Invariant links, mcp_dedup.toml sweep, terminology | Completed | 20261126-220000 | 20261126-234230 | — Procedures 01-16 executed; docs checkers pass for every changed doc; cited proving tests pass. |
| 6 | Validation | Completed | 20261126-220000 | 20261126-234230 | — Procedures 01-16 executed; docs checkers pass for every changed doc; cited proving tests pass. |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | N/A: no blocker recorded at Plan creation | N/A: no blocker recorded | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| `implementations/20261126-212443_01_docs_22_mcp_mcp_00_document-guide.md.md` | 1 | Procedure | Pending | — | — |
| `implementations/20261126-212443_02_docs_22_mcp_mcp_03_01_dispatch-and-routing.md.md` | 2 | Procedure | Pending | — | — |
| `implementations/20261126-212443_03_docs_22_mcp_mcp_02_03_audit-logging-and-errors.md.md` | 3 | Procedure | Pending | — | — |
| `implementations/20261126-212443_04_docs_22_mcp_mcp_04_01_web-search-file-read-github.md.md` | 3 | Procedure | Pending | — | — |
| `implementations/20261126-212443_05_docs_22_mcp_mcp_04_02_file-write-file-delete-shell.md.md` | 3 | Procedure | Pending | — | — |
| `implementations/20261126-212443_06_docs_22_mcp_mcp_04_03_rag-pipeline-and-cicd.md.md` | 3 | Procedure | Pending | — | — |
| `implementations/20261126-212443_07_docs_22_mcp_mcp_04_04_mdq.md.md` | 3 | Procedure | Pending | — | — |
| `implementations/20261126-212443_08_docs_22_mcp_mcp_04_05_git.md.md` | 3 | Procedure | Pending | — | — |
| `implementations/20261126-212443_09_docs_22_mcp_mcp_05_03_fail-open-fail-closed-and-risk-tiers.md.md` | 3 | Procedure | Pending | — | — |
| `implementations/20261126-212443_10_docs_22_mcp_mcp_05_04_mdq-rag-boundary.md.md` | 3 | Procedure | Pending | — | — |
| `implementations/20261126-212443_11_docs_22_mcp_mcp_05_05_mdq-enforcement-and-lockdown.md.md` | 3 | Procedure | Pending | — | — |
| `implementations/20261126-212443_12_docs_22_mcp_mcp_06_06_end-to-end-tool-call-tracing.md.md` | 2 | Procedure | Pending | — | — |
| `implementations/20261126-212443_13_docs_10_adr_adr_02_01_002_platform-config-isolation.md.md` | 4 | Procedure | Pending | — | — |
| `implementations/20261126-212443_14_docs_10_adr_adr_02_01_004_platform-environment-failure-handling-policy.md.md` | 4 | Procedure | Pending | — | — |
| `implementations/20261126-212443_15_docs_10_adr_adr_02_05_008_db-six-sqlite-store-separation.md.md` | 4 | Procedure | Pending | — | — |
| `implementations/20261126-212443_16_docs_41_db_db_03_07_mcp-dedup-and-execution-snapshot.md.md` | 5 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261119-140519_mcpai012_mcp-design-docs-update.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261126-072155
- **Evidence revision**: 41bb4d281ec6e078581aab78b52dd7a3264ce248
- **Related target files**: `docs/22_mcp/mcp_00_document-guide.md`, `docs/22_mcp/mcp_03_01_dispatch-and-routing.md`, `docs/22_mcp/mcp_02_03_audit-logging-and-errors.md`, `docs/22_mcp/mcp_04_01_web-search-file-read-github.md`, `docs/22_mcp/mcp_04_02_file-write-file-delete-shell.md`, `docs/22_mcp/mcp_04_03_rag-pipeline-and-cicd.md`, `docs/22_mcp/mcp_04_04_mdq.md`, `docs/22_mcp/mcp_04_05_git.md`, `docs/22_mcp/mcp_05_03_fail-open-fail-closed-and-risk-tiers.md`, `docs/22_mcp/mcp_05_04_mdq-rag-boundary.md`, `docs/22_mcp/mcp_05_05_mdq-enforcement-and-lockdown.md`, `docs/22_mcp/mcp_06_06_end-to-end-tool-call-tracing.md`, `docs/10_adr/adr_02_01_002_platform-config-isolation.md`, `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md`, `docs/10_adr/adr_02_05_008_db-six-sqlite-store-separation.md`, `docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md`

### Requirement Traceability
See `templates/requirement-traceability.md` for the canonical column format.

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes item 1; `mcp_06_06:60-65`, `mcp_03_01:61` | `docs/22_mcp/mcp_06_06_end-to-end-tool-call-tracing.md`, `docs/22_mcp/mcp_03_01_dispatch-and-routing.md` | Phase 2 | AC-1, AC-2 | `tests/mcp_servers/test_execution_context.py`, `tests/mcp_servers/test_mcp_dispatch.py` | Confirmed by repository evidence |
| REQ-002 | Required Changes item 2 | `docs/22_mcp/mcp_02_03_audit-logging-and-errors.md`, `mcp_04_01`, `mcp_04_02`, `mcp_04_03`, `mcp_04_04`, `mcp_04_05`, `mcp_05_03`, `mcp_05_04`, `mcp_05_05` | Phase 3 | AC-1 | docs consistency checkers; proving tests per claim | Confirmed by repository evidence |
| REQ-003 | Required Changes item 3 | `docs/22_mcp/mcp_03_01_dispatch-and-routing.md`, the three ADRs | Phase 2, Phase 4 | AC-3 | `check_docs_content_policy.py`, `check_adr_structure.py` | Confirmed by repository evidence |
| REQ-004 | Required Changes item 4; owner decision 20261126 | `docs/10_adr/adr_02_01_002_platform-config-isolation.md`, `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md`, `docs/10_adr/adr_02_05_008_db-six-sqlite-store-separation.md`, `docs/22_mcp/mcp_05_03_fail-open-fail-closed-and-risk-tiers.md` | Phase 3, Phase 4 | AC-2 | `check_adr_structure.py` | Confirmed by repository evidence + owner decision |
| REQ-005 | Required Changes item 5; `adr_02_02_003:88` historical note only | `docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md` (sweep scope; no `mcp_dedup.toml` target found) | Phase 5 | AC-5 | grep sweep in Validation plan | Confirmed by repository evidence |
| REQ-006 | Required Changes item 6 | `docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md` | Phase 5 | AC-4 | `tests/mcp_servers/test_mcp_dispatch_concurrency.py`, `tests/shared/test_mcp_dedup.py` | Confirmed by repository evidence |
| REQ-007 | Required Changes item 7 | `docs/22_mcp/mcp_00_document-guide.md` | Phase 1 | AC-5 | `check_docs_structure.py` | Confirmed by repository evidence |
| REQ-008 | Required Changes item 7 (terminology) | all target docs | Phase 3, Phase 4, Phase 5 | AC-1 | docs checkers | Confirmed by repository evidence |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261126-212443 -->