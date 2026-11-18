## Goal
State how ADR-004 classifies a derived-index mismatch, a check timeout, and a check exception, as the maintainer decided, in the pending-amendment form (REQ-007).

## Scope
**Release unit**: N/A: not part of a release unit
- The classification text (a Decision Group 2 availability entry or an `## Exceptions` entry, per the decision) and `### Approval Record`.

## Assumptions
- Gate: confirm that the maintainer's decision on the Source plan's option table (UNK-01: option A, B, or C) is recorded as a maintainer comment on the Source plan; stop and ask when it is not. Option C changes startup behavior and is a Plan amendment: stop. Write no policy decision and no approval text.
- Option A adds the RAG derived-index results (DEGRADED findings, check timeout, check exception) to the availability failures of Group 2 and states the conditions of Group 2 item 8 that hold; option B adds an Exception entry whose rationale the maintainer writes: the implementer writes the structure and an inline `PENDING (Needs confirmation)` marker, never the rationale or an approval.
- The file has almost no room under its per-file size ceiling; procedure 09 re-records the ceiling after this edit.

## Design decisions
- Show an ADR change that alters a decision only in the pending-amendment form of the policy governance document: a `Current Decision Approval (pending)` bullet under `### Approval Record` that cites its ledger entry; the Status line stays `Accepted`.
- Describe the behavior the code has (warn and continue); do not describe a behavior the code lacks.

## Alternatives considered
Option C (fail closed) was excluded from this procedure: it changes startup behavior and is a Plan amendment.

## Implementation
### Target file
`docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md`
### Procedure
1. Confirm the gate.
2. Option A: add one availability entry to Group 2 and one sentence stating the item 8 conditions that hold and the partial-availability signal (the startup warning). Option B: add one `## Exceptions` entry naming the three results and the warn-and-continue outcome, with the inline rationale marker.
3. Add a `Current Decision Approval (pending)` bullet under `### Approval Record` that cites the ledger entry procedure 04 added for ADR-004 (AAL-019); change no other Approval line.
4. Under option B, confirm the NC registry entry of procedure 04 exists for the inline marker.
### Method
Edit in place; keep the section order; use the document's numbering style.
### Details
- Keep the text short: the file is near its size ceiling.
- Do not write a rationale, an approver, or an approval date.

## Compatibility considerations
N/A: classification wording shown as a pending amendment; the code behavior is unchanged.

## Security considerations
N/A: documentation-only change; the exception or classification is recorded, not approved.

## Rollback considerations
N/A: revert the commit

## Validation plan
- `uv run python tools/check_adr_structure.py`, `uv run python tools/check_adr_authority.py`, `uv run python tools/check_adr_invariant_matrix.py`, `uv run python tools/check_adr_preservation.py` (its Approval-section reports are reviewed, not suppressed)
- `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py`, `uv run python tools/check_docs_content_policy.py`, `uv run python tools/check_docs_japanese.py`
- `uv run python tools/check_known_deviation_sync.py`, `uv run python tools/check_needs_confirmation_inventory.py`

## Completion criteria
- ADR-004 explicitly covers the RAG consistency timeout, exception, and DEGRADED behavior as decided (AC-7).
- The change is in the pending form with an existing ledger entry, and no approval text is written.

## Out of Scope
- Writing the rationale or approval text.
- Editing other ADR-004 decisions or code.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Confirm the maintainer decision (UNK-01) | Pending | — | — | Stop and ask if absent; option C is a Plan amendment |
| 2 | Add the classification text or the Exception entry | Pending | — | — |  |
| 3 | Add the pending bullet citing the ledger entry | Pending | — | — |  |
| 4 | Run the ADR and documentation checkers listed in Validation plan | Pending | — | — | Size check fails until procedure 09 |

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
- **Requirement ID**: `REQ-007`: ADR-004 covers the RAG consistency timeout, exception, and DEGRADED behavior
- **Source issue**: issues/20261117-123006_adrchk006_rag-failure-policy.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261118-124317_adrchk006_rag-failure-policy.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-124938
- **Related target files**: `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md`
