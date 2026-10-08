## Goal
Reconcile the Known Issue ledger with verified implementation state: register MCP-005 and EVENTBUS-015, remove MCP-002, rewrite MCP-004 as the residual deviation, and conditionally update RAG-002 (REQ-001 to REQ-007 of the Plan; refuted MCP-006 stays unregistered per REQ-003).

## Scope
- Edit only Part 1 (Known Issues) of the ledger document: the Active Items table and the per-ID detail sections.
- Follow the 17-field Entry Template, the ID-prefix ordering convention, and the Current-Specification-Only policy (no history, no resolved items).

## Assumptions
- First Found for the two new entries is the date `2026-10-08`; existing entries use the free text "Documentation review", which a sibling issue flags as a format defect. Confirm against the Entry Template before writing; follow the template if it states a format.
- Owner stays `Unassigned` (owner assignment is a user decision, Plan UNK-04).
- ADR-012's Known Deviations text (MCP-002 resolved, MCP-004 residual) is the accepted description of the git deviation state.
- Severity High for MCP-005 follows the Issue.

## Design decisions
- Place the MCP-005 table row after the MCP-004 row, and its detail section after the MCP-004 section; place EVENTBUS-015 after EVENTBUS-014 in both lists. This keeps ascending order within each ID-prefix group.
- Keep MCP-004 rather than deleting it, because ADR-012 still retains it as a residual known deviation.
- Do not register MCP-006: current dispatch behavior executes keyless calls without touching the idempotency cache.

## Alternatives considered
- Raise MCP-004 to High as the Issue proposed: rejected; the refspec vector is closed by the write allow-list.
- Delete MCP-004 with MCP-002: rejected; ADR-012 would then cite a missing ID.
- Register EVENTBUS-015 only after the ADR-013 owner decides: rejected for this change; register as a design-gap and let the owner close it by documenting the exception.

## Implementation
### Target file
docs/00_governance/governance_03_issue-and-uncertainty-management.md

### Procedure
1. Re-check the ledger immediately before editing: IDs MCP-005 and EVENTBUS-015 must still be absent, and MCP-002, MCP-004, and RAG-002 sections must still exist as described.
2. Remove the MCP-002 table row and the `#### MCP-002` section.
3. Rewrite the MCP-004 table row title and section fields (Details below).
4. Add the MCP-005 row and section after MCP-004.
5. Add the EVENTBUS-015 row and section after EVENTBUS-014.
6. If ADR-009 contains INV-11, update RAG-002; otherwise leave it byte-identical.
7. Run the Validation plan commands.

### Method
Targeted edits to the existing sections; no restructuring of the document. Locate each section by its `#### <ID>` heading with a text search and edit only that block.

### Details
MCP-004 new field values: Title "git-mcp has no generic technical force-push block"; Severity Low; Type design-gap; Source the git service module; Target ADR-012; Related `None`; Summary: the write allow-list closes the refspec vector, but forced updates are prevented only by the absent force parameter and the allow-list; Current Description: ADR-012 requires force push to be rejected through the normal tool path; Observed Implementation: git_push exposes no force field, the allow-list rejects refspec forms, and the protected-branch check applies to the destination; Impact: no independent guard beyond those layers; Recommended Action: add a regression test that refspec forms are rejected, or record the layering as accepted in ADR-012; Resolution Target: force-push prevention is covered by a test or recorded as accepted in ADR-012.

MCP-005 new entry: Title "rag-pipeline-mcp does not verify the Bearer token"; Status open; Severity High; Area MCP; Type implementation-bug; Source the rag-pipeline server module; Owner Unassigned; Target ADR-007; Related `None`; Summary: ADR-007 requires every MCP server to verify the Bearer token, but this server builds its app without the authentication middleware; Current Description: ADR-007 INV-09 requires a non-empty authentication token and verification (the agent configuration supplies a token entry for this server); Observed Implementation: the app is created without attaching the authentication middleware, while the git, cicd, web_search, and mdq servers attach it; Impact: any local process that can reach the loopback port can call the tools without a token; Recommended Action: attach the middleware and add a test, or record an exception in ADR-007; Resolution Target: requests without a matching token are rejected, covered by a test.

