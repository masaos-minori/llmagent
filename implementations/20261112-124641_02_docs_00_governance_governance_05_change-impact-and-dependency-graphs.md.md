## Goal
Correct the cross-reference `18. Area Dependency Graph Validation` to section 19 (`REQ-001` / `AC-1`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Line numbers have drifted from the Plan; locate each passage by its quoted text, and skip and report it if it is already correct (Phase 1 rule).
- `governance_04` numbers the section `### 19. Area Dependency Graph Validation` (checked).
- Overlap: adrrev016 row 11 edits the Agent ↔ RAG statement of this file (another passage); compatible.

## Design decisions
- Change the number only.

## Alternatives considered
N/A: the Plan fixes the approach for this row.

## Implementation
### Target file
`docs/00_governance/governance_05_change-impact-and-dependency-graphs.md`

### Procedure
1. Replace `"18. Area Dependency Graph Validation"` with `"19. Area Dependency Graph Validation"`.

### Method
- `rg -n 'Area Dependency Graph Validation' docs/00_governance/` confirms one match with `19.` in `governance_05`.

### Details
- Keep the quoted section name unchanged.

## Compatibility considerations
N/A: documentation-only change; no code, config, or schema impact.

## Security considerations
N/A: no authorization, secret, or trust-boundary change.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_consistency.py --domain overview` — pass.
- `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py --strict`, `check_docs_japanese.py` — pass.
- `uv run python tools/check_needs_confirmation_inventory.py` — pass.

## Completion criteria
- The cross-reference cites section 19.

## Out of Scope
- Other governance statements.

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
- **Requirement ID**: `REQ-001` — correct the section cross-reference
- **Source issue**: issues/20261109-113421_adrrev019_docs-stale-statements.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261111-112439_adrrev019_docs-stale-statements.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261112-124641
- **Related target files**: `docs/00_governance/governance_05_change-impact-and-dependency-graphs.md`
