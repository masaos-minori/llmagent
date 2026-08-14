## Goal

Update the `tool_definitions` field docstring in `scripts/agent/config_dataclasses.py`
(current comment block at lines 189-193, field at line 194) to state plainly that this
field is compatibility-only (startup drift validation + test fixtures), removing the "(a)
a fallback if the registry construction is empty/unavailable" framing — that framing
directly contradicts the post-fix behavior, since after this plan's other changes land
(see the `tool_runner.py` and `tool_preparation.py` docs in this set), no code in the
call-preparation/validation/approval/execution path reads `tool_definitions` as a
fallback anymore.

## Scope

In scope: the comment block immediately preceding `tool_definitions: list[dict] =
field(default_factory=list)` (current lines 189-194) in `AgentConfig`'s tool-settings
dataclass. Text-only change; no field name, type, or default-value change.

Out of scope: any other field in this dataclass; `tool_definitions_strict` (line 162,
a different, unrelated field controlling startup drift-check strictness); the field's
actual runtime consumers (`repl_health.py::_check_tool_definitions()`,
`llm_turn_runner.py::_filter_disabled_tool_definitions()`, the three display/count-only
call sites) — none of those are touched by this doc, only the docstring describing the
field itself.

## Assumptions

- After the `tool_runner.py` doc's changes land, `_validate_tool_args()` (the function
  that read `ctx.cfg.tool.tool_definitions` as a fallback) no longer exists — confirmed
  by that doc's Procedure step 4 (full deletion). This doc's docstring update should be
  landed in the same change set as that deletion, not independently, so the docstring
  never describes a fallback that has already been removed by the time a reader sees it
  (or, conversely, is removed before the fallback code that motivated the old wording is
  actually gone).
- `llm_turn_runner.py::_filter_disabled_tool_definitions()` remains a genuine runtime
  consumer of `tool_definitions` after this plan (per the plan's UNK-03, explicitly
  out-of-scope for this plan, filed as a follow-up) — the updated docstring must not
  overclaim the field is unused *everywhere*, only that it is compatibility-only for the
  validation/scheduling/approval/execution path this plan covers.

## Design decisions

- **Scope the docstring's claim precisely to what this plan actually changes.** The
  current comment says the field is retained as "(a) a fallback if the registry
  construction is empty/unavailable and (b) the shape template for test fixtures." Only
  clause (a) becomes false after this plan; clause (b) remains true. The rewritten
  docstring keeps the test-fixture rationale and adds the startup-drift-validation
  rationale (`repl_health.py`), while dropping the fallback claim — it does not claim the
  field is dead code everywhere, since `_filter_disabled_tool_definitions()` still reads
  it for the LLM-facing tool list (a separate, explicitly out-of-scope runtime use per
  the plan's UNK-03).

## Alternatives considered

- Removing the field entirely. Rejected: explicitly named as a non-goal in the plan's
  Out-of-Scope section ("Removing `ctx.cfg.tool.tool_definitions` itself, or its config
  loading in `config_builders.py` — the field stays as a compatibility/test-fixture
  value").
- Leaving the docstring unchanged and only fixing the code. Rejected: the plan's
  Implementation steps explicitly call out updating this docstring (Phase 2, final
  bullet) because the current text actively misdescribes the post-fix behavior, which
  would mislead a future reader into re-adding a fallback that was deliberately removed.

## Implementation

### Target file

`scripts/agent/config_dataclasses.py`

### Procedure

1. Replace the comment block at current lines 189-193:
   ```python
   # Fallback/test-fixture-only static tool schema list; not the runtime source once
   # RuntimeToolRegistry (shared/runtime_tool_registry.py) is populated from live /v1/tools
   # (requirement 05). Retained as: (a) a fallback if the registry construction is empty/unavailable
   # and (b) the shape template for test fixtures.
   ```
   with:
   ```python
   # Compatibility-only static tool schema list; RuntimeToolRegistry
   # (shared/runtime_tool_registry.py), populated from live /v1/tools, is the sole
   # runtime authority for tool validation/scheduling/approval/execution (no fallback
   # to this field remains in that path). Retained for: (a) startup drift validation
   # against /v1/tools (agent/repl_health.py) and (b) the shape template for test
   # fixtures. Still read at runtime by
   # agent/llm_turn_runner.py::_filter_disabled_tool_definitions() to build the
   # LLM-facing tool list (filtered by registry visibility) — a separate, narrower use
   # not covered by this note.
   ```
2. Leave `tool_definitions: list[dict] = field(default_factory=list)` (line 194)
   unchanged.

### Method

Manual, single-comment-block edit — no code logic change, so no test impact beyond a
docstring-diff review.

### Details

- Confirmed via direct read of `scripts/agent/config_dataclasses.py`: the comment block
  is at lines 189-193, immediately above `tool_definitions: list[dict] = field(
  default_factory=list)` at line 194, inside the tool-settings dataclass (docstring
  "Tool execution, caching, approval policy, and prompt settings." at the top of that
  class).
- `tool_definitions_strict: bool = False` (line 162, with comment "Compare
  tool_definitions against /v1/tools at startup") is a distinct field controlling
  whether `repl_health.py`'s drift check is fatal vs. warn-only — confirmed unrelated to
  this docstring's subject and left untouched.

## Compatibility considerations

- Comment-only change; no behavioral or type impact on any consumer of `tool_definitions`
  (`config_builders.py`'s loader, `repl_health.py`'s drift check, `llm_turn_runner.py`'s
  filter, the three display/count-only sites in `repl.py`/`commands/registry.py`/
  `commands/cmd_mcp.py`, and test fixtures across `tests/agent/`).

## Security considerations

N/A — comment-only change, no behavior affected.

## Rollback considerations

- Trivial: revert the comment text; no functional dependency on this change from any
  other file in this plan (unlike the `tool_runner.py`/`tool_approval.py`/
  `tool_preparation.py` trio, which must roll back together).

## Validation plan

Manual review only (no test asserts on docstring content); confirm via `grep -n
"Fallback/test-fixture-only\|Compatibility-only" scripts/agent/config_dataclasses.py`
that the old wording is gone and the new wording is present. Include this file in the
plan's full `uv run ruff format`/`ruff check` pass to confirm the comment doesn't break
line-length or formatting lint rules.

## Out of scope

- Any change to `agent/repl_health.py::_check_tool_definitions()` /
  `check_tool_definitions_runtime()` — explicitly out of scope per the plan's own
  Out-of-Scope section ("startup drift validation must keep working unchanged").
- Any change to `config_reload.py`'s hot-reload of `cfg.tool.tool_definitions` — out of
  scope per the plan.
- `llm_turn_runner.py::_filter_disabled_tool_definitions()` itself — out of scope per the
  plan's UNK-03 (follow-up issue, not this plan).
- Any `docs/*.md` update — out of scope for this document-only phase.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260813-184037_plan.md
- Source implementation procedure: N/A
- Generated at: 20260813-235943
- Related target files: config_dataclasses.py
