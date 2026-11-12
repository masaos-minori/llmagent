## Goal
Replace the `Canonical Source` label for code (`agent/diagnostic_store.py`, `db/maintenance.py`) in `agent_09_01` with wording GV-012 allows (`REQ-002`, `REQ-007` / `AC-2`, `AC-7`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Line numbers have drifted from the Plan; locate each passage by its quoted text, and skip and report it if it is already correct (Phase 1 rule).
- GV-012 says code is not canonical for adopted design decisions; the Responsibility Boundary bullet `**Canonical Source**: agent/diagnostic_store.py, db/maintenance.py` labels code as canonical (checked). Sibling documents (`agent_08_02`, `agent_08_03`, `agent_06_04`, `agent_09_02`) use the same label for other sources; they are outside this Plan and are reported, not edited.
- The plaintext-diagnostics decision (lines near 70-76) stays pending (UNK-01) and is reported, not edited.

## Design decisions
- Relabel the bullet `**Implementation**` and leave the paths.

## Alternatives considered
N/A: the Plan fixes the approach for this row.

## Implementation
### Target file
`docs/23_agent/agent_09_01_data-layer-session-db.md`

### Procedure
1. Replace `**Canonical Source**` in the Responsibility Boundary section with `**Implementation**`.

### Method
- Keep the `**Schema**` bullet unchanged.

### Details
- Report the sibling documents with the same label and the open UNK-01 decision in the final report.

## Compatibility considerations
N/A: documentation-only change; no code, config, or schema impact.

## Security considerations
N/A: no authorization, secret, or trust-boundary change.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py --strict`, `check_docs_japanese.py` — pass.
- `uv run python tools/check_needs_confirmation_inventory.py` — pass.

## Completion criteria
- The bullet no longer calls code a canonical source; the content-policy check passes.

## Out of Scope
- Sibling documents; the plaintext-diagnostics decision.

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
- **Requirement ID**: `REQ-002` / `REQ-007` — stop calling code the canonical source
- **Source issue**: issues/20261109-113421_adrrev019_docs-stale-statements.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261111-112439_adrrev019_docs-stale-statements.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261112-124641
- **Related target files**: `docs/23_agent/agent_09_01_data-layer-session-db.md`
