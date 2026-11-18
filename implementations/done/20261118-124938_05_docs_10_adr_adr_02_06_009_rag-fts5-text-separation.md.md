## Goal
Correct ADR-009's transaction boundary and state its invariant numbering (REQ-004), and after the decision align its Degraded condition (REQ-007).

## Scope
**Release unit**: N/A: not part of a release unit
- `## Data Ownership and Persistence`, `## Invariants`, and after the decision `### Runtime Monitoring`.

## Assumptions
- UNK-05 default: the transaction boundary correction aligns wording to the code (one transaction per URL, `TransactionManager.commit`) and to ADR-005; if the owner treats it as a decision change, show it in the pending-amendment form and add its ledger entry in procedure 04.
- UNK-04 default: state the current numbering; do not renumber. INV-09 was folded into INV-04 (a pending amendment), so the statement is current-specification only and carries no history.

## Design decisions
- Use the ADR-005 term `per document` for the boundary.

## Alternatives considered
Renumbering INV-10 and INV-11 down to close the gap was rejected: it changes citations and needs an approval record (UNK-04).

## Implementation
### Target file
`docs/10_adr/adr_02_06_009_rag-fts5-text-separation.md`
### Procedure
1. `Transaction Boundary`: change `per chunk` to `per document`.
2. After the last invariant (INV-11) of `## Invariants` add one sentence: INV-09 is not used. (Step 3a correction: the list jumps from INV-08 to INV-10, and INV-10 and INV-11 are in the list, not in Implementation Notes.)
3. Gate: confirm that the maintainer's decision on the Source plan's option table (UNK-01: option A, B, or C) is recorded as a maintainer comment on the Source plan; stop and ask when it is not. Option C changes startup behavior and is a Plan amendment: stop. Write no policy decision and no approval text. Then align the `Degraded condition` line of `### Runtime Monitoring` with the decision (it stays `fts_gap > 0` unless the decision changes the Degraded set). Show an ADR change that alters a decision only in the pending-amendment form of the policy governance document: a `Current Decision Approval (pending)` bullet under `### Approval Record` that cites its ledger entry; the Status line stays `Accepted`. Cite the ledger entry that procedure 04 added for ADR-009 (AAL-021, and AAL-022 for a boundary decision change).
### Method
Edit in place; keep the heading order the structure checker requires; do not edit the Status line.
### Details
- Check the Verification table and `### Manual Review`: the line that cites INV-11 stays valid with the new statement.
- The decision-dependent edit may be a wording-only alignment under option A or B; still show it in the pending form if it changes the Degraded set.

## Compatibility considerations
N/A: wording alignment to the code; no invariant is added, removed, or renumbered.

## Security considerations
N/A: documentation-only change; no approval text is written.

## Rollback considerations
N/A: revert the commit

## Validation plan
- `uv run python tools/check_adr_structure.py`, `uv run python tools/check_adr_authority.py`, `uv run python tools/check_adr_invariant_matrix.py`, `uv run python tools/check_adr_preservation.py` (its Approval-section reports are reviewed, not suppressed)
- `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py`, `uv run python tools/check_docs_content_policy.py`, `uv run python tools/check_docs_japanese.py`
- `uv run python tools/check_canonical_source_registry.py`

## Completion criteria
- ADR-009 states `per document` and its invariant numbering (AC-4).
- Any decision-dependent change is in the pending form and cites an existing ledger entry (AC-7).

## Out of Scope
- Renumbering invariants.
- Writing approval text.
- Editing any other ADR.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Confirm UNK-04 and UNK-05 with the owner | Completed | 20261118-130657 | 20261118-130657 | Owner decisions UNK-04 (state the current numbering) and UNK-05 (wording alignment, no approval record) confirmed in session 2026-11-18 via AskUserQuestion |
| 2 | Correct the transaction boundary and add the numbering statement (REQ-004) | Completed | 20261118-130657 | 20261118-130740 | Transaction Boundary corrected to per document (code: one BEGIN IMMEDIATE transaction per URL; ADR-005 says per document); one sentence after the last invariant says INV-09 is not used; changed: docs/10_adr/adr_02_06_009_rag-fts5-text-separation.md. Step 3a correction: the first edit wrongly said INV-10 and INV-11 are in Implementation Notes; they are in the Invariants list after INV-08, so the sentence was rewritten, and the plan and this procedure were corrected |
| 3 | Confirm the maintainer decision (UNK-01) | Completed | 20261118-130740 | 20261118-130740 | Maintainer decision UNK-01 recorded in session 2026-11-18: option A |
| 4 | Align the Degraded condition in the pending form if the decision needs it (REQ-007) | Completed | 20261118-130740 | 20261118-130740 | No change: under option A the Degraded set is unchanged, so the Degraded condition stays fts_gap > 0 and no pending bullet or ledger entry is needed |
| 5 | Run the ADR and documentation checkers listed in Validation plan | Completed | 20261118-130740 | 20261118-130740 | ADR structure, invariant matrix, authority, reference, canonical registry, docs quality/structure/content-policy/japanese: pass; check_adr_preservation reports Data Ownership and Invariants wording changes (WARNING), reviewed: no decision changed |

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
- **Requirement ID**: `REQ-004`: transaction boundary and numbering; `REQ-007`: Degraded condition follows the decision
- **Source issue**: issues/20261117-123006_adrchk006_rag-failure-policy.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261118-124317_adrchk006_rag-failure-policy.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-124938
- **Related target files**: `docs/10_adr/adr_02_06_009_rag-fts5-text-separation.md`
