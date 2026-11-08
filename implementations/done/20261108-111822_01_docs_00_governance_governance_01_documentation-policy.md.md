## Goal
Add to `governance_01` the ADR responsibility rule, the current-versus-historical marking rule, and the relocation rule (REQ-001, REQ-002, REQ-003).

## Scope
**Release unit**: N/A: not part of a release unit
Adds one rule block to `docs/00_governance/governance_01_documentation-policy.md` in the ADR conventions area. No content is relocated and no document class is added.

## Assumptions
- Phase 2 of the Plan: starts only after the owner decides how retained ADR amendment history relates to the Current-Specification-Only Policy (UNK-01) and the approval requirement for a governance edit is checked (UNK-03).
- Run after the contract-correction procedures for ADR-001, ADR-002, ADR-008 and ADR-010 (sequencing dependency). Overlap with the adrauth001 procedure is coordination only: ADR-016 keeps the authority rules, so this rule references them without restating (compatible).
- Verified now: there are six document classes and no specification class; the policy states the current-only rule that the owner must reconcile with retained amendments.

## Design decisions
- State ADR responsibilities (decisions, rationale, alternatives, core invariants and their verification) relative to the existing classes and the Canonical Source Registry; do not restate ADR-015 or ADR-016 rules.
- The marking rule: every current-contract section is complete without its Amendment; an Amendment is in force (rationale only) or superseded (history only); its relation to the Current-Specification-Only Policy follows the owner decision.

## Alternatives considered
N/A: the Plan fixes the approach; relocation is deliberately not performed (UNK-02).

## Implementation
### Target file
`docs/00_governance/governance_01_documentation-policy.md`

### Procedure
1. Read the ADR conventions and the Current-Specification-Only Policy text.
2. Add the ADR responsibility statement, noting that no specification class exists.
3. Add the marking rule with the owner-decided relationship to the policy.
4. Add the relocation rule: move content out of an ADR only with a demonstrated maintenance benefit, exactly one authoritative destination owner, and essential safety or recovery guarantees staying in the ADR.

### Method
Documentation edit of one section; keep it short and rule-shaped.

### Details
- If the owner chooses removal of amendment history instead of an exception, stop and amend the Plan first (transfer-and-remove).
- Respect the size ceiling of the governance file in `check_docs_structure.py`.

## Compatibility considerations
Documentation only; the rule applies going forward and changes no ADR decision.

## Security considerations
N/A: documentation-only change

## Rollback considerations
N/A: revert the commit

## Validation plan
- `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py`, `check_docs_japanese.py`: no findings
- `uv run python tools/check_docs_consistency.py`: no findings

## Completion criteria
- The three rules are present and consistent with ADR-015 and ADR-016 (referenced, not restated).
- The relationship to the Current-Specification-Only Policy matches the owner decision.

## Out of Scope
- Relocating any ADR content; changing the canonical sources registry.
- ADR-015 and ADR-016 text.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit the document as described in Implementation > Procedure | Completed | 20261108-122020 | 20261108-122020 | Gated: owner decision on UNK-01 (policy versus retained amendments) and approval check UNK-03 - do not start the policy edit until both are resolved |
| 2 | Run the documentation checkers named in the Validation plan | Completed | 20261108-122020 | 20261108-122020 | owner decided: ADR Amendment is an explicit exception, marked in force or superseded; docs checkers pass; ADR-010 at 24561 bytes (ceiling 24576) |

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
- **Requirement ID**: `REQ-001`, `REQ-002`, `REQ-003` (ADR responsibilities, marking rule, relocation rule)
- **Source issue**: issues/20261107-050707_adrdoc001_separate-adr-current-history.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261108-093000_adrdoc001_separate-adr-current-history.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261108-111822
- **Related target files**: `docs/00_governance/governance_01_documentation-policy.md`
