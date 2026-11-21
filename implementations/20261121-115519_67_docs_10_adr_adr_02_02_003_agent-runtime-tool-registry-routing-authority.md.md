## Goal

Record the decision and invariant change that moves authority from configuration maps and static sets to declared metadata, with the maintainer approval record (REQ-012; AC-11).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The approval record must be written in the same change as the code; this document records the requirement and cannot supply the approval, so Phase 1 stops if the approval is not given (UNK-03, UNK-04).

## Design decisions
- Decisions 2, 5, 8, 9 and 14 are the statements this change touches; each is edited only where the authority source changes, and no other decision is restated.

## Alternatives considered
- N/A: the plan's design section fixes the shape of this change.

## Implementation
### Target file
`docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md`
### Procedure
- Update Decision 2 (the fields `RuntimeTool` holds), Decision 5 (static definitions limited to tests, expected values and documentation generation), Decision 8 (the declared tier and write attributes as the shared reference), Decision 9 (`apply_policy()` no longer applies a configuration-derived tier) and Decision 14 (reload does not update a tier that is declared rather than policy-derived).
### Method
- Add the `RETRYABLE_TOOLS` ownership statement that `scripts/agent/tool_runner.py` credits to ADR-008, and name the declared `retry_policy` as the owner.
- Add the maintainer approval record line for the decision/invariant change, as `docs/10_adr/adr_02_07_016_adr-authority-model.md` requires.
- Keep the invariant matrix entries consistent with the changed decisions.
### Details
- Verified 2026-11-21: Decision 5 already limits static definitions to tests and documentation, so the change is the wording that makes drift comparison the only use; Decision 14 currently states that reload updates policy-derived fields including Safety Tier, which is what the approval changes.

## Compatibility considerations
- N/A: no public contract is changed by this file alone.

## Security considerations
- N/A: no trust boundary is crossed by this file.

## Rollback considerations
- N/A: revert the commit within the release unit.

## Validation plan
- `uv run python tools/check_adr_reference.py`
- `uv run python tools/check_adr_invariant_matrix.py`

## Completion criteria
- The ADR names declared metadata as the authority for the concepts this plan moves, and the approval record is present in the same change.
- `uv run python tools/check_adr_reference.py` and `uv run python tools/check_adr_invariant_matrix.py` pass.

## Out of Scope
- The ADR-004 startup-abort consequence, which this change must not restate.
- The field-set version value (UNK-01), which is decided with the MCP contract owner.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|---|---|---|---|---|---|
| 1 | Write the decision/invariant change and the approval record | Pending | — | — | The decision and approval record are not available in this cycle (UNK-03, UNK-04); see Blocker Log |
| 2 | Run the ADR checkers | Pending | — | — | Gated: issues/20261120-115845_mcpdl006_two-layer-failure-verification.md phase all - the reconciliation field values and the replay boundary are defined by that issue |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|---|---|---|---|
| 1 | ADR decision/invariant change requires a maintainer approval record (UNK-03, UNK-04) | No | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---|---|---|---|---|---|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-012
- **Source issue**: issues/20261120-114211_agentcfg003_runtime-tool-metadata.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261121-105007_agentcfg003_runtime-tool-metadata.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261121-115519
- **Related target files**: `docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md`
