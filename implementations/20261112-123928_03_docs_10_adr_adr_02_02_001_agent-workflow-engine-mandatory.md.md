## Goal
Remove ADR-001's `Amendment (wflease001, 2026-11-01)` section (`REQ-001` / `AC-1`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Line numbers have drifted from the Plan (other Plans edited these files); locate each passage by its quoted text.
- UNK-03 checked in Step 3a: Decision Details item 11 already states the lease-expiry rule (`owner_id`, `lease_expires_at`, `recover_stale_attempts()` recovers only lease-expired rows); the Amendment only records its rationale, so no rule is lost.
- The rationale sentence (a wall-clock rule compared host-local timestamps and could steal a live owner's attempt) is history; it is dropped, not moved.
- Overlap: adrrev015 edits the INV-02 table row of this ADR; different region.

## Design decisions
- Delete the section whole; keep Decision Details item 11 unchanged.

## Alternatives considered
N/A: the Plan fixes the approach for this row.

## Implementation
### Target file
`docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md`

### Procedure
1. Confirm item 11 states the rule.
2. Delete the `### Amendment (wflease001, ...)` section.
3. Confirm `wflease001` appears nowhere else in the ADR.

### Method
- `rg -n 'wflease001|Amendment' docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md` before and after.

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
- No Amendment section or plan ID remains; item 11 and all invariants are unchanged.

## Out of Scope
- The INV-02 row (adrrev015); approval records.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Run the documentation checkers per Validation plan | Pending | — | — | |

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
- **Requirement ID**: `REQ-001` — remove the `wflease001` Amendment
- **Source issue**: issues/20261109-113318_adrrev017_docs-history-wording.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261111-110144_adrrev017_docs-history-wording.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261112-123928
- **Related target files**: `docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md`
