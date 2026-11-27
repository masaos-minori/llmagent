## Goal

Align the shipped-tier examples in the canonical approval document, which currently exclude the mdq
write tools from the tools that can escalate.

## Scope
**Release unit**: tier change and its pins

- `docs/23_agent/agent_06_02_tool-execution-and-approval-approval.md`: the protected-path scope
  sentence (line 91). The evaluation-order statement (line 48) is not changed.

## Assumptions

- The evaluation order is unchanged, so only the tool list that sits under it changes.
- The document is the canonical source for the order and the shipped-tier examples, so the sentence must
  name the tools as they are declared after the tier change.

## Design decisions

- The sentence keeps its two-mechanism structure — the jail denies, the escalation prompts — and gains the
  two mdq write tools in the escalation list, so the distinction is not blurred.

## Alternatives considered

- N/A: documentation-only change in one sentence.

## Implementation
### Target file
`docs/23_agent/agent_06_02_tool-execution-and-approval-approval.md`

### Procedure
1. In the protected-path scope sentence, name `index_paths` and `refresh_index` with `delete_file`,
   `delete_directory`, and the git write tools as the tools whose declared tier maps to `medium` and that
   escalate to `high` on a protected path in-jail.

### Method

- The tier-derived `none` statement at line 48 stays as written: it describes the order, not a tool list.

### Details

- No new vocabulary is introduced: the tier names and risk levels are the existing closed sets.

## Compatibility considerations

- `scripts/agent/tool_policy.py` `classify_risk()` docstring carries the same enumeration and is aligned by
  row 18; `docs/22_mcp/mcp_01_tool_ownership_matrix.md` and `docs/22_mcp/mcp_05_03_fail-open-fail-closed-and-risk-tiers.md`
  state the same consequence in rows 14 and 15, so all four land in the same phase.

## Security considerations

- N/A.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run python tools/check_docs_structure.py`
- `uv run python tools/check_docs_consistency.py --domain agent`

## Completion criteria

- The canonical approval document names the mdq write tools under the escalation rule (AC-1).

## Out of Scope

- The evaluation order and the tier-risk mapping.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | Docs checkers above |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | This row is the documentation change |

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
- **Requirement ID**: REQ-002, REQ-008
- **Source issue**: `issues/20261119-142129_mdqmcp007_mdq-approval-dry-run.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261127-173835_mdqmcp007_mdq-approval-dry-run.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261128-043728
- **Related target files**: `docs/23_agent/agent_06_02_tool-execution-and-approval-approval.md`
