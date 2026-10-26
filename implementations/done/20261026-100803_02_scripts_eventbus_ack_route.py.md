## Goal

Remove the resolved-history narrative comment and rewrite the resolved-history parenthetical
in `ack_route.py` to the current invariant; classify the remaining `REQ-0xx` tags (all active
invariant markers, kept).

## Scope

- Modify only `scripts/eventbus/ack_route.py`: the comment at line 16 and the parenthetical
  at line 183. All other `REQ-0xx` tags here are active invariants and are kept unchanged.

## Assumptions

- The two flagged comments narrate PAST removed implementation (`write_offset removed`,
  `events.acked_at removed`); every other `REQ-0xx` tag in this file states a CURRENT
  invariant/failure/concurrency rule and is kept.
- Comment edits do not change observable behavior; the ACK/NACK suite is the backstop.

## Design decisions

- **Delete** the standalone narrative at line 16 (`# write_offset removed — replaced by
  ack_event_for_consumer() transactional path`); it narrates a removed implementation detail
  with no current-invariant value.
- **Rewrite** the parenthetical at line 183 to drop the past-tense "removed" clause and state
  the current invariant, e.g. `# Then check events-level DLQ state only (REQ-004: dlq_at is
  the authoritative DLQ indicator)`.
- **Keep** the other 11 `REQ-0xx` tags (lines 34, 43, 49, 114, 127, 135, 139, 161, 163, 174,
  175, 191); each states a current invariant (mandatory consumer_id, principal ownership,
  idempotency, atomic invalid-state check, per-consumer failure count).

## Alternatives considered

- Rewriting line 16 into a current invariant instead of deleting: rejected; the comment
  referred only to a removed code path and carries no current invariant.

## Implementation

### Target file

`scripts/eventbus/ack_route.py`

### Procedure

1. Delete the comment on line 16:
   `# write_offset removed — replaced by ack_event_for_consumer() transactional path`.
2. Rewrite the parenthetical on line 183 from
   `# Then check events-level DLQ state only (REQ-004: events.acked_at removed; dlq_at is the authoritative DLQ indicator)`
   to
   `# Then check events-level DLQ state only (REQ-004: dlq_at is the authoritative DLQ indicator)`.
3. Leave all other `REQ-0xx` tags untouched.

### Method

Two comment edits in one file; no new symbols.

### Details

- Do not alter any code, signature, or delivery logic.
- Verification: `grep -rn "REQ-0" scripts/eventbus/ack_route.py` still returns 13 tags; none
  should now contain a past-tense "removed"/"replaced by"/"legacy"/"no longer" phrase.

## Compatibility considerations

- Behavior unchanged; only comment text changed.

## Security considerations

- No security impact; comment-only edit.

## Rollback considerations

- Revert the commit.

## Validation plan

- `uv run pytest tests/eventbus/` — full EventBus suite passes.
- `uv run ruff format scripts/eventbus/ack_route.py`; `uv run ruff check
  scripts/eventbus/ack_route.py`; `uv run mypy scripts/eventbus/ack_route.py`;
  `uv run bandit scripts/eventbus/ -c pyproject.toml`.
- `PYTHONPATH=scripts uv run lint-imports` — `eventbus-is-isolated` KEPT.

## Completion criteria

- No resolved-history narrative remains; line 183 states the current invariant without
  "removed"; 13 `REQ-0xx` tags remain, all active invariants.

## Out of Scope

- Any change outside `ack_route.py`.
- Editing the 11 active `REQ-0xx` tags.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove resolved-history comment (line 16); rewrite parenthetical (line 183) | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: comment-only |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A |

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
- **Requirement ID**: `REQ-001`
- **Source issue**: `issues/20261023-154326_eventbus008_documentation-comment-drift-cleanup.md`
- **Requirement requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261025-124800_eventbus008_documentation-comment-drift-cleanup.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261026-100803
- **Related target files**: `scripts/eventbus/ack_route.py`
