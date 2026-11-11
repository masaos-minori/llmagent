## Goal
Make ADR-016's closing acceptance sentence match its Approval Record without altering the Approved By, Approval Date, or Approval Reference fields (REQ-005, AC-5). Conditional row: proceed only after the maintainer states which acceptance path applies.

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- UNK-01: only the maintainer can state whether ADR-016 reached `Accepted` through a Named Approval Record or the task-level decision; the approver statement is `不明`. If absent, withhold the edit and report it.
- Approval Record (lines 161-164) names `repository owner`, 2026-10-29, and an Approval Reference; the closing sentence (line 166) claims the Task-level path.

## Design decisions
- The reworded sentence restates only fields already present in the Approval Record; it never invents an approval.
- `tools/check_adr_preservation.py` reporting ERROR for the Approval-section sentence is the intended signal that Approval text changed: report the ERROR to the user, do not suppress it or modify the checker.

## Alternatives considered
N/A: single-sentence conditional edit fixed by the plan design (UNK-01 gate).

## Implementation
### Target file
`docs/10_adr/adr_02_07_016_adr-authority-model.md`

### Procedure
1. Ask the maintainer which acceptance path applies (Named Approval Record acceptance or the task-level decision). If no statement exists, skip steps 2-3 and report the withheld edit.
2. Reword line 166 ("This ADR reached `Accepted` via a Task-level approval decision per the ADR Acceptance Evidence Standard ...") to match the stated path, citing the Approval Record fields; leave Approved By, Approval Date, and Approval Reference text untouched.

### Method
Single-sentence Markdown edit in the Approval Record section; no other section changes.

### Details
- ADR-015 is checked and left unchanged: its Named Approval Record (2026-09-19, acceptance) and task-level Current Decision Approval line (2026-10-08, later text) describe different approvals and agree.

## Compatibility considerations
`plans/20261111-104605_adrrev016_adr-authority-format.md` also targets this file (overlap note); its edits are the authority-format sections, not the closing acceptance sentence — verify the two designs do not contradict each other when both are implemented.

## Security considerations
N/A: documentation-only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_adr_preservation.py` — reports only the intended ADR-016 Approval-section sentence (expected ERROR, reported to the user)
- `uv run python tools/check_adr_structure.py`, `uv run python tools/check_adr_authority.py` — Pass

## Completion criteria
AC-5: ADR-016's acceptance sentence matches its Approval Record, or the edit is withheld and reported until the maintainer states the path, with the Approved By, Approval Date, and Approval Reference text unchanged.

## Out of Scope
Writing any approval record, editing ADR-015 (consistent, no edit), and the authority-format sections targeted by `plans/20261111-104605_adrrev016_adr-authority-format.md`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Obtain the maintainer statement of the acceptance path (UNK-01) or report the withheld edit (REQ-005) | Pending | — | — | Gated: plans/20261111-095422_adrrev011_mcp-audit-auth-adr.md phase all - only live Phase 3 candidate (MCP empty-token documentation contradiction (mcp_02_02 and mcp_06_14 vs scripts/mcp_servers/server.py), REQ-003) is expected to be landed or updated by adrrev011's procedure |
| 2 | Reword line 166 to match the Approval Record; leave approval fields untouched (REQ-005) | Pending | — | — | Gated: plans/20261111-095422_adrrev011_mcp-audit-auth-adr.md phase all - only live Phase 3 candidate (MCP empty-token documentation contradiction (mcp_02_02 and mcp_06_14 vs scripts/mcp_servers/server.py), REQ-003) is expected to be landed or updated by adrrev011's procedure; additionally gated on the UNK-01 maintainer statement |
| 3 | Run the documentation checkers in the Validation plan and report the expected `check_adr_preservation.py` ERROR | Pending | — | — | Gated: plans/20261111-095422_adrrev011_mcp-audit-auth-adr.md phase all - only live Phase 3 candidate (MCP empty-token documentation contradiction (mcp_02_02 and mcp_06_14 vs scripts/mcp_servers/server.py), REQ-003) is expected to be landed or updated by adrrev011's procedure |

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
- **Requirement ID**: REQ-005
- **Source issue**: issues/20261109-113054_adrrev012_adr-approval-ledger.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261111-095703_adrrev012_adr-approval-ledger.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261112-062831
- **Related target files**: docs/10_adr/adr_02_07_016_adr-authority-model.md
