## Goal

Add mode context to the `allowed_tools` whitelist rule so the empty-list denial is qualified by `tool_policy_mode` (`REQ-003`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Line 33 states: "If the tool is not in the list (an empty list denies every tool) → Reject" as an absolute.

## Design decisions
- Qualify the empty-list denial at line 33: an empty list denies every tool only under `explicit_allowlist`; under `discovered` an empty list is valid and base visibility applies.

## Alternatives considered
- Removing the empty-list clause: rejected because it is still correct under `explicit_allowlist`.

## Implementation
### Target file
`docs/23_agent/agent_06_02_tool-execution-and-approval-approval.md`

### Procedure
Edit the `allowed_tools` whitelist rule at line 33 to add mode context.

### Method
Append a mode qualifier to the empty-list parenthetical.

### Details
- Line 33: "(an empty list denies every tool under `explicit_allowlist`; valid under `discovered`)".

## Compatibility considerations
Documentation accuracy only; no behavior change.

## Security considerations
No security impact: wording matches the enforced behavior.

## Rollback considerations
N/A: revert the commit.

## Validation plan
Run the doc checker named in `routing.md` after editing.

## Completion criteria
The whitelist rule states the empty-list denial is mode-dependent; the doc checker passes.

## Out of Scope
Runtime enforcement (`runtime_tool_registry.py`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261120-192100 | 20261120-192100 | Edited `docs/23_agent/agent_06_02_tool-execution-and-approval-approval.md` line 33 whitelist rule: qualified the empty-list parenthetical to "(an empty list denies every tool under `explicit_allowlist`; valid under `discovered`)". Matches enforced behavior (empty list denies only under explicit_allowlist; base visibility applies under discovered). |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261120-192100 | 20261120-192100 | Doc accuracy only; no behavior change. check_docs_quality/structure/content_policy(--strict) all pass; check_docs_consistency --domain agent reports only a pre-existing unrelated warning in agent_14 (not the edited file). |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-003`
- **Source issue**: `issues/20261120-114209_agentcfg001_tool-policy-mode.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261120-123941_agentcfg001_tool-policy-mode.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261120-132256
- **Related target files**: `docs/23_agent/agent_06_02_tool-execution-and-approval-approval.md`
