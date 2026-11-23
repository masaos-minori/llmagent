# Work down the ADR Approval Ledger and the Non-Blocking verification rows

## Priority
Low

## Summary
37 ADR decision-text changes (AAL-001 to AAL-038, with 018 absent) are written into ADRs with approver and date `Not recorded`, including seven entries (AAL-001, 031 to 036) that set a verification row to Non-Blocking in the ADR's own Verification table. Close each through a recorded approval or a revert.

## Background
Source: `docs/00_governance/governance_03_issue-and-uncertainty-management.md` Part 5 (37 entries, counted by `grep` and by a parse of the entry fields on 2026-11-23: every entry has the six fields and both `Approver` and `Date` are `Not recorded`). Verified against the ADRs (adversarial pass, 2026-11-23):
- **Ledger and ADRs agree.** Every ledger entry is cited by exactly the ADR it names, in that ADR's `Current Decision Approval (pending)` bullet. The only ADR citation without an entry is `AAL-018`, which is not dangling: ADR-016's `Current Decision Approval (amendment, 2026-11-20)` records the owner's approval of that change ("previously tracked as AAL-018"). That is the precedent for how an entry closes (the approval is written by the maintainer's statement into the ADR's Approval Record and the entry is then removed); the numbering gap is therefore expected.
- **Per-ADR count** of the 37 entries: ADR-008 7, ADR-006 6, ADR-003 6, ADR-002 3, ADR-004 3, ADR-005 3, ADR-012 3, ADR-015 2, and ADR-001, ADR-009, ADR-010, ADR-014 one each.
- **The seven Non-Blocking entries are AAL-001 (ADR-001 INV-02), AAL-031 and AAL-032 (ADR-002 INV-03, INV-04), AAL-033 to AAL-035 (ADR-003 INV-03, INV-04, INV-07), and AAL-036 (ADR-012 INV-04).** The Non-Blocking value sits in each ADR's own `## Verification` table (`Blocking = No`, `Not verified`), not in the `adr_01_index.md` matrix, except ADR-012 INV-04 which the matrix also lists as Non-Blocking. ADR-001 INV-02 and the ADR-002 rows state `no automated test exists`; for ADR-003 INV-03 the matrix row is `Blocking`/`Partial` (a unit test covers the write-classification part) while the ADR table keeps one separate `Not verified` integration row, so only that row is Non-Blocking. **These rows cite no test, so "restore blocking and make the cited test pass" is not possible as worded: restoring blocking first needs a new automated test.**
- **Entries named after other issues (re-verified):** AAL-013 (ADR-010 fallback withdrawal) and AAL-024 to AAL-028 (ADR-008 scope, schema-mismatch, retention, and canonical-store text) were named after `issues/done/20261123-104600_gov001_resolve-adr-contradictions.md`, which is archived and left all six entries in the ledger, so they are this issue's own open items; AAL-014, AAL-015, AAL-036 (ADR-012) belong with `issues/done/20261123-104601_gov002_git-protected-head-tests.md`, archived without removing them (it added a regression test class for the HEAD-destination check only; AAL-036's INV-04 stays Not verified); AAL-006 to AAL-010 and AAL-029 (EventBus text of ADR-006 and ADR-008) stay open: `issues/done/20261123-104603_gov004_eventbus-client-decision.md` is archived with its plan executed for retiring the two unused client modules only (maintainer decision 2026-11-23), and by the maintainer's decision NC-003 (the producer/consumer model) stays open.
- **Correction of the earlier claim about AAL-002, AAL-003, and AAL-019:** they are ADR-004 text changes (Decision Group 10 amendment, the INV-14 verification text, and the availability classification of RAG derived-index results in Group 2 item 7), not ADR-004 *exceptions*. The three mcpai issues do not carry them: `issues/done/20261119-140508_mcpai001_atomic-dedup-state-machine.md` (archived; its plan `plans/20261123-130937_mcpai001_atomic-dedup-state-machine.md` does not cite them), `issues/20261119-140509_mcpai002_github-read-security-boundary.md` (carries NC-001, not an AAL entry), and `issues/20261119-140519_mcpai012_mcp-design-docs-update.md` (cites MCP-001, MCP-002, NC-001, NC-002). AAL-019 is also the point the maintainer question MCP-003 (`failure_category` versus Group 2 item 7) depends on.
- The remaining entries are AAL-001, 004, 005, 011, 012, 016, 017, 020 to 023, 030 to 035, 037, 038.
- Rules in the document (Part 5 `### Rules`): an entry is removed once its approval is recorded in the ADR's `### Approval Record` or the pending change is reverted; `Approver` and `Date` stay `Not recorded` until the maintainer states them; an implementer must not write approval text or an entry for a past approval.
- Plan feasibility: the approval or revert of every entry needs a maintainer statement; the only part an implementer can do alone is (a) the per-ADR review package and (b) writing the missing automated tests behind the seven Non-Blocking rows.

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
- Produce a per-ADR review package (entry, text change, evidence) for the maintainer. Deliverable form and location are an open question (see Unresolved Questions); it contains no approval text.
- After the maintainer's statement, record the approval in the ADR's `### Approval Record` and remove the ledger entry, or revert the change.
- For each of the seven Non-Blocking verification rows, the maintainer either approves the Non-Blocking value, or an implementer adds the missing automated test (the rows cite none), sets the row to Blocking with the test cited as evidence, and the entry is then removed as a reverted change; the matrix `adr_01_index.md` and its citation count stay consistent.

