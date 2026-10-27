# Align the verification evidence of ADR-001 and ADR-002 with their checklists and the ADR index

## Priority
Medium

## Summary
Some invariants of ADR-001 and ADR-002 have no verification evidence in the ADR's own Automated Tests table, while the ADR-002 Completion Checklist states that every invariant has a Verification, and the ADR index cites evidence for ADR-001 INV-01 that the ADR body lacks. Make the ADR body the canonical home of verification evidence and bring both ADRs, their checklists and the index into agreement.

## Background
- ADR-002 (`adr_02_01_002_platform-config-isolation.md`): the Automated Tests rows for INV-03 ("An MCP server can start standalone without agent.toml") and INV-04 ("The Agent can start without being given MCP-specific Secrets") list Type `Integration`, Blocking `Yes` and Implementation `-`. The Completion Checklist marks "Each Invariant has a corresponding Verification" and "Automatable verification does not rely only on Manual Review" as done. Evidence: `Explicit in code` (document text).
- ADR-001 (`adr_02_02_001_agent-workflow-engine-mandatory.md`): the Automated Tests rows for INV-01, INV-02, INV-03, INV-05 and INV-06 have Implementation `-`. The INV-03 row names a test in its first column, but the Implementation column is still `-`. Evidence: `Explicit in code` (document text).
- `adr_01_index.md` cites a concrete test for ADR-001 INV-01 and marks it `Confirmed`, and the ADR body states that the index holds the invariant verification matrix. The ADR body and the index therefore carry evidence in different places. Evidence: `Explicit in code` (document text).
- `tools/check_adr_invariant_matrix.py` checks that test paths cited in the index matrix exist. It does not read the ADR bodies, so an empty Implementation cell in an ADR body is not detected. Evidence: `Explicit in code` (tool docstring).
- A quick search of `tests/` found no test that clearly covers ADR-002 INV-03 or INV-04; candidates for ADR-001 INV-02, INV-03, INV-05 and INV-06 were not examined. Evidence: `Needs confirmation`.
- No open issue or in-flight plan overlaps (checked `issues/` and `plans/`). Archived `issues/done/20261008-094503_adridx01_correct-adr-index-verification-status-and-pipeline-mapping.md` touched the index statuses only.

## Problem
The Accepted ADRs assert a verification completeness that their own tables do not show, and the evidence for the same invariant is split between the index and the ADR body without a stated canonical source. A test can be renamed or deleted with only one side updated, and the verification level of ADR-002 INV-03 and INV-04 is overstated.

## Reason for Change
Verification status decides whether an invariant is enforceable (see the Gate rules of the ADR index). Overstated evidence in Accepted ADRs defeats that decision. The change depends on the Verification Status vocabulary defined in the dependency below, so it is not independently schedulable earlier.

## Implementation Intent
Treat the ADR body Verification section as the canonical record of evidence, and the index as a synchronized summary of the same evidence. For each invariant with an empty Implementation cell, do exactly one of: cite an existing test by node ID, or record the invariant as not verified using the vocabulary defined by the dependency issue. Make the ADR-002 Completion Checklist state the true status of each item instead of marking it done. Keep the `Completion Checklist` heading, which `check_adr_structure.py` requires. Add the canonical-source statement in one place (the index matrix introduction) and make it consistent with the ADR body note about the index. Do not write new tests in this issue.

## Target Files or Areas
- `docs/10_adr/adr_02_01_002_platform-config-isolation.md` (Verification table, Completion Checklist)
- `docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md` (Verification table)
- `docs/10_adr/adr_01_index.md` (matrix introduction, ADR-001 rows)
- Read-only evidence: `tests/` (search for candidate tests)

