## Goal

Align the canonical Dry-Run Support list, the tier example row, and the tier-`none` reachability
counts with the new mdq write tier.

## Scope
**Release unit**: tier change and its pins

- `docs/22_mcp/mcp_05_03_fail-open-fail-closed-and-risk-tiers.md`: the Dry-Run Support list sentence
  (line 71), the `WRITE_SAFE` example row (line 86), the `WRITE_DANGEROUS` example row (line 87), and
  the reachability counts (line 90).

## Assumptions

- The evaluation-order statement is not changed: the mdq tools become reachable through the tier, not
  through a reorder, so only the lists and counts that name them change.

## Design decisions

- The counts are recomputed from the shipped declarations rather than adjusted by hand, so the
  sentence stays a statement about the current inventory.

## Alternatives considered

- N/A: documentation-only change in one section.

## Implementation
### Target file
`docs/22_mcp/mcp_05_03_fail-open-fail-closed-and-risk-tiers.md`

### Procedure
1. Add the two mdq write tools to the Dry-Run Support list sentence (line 71).
2. Remove `index_paths` from the `WRITE_SAFE` example row (line 86) and add `index_paths` and
   `refresh_index` to the `WRITE_DANGEROUS` example row (line 87).
3. Update the reachability counts (line 90): 64 declared tiers become 39 `READ_ONLY`, 10 `WRITE_SAFE`,
   14 `WRITE_DANGEROUS`, 1 `ADMIN`; the tier-`none` set becomes 49 tools; the prompt-capable set becomes
   the 14 `WRITE_DANGEROUS` tools plus `shell_run`.

### Method

- Line 104 is the dry-run preview-injection note, not a tier statement, so it is unchanged.

### Details

- The provenance test names cited in the same paragraph stay valid: the tier-`NONE` cases in
  `tests/agent/test_tool_policy.py` keep their `READ_ONLY` example, and the mdq tools move to the
  per-mode cases.

## Compatibility considerations

- Cross-plan overlap: this file is shared with plans 008 and 010; this change touches only the lists
  and counts that name the mdq writes.

## Security considerations

- N/A.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run python tools/check_docs_structure.py`
- `uv run python tools/check_docs_content_policy.py`

## Completion criteria

- The doc names the two mdq write tools as dry-run supported and states the tier that maps to
  `medium` (AC-1, AC-5).

## Out of Scope

- The evaluation order and the tier-risk mapping table itself.

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
- **Requirement ID**: REQ-003, REQ-008
- **Source issue**: `issues/20261119-142129_mdqmcp007_mdq-approval-dry-run.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261127-173835_mdqmcp007_mdq-approval-dry-run.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261128-043728
- **Related target files**: `docs/22_mcp/mcp_05_03_fail-open-fail-closed-and-risk-tiers.md`
