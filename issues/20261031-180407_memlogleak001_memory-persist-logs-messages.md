# Session-end memory persistence logs full message content at WARNING for ordinary tool messages

## Priority
High

## Summary
`SessionPersister.persist_session_memories` checks every history message against the key set `{role, content}` and logs a WARNING that includes the complete message when any other key is present. Ordinary messages carry other keys: assistant messages with `tool_calls`, and every tool result with `tool_call_id`. So each session that used a tool writes the full text of its tool results and tool-call arguments to the log at session end, without secret masking. Fix the check so ordinary messages do not trigger it, and make the warning never include message content.

## Background
Found during an adversarial review (`python-code-review`) of the agent REPL runtime.
- Tool results are appended to history as `{"role": "tool", "tool_call_id": ..., "content": ...}` (`tool_runner._collect_tool_result_msgs`), and assistant tool-call messages carry `tool_calls` (`LLMTurnRunner.run`). The message schema whitelist (`ROLE_KEY_WHITELIST` in `message_schema.py`) already allows these keys per role.
- The session-end step converts each message to `HistoryMessage(role, content)`, so the extra keys are not used by the memory service; the check only produces the warning.
- Tool result content can contain whatever a tool read: file contents, configuration values, tokens, personal data. Argument masking (`masked_fields`) and `_mask_secrets` are applied to some audit and error paths, not to this log call.

## Problem
In `persist_session_memories`, for each message `m` the code computes `extra_keys = set(m.keys()) - {"role", "content"}` and, when non-empty, calls `logger.warning("Unexpected keys in history message: %s — full message: %s", extra_keys, m)`.

Reproduction (throwaway script, not committed): a three-message history (user text, assistant with `tool_calls`, tool result whose content was a made-up `DB_PASSWORD_VALUE=...` line), a stub memory service, and a handler attached to the module logger at WARNING. Observed: the tool result text appears verbatim in the captured log output. The agent's real log file and handlers were not used, so which log destination receives this logger in production is not verified.

Consequences:
- Sensitive tool output is copied into logs that have a different retention and access profile than the session database.
- The warning fires for normal, expected messages, so it is noise that hides the real anomalies it was written to flag.

## Reason for Change
Logging complete message content is a data-exposure risk, and it happens on the normal path of every tool-using session rather than on an error path. The check is also wrong on its own terms: it flags messages that the schema allows.

## Implementation Intent
Base the "unexpected keys" check on the schema's per-role allowed keys instead of a fixed pair, so only genuinely unexpected keys are reported. When a message is reported, log only its role and the unexpected key names, never its content. Keep the conversion to `HistoryMessage` and the memory service call unchanged.

## Target Files or Areas
- `scripts/agent/session_persister.py` (`SessionPersister.persist_session_memories`)
- `scripts/agent/message_schema.py` (`ROLE_KEY_WHITELIST`, read as the source of allowed keys)
- `tests/agent/` tests for `SessionPersister`

## Required Changes
- Replace the fixed `{role, content}` comparison with the allowed keys per role from the message schema (`ROLE_KEY_WHITELIST` in `message_schema.py` already includes `tool_calls`, `tool_call_id`, `name`, `importance` and `pinned`; the ephemeral keys `_ephemeral` and `_memory_injected` are handled separately by `validate_message` through the trusted sources, so decide explicitly whether to allow them here).
- Remove the message content from the warning text; report role and key names only.
- Add tests: a history with assistant `tool_calls` and tool results logs no warning and no content; a message with a truly unexpected key logs a warning that contains the key name but not the content.

## Constraints
- Do not change what is passed to `MemoryServices.on_session_stop`.
- Do not change the exceptions handled around the memory call in this issue.
- No message content, tool output, or argument value may appear in the new log text.

## Acceptance Criteria
- Persisting memories for a history that contains tool calls and tool results emits no "unexpected keys" warning.
- For a message with a key outside the allowed set, the warning names the role and key and contains none of the message content.
- The new tests fail on the current code and pass after the change.

## Testing Expectations
- Unit tests with `caplog` and a stub memory service, as described.
- Run the existing `SessionPersister` and message schema tests, `ruff`, and `mypy --no-namespace-packages` on the touched files.

## Documentation Impact
N/A: no documentation describes this internal warning today (not verified by a search of `docs/`; check before closing).

## Out of Scope
- Masking policy for other log call sites.
- The memory extraction rules and what gets stored.
- Handling of exceptions raised by the memory service.

## Dependencies
N/A: none. `issues/20261003-180341_diagmask001_diagnostic-guard-is-incomplete-secret-allowlist.md` concerns a different component (the diagnostic store's secret guard) and is independent.

## Unresolved Questions
- Which handlers and files receive the `agent.session_persister` logger in production (and who can read them): `Needs confirmation`. The priority assumes the agent log.
- Whether other call sites log whole history messages: not searched here.

## AI Implementation Instruction
Change only the key check and the warning text in `persist_session_memories`, plus tests. Do not log any message content, even truncated. Do not change the call into the memory service. Stop and report if the schema offers no single source for allowed keys per role.

## Traceability
- **Workflow phase**: python-code-review -> issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261031-180407
- **Related target files**: scripts/agent/session_persister.py, scripts/agent/message_schema.py
