## Goal

Replace the fixed `{role, content}` comparison in
`SessionPersister.persist_session_memories` with the
`unexpected_message_keys` helper (declared new in the sibling Row 01) and log only the
message role and the sorted unexpected key names — never the message content (REQ-002,
REQ-003; AC-2, AC-3).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- The loop is in `persist_session_memories`, iterating `self._ctx.conv.history` and
  building a `HistoryMessage(role, content)` list passed to `on_session_stop`
  (`scripts/agent/session_persister.py`, current lines ~184-196).
- The current warning is
  `"Unexpected keys in history message: %s — full message: %s"` with the whole message
  `m` (confirmed in Step 2); it therefore leaks tool-result text and tool-call arguments
  on the normal path (Plan Problem).
- The module logger is `agent.session_persister` (`logger = logging.getLogger(__name__)`),
  so tests attach with `caplog.at_level(logging.WARNING, logger="agent.session_persister")`.
- `unexpected_message_keys` returns an empty set for assistant-with-`tool_calls`, tool
  results, and messages carrying only authorized ephemeral keys (Row 01), so those
  ordinary messages emit no warning after the change (AC-2).
- The import target `agent.message_schema` has no back-dependency on this module, so a
  module-level import is safe and matches the file's existing `from agent.* import`
  imports.

## Design decisions

- Compute `unexpected = unexpected_message_keys(m)` and, when non-empty, log
  `"Unexpected keys in history message for role '%s': %s"` with `m.get("role")` and
  `sorted(unexpected)`. Role + sorted key names only, so no content or argument value can
  reach the log (REQ-003; Plan Decision 2).
- Keep the `HistoryMessage(...)` construction and the `on_session_stop` call and its
  `except (RuntimeError, sqlite3.Error, OSError)` handler byte-for-byte unchanged, so
  `on_session_stop` receives identical arguments and no exception behavior changes
  (REQ-002).

## Alternatives considered

- Formatting the keys inline with `", ".join(sorted(unexpected))`: rejected; passing the
  list to `%s` already avoids interpolating content, and `sorted()` gives a stable,
  deterministic log line for the test assertion.

## Implementation
### Target file
`scripts/agent/session_persister.py`

### Procedure
1. Add a module-level import of the helper.
2. Replace the per-message key check + warning inside `persist_session_memories`.

### Method
- Add after the existing `from agent.output_tags import OutputTag` import:
  ```python
  from agent.message_schema import unexpected_message_keys
  ```
- Inside `persist_session_memories`, replace the current per-message block
  ```python
  for m in self._ctx.conv.history:
      expected_keys = {"role", "content"}
      extra_keys = set(m.keys()) - expected_keys
      if extra_keys:
          logger.warning(
              "Unexpected keys in history message: %s — full message: %s",
              extra_keys,
              m,
          )
      history.append(
          HistoryMessage(role=m["role"], content=m.get("content") or "")
      )
  ```
  with
  ```python
  for m in self._ctx.conv.history:
      unexpected = unexpected_message_keys(dict(m))
      if unexpected:
          logger.warning(
              "Unexpected keys in history message for role '%s': %s",
              m.get("role"),
              sorted(unexpected),
          )
      history.append(
          HistoryMessage(role=m["role"], content=m.get("content") or "")
      )
  ```

### Details
- The new warning format string and arguments contain no reference to `m` beyond its
  `role`, so no message content, tool output, or argument value is logged (AC-3).
- `on_session_stop` is called with the same `history`, `session_id`, and `turn_id` as
  before; the `except` clause is unchanged (AC-2).
- Stale-reference marks: `unexpected_message_keys` is declared `(new)` in the earlier-seq
  Row 01 and resolved by the detector; nothing else new is introduced here.

## Compatibility considerations

- Additive at the call site: no signature, API, or persistence change. The generated
  reference document is unaffected (this module's public surface is unchanged).
- `tests/agent/test_repl.py` exercises the persister through the REPL shutdown path and
  must keep passing (Plan Reference Files).

## Security considerations

- Removes the data-exposure risk: whole tool-result text / tool-call arguments are no
  longer written to the log at session end on the normal path (Plan Reason for Change).
  The warning now names only the role and key names.

## Rollback considerations

- Revert the import and the loop body to the pre-change `{role, content}` comparison and
  full-message warning.

## Validation plan

- `uv run pytest tests/agent/test_session_persister.py -v` — the new `caplog` tests pass
  (they fail on the pre-change code).
- Static: `uv run ruff format`, `uv run ruff check`,
  `uv run mypy --no-namespace-packages scripts/`.
- Security/architecture: `uv run bandit -r scripts/ -c pyproject.toml -ll` and
  `PYTHONPATH=scripts uv run lint-imports` report no new findings.
- Baseline: `radon cc` keeps `persist_session_memories` at or below its current grade;
  `vulture` reports no finding in `scripts/agent/session_persister.py`.

## Completion criteria

- Assistant-with-`tool_calls`, tool results, and authorized-ephemeral messages emit no
  "unexpected keys" warning; `on_session_stop` receives the same arguments as before.
- A message with a key outside the allowed set logs a WARNING naming the role and the
  sorted key names and containing none of the message content (AC-3).

## Out of Scope

- Adding the helper (`scripts/agent/message_schema.py`, Row 01).
- The persister tests (Row 03) and helper tests (Row 04).
- Regenerating the reference document (Row 05).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Replace the key check + warning per Procedure | Completed | 20261105-104354 | 20261105-104354 | Applied; mypy forced dict(m) wrapper since conv.history items are LLMMessage TypedDict |
| 2 | Add or update tests per Validation plan | Completed | 20261105-104354 | 20261105-104354 | covered by Row 03 doc |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261105-104354 | 20261105-104354 | — |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261105-104354 | 20261105-104354 | N/A: no `docs/` |

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
- **Requirement ID**: `REQ-002` (use the helper, no warning for ordinary messages),
  `REQ-003` (warning names role + key names, no content), `AC-2`, `AC-3`
- **Source issue**: issues/done/20261031-180407_memlogleak001_memory-persist-logs-messages.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261104-114342_memlogleak001_memory-persist-logs-messages.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261105-070039
- **Related target files**: scripts/agent/session_persister.py
