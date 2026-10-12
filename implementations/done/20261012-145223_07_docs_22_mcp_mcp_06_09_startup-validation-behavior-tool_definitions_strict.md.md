## Goal
- State the strict and non-strict outcome of a failing drift check next to the existing strict semantics (`REQ-005`).

## Scope
- Only the block under the bold heading about routing drift, tool-definition mismatch, and malformed capabilities: one new bullet. The two existing bullets stay as they are.

## Assumptions
- The block currently gives only strict true to FATAL and strict false to WARNING for detected mismatches; it says nothing about the check itself failing.
- Documentation is written in English and states behavior.

## Design decisions
- Add a third bullet distinguishing a failure of the check itself from a detected mismatch, with the same two outcomes.

## Alternatives considered
N/A: the Plan Design section already fixed the approach for this row.

## Implementation
### Target file
`docs/22_mcp/mcp_06_09_startup-validation-behavior-tool_definitions_strict.md`

### Procedure
1. Locate the block with `grep -n "Routing drift, tool-definition" docs/22_mcp/mcp_06_09_startup-validation-behavior-tool_definitions_strict.md`.
2. After its two existing bullets insert: - Unexpected failure of the routing-drift check itself (not a detected drift): strict true gives a FATAL outcome and blocks startup; strict false gives a WARNING outcome and startup continues.
3. Leave every other line untouched.

### Method
- Insert one line directly after the second bullet of that block, matching its formatting.

### Details
- Describe the behavior after procedures 01 and 02 land; apply in the same change set.

## Compatibility considerations
N/A: documentation-only change.

## Security considerations
N/A: no input handling, credentials, or trust boundary is touched.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_quality.py docs/22_mcp/mcp_06_09_startup-validation-behavior-tool_definitions_strict.md`, `uv run python tools/check_docs_structure.py docs/22_mcp/mcp_06_09_startup-validation-behavior-tool_definitions_strict.md`, `uv run python tools/check_docs_consistency.py --domain mcp`, `uv run python tools/check_docs_japanese.py`.

## Completion criteria
- The block has the third bullet; no other line changed; the documentation checkers pass.

## Out of scope
- Any other section and the agent operations documents (procedures 05 and 06).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the third bullet to the routing drift block | Completed | 20261012-145801 | 20261012-145824 | stale_detector clean changed: docs/22_mcp/mcp_06_09_...md (third bullet under the routing drift block) |
| 2 | Run the documentation checkers named in `routing.md` for the edited file | Completed | 20261012-145824 | 20261012-145824 | check_docs_quality, check_docs_structure (rc 0), check_docs_consistency --domain agent/mcp, check_docs_japanese, check_docs_content_policy, check_needs_confirmation_inventory pass |

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
- **Requirement ID**: `REQ-005` (document the drift-check failure rule)
- **Source issue**: issues/20261012-124829_start003_startup-routing-drift-check-downgrades-failures-to-warnings-while-safety-tier-check-stays-fail-closed.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261012-144923_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261012-145223
- **Related target files**: docs/22_mcp/mcp_06_09_startup-validation-behavior-tool_definitions_strict.md