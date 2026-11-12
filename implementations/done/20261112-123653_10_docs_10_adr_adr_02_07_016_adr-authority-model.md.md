## Goal
Name the generated index sections as the generator writes them and make the intentional-pair count agree with the regenerated list (`REQ-002`, `REQ-003`, `REQ-008` / `AC-2`, `AC-3`).

## Scope
**Release unit**: authority-model

## Assumptions
- The generator writes `## ADR Dependency Graph`, `### Authority Graph`, `### Intentional Circular References`; ADR-016 calls the first `Reference Graph` (about lines 64 and 140) (checked).
- ADR-016 says `six intentional circular pairs` (about lines 31 and 47) although the index lists five; after row 01 it lists six. Write the count from the regenerated list after rows 01 and 02.
- Baseline (Step 3a, 2026-11-12): `check_docs_structure.py` already reports ADR-004, ADR-008, and `deployment_01` over their ceilings (pre-existing, unrelated to this Plan).

## Design decisions
- Change names and the count only; leave the finding-code list of the Consequences as is unless it names the wrong section.

## Alternatives considered
N/A: the Plan fixes the approach for this row.

## Implementation
### Target file
`docs/10_adr/adr_02_07_016_adr-authority-model.md`

### Procedure
1. Replace `Reference Graph` with `ADR Dependency Graph` where it names the generated section (keep the guard id `adr-reference-graph`).
2. Set the pair count wording to the regenerated count.
3. Append a `Current Decision Approval (pending)` line.

### Method
- Section list: `ADR Dependency Graph (`adr-reference-graph`), Authority Graph (`adr-authority-graph`), Intentional Circular References (`adr-intentional-cycles`)`.
- Approval line: approver, date, scope 不明; tracked by adrrev012.

### Details
- Each decision-text edit gets a clearly marked `Current Decision Approval (pending)` line in the ADR's Approval Record (approver, date, and scope `不明`), tracked by the approval-ledger Plan (adrrev012); no approval or reviewer name is written (UNK-05).
- Execute after rows 01 and 02 so the count is final.

## Compatibility considerations
N/A: documentation-only change; no code, config, or schema impact.

## Security considerations
N/A: no authorization, secret, or trust-boundary change.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_adr_structure.py`, `check_adr_invariant_matrix.py`, `check_adr_reference.py`, `check_adr_authority.py`, `check_adr_preservation.py` (only intended, explained changes).
- `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py --strict`, `check_docs_japanese.py` — pass.

## Completion criteria
- ADR-016, the index, the guide, and the tools use the same section names; the pair count matches the generated list; a marked pending approval line exists.

## Out of Scope
- The acceptance sentence (adrrev012); changing checker semantics.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 2026-11-12 | 2026-11-12 | — |
| 2 | Run the documentation checkers per Validation plan | Completed | 2026-11-12 | 2026-11-12 | — |

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
- **Requirement ID**: `REQ-002` / `REQ-003` / `REQ-008` — generator section names and pair-count wording; pending approval
- **Source issue**: issues/20261109-113248_adrrev016_adr-authority-format.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261111-104605_adrrev016_adr-authority-format.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261112-123653
- **Related target files**: `docs/10_adr/adr_02_07_016_adr-authority-model.md`
