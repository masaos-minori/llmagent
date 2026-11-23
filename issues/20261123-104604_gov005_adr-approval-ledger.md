# Work down the ADR Approval Ledger and the Non-Blocking verification rows

## Priority
Low

## Summary
37 ADR decision-text changes (AAL-001 to AAL-038, with 018 absent) are written into ADRs with approver and date `Not recorded`, including seven entries that set a verification row to Non-Blocking. Close each through a recorded approval or a revert.

## Background
Source: `docs/00_governance/governance_03_issue-and-uncertainty-management.md` Part 5 (37 entries, counted by `grep`). Entries tied to other work (re-verified 2026-11-23): AAL-013 (ADR-010 fallback withdrawal) and AAL-024 to AAL-028 (ADR-008 scope, schema-mismatch, retention, and canonical-store text) were named after `issues/done/20261123-104600_gov001_resolve-adr-contradictions.md`, but that issue is archived and left all six entries in the ledger, so they are open items of this issue, not entries that close with it; AAL-014, AAL-015, AAL-036 (ADR-012) belong with `issues/done/20261123-104601_gov002_git-protected-head-tests.md`, which is archived without removing them (it added a regression test class for the HEAD-destination check only, and AAL-036 still sets INV-04 to Non-Blocking); AAL-006 to AAL-010 and AAL-029 (EventBus text of ADR-006 and ADR-008) stay open: `issues/done/20261123-104603_gov004_eventbus-client-decision.md` is archived with its plan frozen for retiring the two unused client modules only (maintainer decision 2026-11-23), and by the maintainer's decision NC-003 (the producer/consumer model) stays open, so these entries do not close with it; AAL-002, AAL-003, AAL-019 (ADR-004 exceptions) are carried in `issues/20261119-140508_mcpai001_atomic-dedup-state-machine.md`, `issues/20261119-140509_mcpai002_github-read-security-boundary.md`, and `issues/20261119-140519_mcpai012_mcp-design-docs-update.md`. The rest are AAL-001, 004, 005, 011, 012, 016, 017, 020 to 023, 030 to 035, 037, 038, of which AAL-001 and AAL-031 to AAL-035 each set an INV verification row of ADR-001, ADR-002, or ADR-003 to Non-Blocking. Plan feasibility (re-checked 2026-11-23): every entry ends only through a maintainer-stated approval or a revert, and `AAL-018` is absent by numbering; no part of this issue can be planned as implementer work without a maintainer statement per entry. Rules in the document: an entry is removed once its approval is recorded in the ADR's `### Approval Record` or the pending change is reverted; an implementer must not write an approval.

## Problem
A large backlog of unapproved decision text stays in force, and the Non-Blocking rows weaken verification until approved.

## Reason for Change
Pending approvals are tracked but never closed, so ADR text cannot be treated as approved.

## Implementation Intent
Each entry ends as an approval recorded in its ADR or a reverted change; each Non-Blocking verification row is either approved or restored to blocking with a passing test.

## Target Files or Areas
- `docs/00_governance/governance_03_issue-and-uncertainty-management.md` (Part 5)
- The ADRs named per entry (ADR-001, 002, 003, 004, 005, 006, 008, 009, 010, 012, 014, 015) and `docs/10_adr/adr_01_index.md` (Invariant Verification Matrix)

## Required Changes
- Produce a per-ADR review package (entry, text change, evidence) for the maintainer.
- After the maintainer's statement, record the approval in the ADR's `### Approval Record` and remove the ledger entry, or revert the change.
- For each Non-Blocking verification row, either record its approval or restore the blocking status and make the cited test pass.

## Constraints
- The maintainer states every approval; an implementer never writes an approver, a date, or an approval sentence, and never an entry for a past approval.
- Entries tied to open issues listed in Background close with those issues; entries named after an archived issue (AAL-013, AAL-024 to AAL-028, AAL-014, AAL-015, AAL-036) are handled here.

## Acceptance Criteria
- [ ] Every ledger entry is removed through a recorded approval or a revert.
- [ ] `check_adr_structure.py` and `check_adr_invariant_matrix.py` pass.

## Testing Expectations
ADR-cited invariant tests pass (`.github/run_cited_adr_tests.py`), and the governance checkers pass.

## Documentation Impact
Yes: the ADRs concerned and the governance inventory.

## Out of Scope
- Changing ADR decisions beyond approving or reverting the pending text.

## Dependencies
- AAL-006 to AAL-010 and AAL-029 depend on the maintainer's decision about the EventBus producer/consumer model (NC-003, left open). gov001, gov002, and gov004 are archived and no longer gate any entry.
- Depends on the ADR-004 decisions carried in `issues/20261119-140508_mcpai001_atomic-dedup-state-machine.md`, `issues/20261119-140509_mcpai002_github-read-security-boundary.md`, and `issues/20261119-140519_mcpai012_mcp-design-docs-update.md` for AAL-002, AAL-003, AAL-019.

## Unresolved Questions
- `不明`: the maintainer's decision per entry.

## AI Implementation Instruction
Work ADR by ADR; never write an approver, a date, or an approval sentence, and do not change ADR decisions beyond the pending text.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261123-104604
- **Related target files**: `docs/00_governance/governance_03_issue-and-uncertainty-management.md`, `docs/10_adr/adr_01_index.md`
