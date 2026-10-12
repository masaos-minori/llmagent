## Goal
- State in the Resource Cleanup on Shutdown section when cleanup runs: when the session ends, or when startup fails or is interrupted, and never during a successful startup (`REQ-005`).

## Scope
- Only the sentence introducing the cleanup list in that section (around line 79). The ordered list and the rest of the document are unchanged.

## Assumptions
- The section currently says resources close within a finally block without saying which code that block wraps.
- Documentation is written in English (`skills/DESIGN.md` Output language) and keeps to intent and boundaries, not implementation detail.

## Design decisions
- Replace one sentence with two: the finally block wraps startup and the interactive session; cleanup therefore runs once when the session ends or when startup fails or is interrupted, never in the middle of a successful startup.

## Alternatives considered
N/A: a single-sentence rewording is the smallest change that makes the timing explicit.

## Implementation
### Target file
`docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md`

### Procedure
1. Locate the sentence with `grep -n "within a" docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md` (the line saying resources are closed in the following order within a finally block).
2. Replace it with: Resources are closed once, when the interactive session ends or when startup fails or is interrupted; they are not closed during a successful startup. The cleanup runs in a finally block in this order:
3. Leave the numbered list and every other line untouched.

### Method
- Edit that one line; keep the blank line before the list and the list numbering as they are.

### Details
- The change describes behavior after procedure 01 lands; apply it in the same change set, not before.
- Do not mention internal method names beyond what the section already names.

## Compatibility considerations
N/A: documentation-only change.

## Security considerations
N/A: no input handling, credentials, or trust boundary is touched.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_quality.py docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md`, `uv run python tools/check_docs_structure.py docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md`, `uv run python tools/check_docs_consistency.py --domain agent`, `uv run python tools/check_docs_japanese.py`.

## Completion criteria
- The section states when cleanup runs; the list is unchanged; the documentation checkers pass.

## Out of scope
- Any other section, any code change, and the deployment steps.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Reword the sentence introducing the cleanup list | Completed | 20261012-141643 | 20261012-141712 | stale_detector clean changed: docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md (one sentence reworded; list unchanged) |
| 2 | Run the documentation checkers named in `routing.md` for the edited file | Completed | 20261012-141712 | 20261012-141712 | check_docs_quality, check_docs_structure, check_docs_consistency --domain agent, check_docs_japanese, check_docs_content_policy, check_needs_confirmation_inventory pass; agent_12 line on 'finally always closes resources' stays true, agent_02 has no related text |

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
- **Requirement ID**: `REQ-005` (document when cleanup runs)
- **Source issue**: issues/20261012-124806_start001_startup-failure-cleanup-handler-closes-shared-http-client-before-the-repl-session-begins.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261012-140942_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261012-141133
- **Related target files**: docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md