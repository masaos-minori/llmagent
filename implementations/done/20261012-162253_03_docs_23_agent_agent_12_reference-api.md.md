## Goal
- Extend the memory subsystem On Failure line so it states how an internal error during startup is reported (`REQ-005`).

## Scope
- Only the On Failure bullet of the memory subsystem entry in `docs/23_agent/agent_12_reference-api.md`. Nothing else in the file changes.

## Assumptions
- The bullet currently reads: Errors are logged. REPL continues without memory (graceful degradation); that remains true.
- Documentation is written in English and states behavior, not code structure (`skills/DESIGN.md` Output language).

## Design decisions
- Keep the existing sentences and add one sentence after them, so the general rule and the new detail sit together.

## Alternatives considered
N/A: the Plan Design section already fixed the approach for this row.

## Implementation
### Target file
`docs/23_agent/agent_12_reference-api.md`

### Procedure
1. Locate the bullet with `grep -n "On Failure:" docs/23_agent/agent_12_reference-api.md` (the one saying REPL continues without memory).
2. Append to that bullet, after graceful degradation, the sentence: An internal error of the memory service during startup (a programming error rather than a network or database failure) is logged as an error with a traceback and shown as an internal-error warning; startup still continues without memory.
3. Leave every other line untouched.

### Method
- Edit that single bullet; keep the bullet formatting of the surrounding list.

### Details
- Describe the behavior after procedure 01 lands; apply this change in the same change set, not before.
- Do not name the category strings; the document describes behavior.

## Compatibility considerations
N/A: documentation-only change.

## Security considerations
N/A: no input handling, credentials, or trust boundary is touched.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_quality.py docs/23_agent/agent_12_reference-api.md`, `uv run python tools/check_docs_structure.py docs/23_agent/agent_12_reference-api.md`, `uv run python tools/check_docs_consistency.py --domain agent`, `uv run python tools/check_docs_japanese.py`.

## Completion criteria
- The On Failure bullet states the internal-error case; no other line changed; the documentation checkers pass.

## Out of scope
- Any other section, the startup and health document, and any code change.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Extend the memory On Failure bullet | Completed | 20261012-163552 | 20261012-163606 | stale_detector clean changed: docs/23_agent/agent_12_reference-api.md (On Failure bullet extended) |
| 2 | Run the documentation checkers named in `routing.md` for the edited file | Completed | 20261012-163606 | 20261012-163606 | check_docs_quality, check_docs_structure (rc 0), check_docs_consistency --domain agent, check_docs_japanese, check_docs_content_policy, check_needs_confirmation_inventory pass |

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
- **Requirement ID**: `REQ-005` (document the internal-error case of memory injection)
- **Source issue**: issues/20261012-124838_start004_startup-prompt-setup-swallows-all-memory-injection-errors-as-a-generic-disabled-flag.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261012-154332_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261012-162253
- **Related target files**: docs/23_agent/agent_12_reference-api.md