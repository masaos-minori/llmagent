# Implementation procedure: scripts/agent/mode_classification.py + scripts/agent/commands/cmd_skill.py

## Goal

Route the two ephemeral-system-message append sites in
`mode_classification.py` (`classify_and_inject_mode()`, L38) and
`commands/cmd_skill.py` (`_cmd_skill()`, ~L50-57) through
`ConversationState.append_message()`, each with the trusted `source` value
matching the ephemeral key it injects.

## Scope

- In scope:
  - `scripts/agent/mode_classification.py::classify_and_inject_mode()` — the
    `ctx.conv.history.append({"role": "system", "content": hint, "_ephemeral":
    True})` call (currently at L38).
  - `scripts/agent/commands/cmd_skill.py::_cmd_skill()` — the
    `ctx.conv.history.append({"role": "system", "content": content,
    "_ephemeral": True, "_skill_ephemeral": True})` call (currently ~L50-57).
- Out of scope (unchanged by design, per plan):
  - `cmd_skill.py`'s own ephemeral-filter list comprehension (`ctx.conv.history
    = [m for m in ctx.conv.history if not m.get("_skill_ephemeral")]`,
    currently ~L47-49).
  - `_clear_previous_turn_ephemeral_messages()` in `orchestrator.py` (covered
    by the `orchestrator.py` procedure doc; not touched here).

These two files are grouped into one procedure doc because they are the two
smallest, most tightly-coupled items in the plan's audit list (plan
Implementation step 3 groups them explicitly) — both are single-call-site,
single-purpose "inject one ephemeral system message with a specific trusted
source" changes with no other logic to route.

## Assumptions

- `mode_classification.py`'s hint message carries only `_ephemeral` (confirmed,
  `scripts/agent/mode_classification.py:38`); `TRUSTED_SOURCES["cmd_handler"] =
  {"_ephemeral"}` authorizes exactly this key, so `source="cmd_handler"`
  (per the plan) is sufficient and the message passes validation unchanged.
- **`cmd_skill.py`'s message carries *two* ephemeral keys simultaneously**:
  `"_ephemeral": True` **and** `"_skill_ephemeral": True` (confirmed by direct
  read, `scripts/agent/commands/cmd_skill.py:50-57` — not just
  `_skill_ephemeral` as the plan's Affected-areas table implies). This matters
  for the design decision below.

## Design decisions

- `mode_classification.py`: replace `ctx.conv.history.append({...})` with
  `ctx.conv.append_message({"role": "system", "content": hint, "_ephemeral":
  True}, source="cmd_handler")`. Straightforward — matches
  `TRUSTED_SOURCES["cmd_handler"]` exactly, no sanitization will occur.
- **`cmd_skill.py` needs a decision the plan did not fully resolve.**
  `TRUSTED_SOURCES` maps each source to exactly one authorized ephemeral key:
  `"skill_mixin"` → `{"_skill_ephemeral"}` only, `"cmd_handler"` →
  `{"_ephemeral"}` only. Neither single `source` value authorizes *both* keys
  the current message carries. Passing `source="skill_mixin"` (as the plan's
  Affected-areas table states) will make `validate_message()` return
  `unauthorized = {"_ephemeral"}` (since `_ephemeral` is not in
  `TRUSTED_SOURCES["skill_mixin"]`), and the new `append_message()`'s
  sanitize-and-log fallback will **silently strip `_ephemeral` from the stored
  message on every `/skill` invocation** — a real behavior change: the skill
  content would no longer be swept by `orchestrator.py`'s generic
  `_clear_previous_turn_ephemeral_messages()` (which checks `_ephemeral` only,
  not `_skill_ephemeral`), and would persist across ordinary turns until the
  next `/skill` invocation's own `_skill_ephemeral` filter clears it.
  Changing `TRUSTED_SOURCES["skill_mixin"]` to also authorize `_ephemeral` is
  explicitly out of scope for this plan (no `message_schema.py` value changes
  allowed). Recommended default, to implement unless overridden during code
  review: pass `source="skill_mixin"` as the plan states, and accept/document
  the resulting behavior change (skill context is no longer auto-cleared at
  next-turn boundary by the generic filter; it is still cleared by
  `cmd_skill.py`'s own `_skill_ephemeral` filter on the *next* `/skill`
  invocation, or persists until then). This is a narrower retention window
  change, not a security regression (the message is still eventually cleared,
  and the sanitization is logged at `warning` per `append_message()`'s
  contract).
- Do not attempt to route this message with `source="cmd_handler"` instead —
  that authorizes `_ephemeral` but not `_skill_ephemeral`, which would instead
  break `cmd_skill.py`'s own filter (L47-49) that depends on
  `_skill_ephemeral` surviving in history; that filter is explicitly listed as
  "unchanged" in the plan.

## Alternatives considered

- **Extend `TRUSTED_SOURCES["skill_mixin"]` to `{"_skill_ephemeral",
  "_ephemeral"}`.** Would fully preserve current behavior with no silent
  stripping, but is a `message_schema.py` value change, explicitly out of
  scope for this plan (per requirement doc instruction #6). Flagged here as
  the correct long-term fix; not applied in this pass.
- **Drop the `_ephemeral` key from `cmd_skill.py`'s message entirely before
  the plan's audit was written**, relying solely on the file's own
  `_skill_ephemeral` filter. Rejected as an implementation-time surprise —
  the fact that today's message intentionally carries both keys (for two
  different clearing mechanisms) should be flagged for explicit sign-off
  rather than silently changed by the implementer; hence this doc documents
  it as a known, accepted side-effect of the plan's stated design rather than
  silently "fixing" it out of scope.

## Implementation

### Target file

`scripts/agent/mode_classification.py` and
`scripts/agent/commands/cmd_skill.py`

### Procedure

1. `mode_classification.py::classify_and_inject_mode()`: replace
   `ctx.conv.history.append({"role": "system", "content": hint, "_ephemeral":
   True})` with `ctx.conv.append_message({"role": "system", "content": hint,
   "_ephemeral": True}, source="cmd_handler")`.
2. `cmd_skill.py::_cmd_skill()`: leave the `ctx.conv.history = [m for m in
   ctx.conv.history if not m.get("_skill_ephemeral")]` filter (~L47-49)
   unchanged. Replace the subsequent `ctx.conv.history.append({...})` with
   `ctx.conv.append_message({"role": "system", "content": content,
   "_ephemeral": True, "_skill_ephemeral": True}, source="skill_mixin")`,
   accepting that `_ephemeral` will be sanitized away per the Design decision
   above — add a code comment at the call site documenting why (link back to
   this doc or the plan) so a future reader does not "fix" it by silently
   re-adding `_ephemeral` to `TRUSTED_SOURCES["skill_mixin"]` without review.

### Method

Two independent one-line-call substitutions in two small, single-purpose
files; no shared code path between them beyond both using
`ConversationState.append_message()`.

### Details

- Neither file currently imports anything from `agent.message_schema` or
  needs to — both go through `ctx.conv.append_message()`, so no new import is
  required in either file for this change itself.
- `mode_classification.py` already imports `agent.context.AgentContext`
  (confirmed, L7); no new import needed there either.

## Compatibility considerations

- `mode_classification.py`: no behavior change — message passes validation
  unchanged.
- `cmd_skill.py`: behavior change as documented above (loss of `_ephemeral`
  key on the stored message). External-facing effect: skill-injected context
  may remain visible to the LLM for more turns than before (until the next
  `/skill` invocation), rather than being cleared at the very next turn
  boundary. Should be called out in the eventual PR description for reviewer
  awareness.

## Security considerations

- Both messages now pass through the same validated append path as every
  other history mutation, closing the two gaps named in the requirement doc
  for these files.
- The `cmd_skill.py` sanitization (if it occurs) is logged at `warning` by
  `append_message()`'s contract (see `context.py` procedure doc) — this
  surfaces the retention-window change in logs on every `/skill` call, rather
  than silently changing behavior with no trace.

## Rollback considerations

- Both substitutions are independent single-line reverts.
- If the `cmd_skill.py` retention-window change proves undesirable in review,
  the correct fix is a follow-up `message_schema.py` change to
  `TRUSTED_SOURCES["skill_mixin"]` (tracked as a follow-up per this plan's own
  Risks section pattern), not a revert of this item.

## Validation plan

- Extend `tests/test_mode_classification.py`: regression test confirming the
  mode-hint message still appears in history with `_ephemeral: True` intact
  and no `source` key persisted.
- Extend `tests/test_cmd_skill.py`: regression test confirming
  `_skill_ephemeral: True` still persists on the stored message; add an
  explicit assertion documenting the current expected behavior for
  `_ephemeral` (stripped, per the Design decision) so any future change to
  `TRUSTED_SOURCES` that alters this is caught by a failing test rather than
  silently changing behavior again.
- `pytest tests/test_mode_classification.py tests/test_cmd_skill.py -q` — all
  pass.
- `pytest -k "mode_classification or cmd_skill" -q` — all pass (per plan's
  Regression tests row).
- `ruff check scripts/agent/mode_classification.py
  scripts/agent/commands/cmd_skill.py`, `mypy` same — no new errors.

## Out of scope

- Changing `TRUSTED_SOURCES` values in `message_schema.py` (would be the
  clean fix for the `cmd_skill.py` dual-key issue, but is explicitly
  disallowed by this plan).
- Changing `cmd_skill.py`'s own `_skill_ephemeral` filter or
  `_clear_previous_turn_ephemeral_messages()` in `orchestrator.py`.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260726-093008_plan.md
- Source implementation procedure: N/A
- Generated at: 20260726-101004
- Related target files: mode_classification.py, cmd_skill.py
