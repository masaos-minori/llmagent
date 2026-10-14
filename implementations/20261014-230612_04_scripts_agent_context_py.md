## Goal

Add an in-memory compression-boundary marker (`ctx.conv.undo_floor`) that indexes into `ctx.conv.history` (0 = no boundary), with a set/reset lifecycle tied to compression and `/clear`.

## Scope

Only `scripts/agent/context.py`: the `ConversationState` dataclass (line 84). This document names exactly one target file.

## Assumptions

- `ConversationState` is an `asyncio`-based dataclass (`scripts/agent/context.py:84`) with fields like `history`, `llm_url`, etc.
- `undo_floor` is a plain `int` field (not synchronized separately); `history` access is already guarded by `_history_lock`.
- `/clear` resets live in `conversation_service.clear_conversation()` (`scripts/agent/services/conversation_service.py:28`).

## Design decisions

- Add `undo_floor: int = 0` as a simple dataclass field; `0` encodes "no boundary / never compressed."
- No new lock: the field is written only synchronously right after `history` is reassigned within an already-synchronized turn, so it cannot race independently of `history`.

## Alternatives considered

- **Store the boundary as a row ID in memory too** — rejected: the plan specifies a history *index* in memory (fast, no DB lookup on the hot path) and a row ID in the DB (authoritative). Convert between them on restore (row 10).
- **Guard `undo_floor` with its own lock** — rejected: it is always updated alongside `history`, which is already locked; a separate lock adds complexity with no concurrency benefit under the single-threaded model.

## Implementation

### Target file

`scripts/agent/context.py`

### Procedure

Add `undo_floor: int = 0` to the `ConversationState` dataclass (line 84), after the existing fields.

### Method

Insert the field into `ConversationState` (lines 84-106), e.g. after `memory_warning_shown` (line 104-106):

```python
    undo_floor: int = 0  # index into history of the /undo compression boundary; 0 = none
```

Place it among the other dataclass fields (order does not affect behavior). Do not touch any other file in this document.

### Details

- Set point (row 02→08): after a successful `session.replace_messages()` during compression, callers set `ctx.conv.undo_floor = <history index of the boundary message>`.
- Reset points: `/clear` and `/clear new` reset `ctx.conv.undo_floor = 0` (see Plan Gap note below).
- On restore (row 10): convert the stored boundary row ID into a history index and assign here.

## Compatibility considerations

N/A: adding a dataclass field with a default is backward compatible; existing `ConversationState` construction is unaffected.

## Security considerations

N/A: in-memory integrity marker only.

## Rollback considerations

Revert the commit. Removing the field is safe once all setters/removers (rows 08/10) are reverted together.

## Validation plan

```bash
uv run pytest tests/agent/ -p no.cacheprovider -k "context or conversation_state"
```

Assert: `ConversationState().undo_floor == 0` by default; setting `history`/compression updates `undo_floor` consistently.

## Completion criteria

`ConversationState` has `undo_floor: int = 0`; default instance has `undo_floor == 0`; related tests pass.

## Out of scope

The `/clear` reset in `conversation_service.clear_conversation()` — see Plan Gap note below. The in-memory set-on-compression (row 08), the restore conversion (row 10), and the DB column (row 01).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Plan gap

REQ-003 also requires resetting `ctx.conv.undo_floor` to `0` in `clear_conversation()` for both `/clear` and `/clear new` (`scripts/agent/services/conversation_service.py:28`). That file is **not** an Implementation Target Files row, so per the one-target-file-per-row rule this document does NOT contain its modification instructions. It must be covered by a dedicated row before implementation. Implementers following REQ-003 will perform both changes; add the missing row to the plan first.

## Traceability

- **Workflow phase**: plan-to-implementation-procedure
- **Source issue**: N/A
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261014-214826_plan.md
- **Source implementation procedure**: N/A
- **Generated at**: 20261014-230612
- **Related target files**: scripts/agent/context.py
