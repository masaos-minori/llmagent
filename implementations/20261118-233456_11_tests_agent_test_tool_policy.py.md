## Goal

Add branch-provenance and tier-`NONE` gap characterization tests to the policy test suite, pinning
which branch produced each risk level (REQ-003) and the measured reachability findings (REQ-001).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Phase 1 baseline: every new test must pass against unmodified approval code (Plan Phase 1 step).
- Existing pinned cases to build on: `tests/agent/test_tool_policy.py:185-192` (tier-derived levels),
  `:601-603` (fallback), `:374-534` (`_escalate_for_path` coverage).

## Design decisions
- Provenance is asserted by stubbing the branch entry points (`_special_case_risk()`,
  `_escalate_for_path()`) or by asserting the level a known rule/tier produces, not by adding logging
  to `scripts/agent/tool_policy.py` (Plan row 01).
- One test per provenance claim, named `test_*_provenance_*` so a later delta is attributable.

## Alternatives considered
Asserting only the final level (status quo) — rejected; AC-003 requires each test to assert which
branch produced the level.

## Implementation
### Target file
`tests/agent/test_tool_policy.py`
### Procedure
1. Add rule-over-tier provenance tests: a tool with both an `approval_risk_rules` entry and a
   `tool_safety_tiers` entry resolves to the rule value.
2. Add tier-`NONE` gap tests: `git_add`, `git_commit`, `index_paths`, `refresh_index` and a
   `READ_ONLY` tool return `NONE` even when called with a protected path argument
   (measured: `git_add`/`git_commit` → `none`).
3. Add plan-mode provenance: `is_plan_mode_blocked()` consults the tier, and `plan_blocked_tools`
   extends it (DT-03 Option A posture).
### Method
New test functions in the existing class structure; no change to existing assertions.
### Details
- Build configs with the shared fixture constants from `tests/agent/_config_test_defaults.py`
  (Plan row 20) so the shipped posture is what is pinned.
- Fail-closed assertions already exist for unknown tools and empty allowlists elsewhere; do not
  duplicate them here.

## Compatibility considerations
Characterization only: no production code touched, no existing assertion changed.

## Security considerations
N/A: test-only, no runtime change.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/agent/test_tool_policy.py -q` against unmodified `scripts/agent/tool_policy.py`.
- `uv run pytest tests/agent/test_tool_policy.py tests/agent/test_tool_policy_comprehensive.py tests/agent/test_tool_approval_risk.py -q`
  after Plan row 01's docstring edits.

## Completion criteria
New tests pass against unmodified code, and each names the branch (rule, tier, constant, or
escalation) that produced the asserted level (AC-003).

## Out of Scope
Changes to `scripts/agent/tool_policy.py` (row 01), tier-`NONE` pinning in the comprehensive suite
(row 12), in-jail escalation pinning (row 14).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the provenance and tier-`NONE` tests per Procedure | Pending | — | — | Phase 1, must pass against unmodified code |
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
- **Related target files**: `tests/agent/test_tool_policy.py`
