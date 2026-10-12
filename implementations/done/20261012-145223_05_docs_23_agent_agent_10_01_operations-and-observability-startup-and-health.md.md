## Goal
- State in the Important Notes list how routing_drift severity is decided, including an unexpected failure of the check itself (`REQ-005`).

## Scope
- Only the Important Notes list that follows the severity table: one new bullet. Everything else is unchanged.

## Assumptions
- The list already gives per-check severity for tool_definitions and mcp_tool_discovery; the new bullet follows the same style.
- Documentation is written in English and states behavior, not code structure (`skills/DESIGN.md` Output language).

## Design decisions
- Add one bullet right after the tool_definitions bullet, so the strict-dependent checks sit together.

## Alternatives considered
N/A: the Plan Design section already fixed the approach for this row.

## Implementation
### Target file
`docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md`

### Procedure
1. Locate the Important Notes list (`grep -n "Important Notes" docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md`).
2. Insert after the tool_definitions bullet exactly this bullet: - `routing_drift` follows `routing_drift_strict`: a detected drift is FATAL when strict and WARNING otherwise, and an unexpected failure of the drift check itself follows the same rule (FATAL when strict, WARNING otherwise), so a broken check is never reported as a clean result.
3. Leave every other line untouched.

### Method
- Insert one line; keep the blank line structure and bullet formatting of the list.

### Details
- Describe the behavior after procedures 01 and 02 land; apply this change in the same change set, not before.

## Compatibility considerations
N/A: documentation-only change.

## Security considerations
N/A: no input handling, credentials, or trust boundary is touched.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_quality.py docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md`, `uv run python tools/check_docs_structure.py docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md`, `uv run python tools/check_docs_consistency.py --domain agent`, `uv run python tools/check_docs_japanese.py`.

## Completion criteria
- The list has the new bullet; no other line changed; the documentation checkers pass.

## Out of scope
- Any other section, and the mirrored list in the sibling document (procedure 06).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the routing_drift bullet to the Important Notes list | Completed | 20261012-145752 | 20261012-145824 | stale_detector clean changed: docs/23_agent/agent_10_01_...md (one bullet after tool_definitions) |
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
- **Related target files**: docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md