## Goal
Change the turn-entry control contract so the engine returns control text plus directives, and remove the
logical call id from the LLM-facing text.

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The control text may show tool name and canonical argument hash; the hash is not the id and is not editable
  identity (Plan Assumptions).
- Directives are built from the rows `classify_stale_pending` returned in the same call, so no second
  classification call is made.

## Design decisions
- `build_turn_control_message` returns `TurnControl` (new) — control text plus directives — from the single
  `classify_stale_pending` call (Plan Design D2), because classification transitions rows and cannot be called
  twice.
- The return type stays `TurnControl` (new) or `None`: no listed rows still returns `None`, so a turn with
  nothing to report is byte-identical to the current behavior.

## Alternatives considered
- A second method that builds directives separately — rejected per Plan D2: the second call sees no source-state
  rows.
- Engine-side cached state — rejected: hidden state is not a contract.

## Implementation
### Target file
`scripts/agent/workflow/workflow_engine.py`

### Procedure
Add the `TurnControl` (new) dataclass and change the return value of `build_turn_control_message`.

### Method
- `TurnControl` (new) carries the control text and the directives built from the classified rows.
- Build directives only from rows with `state = 'interrupted'` and `retry_class = 'retryable'`, using
  `reconstruct_replay_directives` (new, declared by sibling procedure seq 02) on the rows this call returned.
- Rewrite the replay and unreplayable lines to name tool and `args_hash` only; the id does not appear in the
  text.

### Details
- Keep the existing error behavior: on store or config errors the turn proceeds with no control message.
- The function is already at radon C rank; extract the line-building and directive-building steps into helpers
  so neither new function exceeds B rank (`rules/toolchain.md`).
- Outcome-unknown rows stay in the unreplayable section only and produce no directive (AC-003).

## Compatibility considerations
Every consumer of the method must move to the new contract in the same change set: the adapter (target row) and
the hand-written fake engines and mock return values listed in the Plan's consumer scan. Files that only import
the engine are not affected.

## Security considerations
Removing the id from LLM text closes the edit path the Issue's constraint targets: the LLM can no longer copy or
alter an identity value.

## Rollback considerations
N/A: revert the commit; the contract change must be reverted together with the adapter and the test stubs.

## Validation plan
- `uv run pytest tests/agent/workflow/test_workflow_engine.py` — control text has no id (AC-004); no directive for
  non-retryable or outcome-unknown rows (AC-003).
- Full sequence per `rules/toolchain.md`.

## Completion criteria
The control text names tool and hash only, directives exist only for `interrupted` replayable rows, and the
single classification call produces both.

## Out of Scope
No change to the dispatcher-side dedup semantics or to `mcp_dedup.sqlite`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `TurnControl` (new) and change the return contract | Pending | — | — | |
| 2 | Build directives from classified rows; remove the id from the text | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-004` (no directive for non-retryable or outcome-unknown), `REQ-005` (control text carries no id)
- **Source issue**: `issues/20261119-140511_mcpai004_logical-idempotency-key-replay.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261125-105505_mcpai004_logical-idempotency-key-replay.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-112546
- **Related target files**: `scripts/agent/workflow/workflow_engine.py`
