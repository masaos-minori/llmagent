## Goal

Remove the call site that reaches the deleted private classifier and add the pending-restart display
cases, so the command test shows the pending view without asserting the deleted implementation (REQ-008,
restart-only MCP; REQ-009, pending display; REQ-013, dead reload code removed).

## Scope
**Release unit**: R6-dead-code-removal

## Assumptions
- Verified against current source: `tests/agent/commands/test_cmd_mcp.py:171` calls
  `reload_svc._classify_mcp_server_changes(ctx, {})`, which row 6 deletes.
- Live probe-row assertions stay unchanged; only the pending display is added.
- The pending row model is exposed by row 22 and the rendering helper by row 21.

## Design decisions
- The retargeting lands in the same commit as the deletion (Plan Phase 6), so the suite is never red
  between commits.
- Pending display cases assert the heading and the row content, not the formatting width.

## Alternatives considered
- Keeping the call site against a renamed method — rejected: the method is deleted, not renamed.

## Implementation
### Target file
`tests/agent/commands/test_cmd_mcp.py`

### Procedure
Retarget this file in the same commit as the deletion, per the Plan's Phase 6 step 1: drop the call site
that reaches the private classifier and add the pending-restart display cases.

### Method
- Remove the `_classify_mcp_server_changes` call site.
- Add pending-restart display cases for an added, changed, and removed definition.
- Keep the live probe-row assertions unchanged.

### Details
- A case asserts a pending definition produces no probe row, which is the AC-4 separation.

## Compatibility considerations
- Blast radius: the command test is the only place the pending MCP display is observed end to end.

## Security considerations
- N/A: the tests assert display structure, not output values.

## Rollback considerations
- Revert the Phase 6 commit.

## Validation plan
- `uv run pytest tests/agent/commands/test_cmd_mcp.py -q`

## Completion criteria
- No test here references a deleted symbol, and each pending change kind has a display case that shows it
  as pending rather than as a live row.

## Out of Scope
- The pending-state storage (row 8).
- The rendering helper (row 21).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261125-205000 | 20261125-210919 | lands with the deletion R6 run 20261125: no test references a deleted symbol; the pending display cases are TestCmdMcpStatusPendingRows added in R5 |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261125-205000 | 20261125-210919 | R6 run 20261125: no test references a deleted symbol; the pending display cases are TestCmdMcpStatusPendingRows added in R5 |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | The `_classify_mcp_server_changes` call site named in Assumptions no longer exists: the classifier was deleted in the R5 run and this file already reads the pending rows from `PendingConfigState` on the ctx. The R6 run confirms no test here references a deleted symbol | Yes | 2026-11-25 |
| 1 | The pending display cases the procedure asks for are the `TestCmdMcpStatusPendingRows` class added in the R5 run: added, changed, and removed definitions each get a row, and the added-definition case splits the output at the pending heading to assert the pending definition produces no live probe row (AC-4) | Yes | 2026-11-25 |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-008 (restart-only MCP), REQ-009 (pending display), REQ-013 (dead reload code removed); AC-4, AC-5
- **Source issue**: issues/20261119-145303_cliplc005_staged-reload-transaction.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-110935_cliplc005_staged-reload-transaction.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-074359
- **Related target files**: `tests/agent/commands/test_cmd_mcp.py`