# Work down the ADR Approval Ledger and the Non-Blocking verification rows

## Priority
Low

## Summary
32 ADR decision-text changes (AAL-002 to AAL-041; AAL-001, AAL-018, AAL-026, AAL-027, AAL-031, and AAL-033 to AAL-036 are absent) are written into ADRs with approver and date `Not recorded`, including one entry (AAL-032) that sets a verification row to Non-Blocking in the ADR's own Verification table. Close each through a recorded approval or a revert.

## Background
Source: `docs/00_governance/governance_03_issue-and-uncertainty-management.md` Part 5 (32 entries, re-counted by a parse of the entry fields on 2026-11-24 after the gov006 and adrdoc001 changes; the issue was filed on 2026-11-23 with 37 entries: every entry has the six fields and both `Approver` and `Date` are `Not recorded`). Verified against the ADRs (adversarial pass, 2026-11-23):
- **Ledger and ADRs agree.** Every ledger entry is cited by exactly the ADR it names, in that ADR's `Current Decision Approval (pending)` bullet. The only ADR citation without an entry is `AAL-018`, which is not dangling: ADR-016's `Current Decision Approval (amendment, 2026-11-20)` records the owner's approval of that change ("previously tracked as AAL-018"). That is the precedent for how an entry closes (the approval is written by the maintainer's statement into the ADR's Approval Record and the entry is then removed); the numbering gap is therefore expected.
- **Per-ADR count** of the 32 entries (2026-11-24): ADR-006 8, ADR-008 6, ADR-003 3, ADR-004 3, ADR-005 3, ADR-002 2, ADR-012 2, ADR-015 2, and ADR-009, ADR-010, ADR-014 one each; ADR-001 has none.
- **One Non-Blocking entry remains: AAL-032 (ADR-002 INV-04).** The other six (AAL-001, AAL-031, AAL-033 to AAL-036) were closed by gov006, which added automated tests and restored the blocking rows (commit c4ec52349); their entries no longer exist. The remaining row sits in the ADR's own `## Verification` table (`Blocking = No`, `Not verified`) and cites no test, so restoring blocking first needs a new automated test.
- **Entries named after other issues (re-verified 2026-11-24):** AAL-013 (ADR-010 fallback withdrawal), AAL-025 and AAL-028 (ADR-008 schema-mismatch rule and INV-04) were named after `issues/done/20261123-104600_gov001_resolve-adr-contradictions.md`, which is archived and left them in the ledger, so they are this issue's own open items; AAL-014 and AAL-015 (ADR-012) belong with `issues/done/20261123-104601_gov002_git-protected-head-tests.md`, archived without removing them; AAL-006 to AAL-010 and AAL-029 (EventBus text of ADR-006 and ADR-008) stay open: `issues/done/20261123-104603_gov004_eventbus-client-decision.md` is archived with its plan executed for retiring the two unused client modules only (maintainer decision 2026-11-23), and by the maintainer's decision NC-003 (the producer/consumer model) stays open. The ADR-008 amendment of 2026-11-24 (`issues/done/20261124-093927_adrdoc001_adr-eventbus-memory-amendment.md`) changed the set: AAL-024 now reads six SQLite stores; AAL-026 and AAL-027 were withdrawn and their entries removed; AAL-029 was narrowed to the no-loss statement under the ADR-008 schema-mismatch rule; AAL-039 (Repository Context and Episodic Memory), AAL-040 (removal of EventBus `events.jsonl`), and AAL-041 (state-aware retention and replay expiration) were added. These new entries are this issue's open items, and the per-ADR review packages in Required Changes cover them.
- **Correction of the earlier claim about AAL-002, AAL-003, and AAL-019:** they are ADR-004 text changes (Decision Group 10 amendment, the INV-14 verification text, and the availability classification of RAG derived-index results in Group 2 item 7), not ADR-004 *exceptions*. The three mcpai issues do not carry them: `issues/done/20261119-140508_mcpai001_atomic-dedup-state-machine.md` (archived; its plan `plans/20261123-130937_mcpai001_atomic-dedup-state-machine.md` does not cite them), `issues/20261119-140509_mcpai002_github-read-security-boundary.md` (carries NC-001, not an AAL entry), and `issues/20261119-140519_mcpai012_mcp-design-docs-update.md` (cites MCP-001, MCP-002, NC-001, NC-002). AAL-019 is also the point the maintainer question MCP-003 (`failure_category` versus Group 2 item 7) depends on.
- The remaining entries are AAL-002 to AAL-005, AAL-011, AAL-012, AAL-016, AAL-017, AAL-019 to AAL-023, AAL-030, AAL-032, AAL-037, and AAL-038.
- Rules in the document (Part 5 `### Rules`): an entry is removed once its approval is recorded in the ADR's `### Approval Record` or the pending change is reverted; `Approver` and `Date` stay `Not recorded` until the maintainer states them; an implementer must not write approval text or an entry for a past approval.
- Plan feasibility: the approval or revert of every entry needs a maintainer statement; the only part an implementer can do alone is (a) the per-ADR review package and (b) writing the missing automated test behind the remaining Non-Blocking row (AAL-032).