EVENTBUS-015 new entry: Title "Shared auth_token and admin_token grant every role"; Status open; Severity Medium; Area EventBus; Type design-gap; Source the EventBus auth module; Owner Unassigned; Target ADR-013; Related `EVENTBUS-008`; Summary: the mandatory shared token and the admin token map to every role, so per-role separation holds only for callers holding per-role tokens; Current Description: ADR-013 defines five roles with fixed routes; Observed Implementation: the principal map assigns every role to auth_token and admin_token; Impact: a publisher or consumer process given auth_token can call operator and admin routes; Recommended Action: keep these tokens operator-only and record that in ADR-013, or make per-role tokens sufficient; Resolution Target: ADR-013 and the deployment practice agree, or per-role tokens suffice.

RAG-002 (conditional): Current Description cites INV-11 (a sentence with empty normalized text keeps its original text in `content`); Target uses the ADR-009 file name in effect at that time.

## Compatibility considerations
- ADR Known Deviations and `tools/check_known_deviation_sync.py` read this document; IDs cited by ADRs (MCP-001, MCP-004, AGENT-003, and others) must still resolve after the edit.
- Other documents that cite MCP-002 (outside this Plan's targets) are reported, not edited.

## Security considerations
- Entries describe missing authentication and over-broad tokens; do not include token values, host secrets, or exploit steps.

## Rollback considerations
- Documentation only; revert with a single `git revert` of the implementation commit. No data or runtime state is affected.

## Validation plan
- `uv run python tools/check_issue_inventory_conformance.py`
- `uv run python tools/check_known_deviation_sync.py`
- `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py`
- Search `docs/` for `MCP-006` (expect none) and `MCP-002` (expect only reportable external citations).

## Completion criteria
- MCP-005 and EVENTBUS-015 exist with all 17 fields in both table and detail form, in the specified positions (REQ-001, REQ-002, REQ-007).
- No `MCP-006` and no `MCP-002` remains in this document (REQ-003, REQ-004).
- MCP-004 describes only the residual deviation, Severity Low, Related `None` (REQ-005).
- RAG-002 cites INV-11 if it exists, otherwise unchanged (REQ-006).
- All checkers above report no new findings (REQ-008).

## Out of scope
- Code changes; ADR, adr-index, or security-document edits; Owner assignment; restructuring this document; fixing the sibling issues that still cite MCP-006 or MCP-002.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove the MCP-002 row and section | Completed | 20261008-101237 | 20261008-101237 |  |
| 2 | Rewrite MCP-004 row and section | Completed | 20261008-101237 | 20261008-101237 |  |
| 3 | Add MCP-005 row and section | Completed | 20261008-101237 | 20261008-101237 |  |
| 4 | Add EVENTBUS-015 row and section | Completed | 20261008-101237 | 20261008-101237 |  |
| 5 | Update RAG-002 if ADR-009 has INV-11 | Completed | 20261008-101237 | 20261008-101237 | N/A: ADR-009 has no INV-11 yet; RAG-002 left unchanged |
| 6 | Run the checkers and the residual-reference search | Completed | 20261008-101237 | 20261008-101607 | check_docs_structure: size 28414 > 26861 ceiling (was 26843); needs user decision unblocked: ceiling raised via procedure 03 (user approved 2026-10-08); structure check passes |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-001 (register MCP-005), REQ-002 (register EVENTBUS-015), REQ-003 (no MCP-006), REQ-004 (remove MCP-002), REQ-005 (rewrite MCP-004), REQ-006 (RAG-002), REQ-007 (entry format), REQ-008 (checkers pass)
- **Source issue**: issues/20261008-094504_kiupd01_register-new-known-issues-and-update-mcp-004-and-rag-002.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261008-100307_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261008-100819
- **Related target files**: docs/00_governance/governance_03_issue-and-uncertainty-management.md