# Implementation: 05_agent_04_state-and-persistence.md — message save rules update

## Goal

Update the "Message save rules" section to document the new skip counters and
strict mode behavior.

## Scope

`docs/05_agent_04_state-and-persistence.md` — "Message save rules" subsection only.

## Assumptions

1. The existing section at approximately line 78 reads three bullet points.
2. Replacement adds counters and strict mode documentation without restructuring the rest of the file.

## Implementation

### Target file

`docs/05_agent_04_state-and-persistence.md`

### Procedure

Replace the existing "Message save rules" bullet list with the expanded version below.

### Method

Edit the three-bullet block. No other section changes.

### Details

Replace:

```
### Message save rules

- `save(role, content)` saves only valid roles: `user`, `assistant`, `tool`, `system`
- Invalid roles are silently skipped
- `save_many()` batches multiple messages in one transaction
```

With:

```
### Message save rules

- `save(role, content)` saves only valid roles: `user`, `assistant`, `tool`, `system`
- Invalid roles are logged as warnings and counted (`stat_skipped_invalid_role`)
- Missing `session_id` is logged as a warning and counted (`stat_skipped_no_session`)
- When `strict_mode=True`, both conditions raise `RuntimeError` instead of skipping
- Counters accessible via `session.skipped_no_session_count` and `session.skipped_invalid_role_count`
- `save_many()` batches multiple messages in one transaction; invalid roles are skipped with a single warning log
- `save_diagnostic(content)` persists to role `"diagnostic"` — not returned by `fetch_messages()` for history reconstruction
```

## Validation plan

No toolchain validation needed for doc-only change. Review diff before staging.
