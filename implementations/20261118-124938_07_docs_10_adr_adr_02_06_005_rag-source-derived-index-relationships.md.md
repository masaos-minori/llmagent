## Goal
Align ADR-005's Fail-Open or Degraded Conditions with the recorded decision, in the pending-amendment form (REQ-007).

## Scope
**Release unit**: N/A: not part of a release unit
- `### Fail-Open or Degraded Conditions`, the Degraded condition line, and `### Approval Record`.

## Assumptions
- Gate: confirm that the maintainer's decision on the Source plan's option table (UNK-01: option A, B, or C) is recorded as a maintainer comment on the Source plan; stop and ask when it is not. Option C changes startup behavior and is a Plan amendment: stop. Write no policy decision and no approval text.
- The section's first bullet delegates the startup policy and the timeout behavior to the RAG guide; after the decision ADR-005 points to ADR-004, which owns the classification, and keeps its own statement that the post-ingestion check only logs warnings.
- The file already has two pending bullets (the ledger entries for the Decision 10 remediation and the Decision 8 rewrite); do not touch them.

## Design decisions
- Show an ADR change that alters a decision only in the pending-amendment form of the policy governance document: a `Current Decision Approval (pending)` bullet under `### Approval Record` that cites its ledger entry; the Status line stays `Accepted`.

## Alternatives considered
N/A: the section follows the decision.

## Implementation
### Target file
`docs/10_adr/adr_02_06_005_rag-source-derived-index-relationships.md`
### Procedure
1. Confirm the gate.
2. Replace the delegation to the guide with a statement that the startup classification of a derived-index mismatch, a check timeout, and a check exception is owned by ADR-004; keep the post-ingestion bullet.
3. Align the `Degraded condition` line only if the decision changes the Degraded set.
4. Add a `Current Decision Approval (pending)` bullet citing the ledger entry procedure 04 added for ADR-005 (AAL-020).
### Method
Edit in place; keep the section order and the existing pending bullets.
### Details
- Do not restate the policy: ADR-004 owns it.

## Compatibility considerations
N/A: wording shown as a pending amendment; no code change.

## Security considerations
N/A: documentation-only change; no approval text is written.

## Rollback considerations
N/A: revert the commit

## Validation plan
- `uv run python tools/check_adr_structure.py`, `uv run python tools/check_adr_authority.py`, `uv run python tools/check_adr_invariant_matrix.py`, `uv run python tools/check_adr_preservation.py` (its Approval-section reports are reviewed, not suppressed)
- `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py`, `uv run python tools/check_docs_content_policy.py`, `uv run python tools/check_docs_japanese.py`
- `uv run python tools/check_canonical_source_registry.py`

## Completion criteria
- ADR-005 points to ADR-004 for the classification and the change is in the pending form with an existing ledger entry (AC-7).

## Out of Scope
- Writing approval text.
- Editing ADR-004 or the guide.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Confirm the maintainer decision (UNK-01) | Pending | — | — | Stop and ask if absent |
| 2 | Edit the Fail-Open or Degraded Conditions section | Pending | — | — |  |
| 3 | Add the pending bullet citing the ledger entry | Pending | — | — |  |
| 4 | Run the ADR and documentation checkers listed in Validation plan | Pending | — | — |  |

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
- **Requirement ID**: `REQ-007`: ADR-005 follows the decision
- **Source issue**: issues/20261117-123006_adrchk006_rag-failure-policy.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261118-124317_adrchk006_rag-failure-policy.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-124938
- **Related target files**: `docs/10_adr/adr_02_06_005_rag-source-derived-index-relationships.md`
