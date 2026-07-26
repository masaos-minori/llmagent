# Implementation procedure: scripts/agent/startup.py + scripts/agent/services/session_restore.py

## Goal

Route the two bulk `ctx.conv.history = [...]` reassignment sites — startup's
initial-history construction and session-restore's history rebuild — through
`ConversationState.replace_history()`, as defense in depth against tampered or
corrupted persisted data surfacing a reserved/ephemeral key.

## Scope

- In scope:
  - `scripts/agent/startup.py`: `ctx.conv.history = [{"role": "system",
    "content": initial_prompt}]` (currently L572).
  - `scripts/agent/services/session_restore.py::restore_session()`: both
    `ctx.conv.history = system_msgs + non_system` and `ctx.conv.history =
    messages` branches (currently L39-44).
- Out of scope: `ctx.conv.system_prompt_content` assignment in `startup.py`
  (not a history mutation); `ctx.session.fetch_messages()` / DB read logic in
  `session_restore.py`; `reset_session_stats()`.

These two files are grouped into one procedure doc because they are the
plan's other explicitly paired item (Implementation step 6) — both are
single-call-site *bulk reassignment* of `ctx.conv.history` from either a
freshly-constructed list (`startup.py`) or persisted DB rows
(`session_restore.py`), and both map onto the exact same new primitive,
`replace_history()`, for the same defense-in-depth reason.

## Assumptions

