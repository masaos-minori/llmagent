# Define the Gate effect of Partial verification in the ADR Invariant Verification Matrix

## Priority
Medium

## Summary
`adr_01_index.md` defines the Gate effect only for rows whose Verification Status is "Not verified" (Non-Blocking). A row that is partially verified but keeps a Blocking Gate has no defined merge or deployment effect. Define the Verification Status vocabulary and the Gate effect of each value, and add the required evidence for a partially verified Blocking row.

## Background
- The matrix section of `adr_01_index.md` states: a row whose Verification Status is "Not verified" is Non-Blocking, because a gate cannot be enforced without a verification. No other status value has a stated Gate effect. Evidence: `Explicit in code` (document text).
- ADR-004 INV-07 and INV-10 have Gate `Deployment Blocking` and a Verification Status that begins "By phase". The text lists the phases that are confirmed and states that no test covers every listed failure class as a single cross-cutting guarantee. The `Pipeline Mapping Summary` lists both rows under "partial or not verified" for the CI timing and as "(partial)" for startup validation. Evidence: `Explicit in code` (document text).
- Other rows use status text that is neither "Confirmed" nor "Not verified" (for example a Manual Review decision with a stated rationale). Evidence: `Explicit in code`. The full set of status values in use has not been surveyed (`Needs confirmation`).
- `governance_01_documentation-policy.md` Merge Conditions define Blocking and Non-Blocking Conditions for Known Issues, approvals, canonical-source conflicts and test failures. They do not mention ADR verification status. The same document states that the ADR list, dependency graph and invariant verification matrix are maintained in `adr_01_index.md`. Evidence: `Explicit in code`.
- Recent archived issue `issues/done/20261008-094503_adridx01_correct-adr-index-verification-status-and-pipeline-mapping.md` corrected index statuses; it did not define the vocabulary. No open issue or in-flight plan overlaps (checked `issues/` and `plans/`).

## Problem
For a partially verified invariant with a Blocking Gate, it is undefined whether the Gate is met, whether only the unverified part falls back to a manual gate, and whether merge or deployment is blocked. Reviewers can judge the same row differently, and a Blocking invariant can silently behave as a warning.

## Reason for Change
The Gate column is the mechanism that makes an Accepted ADR enforceable. An undefined case for partial verification weakens that mechanism for the ADR-004 fail-fast invariants, which are Deployment Blocking.

## Implementation Intent
Keep the existing Gate values and the existing "Not verified is Non-Blocking" rule. Add a definition of the Verification Status vocabulary (at least Confirmed, Partial, Not verified) next to the matrix in `adr_01_index.md`, which is the maintained source of the matrix. State the Gate effect of each value. Recommended rule for Partial: the Gate is unchanged, and the row MUST state the unverified scope, the alternative manual verification procedure, and the Owner. Do not lower any Gate and do not change any Invariant. Reference the definition from `governance_01` Merge Conditions only if a pointer is needed for discoverability.

## Target Files or Areas
- `docs/10_adr/adr_01_index.md` (matrix introduction and the ADR-004 INV-07 and INV-10 rows)
- `docs/00_governance/governance_01_documentation-policy.md` (Merge Conditions, pointer only if needed)

## Required Changes
- Survey the Verification Status values currently used in the matrix and map each to a defined value.
- Define each Verification Status value and its Gate effect in the matrix introduction.
- Define the mandatory content of a Partial row: unverified scope, alternative manual procedure, Owner.
- Update the ADR-004 INV-07 and INV-10 rows to the defined form without changing their Gate or their invariant statement.
- Align the `Pipeline Mapping Summary` wording with the defined vocabulary.

## Constraints
- Gate values of existing rows MUST NOT be lowered or removed.
- Invariant statements, ADR Decisions and Approval records MUST NOT change; `check_adr_preservation.py` MUST report no ERROR.
- `docs/` content MUST be English and MUST follow `skills/DESIGN.md` "Docs content policy — remove" and "No implementation counts".

## Acceptance Criteria
- The vocabulary and the Gate effect of every Verification Status value are stated once, in `adr_01_index.md`.
- Every row of the matrix uses a defined status value.
- Each Partial row names its unverified scope, an alternative manual procedure and an Owner.
- ADR-004 INV-07 and INV-10 keep their Gate and satisfy the Partial row rule.
- The checkers listed under Testing Expectations pass.

## Testing Expectations
Documentation-only change. Run:
- `uv run python tools/check_adr_invariant_matrix.py`
- `uv run python tools/check_adr_preservation.py`
- `uv run python tools/check_adr_structure.py`
- `uv run python tools/check_docs_quality.py`
- `uv run python tools/check_docs_structure.py docs/10_adr/adr_01_index.md`
- `uv run python tools/check_docs_content_policy.py --strict`
- `uv run python tools/check_docs_japanese.py`

## Documentation Impact
`adr_01_index.md` must be updated with the status vocabulary, Gate effects and the Partial row requirements (verification boundary, failure behavior of the gate, Owner). `governance_01` changes only by an optional pointer.

## Out of Scope
- Writing new tests for ADR-004 INV-07 and INV-10.
- Changing any Gate value or any ADR invariant.
- Making the matrix machine-generated, and extending `check_adr_invariant_matrix.py` (a separate issue in this batch).
- Reconciling ADR body and index evidence (a separate issue in this batch).

## Dependencies
N/A: none. No open issue or in-flight plan touches these sections. This issue should be completed before the ADR verification-evidence issues of this batch, which use the vocabulary defined here.

## Unresolved Questions
- Should a Partial row carry an expiry date or review deadline in addition to Owner? `不明` (the recommendation omits it; the repository owner decides).
- Which Verification Status values are in use today beyond Confirmed, Not verified and "By phase"? `Needs confirmation` (survey in the first Required Change).
- Whether `governance_01` Merge Conditions should state the effect of a partially verified Blocking row directly is `不明`.

## AI Implementation Instruction
Change only the matrix introduction, the two ADR-004 rows, the Pipeline Mapping Summary wording and, if needed, one pointer line in `governance_01`. Do not edit other rows' invariant statements or Gates. Keep a table row in a single line. Write in English. Stop and report if the survey shows a status value whose meaning cannot be mapped.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261027-101850
- **Related target files**: `docs/10_adr/adr_01_index.md`, `docs/00_governance/governance_01_documentation-policy.md`
