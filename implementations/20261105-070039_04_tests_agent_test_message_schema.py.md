## Goal

Add unit tests for the new public `unexpected_message_keys` helper in
`tests/agent/test_message_schema.py` (REQ-004; AC-1, AC-4): assert the helper returns
an empty set for every allowed message shape and the offending key name otherwise,
including the unknown-role fallback to `{"role", "content"}`. The tests MUST fail on the
pre-change code (the helper does not exist) and pass after it is added (Row 01).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- `tests/agent/test_message_schema.py` already imports `ROLE_KEY_WHITELIST`,
  `TRUSTED_SOURCES`, `get_allowed_ephemeral_keys`, `is_trusted_source`, and
  `validate_message` from `agent.message_schema`, and has four test classes
  (`TestValidateMessageRequiredFields`, plus three more).
- History message shapes mirror `scripts/shared/types.py` `LLMMessage`: `role` is one of
  `user` / `assistant` / `tool` / `system`; assistant messages may carry `tool_calls`;
  tool messages carry `tool_call_id` and `name`; ephemeral keys are `_ephemeral` /
  `_memory_injected`.
- The pre-change code has no `unexpected_message_keys`, so importing it fails the test
  collection (AC-4).

## Design decisions

- Add a new class `TestUnexpectedMessageKeys` (new) with one test per allowed shape plus the
  off-whitelist and unknown-role cases, importing `unexpected_message_keys` in the same
  import block as the other names.
- Reuse the concrete message dicts already exercised by `TestValidateMessageRequiredFields`
  (valid system/user/assistant-with-tool_calls) so coverage overlaps the existing
  validation tests.

## Alternatives considered

- One parametrized test over all shapes: works, but separate methods give clearer failure
  messages and match the file's existing per-method style.

## Implementation
### Target file
`tests/agent/test_message_schema.py`

### Procedure
1. Add `unexpected_message_keys` to the import from `agent.message_schema`.
2. Append a `TestUnexpectedMessageKeys` (new) class with seven tests.

### Method
- Update the import block to include `unexpected_message_keys`.
- Append:
  ```python
  class TestUnexpectedMessageKeys:
      def test_user_message_has_no_unexpected_keys(self) -> None:
          assert unexpected_message_keys({"role": "user", "content": "hello"}) == set()

      def test_assistant_with_tool_calls_has_no_unexpected_keys(self) -> None:
          msg = {
              "role": "assistant",
              "content": "ok",
              "tool_calls": [
                  {"id": "tc1", "function": {"name": "test", "arguments": "{}"}}
              ],
          }
          assert unexpected_message_keys(msg) == set()

      def test_tool_result_has_no_unexpected_keys(self) -> None:
          msg = {"role": "tool", "content": "result", "tool_call_id": "tc1", "name": "test"}
          assert unexpected_message_keys(msg) == set()

      def test_system_message_has_no_unexpected_keys(self) -> None:
          assert unexpected_message_keys({"role": "system", "content": "be nice"}) == set()

      def test_authorized_ephemeral_key_is_not_unexpected(self) -> None:
          msg = {"role": "system", "content": "x", "_ephemeral": True}
          assert unexpected_message_keys(msg) == set()

      def test_off_whitelist_key_is_reported(self) -> None:
          assert unexpected_message_keys(
              {"role": "user", "content": "hi", "rogue_key": "v"}
          ) == {"rogue_key"}

      def test_unknown_role_falls_back_to_role_content(self) -> None:
          # An unknown role falls back to {'role', 'content'}; an extra key is reported.
          assert unexpected_message_keys(
              {"role": "unknown", "content": "hi", "rogue_key": "v"}
          ) == {"rogue_key"}
  ```

### Details
- The `test_authorized_ephemeral_key_is_not_unexpected` (new) case pins the Plan Decision
  1(a) requirement that authorized ephemeral keys are NOT flagged (whitelist-only would
  fail this).
- "rogue_key" is a literal dict key name, not a Python symbol; it is written as a quoted
  string key, so it is not a stale-reference target.
- Stale-reference marks: `unexpected_message_keys` is declared `(new)` in the earlier-seq
  Row 01 and resolved by the detector; the new test class and method names are created
  here, so they are marked `(new)`.

## Compatibility considerations

- Adds tests only; does not modify any existing test or production code.
- Regression surface includes `tests/agent/test_message_schema.py` itself and, through
  the helper's consumer, `tests/agent/test_session_persister.py` (Row 03).

## Security considerations

- The off-whitelist case pins the data-exposure fix at the schema level: any key outside
  the allowed set is detected, which is what lets the persister log only key names.

## Rollback considerations

- Revert the import addition and the `TestUnexpectedMessageKeys` (new) class.

## Validation plan

- `uv run pytest tests/agent/test_message_schema.py -v` — the new tests pass after Row 01
  and fail on the pre-change code (AC-4); existing tests still pass.
- Static: `uv run ruff format`, `uv run ruff check`,
  `uv run mypy --no-namespace-packages scripts/ tests/eventbus`.

## Completion criteria

- The helper returns an empty set for user, assistant-with-`tool_calls`, tool result,
  system, and authorized-ephemeral messages, and the offending key name otherwise; the
  unknown role falls back to `{"role", "content"}`.
- The new tests fail on the pre-change code and pass after it (AC-4).

## Out of Scope

- Adding the helper (`scripts/agent/message_schema.py`, Row 01).
- The persister change (`scripts/agent/session_persister.py`, Row 02) and its tests
  (Row 03).
- Regenerating the reference document (Row 05).

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
- **Requirement ID**: `REQ-004` (helper unit tests, fail on pre-change code), `AC-1`, `AC-4`
- **Source issue**: issues/done/20261031-180407_memlogleak001_memory-persist-logs-messages.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261104-114342_memlogleak001_memory-persist-logs-messages.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261105-070039
- **Related target files**: tests/agent/test_message_schema.py
