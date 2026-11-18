## Goal

Pin the rule-over-tier precedence and the tier-`NONE` escalation gap measured under the shipped config
(REQ-003).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Existing pinned cases to extend: `tests/agent/test_tool_approval_risk.py:97-110` (rule- and
  tier-derived levels), `:196-210` (`test_custom_risk_rules_override_default`,
  `test_empty_risk_rules_falls_back_to_tier`).
- The issue's inverted claim (tier `NONE` prevents rules) is what the new assertions must make
  impossible to re-introduce.

## Design decisions
- Add one assertion pair: a `medium`-ruled tool with a `WRITE_DANGEROUS` tier resolves to `medium`
  (rule wins), and a tier-`NONE` rule-less tool with a protected path stays `none` (short-circuit).
- Do not modify the existing `:196-210` cases; they already characterize rule-over-tier for custom
  configs.

## Alternatives considered
N/A: assertion placement follows AC-003.

## Implementation
### Target file
`tests/agent/test_tool_approval_risk.py`
### Procedure
1. Add a shipped-config test asserting rule-over-tier precedence for one ruled tool
   (`github_create_branch` or `github_create_issue`, both `medium`).
2. Add a tier-`NONE` gap test for `git_add`/`git_commit` with a protected path argument.
### Method
Append cases to the existing risk classes, using the shipped `config/agent.toml` posture via the
shared fixture constants.
### Details
N/A: nothing beyond the two assertions is not inferable from REQ-003.

## Compatibility considerations
Test-only; must pass against unmodified production code (Phase 1 gate).

## Security considerations
N/A: test-only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/agent/test_tool_approval_risk.py -q`

## Completion criteria
Both assertions pass against unmodified code and name the branch that produced the level (AC-003).

## Out of Scope
In-jail escalation pinning (row 14), the comprehensive-suite short-circuit pinning (row 12).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the precedence and gap assertions per Procedure | Completed | 20261119-075430 | 20261119-075430 | Two cases added to `TestClassifyRisk`: shipped `github_create_branch`/`github_create_issue` (medium rule over WRITE_SAFE tier) and `git_add`/`git_commit` protected-path NONE gap; configs built from `SHIPPED_APPROVAL_PROTECTED_PATHS` + the existing `ALL_*` fixture mirrors; existing `:196-210` cases untouched |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261119-075430 | 20261119-075430 | ruff format/check pass; 40 tests pass (35 pre-existing + 5 new params) |

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
- **Requirement ID**: `REQ-003` (characterization tests)
- **Source issue**: `issues/20261117-123003_adrchk003_agent-approval-policy.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261118-224457_adrchk003_agent-approval-policy.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-233456
- **Related target files**: `tests/agent/test_tool_approval_risk.py`
