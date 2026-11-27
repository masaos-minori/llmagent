## Goal

Add the per-mode approval-risk tests for the two MDQ write tools: index `medium`, normal refresh
`medium`, forced refresh `high`, and a protected in-jail path `high`.

## Scope
**Release unit**: tier change and its pins

- New tests in `TestClassifyRisk` (class at line 111) of `tests/agent/test_tool_approval_risk.py`.

## Assumptions

- The tests read the producer declarations through `make_producer_registry()`, so they assert the
  consequence of the declaration in `scripts/mcp_servers/mdq/mdq_tools.py` rather than a tier set by
  the test.
- `_make_cfg()` already carries `approval_protected_paths` with `/opt/llm/` and an `allowed_root`
  that contains it, as the existing escalation test at line 166 relies on.

## Design decisions

- The cases live in `TestClassifyRisk`, the class that already proves the declared tier is the only
  risk source, rather than in `TestClassifyOperationType` (class at line 389, method
  `test_mdq_rag_cicd_git_write_tools` at line 402), which pins operation type only and stays
  unchanged.
- Each case asserts one mode, so a failure names the mode that regressed: base risk, the `force`
  special case, and path escalation are three different branches.

## Alternatives considered

- One parametrized case over the four modes: rejected, the four modes exercise three different
  branches of `classify_risk()` and a single parametrized case cannot show which branch produced the
  result.

## Implementation
### Target file
`tests/agent/test_tool_approval_risk.py`

### Procedure
1. Add `test_mdq_index_paths_resolves_medium_from_declared_tier` (new).
2. Add `test_refresh_index_resolves_medium_without_force` (new).
3. Add `test_forced_refresh_escalates_to_high` (new) passing `force=True`.
4. Add `test_mdq_write_on_protected_in_jail_path_escalates_to_high` (new) for both tools.

### Method

- Call `_classify_risk(cfg, tool_name, args, make_producer_registry())` with the existing `_make_cfg()`
  helper, matching the style of `test_write_to_protected_path_escalates_to_high` (line 166).
- The mdq args carry the declared path-kind key `paths` as a list; `_escalate_for_path()` (315-345)
  iterates every element of a list-valued argument, so a protected path in the list escalates.

### Details

- The in-jail case uses a path under `approval_protected_paths` that is also inside `allowed_root`, so
  the jail does not deny before classification.

## Compatibility considerations

- `test_declared_tier_is_the_only_risk_source` (line 284) is unchanged: it asserts that no per-tool
  risk rule contributes, which the tier change does not affect.
- The plan-mode block in `tests/agent/test_tool_approval_preflight.py` (method at line 991) already
  covers `index_paths` by name (line 987) and `refresh_index` through the tier mapping.

## Security considerations

- N/A: test-only change.

## Rollback considerations

- Revert the commit.

## Validation plan

- `uv run pytest tests/agent/test_tool_approval_risk.py tests/agent/test_tool_policy.py`
- Full sequence per `rules/toolchain.md`.

## Completion criteria

- AC-1 passes for all four modes, and no MDQ write resolves to `none`.

## Out of Scope

- The tier declaration: row 1.
- The shipped tier-`NONE` provenance set: row 11.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | This row is the test change |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | Docs rows 14 and 17 state the consequence |

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
- **Requirement ID**: REQ-002, REQ-007
- **Source issue**: `issues/20261119-142129_mdqmcp007_mdq-approval-dry-run.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261127-173835_mdqmcp007_mdq-approval-dry-run.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261128-043728
- **Related target files**: `tests/agent/test_tool_approval_risk.py`