## Required Changes
- For ADR-001 INV-01, INV-02, INV-03, INV-05, INV-06 and ADR-002 INV-03, INV-04: search `tests/` for an existing covering test and cite it, or record the invariant as not verified.
- Copy the evidence for ADR-001 INV-01 that the index already cites into the ADR body (or reconcile both to the same test).
- Update the ADR-002 Completion Checklist items about Verification to match the recorded status.
- State in the index matrix introduction that the ADR body Verification section is canonical and the index mirrors it.

## Constraints
- Invariant statements, Decisions and Approval records of both ADRs MUST NOT change.
- A `Blocking` value in an ADR body table MUST NOT be silently changed; if an invariant is recorded as not verified, state how the Blocking column and the index Gate remain consistent under the vocabulary of the dependency issue.
- `check_adr_preservation.py` compares test citations and is expected to report an ERROR for the intended evidence changes. The implementer MUST confirm that every reported change is an intended one and MUST NOT suppress the check.
- `docs/` content MUST be English and MUST follow `skills/DESIGN.md` "Docs content policy — remove" (no source line numbers, no implementation counts).

## Acceptance Criteria
- No invariant of ADR-001 or ADR-002 has an empty Implementation cell without an explicit not-verified status.
- ADR-002 Completion Checklist items about Verification are consistent with the table.
- For every invariant that appears in both an ADR body and the index matrix, the status and the cited evidence agree.
- The index states which side is canonical, and the ADR body note about the index does not contradict it.
- The checkers listed under Testing Expectations pass, except for the `check_adr_preservation.py` entries that are reviewed and recorded as intended.

## Testing Expectations
Documentation-only change. Run:
- `uv run python tools/check_adr_invariant_matrix.py`
- `uv run python tools/check_adr_structure.py`
- `uv run python tools/check_adr_preservation.py` (review each reported change)
- `uv run python tools/check_docs_quality.py`
- `uv run python tools/check_docs_structure.py docs/10_adr/adr_02_01_002_platform-config-isolation.md docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md docs/10_adr/adr_01_index.md`
- `uv run python tools/check_docs_content_policy.py --strict`
- `uv run python tools/check_docs_japanese.py`

## Documentation Impact
Both ADRs and the index must be updated. Kind of information: verification evidence and boundary, completion state of the ADR checklist, and the canonical-source rule between ADR body and index. Any invariant recorded as not verified is a candidate Needs Confirmation or Known Issue entry only if the repository owner decides so.

## Out of Scope
- Writing new tests for the unverified invariants.
- Changing ADR Decisions, Invariants, Gates or Approval records.
- Defining the Verification Status vocabulary (dependency issue).
- Extending `check_adr_invariant_matrix.py` to read ADR bodies (a separate issue in this batch).
- The "diff command" wording in ADR-001 Negative Consequences (a separate issue in this batch).
- ADRs other than ADR-001 and ADR-002.

## Dependencies
- Depends on `issues/20261027-101850_govrev003_partial-verification-gate-rules.md`: that issue defines the Verification Status vocabulary and Gate effects used here. Complete it first.

## Unresolved Questions
- Do existing tests cover ADR-001 INV-02, INV-03, INV-05, INV-06 or ADR-002 INV-03, INV-04? `Needs confirmation` (search during implementation; none found for ADR-002 in a quick search).
- If an invariant is recorded as not verified while its ADR body row says `Blocking: Yes`, which side changes? `不明` (decided under the vocabulary of the dependency issue, with the repository owner).
- Should the ADR-002 Completion Checklist items be unchecked, or kept checked with a status note? `不明`; the checklist heading must remain.

## AI Implementation Instruction
Change only the evidence cells, checklist items and index sentences named above. Cite only test node IDs that exist (verify each path before writing it). Do not invent evidence; record not verified when no test is found. Write in English. Stop and report if `check_adr_preservation.py` shows a change to an Invariant, Decision or Approval text.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261027-101918
- **Related target files**: `docs/10_adr/adr_02_01_002_platform-config-isolation.md`, `docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md`, `docs/10_adr/adr_01_index.md`
