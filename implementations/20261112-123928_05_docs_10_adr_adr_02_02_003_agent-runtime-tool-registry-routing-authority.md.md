## Goal
Remove `regardless of Profile` from the context bullet and Decision Detail 7 of ADR-003 (`REQ-001` / `AC-1`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Line numbers have drifted from the Plan (other Plans edited these files); locate each passage by its quoted text.
- ADR-004 applies one failure-handling policy to every environment and mentions Profile only in a rejected alternative (checked); the `Target Environment Profile` line stays because it is a metadata field.
- The edit leaves the sentence's meaning intact: duplicate Tool names make routing unclear, and startup fails.

## Design decisions
- Drop the trailing clause only.

## Alternatives considered
N/A: the Plan fixes the approach for this row.

## Implementation
### Target file
`docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md`

### Procedure
1. Context bullet: `... it becomes unclear which one to route to` (remove `, regardless of Profile`).
2. Decision Detail 7: `... startup fails.` (remove `regardless of Profile`).

### Method
- `rg -n 'regardless of Profile' docs/10_adr/adr_02_02_003_*.md` returns no match afterwards.

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
- No `regardless of Profile` wording remains; no decision or invariant changes.

## Out of Scope
- The `Target Environment Profile` line; ADR-004.

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
- **Requirement ID**: `REQ-001` — remove `regardless of Profile` leftovers
- **Source issue**: issues/20261109-113318_adrrev017_docs-history-wording.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261111-110144_adrrev017_docs-history-wording.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261112-123928
- **Related target files**: `docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md`
