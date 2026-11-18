## Goal

Pin the tier-`NONE` short-circuit for ruled-but-tiered tools and the `sideeffect001` static-membership
contract this Plan depends on (REQ-001, REQ-003).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Existing coverage to extend: `tests/agent/test_tool_policy_comprehensive.py:230-275`.
- The Plan's tier/rule reachability claims (19 ruled tools, all tiered) are derived from the shipped
  `config/agent.toml`; the `sideeffect001` static-membership test is the contract the reachability
  report reads.

## Design decisions
- Assert the short-circuit as a property over the config-derived tool list (fixture constants from
  `tests/agent/_config_test_defaults.py`), so a future config change surfaces as a test failure
  rather than a silent policy drift.

## Alternatives considered
Hard-coding a tool-name list in the test body — rejected; it drifts from `config/agent.toml`.

## Implementation
### Target file
`tests/agent/test_tool_policy_comprehensive.py`
### Procedure
1. Add a test asserting that for every tool with an `approval_risk_rules` entry the resolved level
   equals the rule value, not the tier value.
2. Add a test asserting the `NONE` short-circuit for tier-`NONE` tools with no rule: no
   special-case and no path escalation is reached.
3. Keep the `sideeffect001` static-membership assertion passing unchanged.
### Method
Config-driven parametrized tests appended to the existing classes.
### Details
N/A: nothing beyond the two assertions is not inferable from REQ-001/REQ-003.

## Compatibility considerations
Test-only; must pass against unmodified production code (Phase 1 gate).

## Security considerations
N/A: test-only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/agent/test_tool_policy_comprehensive.py -q`

## Completion criteria
Both new assertions pass against unmodified code and identify the branch that produced the level
(AC-003).

## Out of Scope
Provenance tests in `tests/agent/test_tool_policy.py` (row 11), `scripts/agent/tool_policy.py` (row 01).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the config-driven short-circuit tests per Procedure | Pending | — | — | Phase 1 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-001` (reachability), `REQ-003` (characterization tests)
- **Source issue**: `issues/20261117-123003_adrchk003_agent-approval-policy.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261118-224457_adrchk003_agent-approval-policy.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-233456
- **Related target files**: `tests/agent/test_tool_policy_comprehensive.py`
