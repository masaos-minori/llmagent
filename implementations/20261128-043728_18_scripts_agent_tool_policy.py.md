## Goal

Align the `classify_risk()` docstring's tier-`NONE` tool enumeration, which names `index_paths` and
`refresh_index` as tier-`NONE` examples and becomes a stale claim once the declared tier changes.

## Scope
**Release unit**: tier change and its pins

- The `classify_risk()` docstring in `scripts/agent/tool_policy.py` (line 464). No classification
  behavior changes in this file.

## Assumptions

- The lookup order is unchanged, so only the parenthetical tool list is edited.
- The enumeration is prose evidence for the canonical policy in
  `docs/23_agent/agent_06_02_tool-execution-and-approval-approval.md`; the docstring must agree with
  the shipped declarations, which is what the plan's doc rows also align.

## Design decisions

- The enumeration lists only tools that remain tier-`NONE` after the change (`git_add`,
  `git_commit`, `write_file`, `edit_file`, `create_directory`, `move_file`, every `READ_ONLY` tool),
  so it stays a statement about the shipped declarations rather than a list that has to be edited
  whenever a producer changes a tier.

## Alternatives considered

- N/A: single docstring sentence, no behavior change.

## Implementation
### Target file
`scripts/agent/tool_policy.py`

### Procedure
1. In the `classify_risk()` docstring (line 464), remove `index_paths` and `refresh_index` from the
   tier-`NONE` tool enumeration.

### Method

- `_TIER_TO_RISK` (78-82), `_special_case_risk()` (383-427), `_escalate_for_path()` (315-345), and the
  lookup order in `classify_risk()` (453-499) are unchanged: the tier declaration in
  `scripts/mcp_servers/mdq/mdq_tools.py` alone makes the branches reachable for the two tools.

### Details

- The sentence keeps its shape: "a tier-`NONE` tool ( … ) is never escalated by
  approval_protected_paths", with the two mdq names dropped from the list.

## Compatibility considerations

- `tests/agent/test_tool_policy.py` row 11 removes the same two tools from the shipped tier-`NONE`
  set, so the docstring and the test set agree after both land.

## Security considerations

- N/A: documentation inside the module only.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run pytest tests/agent/test_tool_policy.py tests/agent/test_tool_approval_risk.py`
- Full sequence per `rules/toolchain.md`.

## Completion criteria

- The docstring enumeration matches the shipped declarations, and the policy tests pass (AC-1, AC-5).

## Out of Scope

- The tier declaration: row 1.
- The canonical policy docs: rows 15 and 17.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | Test change is row 11 |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | Docs rows 15 and 17 state the same consequence |

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
- **Requirement ID**: REQ-002
- **Source issue**: `issues/20261119-142129_mdqmcp007_mdq-approval-dry-run.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261127-173835_mdqmcp007_mdq-approval-dry-run.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261128-043728
- **Related target files**: `scripts/agent/tool_policy.py`
