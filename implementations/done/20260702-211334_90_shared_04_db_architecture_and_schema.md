# Implementation: Verify `tool_call_id` documentation in `90_shared_04_db_architecture_and_schema.md`

## Goal

Confirm that `docs/90_shared_04_db_architecture_and_schema.md` already correctly documents
`messages.tool_call_id` as an active column persisted and restored by `SessionMessageRepository`.
Identify and remove any remaining stale or contradictory mentions if found.

## Scope

- **In scope**: Read and verify line 173 and any other `tool_call_id` reference in
  `docs/90_shared_04_db_architecture_and_schema.md`.
- **Out of scope**: Editing source code, changing schema, or modifying other doc files.

## Assumptions

1. Per the plan, line 173 already reads:
   `| tool_call_id | TEXT | Tool call correlation ID (for tool role messages). Persisted/restored by SessionMessageRepository. NULL for non-tool messages. |`
2. No other stale mention of `tool_call_id` is expected in this file.
3. If the above is confirmed, no edit is required.

## Implementation

### Target file

`docs/90_shared_04_db_architecture_and_schema.md`

### Procedure

1. Open `docs/90_shared_04_db_architecture_and_schema.md`.
2. Search for all occurrences of `tool_call_id`:
   ```bash
   grep -n "tool_call_id" docs/90_shared_04_db_architecture_and_schema.md
   ```
3. Verify line 173 contains:
   - Column name: `tool_call_id`
   - Type: `TEXT`
   - Description: references `SessionMessageRepository`, states persisted/restored, notes NULL for non-tool messages.
4. Check for any other occurrence that contradicts the above (e.g., "unused", "UNUSED", "not used", "TODO").
5. If all occurrences are consistent: **no edit required**.
6. If a stale or contradictory mention is found: update or remove the offending text.

### Method

Manual review followed by targeted grep. No automated rewrite needed unless stale text is found.

### Details

- The expected correct description at line 173 (to verify verbatim):
  ```
  | `tool_call_id` | TEXT | Tool call correlation ID (for tool role messages). Persisted/restored by `SessionMessageRepository`. NULL for non-tool messages. |
  ```
- The column behavior (for reference if a correction is needed):
  - `tool_call_id` is stored when present in the message dict (tool role messages).
  - `tool_call_id` is NULL for user/assistant/system roles.
  - The DB schema has no NOT NULL constraint; `store_impl.py` accepts `str | None = None`.

## Validation plan

| Check | Command / Action | Expected result |
|---|---|---|
| Line 173 description is accurate | `grep -n "tool_call_id" docs/90_shared_04_db_architecture_and_schema.md` | Single result at line ~173 with "Persisted/restored by `SessionMessageRepository`" |
| No stale "unused" claim | `grep -in "tool_call_id.*unused\|unused.*tool_call_id" docs/90_shared_04_db_architecture_and_schema.md` | 0 results |
| No contradictory "not used" claim | `grep -in "tool_call_id.*not used\|not used.*tool_call_id" docs/90_shared_04_db_architecture_and_schema.md` | 0 results |
