## Goal
Remove `EBAUTHGEN001` and the `deliberate breaking change ... (owner decision 2026-10-30)` wording from ADR-013 Decision Detail 12, keeping the 409 and 422 rules (`REQ-001` / `AC-1`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Line numbers have drifted from the Plan (other Plans edited these files); locate each passage by its quoted text.
- The rule text stays: every request carries `expected_generation`; a mismatch is HTTP 409 `generation_conflict`; a missing or non-integer value is HTTP 422; an accepted update publishes `generation + 1` with the additive response fields.
- Overlap: adrrev016 adds an Implementation column to the Automated Tests table; `rmcompat004` and adrrev010 edit other regions (compatible).
- This edit shortens the file; the size ceiling (28647) is not at risk from it.

## Design decisions
- Rewrite as: `Optimistic concurrency: every request MUST carry `expected_generation` ... A missing or non-integer `expected_generation` is rejected with HTTP 422, so callers that omit the field are rejected. ...`

## Alternatives considered
N/A: the Plan fixes the approach for this row.

## Implementation
### Target file
`docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`

### Procedure
1. Remove `(EBAUTHGEN001)` from the Optimistic concurrency sentence.
2. Replace `this is a deliberate breaking change for callers that omit the field (owner decision 2026-10-30)` with a present-tense statement.

### Method
- `rg -n 'EBAUTHGEN001|owner decision|breaking change' docs/10_adr/adr_02_04_013_*.md` before and after.

### Details
- Removing history is a wording edit, not a decision change (`governance_05`), so no approval record is added; any decision hidden in the passage is first confirmed present in the current sections (UNK-03).

## Compatibility considerations
N/A: documentation-only change; no code, config, or schema impact.

## Security considerations
N/A: no authorization, secret, or trust-boundary change.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_adr_structure.py`, `check_adr_invariant_matrix.py`, `check_adr_authority.py`, `check_adr_preservation.py`, `generate_adr_authority.py --check` — pass; preservation reports only the removed Amendment text.
- `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py --strict`, `check_docs_japanese.py` — pass.
- `uv run python tools/check_known_deviation_sync.py`, `check_needs_confirmation_inventory.py` — pass (UNK-05).

## Completion criteria
- No plan ID or decision date remains in Decision Detail 12; the 409 and 422 rules are unchanged.

## Out of Scope
- The Automated Tests table (adrrev016); the Approval and Known Deviations sections.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261112-175741 | 20261112-175741 | docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md |
| 2 | Run the documentation checkers per Validation plan | Completed | 20261112-175741 | 20261112-175741 | checkers pass; preservation WARNING is the intended wording change |

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
- **Requirement ID**: `REQ-001` — remove the plan ID and the dated owner-decision note
- **Source issue**: issues/20261109-113318_adrrev017_docs-history-wording.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261111-110144_adrrev017_docs-history-wording.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261112-123928
- **Related target files**: `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`
