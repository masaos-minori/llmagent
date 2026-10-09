## Goal

Implement **REQ-003**: update `docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md` so it records that the `require_approval` policy is now enforced at workflow load time, and drop the "no code enforces it" limitation. Complements seq 02 (loader enforcement).

## Scope

Modify `docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md` only. Reference read only: `scripts/agent/workflow/workflow_loader.py` (seq 02, the enforcement being documented).

## Assumptions

- English-only doc content (per `skills/DESIGN.md` Output language); edits stay in English.
- The operation-category table (lines 52-60) and its "Required" categories are accurate and stay as-is.

## Design decisions

- Keep the policy statement that workflows reaching a "Required" category MUST set `require_approval: true`; only correct the claim that nothing enforces it.
- Remove the Known Limitations bullet that tracks the gap as AGENT-001.

## Alternatives considered

- Rewriting the whole Approval Gates section: rejected — narrow, localized edits suffice and keep the diff reviewable.

## Implementation
### Target file
`docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md`

### Procedure
Two edits: (1) correct the Operations Policy note; (2) remove the AGENT-001 Known Limitation.

### Method
1. **Operations Policy note (line 50).** Replace the clause beginning "This is an operational policy only:" through the end of the sentence "...does not fire with it." State instead that enforcement now exists. Suggested replacement for that clause:
   > This is enforced at startup: `WorkflowLoader._validate()` rejects any workflow definition whose `require_approval` is absent or `false` (`WorkflowLoadError`), so a misconfiguration fails startup rather than silently running without the workflow-level gate. The bundled `config/workflows/default.json` sets `require_approval: true` and therefore satisfies this policy for the "Required" categories.
   Keep the preceding sentence ("...MUST explicitly set `require_approval: true` in its `config/workflows/*.json`.") unchanged.
2. **Known Limitations (line 157).** Remove the bullet:
   > - The workflow-level approval gate is disabled in the bundled workflow definition, and no code enforces the operations policy above; enabling it requires an explicit workflow definition change. This gap is tracked as AGENT-001 in `governance_03_issue-and-uncertainty-management.md`.

### Details
- Verify exact current wording with a fresh read before editing (line numbers may have shifted).
- Do not alter the tool-level gate note (line 62) or the approval lifecycle (lines 64-70); those are unaffected.

## Compatibility considerations

- Doc-only change; no code impact. Ensure no other doc cross-references this removed limitation as still-open.

## Security considerations

- Documenting enforcement accurately prevents reviewers from assuming the gate is nominal (the original defect behind AGENT-001).

## Rollback considerations

- Restore the two edited regions from git.

## Validation plan
| Target | Strategy | Command | Expected |
|---|---|---|---|
| `agent_03_03` | Doc review | manual / `check_docs_*` | Enforcement noted; AGENT-001 limitation removed |

## Completion criteria

- Line 50 no longer states that neither loader nor validator enforces `require_approval`.
- The Known Limitations section no longer lists the AGENT-001 workflow-gate gap.

## Out of scope
- Loader logic (seq 02). Ledger removal in governance_03 (seq 04).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20261009-122445 |  |
| 2 | Add or update tests per Validation plan | Completed | — | 20261009-122445 | N/A: doc-only |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261009-122445 | doc quality checks |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20261009-122445 |  |

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
- **Requirement ID**: REQ-003
- **Source issue**: `issues/done/20261007-154046_approval01_enforce-approval-policy-in-configuration-validation.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261008-161457_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261009-120153
- **Related target files**: `docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md`