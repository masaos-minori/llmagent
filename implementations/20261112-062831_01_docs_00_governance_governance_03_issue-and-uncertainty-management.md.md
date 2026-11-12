## Goal
Make `governance_03` well-formed (Part 3 Entry Template Status field, corrected merge-condition references) and register only ledger entries that re-verification confirms are still true at implementation time (REQ-001, REQ-002, REQ-003, REQ-004).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Part 3 entries use the Part 1 "Owner Values" set (`Repository owner`); NC-001's existing `maintainer` value is not changed (plan UNK-02).
- Candidate verdicts at conversion 2026-11-12, re-verified 2026-11-12: posture, mcp_dedup, and `tool_call_state` candidates refuted by landed sibling procedures (`mcp_dedup.sqlite` and `tool_call_state` documented in `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md` lines 88-91 and 138); Dry Run versus WAL already registered as SHARED-001. Live candidates at re-verification: the MCP empty-token documentation contradiction (REQ-003; register only if adrrev011 has not closed it first) and the RAG unverifiable-handling contradiction (ADR-010 `Withdrawn` at line 28 while its Decision 11 and the `Identity unverifiable` table row remain normative; owner `issues/20261110-170753_rmcompat003_rag-corpus-identity-decision.md` still open).

## Design decisions
- Phases 1-2 (template and numbering fixes) are independent of every other Plan and safe to run first; Phase 3 is evaluated at implementation time: register only candidates verified true then, never a refuted claim.
- Do not touch the existing SHARED-001/SHARED-002 entries in Part 1 (registered by the landed adrrev009 procedures); re-registering Dry Run versus WAL would duplicate SHARED-001.

## Alternatives considered
N/A: documentation-only change with the approach fixed by the plan design.

## Implementation
### Target file
`docs/00_governance/governance_03_issue-and-uncertainty-management.md`

### Procedure
1. (REQ-001) Add `Status` to the Part 3 Entry Template field list and update the count text (12 to 13) so the list agrees with the Status Values section.
2. (REQ-002) Change both `### 19. Merge Condition Validation` references (lines 250 and 264) to `### 20. Merge Condition Validation`.
3. (REQ-003, REQ-004) Re-verify each candidate (plan UNK-04) against current docs and source; record refuted or already-resolved ones in the completion report; write only confirmed Part 3 entries (13 fields) and Part 1 entries (17 fields, ID prefix per the Active Items ordering convention) with owner `Repository owner` and the sibling Plan or issue as validation evidence.

### Method
Direct Markdown edits. Part 3 template and Active Items are at lines 198-209; the two reference sentences are inside the Temporary Exception Process section.

### Details
- Empty-token candidate (register only if adrrev011 has not already corrected these docs): `docs/22_mcp/mcp_02_02_startup-modes-and-health.md` (last Bearer bullet: "Empty server-side token ... `attach_auth_middleware()` skips the authentication check") and `docs/22_mcp/mcp_06_14_mcp-authentication-setup.md` ("Missing secrets via environment variables ... The server starts, but health checks fail") contradict `require_auth_token()` (`scripts/mcp_servers/server.py:134-144`, raises `RuntimeError` for an empty token) and the fail-closed `attach_auth_middleware()` (`scripts/mcp_servers/server.py:95`); cite `plans/20261111-095422_adrrev011_mcp-audit-auth-adr.md` as the resolving Plan.
- Part 1 Part-placeholder text ("No active Known Issue items remain.") no longer exists; new Part 1 entries append after SHARED-002.
- RAG candidate (re-verified 2026-11-12, register only if still confirmed true at implementation time): `docs/10_adr/adr_02_06_010_rag-fallback.md` keeps `Withdrawn` status (line 28) while Decision 11 (line 76) and the `Identity unverifiable (either identity absent)` table row (line 89) still record the identity-comparison contract as current; cite `issues/20261110-170753_rmcompat003_rag-corpus-identity-decision.md` as the resolving owner. Registering a Part 3 entry needs no ADR edit: `check_known_deviation_sync.py` syncs only Part 1 Known Issue IDs.

