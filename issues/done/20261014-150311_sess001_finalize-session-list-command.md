# Finalize session list command: add message count, roundtrip test, docs

## Priority
Medium

## Summary
Close the remaining gaps in the `/session list` slash command so it fully matches its
specification: add the per-session **message count** to the output, add a roundtrip test
that an ID printed by `/session list` can be used with `/session load` and `/session
delete`, and update the affected documentation.

Note: the command already exists and works. This issue finalizes it rather than building
it from scratch (see Adversarial Validation Findings).

## Background
The `/session list [n]` command lists recent sessions via `AgentSession.list_sessions()`,
queried through `SQLiteHelper("session")` against `session.sqlite`. It is dispatched in
`scripts/agent/commands/cmd_session.py` (`_cmd_session`, `sub == "list"` ->
`_session_list`) and its help text already advertises `list [n]`.

The originating requirement specified five items:
- H-1-1 production-path listing returning newest-first with ID, title, created date, and
  message count (no `SQLiteSessionStore`)
- H-1-2 a `list [n]` subcommand (default 20, mark the current session)
- H-1-3 `list` in the `/session` help text
- H-1-4 a test that a listed ID works with `/session load` and `/session delete`
- H-1-5 doc updates (agent_07_07 Session Category, agent_04_03 session lifecycle)

Investigation confirms H-1-2 and H-1-3 are done, and the stated completion condition
(find past session IDs within the REPL and use them for `load` and `delete`) is already
met. Only the message-count column (H-1-1), the roundtrip test (H-1-4), and full doc
coverage (H-1-5) remain.

## Problem
The `/session list` output omits the message count that the specification requires, so a
user cannot gauge a session's size from the REPL before loading it. In addition, no test
verifies the list -> load/delete contract, and the docs under-document the data
subcommands (they currently enumerate only the maintenance subcommands).

## Reason for Change
Without the message count, triaging which sessions are large before loading is guesswork.
Without a roundtrip test, a regression in the list -> load/delete contract would go
undetected. The docs currently list only maintenance subcommands, so readers miss the
data subcommands (`list`, `load`, `rename`, `delete`).

## Implementation Intent
Extend the existing `list_sessions()` result and `_session_list()` display to include a
per-session message count, computed with a `LEFT JOIN` on the `messages` table grouped by
`session_id`. Preserve newest-first ordering, the `is_current` marker, the default limit
of 20, and title truncation. Add a roundtrip test. Update the docs. Do not reintroduce
`SQLiteSessionStore`.

`_session_list` renders rows via the frozen `SessionRow` dataclass in
`scripts/agent/services/models.py`; `message_count` MUST flow through that dataclass
(which has a single construction site in `_session_list`) rather than being read ad hoc in
the render loop.

## Target Files or Areas
- `scripts/agent/session.py` (`list_sessions`)
- `scripts/agent/commands/cmd_session.py` (`_session_list`)
- `tests/agent/test_agent_session.py`
- `tests/agent/commands/test_agent_cmd_session.py`
- `docs/23_agent/agent_07_07_cli-and-commands-slash-commands-session-mcp.md` (Session Category)
- `docs/23_agent/agent_04_03_state-and-persistence-platform-databases.md` (session lifecycle)
- `scripts/db/schema_sql.py` (sessions/messages schema reference)

## Required Changes
- Add `message_count` to each row returned by `AgentSession.list_sessions()` via a
  `LEFT JOIN messages ... GROUP BY session_id`.
- Extend the `SessionRow` dataclass (`scripts/agent/services/models.py`) with a
  `message_count` field and pass it through in `_session_list`, then render it as a new
  column in the `/session list` table.
- Add a roundtrip test: create sessions, run `/session list`, take a printed ID, and
  assert `/session load` and `/session delete` both succeed for it.
- Update agent_07_07 Session Category to list the data subcommands (`list`, `load`,
  `rename`, `delete`) alongside the maintenance subcommands.
- Verify the agent_04_03 session lifecycle diagram reference and update or correct it.
  NOTE (from adversarial validation): `agent_04_03` has no mermaid diagram and no
  session-lifecycle section; the authoritative lifecycle is a text flow diagram in
  `agent_04_01` (lines 34-42). Confirm with the requester whether the agent_04_03 doc
  update is dropped (nothing to correct) or whether lifecycle coverage should be added to
  agent_04_03 explicitly. Do not invent a diagram.

## Constraints
- Do not reintroduce `SQLiteSessionStore` (removed under SHARED-002).
- Use a `LEFT JOIN` so sessions with zero messages still appear with count 0.
- Keep newest-first ordering; the current `ORDER BY session_id DESC` relies on
  `session_id` being a monotonic AUTOINCREMENT key — flag if a chronological sort is
  preferred.
- Preserve the default limit of 20, the current-session marker, and title truncation.
- Guard non-positive limits: SQLite treats `LIMIT -1` as "return all rows", so
  `/session list -1` would currently list every session.

## Acceptance Criteria
- `/session list` shows ID, title, created date, and message count.
- An ID printed by `/session list` can be used with `/session load` and `/session delete`.
- Existing behavior (default 20, current-session marker, title display) is unchanged.
- The docs reflect the data subcommands.

## Testing Expectations
- Unit test for `list_sessions()` including the message count.
- Roundtrip command test in `test_agent_cmd_session.py`.
- Full command test suite passes; type and lint checks clean.