- `startup.py`'s message is a single literal `{"role": "system", "content":
  initial_prompt}` — confirmed, `scripts/agent/startup.py:572` — already
  satisfies `ROLE_KEY_WHITELIST["system"]`; no ephemeral keys, no `source`
  needed.
- `session_restore.py`'s `messages` come from `ctx.session.fetch_messages(session_id)`
  — i.e. rows read back from the SQLite `messages` table — confirmed,
  `scripts/agent/services/session_restore.py:31-44`. The plan's threat model
  here (Design point 5) is a *tampered/corrupted* DB row surfacing an
  ephemeral key, not the primary LLM-influenced-content threat model that
  motivates the rest of this plan; this is explicitly a defense-in-depth
  addition, not closing an active gap.
- `session_restore.py` has two branches: `system_msgs + non_system` (when
  `ctx.conv.system_prompt_content` is set) and plain `messages` (otherwise) —
  both need to go through `replace_history()`.

## Design decisions

- `startup.py`: replace `ctx.conv.history = [{"role": "system", "content":
  initial_prompt}]` with `ctx.conv.replace_history([{"role": "system",
  "content": initial_prompt}])`, no `source`.
- `session_restore.py`: replace both `ctx.conv.history = system_msgs +
  non_system` and `ctx.conv.history = messages` with
  `ctx.conv.replace_history(system_msgs + non_system)` and
  `ctx.conv.replace_history(messages)` respectively, no `source`.
- `replace_history()` (not `extend_messages()`) is correct for both sites
  since both are *full replacements* of `ctx.conv.history`, not additions to
  existing history — matching the semantics `replace_history()` was designed
  for (per the `context.py` procedure doc: clear then extend).
- If any individual persisted row in `session_restore.py`'s `messages` fails
  validation (e.g. a corrupted/tampered row with an unauthorized reserved
  key), `replace_history()`'s per-message sanitize-and-log behavior means that
  row is sanitized or dropped rather than the whole restore failing — this is
  the intended defense-in-depth behavior (log-visible, non-fatal).

## Alternatives considered

- **Leave `session_restore.py` unrouted since the plan's primary threat model
  is live-turn LLM content, not persisted rows.** Rejected: the plan
  explicitly includes this site (Design point 5) as defense-in-depth; the
  cost of routing it is one line per branch with no behavior change for
  well-formed data, so there is no reason to skip it.
- **Use `extend_messages()` after manually clearing `ctx.conv.history`.**
  Rejected: functionally identical to `replace_history()` but requires two
  statements instead of one and duplicates logic `replace_history()` already
  encapsulates.

## Implementation

### Target file

`scripts/agent/startup.py` and `scripts/agent/services/session_restore.py`

### Procedure

1. `startup.py` (currently L572): replace `ctx.conv.history = [{"role":
   "system", "content": initial_prompt}]` with `ctx.conv.replace_history([
   {"role": "system", "content": initial_prompt}])`.
2. `session_restore.py::restore_session()` (currently L39-44): replace
   `ctx.conv.history = system_msgs + non_system` with
   `ctx.conv.replace_history(system_msgs + non_system)` in the `if
   ctx.conv.system_prompt_content:` branch, and replace `ctx.conv.history =
   messages` with `ctx.conv.replace_history(messages)` in the `else` branch.

### Method

Two independent single-statement substitutions in two different files; no
change to `ctx.conv.system_prompt_content` assignment order in `startup.py`
(the assignment at the line immediately before L572 stays before the
`replace_history()` call), and no change to `session_restore.py`'s
`system_msgs`/`non_system` construction (L36-40) or the subsequent
`ctx.session.session_id = session_id` / `reset_session_stats(ctx)` /
`logger.info(...)` calls (L42-45).

### Details

- `startup.py`'s call site is inside a larger startup function that also sets
  `ctx.conv.memory_disabled` / writes warnings on memory-injection failure
  (L561-570) — none of that logic changes; only the final history assignment
  line is touched.
- `session_restore.py` already has `from agent.context import AgentContext`
  under `TYPE_CHECKING` (L20) — no new import needed since `ctx.conv` is
  accessed via the existing `ctx: AgentContext` parameter.

## Compatibility considerations

- No behavior change for well-formed data in either file: `startup.py`'s
  single system message and `session_restore.py`'s persisted messages
  (assumed well-formed under normal operation) already satisfy
  `ROLE_KEY_WHITELIST`, so validation always succeeds and stored content is
  unchanged.
- `SessionRestoreResult(session_id=session_id, n_messages=len(messages))`
  (session_restore.py's return value) reports `len(messages)` from the
  *original* fetched list, not the post-sanitization stored list — if
  `replace_history()` ever drops a malformed message, `n_messages` would
  overstate the actual stored count by the dropped count. This is a minor
  reporting inconsistency introduced only in the rare tampered-row case;
  acceptable given this is a defense-in-depth path, but worth a one-line
  comment at the call site.

## Security considerations

- `session_restore.py`: closes a defense-in-depth gap against corrupted or
  tampered persisted rows surfacing a reserved/ephemeral key on session
  restore (e.g. if a message was written directly to the DB outside the
  normal `ctx.session.save()`/`save_many()` path, or a future schema/migration
  bug leaks an internal key into a stored row).
- `startup.py`: no meaningful new security value on its own (the single
  literal message is always well-formed), but closes the audit gap and keeps
  every `ctx.conv.history` mutation flowing through one path, per the
  requirement's stated goal.

## Rollback considerations

- Both substitutions are independent, single-statement reverts with no data
  migration; stored message shape is unchanged for well-formed input in both
  files.

## Validation plan

- Extend `tests/test_startup.py` with a regression test confirming the
  initial system-prompt message still lands in `ctx.conv.history` unchanged
  after routing through `replace_history()`.
- Extend `tests/test_session_restore.py` with a regression test confirming
  both branches (`system_prompt_content` set / unset) still populate
  `ctx.conv.history` unchanged for well-formed persisted messages, plus one
  new test: a persisted row carrying an unauthorized reserved key (e.g. a
  forged `_memory_injected` with no matching `source` semantics available at
  restore time) is sanitized/dropped rather than crashing `restore_session()`.
- `pytest tests/test_startup.py tests/test_session_restore.py -q` — all pass.
- `pytest -k "startup or session_restore" -q` — all pass (per plan's
  Regression tests row); note this will also match unrelated pre-existing
  tests such as `test_startup_consistency.py`, `test_startup_routing_drift.py`,
  `test_startup_validation_pipeline.py`, `test_eventbus_startup.py` — confirm
  none of those regress.
- `ruff check scripts/agent/startup.py scripts/agent/services/session_restore.py`,
  `mypy` same — no new errors.

## Out of scope

- `ctx.session.fetch_messages()` / DB read implementation.
- `reset_session_stats()`.
- Any change to how `SessionRestoreResult.n_messages` is computed (noted as a
  minor pre-existing-pattern inconsistency above, not fixed in this pass).

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260726-093008_plan.md
- Source implementation procedure: N/A
- Generated at: 20260726-101136
- Related target files: startup.py, session_restore.py
