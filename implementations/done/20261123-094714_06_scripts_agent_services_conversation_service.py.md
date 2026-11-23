## Goal

Route /clear new through `SessionTransitionService` and state in-memory history explicitly in the result messages (REQ-002 clear-new finalization, REQ-007 in-memory wording; AC-1, AC-4).

## Scope
**Release unit**: N/A: not part of a release unit

Single-file change; row 25 is covered as this document's companion.

## Assumptions
- Current code verified: `conversation_service.py:24-44` cuts history to the system prompt, resets stats, then on new_session calls `ctx.session.start()`, `refresh_session_correlation`, and `set_title("(New Session)")` without finalizing the old session.
- Long-term Memory tables and JSONL are not touched by this function today and must stay untouched (REQ-007).

## Design decisions
- new_session=True delegates the whole switch (finalize, start, commit) to the transition service (seq 02); this function keeps only the in-memory-only path and the result messages.
- Result messages say "in-memory conversation history" and note that persisted rows remain (REQ-007/REQ-010 wording), replacing "History cleared. New session started." phrasing that hides reload behavior.

## Alternatives considered
- Making /clear delete persisted rows: excluded by the owner decision (plan Assumptions, 2026-11-22).

## Implementation
### Target file
`scripts/agent/services/conversation_service.py`
### Procedure
1. Replace the new_session branch body (`ctx.session.start()` plus correlation/title calls) with the transition service clear_new call; set the new session's title after the commit.
2. Reword both `ConversationActionResult.message` values to name in-memory conversation history and persisted-row survival.
### Method
Delegate to seq 02. Verification finding (2026-11-23): the Assumptions' "signature unchanged" is not implementable — `clear_new` awaits the async persister, so `clear_conversation` became `async def` and gained a required `transition_service` kwarg for the new_session path; the `/clear` CommandDef flips to `is_async=True` (seq 13) and `_cmd_clear` awaits the call. Return type unchanged.
### Details
N/A: none beyond the plan text.

### Companion test files
- `tests/agent/services/test_conversation_service.py`
  - Procedure: assert /clear new calls the transition service (finalizes the old session before switching) and that long-term Memory tables and JSONL are unchanged; assert the new message wording.
  - Validation: `uv run pytest tests/agent/services/test_conversation_service.py -q`.

## Compatibility considerations
- Existing tests asserting the old message strings are updated (companion row); no signature change for `cmd_context.py`.

## Security considerations
N/A: no new surface.

## Rollback considerations
N/A: revert the commit (requires seq 02 present; revert together with it).

## Validation plan
- `uv run pytest tests/agent/services/test_conversation_service.py tests/agent/commands/test_agent_cmd_context.py -q`.

## Completion criteria
/clear new finalizes the old session before switching via the service, both messages describe the in-memory reset explicitly, and Memory data is unchanged (AC-1, AC-4).

## Out of Scope
Transition pipeline (seq 02), command display text (seq 13), docs (seq 15, 17).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 2026-11-23 | 2026-11-23 | After seq 02 async + transition_service kwarg per verification finding (see Method); messages reworded |
| 2 | Add or update tests per Validation plan (companion row 25) | Completed | 2026-11-23 | 2026-11-23 | 13 tests pass (async conversion + delegation + wording) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-11-23 | 2026-11-23 | ruff, mypy, lint-imports, targeted pytest pass |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 2026-11-23 | 2026-11-23 | Docs via seq 15, 17 Docs updated via seq 15-20 (2026-11-23) |

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
- **Requirement ID**: `REQ-002` (route clear-new through the service), `REQ-007` (explicit in-memory wording)
- **Source issue**: `issues/20261119-145300_cliplc002_session-transition-generation.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261122-232757_cliplc002_session-transition-generation.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261123-094714
- **Related target files**: `scripts/agent/services/conversation_service.py`, `tests/agent/services/test_conversation_service.py`