### Review package for the ADR-006 and ADR-008 entries changed on 2026-11-24

Prepared from the ADR amendment of 2026-11-24 (`issues/done/20261124-093927_adrdoc001_adr-eventbus-memory-amendment.md` and its plan). It contains no approval text; `Approver` and `Date` stay `Not recorded`. The "Proposed disposition" column is a recommendation of the preparer, not a decision.

| Entry | ADR | Old decision | Proposed decision | Implementation impact (tracking Known Issue) | Verification expectation | Proposed disposition |
|---|---|---|---|---|---|---|
| AAL-024 | ADR-008 | Four platform databases | Six SQLite stores (title, Summary, Scope, Recovery Policy Matrix) | None (documentation) | Existing `tools/check_db_separation.py` covers the four platform-domain databases | Approve |
| AAL-025 | ADR-008 | Schema mismatch: archive and recreate, memory recovered from the JSONL archive with `/memory rebuild` | Archive and recreate; Episodic Memory is not carried over (only the JSONL precondition is removed) | None for the rule; the `/memory rebuild` removal is SHARED-003 | Existing | Approve |
| AAL-028 | ADR-008 | INV-04 without the outbox record | INV-04 names the `dlq_outbox` durable promotion record | None | Existing | Approve |
| AAL-029 | ADR-006 | No-loss claims plus an accepted retention risk | No-loss claims hold under the ADR-008 schema-mismatch rule (the retention-risk part is withdrawn) | None | Existing | Approve |
| AAL-039 | ADR-008 | Semantic and Episodic memory, JSONL archive, pin, manual writes, `/memory` | Repository Context (non-persistent) and Episodic Memory (only persistent memory, `session.sqlite` only); INV-19 to INV-22 | Large: remove the old memory model and JSONL, add the Repository Context loader, `/reload` snapshot and diagnostics, retire configuration keys (SHARED-003) | INV-20 to INV-22 Not verified until implemented | Approve; undecided parts stay under SHARED-004 |
| AAL-040 | ADR-006 | JSONL archive as a secondary audit log | No `events.jsonl`; `eventbus.sqlite` is the sole source of truth (Decision Details 15 to 17, INV-17, INV-18, INV-21) | Medium: remove the JSONL append and its metric from the publish route (EVENTBUS-001) | INV-17 partial, INV-18 and INV-21 Not verified | Approve |
| AAL-041 | ADR-006 | Unbounded growth accepted | State-aware retention, replay floor with HTTP 410 `replay_position_expired`, capacity and readiness rules (Decision Details 18 to 20, INV-19, INV-20, INV-22) | Large: retention task and registry, purge, floor check, health fields, configuration keys, EventBus schema change (recreate policy) (EVENTBUS-002) | INV-19, INV-20, INV-22 Not verified | Approve; purge stays forbidden until the registry is implemented |

Not touched by the amendment and still pending: AAL-006 to AAL-009 and AAL-037 (ADR-006), AAL-010 and AAL-011 (ADR-008).

