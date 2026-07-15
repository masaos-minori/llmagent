# Implementation Procedure: test_command_def_sync.py

## Goal

Update `INTENTIONAL_HANDLER_EXCLUSIONS` to drop `_cmd_db_rag` and `_cmd_db_session`,
since both handlers cease to exist once `cmd_db.py` is deleted (they were previously
listed as intentional sub-dispatch helpers absent from `_COMMANDS`; now there is
nothing left to exclude for them).

## Scope

### In scope
- Remove `"_cmd_db_rag"` and `"_cmd_db_session"` from the `INTENTIONAL_HANDLER_EXCLUSIONS`
  frozenset (current lines 19-32).

### Out of scope
- The remaining exclusions (`_cmd_mcp_status`, `_cmd_mdq_get`, `_cmd_mdq_grep`,
  `_cmd_mdq_index`, `_cmd_mdq_outline`, `_cmd_mdq_refresh`, `_cmd_mdq_search`,
  `_cmd_mdq_status`) — untouched, unrelated to this plan.
- Every other test function in this file (`test_every_commanddef_has_handler`,
  `test_every_handler_has_commanddef`, `test_commanddef_names_are_unique`,
  `test_commanddef_handlers_are_unique`, `test_help_output_mentions_all_command_names`,
  `test_get_handler_exact_match`, `test_get_handler_prefix_command`,
  `test_dispatch_help_returns_true`, `test_dispatch_unknown_returns_false`,
  `test_dispatch_empty_returns_false`, `test_all_commands_have_nonempty_help`,
  `test_all_command_names_start_with_slash`) — unchanged; they already operate
  generically over `_COMMANDS`/`CommandRegistry` and require no per-command edits.

## Assumptions

- `test_get_handler_prefix_command` (current lines 106-112) asserts on `/memory`
  specifically (not `/db` or `/set`), so it needs no change.
- `test_get_handler_exact_match` (current lines 98-103) asserts on `/reload`
  specifically, so it needs no change.
- Neither `_cmd_db_rag` nor `_cmd_db_session` currently exists in the codebase as a
  callable method name that `test_every_handler_has_commanddef`'s `dir(registry)`
  scan would find (verified: reading the current `cmd_db.py` shows methods named
  `_cmd_db` and `_cmd_db_session` — note `_cmd_db_session` **does** currently exist
  as a method, it is `_cmd_db_rag` that is already gone per the earlier RAG-removal
  change). Once `cmd_db.py` is deleted entirely by this plan, both names cease to
  exist as registry methods, making both exclusions dead entries that should be
  removed rather than left as no-op placeholders (a stale exclusion for a
  nonexistent method is harmless functionally but misleading to future readers).

## Implementation

### Target file

`tests/test_command_def_sync.py`

### Procedure

1. Change:
   ```python
   INTENTIONAL_HANDLER_EXCLUSIONS: frozenset[str] = frozenset(
       {
           "_cmd_db_rag",
           "_cmd_db_session",
           "_cmd_mcp_status",
           "_cmd_mdq_get",
           "_cmd_mdq_grep",
           "_cmd_mdq_index",
           "_cmd_mdq_outline",
           "_cmd_mdq_refresh",
           "_cmd_mdq_search",
           "_cmd_mdq_status",
       }
   )
   ```
   to:
   ```python
   INTENTIONAL_HANDLER_EXCLUSIONS: frozenset[str] = frozenset(
       {
           "_cmd_mcp_status",
           "_cmd_mdq_get",
           "_cmd_mdq_grep",
           "_cmd_mdq_index",
           "_cmd_mdq_outline",
           "_cmd_mdq_refresh",
           "_cmd_mdq_search",
           "_cmd_mdq_status",
       }
   )
   ```

### Method

Single-set-literal edit removing two string entries. No other code path changes.

### Details

- Sequence this edit in the same change-set as `cmd_db.py`'s deletion. If the
  exclusion removal lands before `cmd_db.py` is deleted, `test_every_handler_has_commanddef`
  would still pass (since `_cmd_db_rag` doesn't exist as a method and `_cmd_db_session`
  would newly surface as an "undefined handler" — an existing method with no
  `CommandDef`), which is the correct pre-deletion-detection behavior: it should fail
  loudly if `cmd_db.py` still exists but the exclusion has been prematurely removed,
  reinforcing that the two changes belong together.

## Validation plan

- `uv run pytest tests/test_command_def_sync.py -v` — all pass once `cmd_db.py` is
  deleted (so `_cmd_db_session` no longer exists as a `dir(registry)` hit needing
  exclusion).
- If run with `cmd_db.py` NOT yet deleted but this exclusion already removed:
  `test_every_handler_has_commanddef` should fail, correctly flagging the
  out-of-sequence change — confirms the test's fail-fast value.
- `uv run pytest tests/ -k "command_def"` — no new failures.
