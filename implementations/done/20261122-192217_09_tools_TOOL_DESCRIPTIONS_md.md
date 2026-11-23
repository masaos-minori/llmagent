## Goal

Register the new comment-lint tool's row in the tool inventory (REQ-005 - inventory row required by `routing.md` Tools step 5).

## Scope
**Release unit**: N/A: not part of a release unit

Registry-file change only: add the row for `check_config_comment_length.py` (defined by sibling procedure seq 07).

## Assumptions
- The row content must match the tool as implemented by seq 07; write it in the same change as the tool (same-change rule).

## Design decisions
- Follow the existing two-part inventory format (summary table row and detail section) used by sibling checker entries.
- No exception mechanism is involved: `check_tool_descriptions_sync.py` has no baseline or self-exception, so the row is simply added and the checker then passes. Only the private helper `_agent_config_migration.py` (sibling procedure seq 12) needs the "Reference generation (private)" shape used by `_contract_manifests.py`.

## Alternatives considered
N/A: the sync checker enforces the row; no alternative.

## Compatibility considerations
`check_tool_descriptions_sync.py` fails until this row exists; it already runs as a gate, so no new check is added.

## Security considerations
N/A: documentation-only.

## Rollback considerations
N/A: revert the commit.

## Implementation
### Target file
`tools/TOOL_DESCRIPTIONS.md`
### Procedure
1. Add the tool's row in the same change as the tool itself.
### Method
Match the tool's actual behavior from seq 07 (finding codes, exit codes, allowlist); do not describe unimplemented behavior.
### Details
N/A: single row addition.

## Validation plan
- `uv run python tools/check_tool_descriptions_sync.py` — no drift.

## Completion criteria
The inventory row exists, matches the implemented tool, and the sync checker reports no findings.

## Out of Scope
The tool itself (sibling procedure seq 07).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the tool row | Completed | 2026-11-22 | 2026-11-22 | Same change as seq 07; Index row plus the "Config Comment Lint" detail section, and the `_agent_config_migration.py` row for seq 12 in the Index and "Reference Generators" section |
| 2 | Run `check_tool_descriptions_sync.py` | Completed | 2026-11-22 | 2026-11-23 | "No issues found"; the pre-commit hook also passes |

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
- **Requirement ID**: `REQ-005` (tool inventory registration)
- **Source issue**: `issues/20261120-114214_agentcfg006_reduction-integration-verification.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261122-190238_agentcfg006_reduction-integration-verification.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261122-192217
- **Related target files**: `tools/TOOL_DESCRIPTIONS.md`
