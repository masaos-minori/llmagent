# Implementation: Update `tool_call_id` in SessionStore Protocol section of `90_shared_05_db_api_and_operations.md`

## Goal

Update `docs/90_shared_05_db_api_and_operations.md` so that the `SessionStore` Protocol stub
correctly reflects `tool_call_id` in both the `message_save` signature and the `message_list`
return field list. Add a clarifying note about when `tool_call_id` is populated vs. NULL.

## Scope

- **In scope**: Lines ~164–177 (SessionStore Protocol section) in
  `docs/90_shared_05_db_api_and_operations.md`.
- **Out of scope**: Source code files (`store_protocols.py`, `store_impl.py`,
  `session_message_repo.py`); other sections of the same doc file.

## Assumptions

1. The primary stale area is the SessionStore Protocol stub at lines 164–177.
2. `message_save` currently omits `tool_call_id` from its signature in the stub.
3. `message_list` return description currently omits `tool_call_id`.
4. The actual `scripts/db/store_protocols.py` (lines 144–155) is the source of truth;
   cross-check before editing to ensure the doc matches the real signature.
5. The column behavior is: stored when present for tool role messages; NULL for all other roles.

## Implementation

### Target file

`docs/90_shared_05_db_api_and_operations.md`

### Procedure

1. Read the current content of `docs/90_shared_05_db_api_and_operations.md` around lines 164–177.
2. Cross-check `scripts/db/store_protocols.py` lines 144–155 to confirm the real `message_save`
   and `message_list` signatures.
3. In the `message_save` Protocol stub, add `tool_call_id: str | None = None` as a parameter.
4. In the `message_list` return description, add `tool_call_id` to the list of returned fields.
5. Add (or confirm presence of) the clarifying note:
   "`tool_call_id` is stored when present (tool role messages); NULL for user/assistant/system roles"

### Method

Direct edit of the markdown file. Use the Edit tool with targeted `old_string` / `new_string`.

### Details

**Step 2 — Source of truth cross-check:**
```bash
grep -n "message_save\|message_list\|tool_call_id" scripts/db/store_protocols.py
```
Confirm the actual Protocol matches before editing the doc.

**Step 3 — `message_save` signature update:**

Current (approximate):
```python
def message_save(self, session_id, role, content, tool_calls) -> None: ...
```

Target:
```python
def message_save(self, session_id, role, content, tool_calls, tool_call_id: str | None = None) -> None: ...
```

**Step 4 — `message_list` return description update:**

Current (approximate):
```
- `message_list` returns `{role, content, tool_calls}` in `message_id ASC` order
```

Target:
```
- `message_list` returns `{role, content, tool_calls, tool_call_id}` in `message_id ASC` order
```

**Step 5 — Clarifying note (add if absent):**
```
- `tool_call_id` is `str | None`; always set for `tool` role messages, NULL for all other roles
```

If this note already exists verbatim, skip step 5.

## Validation plan

| Check | Command / Action | Expected result |
|---|---|---|
| `message_save` stub includes `tool_call_id` | `grep -n "message_save" docs/90_shared_05_db_api_and_operations.md` | Line contains `tool_call_id` parameter |
| `message_list` return lists `tool_call_id` | `grep -n "message_list" docs/90_shared_05_db_api_and_operations.md` | Line contains `tool_call_id` |
| Clarifying note present | `grep -n "tool_call_id" docs/90_shared_05_db_api_and_operations.md` | Note about "NULL for all other roles" is present |
| Doc matches real protocol | `grep -n "message_save\|tool_call_id" scripts/db/store_protocols.py` | Parameters align with the doc stub |
| No stale "unused" claim | `grep -in "tool_call_id.*unused\|unused.*tool_call_id" docs/90_shared_05_db_api_and_operations.md` | 0 results |