## Constraints
- The maintainer states every approval; an implementer never writes an approver, a date, or an approval sentence, and never an entry for a past approval.
- Entries tied to an open issue close with that issue (currently none: gov001, gov002, and gov004 are archived and left their entries open); entries that were named after an archived issue (AAL-013, AAL-024 to AAL-028, AAL-014, AAL-015, AAL-036, AAL-006 to AAL-010, AAL-029) are handled here.
- A new test for a Non-Blocking row must be a real automated test that fails when the invariant is violated; a test that only asserts the current state does not restore blocking.

## Acceptance Criteria
- [ ] Every ledger entry is removed through a recorded approval or a revert.
- [ ] Each of the seven Non-Blocking rows is either approved by the maintainer or Blocking with a cited, passing automated test.
- [ ] `check_adr_structure.py` and `check_adr_invariant_matrix.py` pass.

## Testing Expectations
ADR-cited invariant tests pass (`.github/run_cited_adr_tests.py`) including any new test added for a restored Blocking row, `tests/test_run_cited_adr_tests.py` citation-count pins are updated with the matrix, and the governance checkers pass.

## Documentation Impact
Yes: the ADRs concerned and the governance inventory.

## Out of Scope
- Changing ADR decisions beyond approving or reverting the pending text.

## Dependencies
- AAL-006 to AAL-010 and AAL-029 depend on the maintainer's decision about the EventBus producer/consumer model (NC-003, left open). gov001, gov002, and gov004 are archived and no longer gate any entry.
- AAL-019 is linked to the open maintainer question in MCP-003 (`failure_category` versus ADR-004 Group 2 item 7); the two should be decided together.
- No dependency on the mcpai issues (the earlier statement was wrong, see Background).

## Unresolved Questions
- `不明`: the maintainer's decision per entry (approve or revert), all 37.
- `不明`: whether the maintainer wants the per-ADR review package, and in what form and location (a one-time artifact or a repository document); without that answer it is not planned.
- `不明`: for each of the seven Non-Blocking rows, approve the Non-Blocking value or have an automated test added; the second option is the only part an implementer can plan on its own, and the ADR-003 INV-03 row needs a decision on whether the matrix `Partial` row already satisfies it.

## AI Implementation Instruction
Work ADR by ADR; never write an approver, a date, or an approval sentence, and do not change ADR decisions beyond the pending text. Plan only the part an implementer can do alone (adding the missing automated test behind a Non-Blocking row, and the review package once its form is decided); every approval or revert waits for the maintainer's statement.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261123-104604
- **Related target files**: `docs/00_governance/governance_03_issue-and-uncertainty-management.md`, `docs/10_adr/adr_01_index.md`
