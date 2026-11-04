## Goal

Add `caplog` tests to `TestPersistSessionMemoriesGate` in
`tests/agent/test_session_persister.py` (REQ-004; AC-2, AC-3, AC-4): a history of
tool-call, tool-result, and ephemeral messages logs no warning and no content; and a
message with a truly unexpected key logs the role and the key name but not the content.
The tests MUST fail on the pre-change code and pass after `session_persister.py` is
changed (Row 02).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- `TestPersistSessionMemoriesGate` already exists in the file with the pattern
  ```python
  ctx = _ctx(1)
  ctx.services = MagicMock()
  ctx.services.memory.on_session_stop = AsyncMock()
  persister = SessionPersister(ctx, MagicMock(), MagicMock())
  await persister.persist_session_memories()
  ```
  (`_ctx` builds a `MagicMock` ctx with `ctx.conv.history = []`; `on_session_stop` is an
  `AsyncMock`).
- The module logger is `agent.session_persister`; tests attach with
  `caplog.at_level(logging.WARNING, logger="agent.session_persister")`.
- `logging`, `MagicMock`, `AsyncMock`, `pytest`, and `SessionPersister` are already
  imported at the top of the file.
- The pre-change loop uses `expected_keys = {"role", "content"}`, so assistant
  `tool_calls`, tool `tool_call_id`, and `_ephemeral` all count as "extra" and trigger a
  full-message WARNING; after Row 02 they are allowed and produce none.

## Design decisions

- Add two async tests inside `TestPersistSessionMemoriesGate`, each populating
  `ctx.conv.history` before calling `persist_session_memories`, so the key-check loop
  runs against real history entries.
- Use a made-up secret-like string as a tool-result / message content and assert it is
  absent from `caplog.text` after the change (and present on the pre-change code, which
  is why the test fails before the fix).

## Alternatives considered

- Asserting `caplog.text` contains no `"Unexpected keys"` substring vs. counting WARNING
  records: both work since `persist_session_memories` has a single warning path; the
  WARNING-count assertion is stricter and chosen.

## Implementation
### Target file
`tests/agent/test_session_persister.py`

### Procedure
1. Add two async tests to `TestPersistSessionMemoriesGate`:
   - `test_tool_and_ephemeral_history_logs_no_warning_and_no_content` (new)
   - `test_unexpected_key_logs_role_and_key_without_content` (new)

### Method
- **ordinary tool/ephemeral history logs nothing**: build history with a user message,
  an assistant message carrying `tool_calls`, a tool result whose `content` is a
  made-up secret line, and an ephemeral system message; call
  `persist_session_memories` under `caplog.at_level(logging.WARNING, ...)`.
  - Assert no `WARNING` record is captured.
  - Assert the secret string is not in `caplog.text`.
- **unexpected key logs role + key name, not content**: add a second user message with a
  genuinely unexpected key ("rogue_key") alongside a secret `content`; run under
  `caplog.at_level(logging.WARNING, ...)`.
  - Assert `caplog.text` contains the role (`user`) and the key name ("rogue_key").
  - Assert the secret string is not in `caplog.text`.

### Details
- Secret value (reuse in both tests): `"sk-live-deadbeefcafe"`.
- Ordinary-history `conv.history`:
  - `{"role": "user", "content": "what is the weather?"}`
  - `{"role": "assistant", "content": "checking", "tool_calls": [{"id": "tc1", "function": {"name": "weather", "arguments": "{}"}}]}`
  - `{"role": "tool", "content": secret, "tool_call_id": "tc1"}`
  - `{"role": "system", "content": "produce a final answer", "_ephemeral": True}`
- Unexpected-key `conv.history`:
  - `{"role": "user", "content": "hello"}`
  - `{"role": "user", "content": secret, "rogue_key": "value"}`
- Pre-change behavior these tests catch: the tool/ephemeral history produces WARNING
  records and logs `secret` (the tool result), and the unexpected-key message logs its
  whole dict including `secret`; both assertions therefore fail before Row 02 and pass
  after it (AC-4).
- Stale-reference marks: the two new test method names are created here, so they are
  marked `(new)`; all other referenced symbols (`_ctx`, `SessionPersister`,
  `on_session_stop`) already exist.

## Compatibility considerations

- Adds tests only; does not modify any existing test or the production code.
- Regression surface includes `tests/agent/test_repl.py` (persister via REPL shutdown)
  and `tests/agent/test_ephemeral_filtering_security.py` (Plan Tests).

## Security considerations

- The unexpected-key test pins the data-exposure fix: the captured log must contain the
  key name but never the secret content, even if the persister is later changed to
  interpolate the message again.

## Rollback considerations

- Revert the two added tests.

## Validation plan

- `uv run pytest tests/agent/test_session_persister.py -v` — the two new tests pass after
  Row 02 and fail on the pre-change code (AC-4); existing gate tests still pass.
- Regression: `uv run pytest tests/agent/test_repl.py tests/agent/test_ephemeral_filtering_security.py -v`.
- Static: `uv run ruff format`, `uv run ruff check`,
  `uv run mypy --no-namespace-packages scripts/ tests/eventbus`.

## Completion criteria

- Tool-call, tool-result, and authorized-ephemeral history emit no WARNING and no
  content; a message with a key outside the allowed set logs the role and the sorted key
  names without any content (AC-2, AC-3).
- The new tests fail on the pre-change code and pass after it (AC-4).

## Out of Scope

- Adding the helper (`scripts/agent/message_schema.py`, Row 01).
- The persister change (`scripts/agent/session_persister.py`, Row 02).
- The helper tests (Row 04) and reference regeneration (Row 05).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | this row |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: no `docs/` |

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
- **Requirement ID**: `REQ-004` (persister `caplog` tests, fail on pre-change code),
  `AC-2`, `AC-3`
- **Source issue**: issues/done/20261031-180407_memlogleak001_memory-persist-logs-messages.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261104-114342_memlogleak001_memory-persist-logs-messages.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261105-070039
- **Related target files**: tests/agent/test_session_persister.py
