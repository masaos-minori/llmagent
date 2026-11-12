## Goal
Add the ADRs that ADR-014's body links to (ADR-003 required by the model; ADR-002 and ADR-004 per UNK-02) to its front matter `related` and Related ADRs (`REQ-002`, `REQ-008` / `AC-2`).

## Scope
**Release unit**: authority-model

## Assumptions
- Related ADRs lists ADR-001 only; the body cites ADR-003 (Agent-side posture row) and says the Security Posture change is `linked with ADR-002, ADR-003, ADR-004` (checked); UNK-02 is resolved to add all three.
- The matching model edges come from row 01; execute with it.
- Overlap: adrrev015 edits INV-02 and the Decision paragraph, not front matter.

## Design decisions
- Front matter and Related ADRs only; no invariant or decision text changes.

## Alternatives considered
N/A: the Plan fixes the approach for this row.

## Implementation
### Target file
`docs/10_adr/adr_02_02_014_agent-control-plane-responsibility-boundaries.md`

### Procedure
1. Add `adr_02_01_002_platform-config-isolation.md`, `adr_02_02_003_agent-runtime-tool-registry-routing-authority.md`, and `adr_02_01_004_platform-environment-failure-handling-policy.md` to the front matter `related`.
2. Add the three ADR lines to Related ADRs.
3. Because no decision text changes, report that no approval line is added.

### Method
- Related ADRs lines: `- ADR-002: Per-Process Configuration Ownership and Config Isolation`, `- ADR-003: Runtime Tool Registry and Routing Authority` (use the ADR-003 heading's actual title), `- ADR-004: Failure Handling Policy Across Environments`.

### Details
- A front-matter entry without its edge fails `FRONTMATTER_DIVERGENCE`; run `check_adr_reference.py` after row 01.

## Compatibility considerations
N/A: documentation-only change; no code, config, or schema impact.

## Security considerations
N/A: no authorization, secret, or trust-boundary change.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_adr_reference.py`, `check_adr_authority.py`, `check_adr_structure.py`, `check_adr_preservation.py` — pass; docs checkers pass.

## Completion criteria
- Front matter and Related ADRs list ADR-002, ADR-003, and ADR-004; the front-matter check passes.

## Out of Scope
- INV-02 and Decision wording (adrrev015).

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
- **Requirement ID**: `REQ-002` / `REQ-008` — ADR-003, ADR-002, ADR-004 in front matter and Related ADRs
- **Source issue**: issues/20261109-113248_adrrev016_adr-authority-format.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261111-104605_adrrev016_adr-authority-format.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261112-123653
- **Related target files**: `docs/10_adr/adr_02_02_014_agent-control-plane-responsibility-boundaries.md`