Maintainer decisions stated in the session of 2026-11-24 (preference statements that unblock the approvals; they are not Approval Records, and each text change that follows needs its own pending entry or approval):
- D1, retention-participant registry: an explicit registry in `eventbus.sqlite` with explicit registration and decommission. Follow-up: amend ADR-006 Decision Detail 18 from the open owner decision to this model (a new pending entry), and update EVENTBUS-002 and the EventBus documents that cite the open decision.
- D3, Episodic Memory schema mismatch: the ADR-008 Decision Detail 22 text (archive and recreate, Episodic Memory not carried over) is the final policy. Follow-up: remove the "undecided (SHARED-004)" qualifier for the schema-mismatch handling from `agent_09_01`, `db_03`, `deployment_01`, ADR-008 Known Deviations, and SHARED-004; retention and event categories stay undecided.
- D10, `/memory`: remove it from the code first (the SHARED-003 implementation issue), then remove the retired entry, the retired usage-form table, and the retired configuration-key rows from the documents.

Decisions still open (each cites its Known Issue): the `/subscribe` meaning of `since_seq=0` (ADR-006 open decision); Episodic event categories and retention (SHARED-004); Repository Context configuration keys, source list, and authority values (SHARED-003); the failure behavior when mandatory input exceeds the context limit (SHARED-004); archive retention bounds and the minimum number of verified generations (EVENTBUS-002); the EventBus-generated retention timestamp column (EVENTBUS-002); health field names, thresholds, and the audit-log destination (EVENTBUS-002).

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
- Keep the review package under Background up to date: it is the deliverable for the maintainer (entry, old and proposed decision, implementation impact, verification expectation); it contains no approval text. Its form and location were decided by the maintainer on 2026-11-24 (a repository document; this issue is the location, because `docs/` keeps current specifications only).
- After the maintainer's statement, record the approval in the ADR's `### Approval Record` and remove the ledger entry, or revert the change.
- For the remaining Non-Blocking verification row (AAL-032, ADR-002 INV-04), the maintainer either approves the Non-Blocking value, or an implementer adds the missing automated test (the rows cite none), sets the row to Blocking with the test cited as evidence, and the entry is then removed as a reverted change; the matrix `adr_01_index.md` and its citation count stay consistent.

## Constraints
- The maintainer states every approval; an implementer never writes an approver, a date, or an approval sentence, and never an entry for a past approval.
- Entries tied to an open issue close with that issue (currently none: gov001, gov002, and gov004 are archived and left their entries open); entries that were named after an archived issue (AAL-013, AAL-025, AAL-028, AAL-014, AAL-015, AAL-006 to AAL-010, AAL-029, and the entries AAL-024 and AAL-039 to AAL-041 from the archived adrdoc001) are handled here.
- A new test for a Non-Blocking row must be a real automated test that fails when the invariant is violated; a test that only asserts the current state does not restore blocking.

## Acceptance Criteria
- [ ] Every ledger entry is removed through a recorded approval or a revert.
- [ ] The remaining Non-Blocking row (AAL-032) is either approved by the maintainer or Blocking with a cited, passing automated test.
- [ ] `check_adr_structure.py` and `check_adr_invariant_matrix.py` pass.

## Testing Expectations
ADR-cited invariant tests pass (`.github/run_cited_adr_tests.py`) including any new test added for a restored Blocking row, `tests/test_run_cited_adr_tests.py` citation-count pins are updated with the matrix, and the governance checkers pass.

## Documentation Impact
Yes: the ADRs concerned and the governance inventory.

## Out of Scope
- Changing ADR decisions beyond approving or reverting the pending text.

## Dependencies
- AAL-006 to AAL-010 and AAL-029 depend on the maintainer's decision about the EventBus producer/consumer model (NC-003, left open). AAL-041 also depends on the approval of the retention-participant registry model (an open owner decision recorded in ADR-006). gov001, gov002, and gov004 are archived and no longer gate any entry.
- AAL-019 is linked to the open maintainer question in MCP-003 (`failure_category` versus ADR-004 Group 2 item 7); the two should be decided together.
- No dependency on the mcpai issues (the earlier statement was wrong, see Background).

## Unresolved Questions
- `不明`: the maintainer's decision per entry (approve or revert), all 32.
- `不明`: whether the proposed dispositions in the review package are accepted; each approval still needs the maintainer's own statement.
- `不明`: for the remaining Non-Blocking row (AAL-032, ADR-002 INV-04), approve the Non-Blocking value or have an automated test added; the second option is the only part an implementer can plan on its own.

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
