## Goal
Update `governance_01` ADR Responsibilities and Historical Content so an ADR holds no Amendment section and the Amendment-as-exception sentence is removed (`REQ-003` / `AC-3`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Line numbers have drifted from the Plan (other Plans edited these files); locate each passage by its quoted text.
- Execute in the same pass as the ADR Amendment removals (rows 02 to 04) so the policy never permits what the ADRs no longer contain.
- The paragraph to change begins `Every current-contract section of an ADR ... must be complete without its Amendment` and ends with the sentence `An ADR Amendment is the one exception ... superseded (a historical record only).`

## Design decisions
- Keep the completeness rule (current-contract sections are complete on their own) and delete the exception sentence.

## Alternatives considered
N/A: the Plan fixes the approach for this row.

## Implementation
### Target file
`docs/00_governance/governance_01_documentation-policy.md`

### Procedure
1. Rewrite the paragraph so it states that an ADR carries no Amendment section and that current-contract sections are complete on their own.
2. Search `governance_01` for other `Amendment` mentions and classify each.

### Method
- New text: `Every current-contract section of an ADR (Decision, Invariants, Failure Policy, Verification) must be complete on its own; an ADR holds no Amendment section, and history stays in version control.`

### Details
- Do not change the Current-Specification-Only Policy section itself.

## Compatibility considerations
N/A: documentation-only change; no code, config, or schema impact.

## Security considerations
N/A: no authorization, secret, or trust-boundary change.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py --strict`, `check_docs_japanese.py` — pass.
- `uv run python tools/check_known_deviation_sync.py`, `check_needs_confirmation_inventory.py` — pass (UNK-05).

## Completion criteria
- No sentence of `governance_01` permits an ADR Amendment; the checkers pass.

## Out of Scope
- Approval Evidence Standard text; other policy sections.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261112-175456 | 20261112-175456 | docs/00_governance/governance_01_documentation-policy.md |
| 2 | Run the documentation checkers per Validation plan | Completed | 20261112-175456 | 20261112-175456 | all docs checkers pass; adr_00_document-guide.md:19 now stale (out of scope, reported) |

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
- **Requirement ID**: `REQ-003` — an ADR holds no Amendment section
- **Source issue**: issues/20261109-113318_adrrev017_docs-history-wording.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261111-110144_adrrev017_docs-history-wording.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261112-123928
- **Related target files**: `docs/00_governance/governance_01_documentation-policy.md`