## Compatibility considerations
N/A: no code, checker, or config change; only the ledger document.

## Security considerations
N/A: documentation-only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_known_deviation_sync.py` — Pass (AC-4)
- `uv run python tools/check_needs_confirmation_inventory.py` — Pass
- `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py --strict`, `check_docs_japanese.py` — Pass (AC-1, AC-2)
- `uv run python tools/check_metadata_field_policy.py` — Exit 0 with no new warning
- `uv run python tools/check_docs_consistency.py --domain overview` — Pass (AC-2)

## Completion criteria
AC-1 (13-field template with Status), AC-2 (no `### 19. Merge Condition Validation` reference remains), AC-3 (every registered Part 3 entry has all 13 fields, owner `Repository owner`, Status `open`, sibling Plan/issue evidence; no refuted claim registered), AC-4 (every registered Part 1 entry has all 17 fields and a valid owner; refuted candidates reported, not registered).

## Out of Scope
ADR-008 `## Known Deviations` edits (procedure 02), ADR-016 acceptance wording (procedure 03), modifying any governance checker, and fixing the underlying contradictions (sibling Plans).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: add `Status` to the Part 3 Entry Template and update the count (REQ-001) | Completed | — | 20261112-054929 | Gated: plans/20261111-095422_adrrev011_mcp-audit-auth-adr.md phase all - only live Phase 3 candidate (MCP empty-token documentation contradiction (mcp_02_02 and mcp_06_14 vs scripts/mcp_servers/server.py), REQ-003) is expected to be landed or updated by adrrev011's procedure Part 3 template now lists 13 fields incl. Status |
| 2 | Phase 2: fix both `### 19. Merge Condition Validation` references to `### 20.` (REQ-002) | Completed | — | 20261112-054929 | Gated: plans/20261111-095422_adrrev011_mcp-audit-auth-adr.md phase all - only live Phase 3 candidate (MCP empty-token documentation contradiction (mcp_02_02 and mcp_06_14 vs scripts/mcp_servers/server.py), REQ-003) is expected to be landed or updated by adrrev011's procedure both references now cite ### 20. Merge Condition Validation |
| 3 | Phase 3: re-verify candidates, register only confirmed Part 1/Part 3 entries, report refuted ones (REQ-003, REQ-004) | Completed | — | 20261112-054929 | Gated: plans/20261111-095422_adrrev011_mcp-audit-auth-adr.md phase all - only live Phase 3 candidate (MCP empty-token documentation contradiction (mcp_02_02 and mcp_06_14 vs scripts/mcp_servers/server.py), REQ-003) is expected to be landed or updated by adrrev011's procedure re-verification: empty-token candidate RESOLVED by landed adrrev011 procedures _09/_10 (not registered); posture/mcp_dedup/tool_call_state refuted; Dry Run vs WAL already SHARED-001; RAG candidate confirmed and registered as CSC-001; Part 1 registrations: no-op |
| 4 | Run the documentation checkers in the Validation plan | Completed | — | 20261112-054929 | Gated: plans/20261111-095422_adrrev011_mcp-audit-auth-adr.md phase all - only live Phase 3 candidate (MCP empty-token documentation contradiction (mcp_02_02 and mcp_06_14 vs scripts/mcp_servers/server.py), REQ-003) is expected to be landed or updated by adrrev011's procedure all Validation-plan checkers green; fallout fix: check_issue_inventory_conformance.py parsed Part 3/4 entries as Part 2 (15-field rule); added Part 3/4 tracking + 13/6 field counts + 2 regression tests (29 pass) |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-003, REQ-004
- **Source issue**: issues/20261109-113054_adrrev012_adr-approval-ledger.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261111-095703_adrrev012_adr-approval-ledger.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261112-062831
- **Related target files**: docs/00_governance/governance_03_issue-and-uncertainty-management.md