## Documentation Impact
Yes. Document intent and responsibility boundaries, not implementation detail:
- agent_07_07 Session Category: add the data subcommands.
- agent_04_03: confirm whether a session lifecycle diagram exists; update or correct the
  reference.

## Out of Scope
Reimplementing the command; changing `/session load` or `/session delete` semantics;
adding columns beyond the message count.

## Dependencies
Context only: SHARED-002 (removal of unused code) is why `SQLiteSessionStore` must not be
reintroduced. No blocking dependencies.

## Unresolved Questions
- Title column name is `title` (confirmed in `scripts/db/schema_sql.py`). Message count is
  `COUNT(m.message_id)` over a `LEFT JOIN messages m ON m.session_id = s.session_id`,
  grouped by `s.session_id`.
- Ordering: RESOLVED by repository evidence. `sessions.session_id` is
  `INTEGER PRIMARY KEY AUTOINCREMENT` (`scripts/db/schema_sql.py`), so `ORDER BY
  session_id DESC` is strictly newest-first; no chronological sort is needed. Keep the
  existing ordering.
- agent_04_03: RESOLVED by repository evidence. `agent_04_03` contains no mermaid diagram
  and no session-lifecycle section at all (its only `state` token is a frontmatter tag;
  grep for `lifecycle` / `session lifecycle` finds nothing in that file). The authoritative
  session lifecycle lives in `docs/23_agent/agent_04_01_state-and-persistence-state-model.md`
  (a text flow diagram, lines 34-42). So the H-1-5 reference to "agent_04_03 session
  lifecycle" points at the wrong file. Decision needed: drop the agent_04_03 doc update
  (nothing to correct — its lifecycle content is absent) or add lifecycle coverage to
  agent_04_03 explicitly. See the open question in the issue body.

## AI Implementation Instruction
Make minimal changes to add the message count and close the test/doc gaps. Preserve the
existing command behavior (default limit 20, current-session marker, title truncation,
newest-first ordering). Do not reintroduce `SQLiteSessionStore`. If agent_04_03 has no
session lifecycle diagram, report that rather than inventing one. Keep the diff scoped to
the files in Target Files or Areas.

## Adversarial Validation Findings
Validated against current source (scripts/, tests/, docs/, schema). Result: the command
exists and the completion condition is met; remaining work is scoped below.

- Current state vs. spec:
  - H-1-1 production path, newest-first, ID/title/created: implemented via
    `AgentSession.list_sessions()` (`scripts/agent/session.py:165`) using
    `SQLiteHelper("session")` on `session.sqlite`. Message count: MISSING.
  - H-1-2 `list [n]` subcommand (default 20, mark current): implemented and unit-tested.
  - H-1-3 `list` in `/session` help text: present in `command_defs_list.py`.
  - H-1-4 roundtrip test (listed ID -> load/delete): NOT present (command is unit-tested
    but nothing asserts a listed ID loads/deletes successfully).
  - H-1-5 docs: agent_07_07 lists only maintenance subcommands (data subcommands
    unmentioned); agent_04_03 has no mermaid lifecycle diagram (reference mismatch).
  - agent_04_03 lifecycle finding (deeper pass): `agent_04_03` has no mermaid diagram and
    no session-lifecycle section (only a frontmatter `state` tag; grep for `lifecycle` /
    `session lifecycle` finds nothing). The authoritative session lifecycle is a text flow
    diagram in `agent_04_01` (lines 34-42). The H-1-5 "agent_04_03 session lifecycle"
    target is therefore misdirected — the lifecycle doc exists and is current in
    agent_04_01, not agent_04_03.
- Edge cases found (added as Constraints/Unresolved Questions):
  - `/session list -1` (or any non-positive) hits SQLite `LIMIT -1` = return all rows.
  - Ordering assumes `session_id` monotonicity (AUTOINCREMENT); a chronological sort is
    safer but may tie on `created_at`.
  - Zero-message sessions must still appear -> require `LEFT JOIN`, not `INNER JOIN`.
- Schema confirmation: `sessions(session_id, created_at, title)`; `messages(message_id,
  session_id, role, content, ...)`, FK `ON DELETE CASCADE`. Title column is `title`.
- Blast radius of `AgentSession.list_sessions()`: single production caller
  (`_session_list` in `scripts/agent/commands/cmd_session.py`); the only constructor of the
  intermediate `SessionRow` dataclass (`scripts/agent/services/models.py`) is also in
  `_session_list`; tests mock it or call it against a real in-memory DB. Adding a
  `message_count` key is additive and backward-compatible with existing callers.
- Design constraint surfaced: `_session_list` maps each dict to a frozen `SessionRow`
  dataclass before rendering, so `message_count` must flow through that dataclass (extend
  `SessionRow`, which has a single construction site) rather than being read ad hoc.
- Architecture: `lint-imports` reports 6 contracts, 0 broken; the change adds no new
  imports and stays within the `agent` layer (direct `SQLiteHelper("session")` read), so no
  import-boundary risk.

## Traceability
- **Workflow phase**: issue-creator (with adversarial validation)
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261014-150311
- **Related target files**: scripts/agent/session.py, scripts/agent/commands/cmd_session.py, tests/agent/test_agent_session.py, tests/agent/commands/test_agent_cmd_session.py, docs/23_agent/agent_07_07_cli-and-commands-slash-commands-session-mcp.md, docs/23_agent/agent_04_03_state-and-persistence-platform-databases.md
