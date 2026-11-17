## Goal

Align `docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md` with the strict workflow-definition contract so current sections state the required fields, historical omitted-`retry_on` compatibility wording is removed, and the failure-at-boundary behavior is documented (`REQ-006`). Documentation-only; no code change.

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The correct file path is `docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md` (underscore separators). The Plan originally wrote the path with hyphens; verified against the filesystem before authoring.
- REQ-003/REQ-004 (model) and REQ-001/REQ-002 (loader) make the fields required; this doc describes that end state. Schema-level `NOT NULL` / constructor-required statements for the attempt lease belong to the frozen compat002 Plan, not this one.
- `DESIGN.md` "Docs content policy — remove" governs deleting the omitted-`retry_on` legacy wording.

## Design decisions
- State the contract positively (fields are required, allowed kinds, owner of empty-stage validation, empty-`retry_on` semantics) rather than enumerating every old-code difference, keeping the section current-only.

## Alternatives considered
- Leaving the omitted-`retry_on` legacy wording: rejected; it presents a now-invalid shape as supported and drifts from the enforced contract.

## Implementation
### Target file
`docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md`
### Procedure
1. Mark `stages`, `retry_policy`, and `retry_policy.retry_on` as required in the workflow-definition schema description.
2. State the allowed `retry_on` kinds (`exception`, `timeout`, `llm_failure`) and the empty-`retry_on` semantics (`[]` = "retry nothing"; absent key is rejected).
3. State who validates empty stages (the model owns the invariant; the loader rejects a non-empty-list requirement at the config path).
4. Remove any wording that presents an omitted `retry_on` (or omitted `stages`/`retry_policy`) as a supported legacy format.
### Method
Targeted prose edits in the workflow-definition / retry-policy sections; delete the legacy-compatibility sentences, add the required-field and semantics statements.
### Details
- Locate the retry-policy / workflow-definition schema prose (search `retry_on`, `retry_policy`, `stages`) and rewrite the field tables/bullets to mark all three required.
- Delete the omitted-`retry_on` legacy sentence(s) describing pre-wfretry001 definitions loading with a default.
- Do not introduce schema-level `NOT NULL` or constructor-required language that belongs to compat002; keep this doc at the loader/config-contract level.

## Compatibility considerations
N/A: documentation-only wording change; no behavioral contract introduced here beyond describing REQ-001/REQ-003.

## Security considerations
N/A.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_quality.py`
- `uv run python tools/check_docs_consistency.py --domain agent`
- `uv run python tools/check_compat_shims.py`
- All pass with no new errors; no remaining omitted-`retry_on` legacy wording.

## Completion criteria
- The workflow-engine doc states `stages`, `retry_policy`, `retry_policy.retry_on` are required, lists the allowed kinds and empty-`retry_on` semantics, and no longer describes omitted fields as supported.

## Out of Scope
Code/schema/test changes; schema-level `NOT NULL` statements (compat002); other domain docs.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261117-093402 | 20261117-093402 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) — documentation checkers named above | Completed | 20261117-093402 | 20261117-093402 |  |

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
- **Requirement ID**: `REQ-006` (document the strict workflow-definition contract in the workflow-engine doc)
- **Source issue**: `issues/20261116-114753_compat001_workflow-definition-strict-contract.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261116-214100_compat001_workflow-definition-strict-contract.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261117-005004
- **Related target files**: `docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md`