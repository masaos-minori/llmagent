# Implementation Procedure

## Goal

Add a roundtrip command test verifying that an ID printed by `/session list` succeeds with both `/session load` and `/session delete` (`REQ-002` / `AC-2`).

## Scope

Add one test method to the existing `TestCmdSessionList` class in `tests/agent/commands/test_agent_cmd_session.py` (class starts at line 63). Test-only change.

## Assumptions

- `_make_cmd(sessions=..., session_id=...)` builds a `_SessionMixin` with a mocked session; `list_sessions.return_value` is set from `sessions`.
- `_session_list` reads `message_count` from each row (sibling procedure for `scripts/agent/commands/cmd_session.py`), so the mock rows must include it.
- `_load_session` can be patched via `patch.object(cmd, "_load_session")` (pattern already used in `TestCmdSessionLoad`, line 186); `delete_session` return value is settable on the mock.

## Design decisions

- Use a `session_id` distinct from the current session (`is_current=False`) so the listed row is a normal, loadable/deletable entry.
- Extract the ID from the captured `list` output (parse the printed table) rather than hard-coding, so the test truly exercises the list -> load/delete contract end to end.

## Alternatives considered

- Patching `list_sessions` to return a fixed id and asserting directly: weaker — does not confirm the id actually appears in the rendered output. The chosen approach parses the printed output.

## Implementation

### Target file

`tests/agent/commands/test_agent_cmd_session.py`

### Procedure

Add `test_list_roundtrip_load_and_delete`(new) to `TestCmdSessionList`:

1. Build `sessions` as a list with one dict: `{"session_id": <id>, "title": "Roundtrip", "created_at": "2026-01-01", "is_current": False, "message_count": 3}`.
2. `cmd = _make_cmd(session_id=<different current id>, sessions=sessions)`.
3. `await cmd._cmd_session("list")`; capture `out`; assert the printed id substring appears in `out`.
4. Parse the id from `out` (e.g. strip to digits) into `listed_id`(new).
5. `with patch.object(cmd, "_load_session") as mock_load:` run `await cmd._cmd_session(f"load {listed_id}")`; assert `mock_load.assert_called_once_with(listed_id)`.
6. Set `cmd._ctx.session.delete_session.return_value = True`; run `await cmd._cmd_session(f"delete {listed_id}")`; assert `"deleted"` is in the lowercased output.

### Method

Keep the method inside `TestCmdSessionList` (after `test_list_shows_no_title_when_title_is_empty_string`, around line 148). Signature `(self, capsys)`. Reuse the `@pytest.mark.asyncio` decorator and the existing `_make_cmd` helper.

### Details

- The mock row MUST include `message_count` (the production `_session_list` reads it); omitting it would raise `KeyError` once the column render lands.
- Parsing the id from output decouples the test from the exact table formatting while still requiring the id to be presentable.

## Compatibility considerations

Test-only; additive method. Does not modify existing tests. The `_make_cmd` helper already supports the needed kwargs.

## Security considerations

N/A: test-only.

## Rollback considerations

Remove the added test method.

## Validation plan

| Target/Module | Strategy | Command | Expected |
|---|---|---|---|
| `tests/agent/commands/test_agent_cmd_session.py` | Integration — listed id loads and deletes | `uv run pytest tests/agent/commands/test_agent_cmd_session.py` | Roundtrip test passes; full suite green |

## Completion criteria

The roundtrip test confirms an id printed by `/session list` both loads and deletes successfully.

## Out of scope

Source changes (`scripts/agent/commands/cmd_session.py`, `scripts/agent/session.py`, `scripts/agent/services/models.py`) are separate rows.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | N/A | — | — | test-only row |
| 2 | Add or update tests per Validation plan | Completed | 20261014-210723 | 20261014-210723 | roundtrip command test |
| 3 | Run validation sequence (`rules/toolchain.md`) | Completed | 20261014-210723 | 20261014-210723 | — |
| 4 | Update documentation | N/A | — | — | not in scope for this row |

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
- **Requirement ID**: `REQ-002` — a listed ID works with `/session load` and `/session delete`
- **Source issue**: `issues/20261014-150311_sess001_finalize-session-list-command.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261014-160933_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261014-171726
- **Related target files**: `tests/agent/commands/test_agent_cmd_session.py`