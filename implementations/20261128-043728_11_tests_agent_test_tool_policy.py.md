## Goal

Remove the two MDQ write tools from the shipped tier-`NONE` provenance set and add the medium-base
and force-escalation cases, so the policy tests describe the tier the tools now declare.

## Scope
**Release unit**: tier change and its pins

- `TestTierNoneGapProvenance` in `tests/agent/test_tool_policy.py`: the shipped tier-`NONE` tool list
  (line 2141) and the new per-mode cases.

## Assumptions

- `PRODUCER_TIERS` is derived from the producer declarations (`tests/agent/_producer_registry.py`,
  75-77), so the new cases read the tier that row 1 declares rather than a hand-set tier.
- `test_tier_none_short_circuits_escalation` (`TestClassifyRiskBranchProvenance`, method at line 2122,
  class at line 2081) pins the lookup order with a `READ_ONLY` tool and is unchanged: the plan does
  not reorder the short-circuit (UNK-02).

## Design decisions

- The provenance set keeps only tools that remain tier-`NONE` (`git_add`, `git_commit`), so the set
  stays a statement about the shipped declarations instead of a list that has to be edited whenever
  a producer changes a tier.
- The new cases assert the resolved risk, not the tier value, so they test the consequence of the
  declaration through `classify_risk()`.

## Alternatives considered

- Keeping the mdq tools in the set with a per-tool exception: rejected, the set's purpose is to prove
  that a `NONE` base returns before escalation, which no longer holds for these tools.

## Implementation
### Target file
`tests/agent/test_tool_policy.py`

### Procedure
1. In `TestTierNoneGapProvenance.SHIPPED_NONE_TIER_TOOLS` (line 2141), remove `index_paths` and
   `refresh_index`.
2. Add a case that resolves each tool to `medium` with no path argument and no `force`.
3. Add the force case for `refresh_index` (`force=True` resolves to `high`) and the protected
   in-jail path case for both tools (`high`).

### Method

- Use the existing `_tier_reg()` helper (line 2145) so the registry entry carries the declared tier
  and the `path` scope key, which is what the escalation branch reads.
- The force case passes `{"paths": [...], "force": True}` through `classify_risk()`; the `force`
  special case in `scripts/agent/tool_policy.py` `_special_case_risk()` (383-427) is reached because
  the base is no longer `NONE`.

### Details

- The in-jail protected path uses `approval_protected_paths=["/opt/llm/"]` with a path inside the
  jail, matching the existing provenance cases.

## Compatibility considerations

- `tests/agent/test_tool_policy_comprehensive.py` (300-314) asserts side-effect membership and
  operation type for these tools, which the tier change does not affect.
- `tests/agent/test_tool_approval_preflight.py` `test_plan_mode_blocks_every_non_read_only_tool`
  (line 990 in `tests/agent/test_tool_approval_preflight.py`) names `index_paths` in its
  parametrize list (line 987) and covers `refresh_index`
  through the tier mapping; both remain blocked after the change.

## Security considerations

- N/A: test-only change.

## Rollback considerations

- Revert the commit.

## Validation plan

- `uv run pytest tests/agent/test_tool_policy.py tests/agent/test_tool_approval_risk.py`
- Full sequence per `rules/toolchain.md`.

## Completion criteria

- The provenance set no longer names the mdq writes, and the new cases pass (AC-1, AC-5).

## Out of Scope

- The tier declaration: row 1.
- The per-mode approval-risk suite: row 12.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | This row is the test change |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | Docs rows 14 and 17 state the tier consequence |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-007
- **Source issue**: `issues/20261119-142129_mdqmcp007_mdq-approval-dry-run.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261127-173835_mdqmcp007_mdq-approval-dry-run.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261128-043728
- **Related target files**: `tests/agent/test_tool_policy.py`
