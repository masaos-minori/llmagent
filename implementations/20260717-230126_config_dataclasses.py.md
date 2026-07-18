# Implementation procedure: `scripts/agent/config_dataclasses.py` (`ToolConfig.tool_definitions` doc-comment)

Source plan: `plans/20260717-130629_plan.md` (requirement `requires/done/20260717_10_require.md`),
Implementation step 4.

## Goal

Add a doc-comment on `ToolConfig.tool_definitions` (`scripts/agent/config_dataclasses.py:193`) stating
its fallback/test-fixture-only status, so no future contributor mistakes it for the runtime-authoritative
tool schema source once `RuntimeToolRegistry` (requirement 05) supplies LLM-visible tool schemas
instead.

## Scope

**In scope**
- A comment addition immediately above the `tool_definitions` field declaration. No field type,
  default, or dataclass shape change.

**Out of scope**
- Requirement 05's actual migration of `agent/llm_turn_runner.py`/`shared/llm_client.py` off this
  field (not landed yet — see Assumption 1; this item is independent of that gate regardless, see
  Assumption 2).
- Removing the field or changing `config/agent.toml`'s `[[tool_definitions]]` block (explicitly out
  of scope for this whole requirement).

## Assumptions

1. Per `implementations/20260717-225949_requirements_04_09_landing_check.md`, requirement 05 (LLM
   tool schema sourced from `RuntimeToolRegistry` instead of `ctx.cfg.tool.tool_definitions`) has
   **not landed** yet (no implementation procedure doc found for `agent/llm_turn_runner.py`,
   `shared/llm_client.py`, or `agent/commands/registry.py`'s `/help` migration).
2. Unlike the `tool_registry.py`/`tool_constants.py`/`tool_executor_helpers.py`/`tool_policy.py`
   items, this comment addition does **not** need to wait for requirement 05 to land: it is a
   forward-looking annotation on a config field whose runtime meaning doesn't change from this edit
   (the field keeps its current type/default/behavior); it only documents the field's *intended*
   future role, which is safe to state now as "this will become fallback/test-fixture-only" rather
   than "this already is." This is a judgment call — if a stricter reading of the requirement's
   gating is preferred, defer this edit until requirement 05 lands, same as the other docstring items.
3. Current field (verbatim, read directly, `scripts/agent/config_dataclasses.py:193`):
   `tool_definitions: list[dict] = field(default_factory=list)` — no preceding comment today. The
   nearby comment at line 165 ("Compare tool_definitions against /v1/tools at startup") documents a
   *different* field (`tool_definitions_strict`, line 166), not this one.

## Implementation

### Target file

`scripts/agent/config_dataclasses.py` — `ToolConfig` dataclass, line 193 (comment insertion above
this line only).

### Procedure

1. Insert a one-to-two-line `#` comment immediately above line 193's field declaration.
2. Do not alter the field's type annotation or `default_factory`.

### Method

Text insertion of a `#`-prefixed comment line(s) directly above the existing field declaration; no
dataclass shape/type change; `mypy`/`ruff` unaffected by a comment-only change.

### Details

- Insert above `tool_definitions: list[dict] = field(default_factory=list)` (line 193), a comment
  conveying (paraphrase, not verbatim-mandated wording):
  "Fallback/test-fixture-only static tool schema list; not the runtime source once
  `RuntimeToolRegistry` (`shared/runtime_tool_registry.py`) is populated from live `/v1/tools`
  (requirement 05). Retained as: (a) a fallback if the registry construction is empty/unavailable
  — see `implementations/20260717-230218_startup_static_fallback_unknown_resolution.md` for whether
  this fallback path is actually exercised at runtime or the registry-empty case is fatal instead —
  and (b) the shape template for test fixtures."
- Keep this comment distinct from line 165's comment (which documents `tool_definitions_strict`, a
  different field controlling drift-check strictness, not the schema source itself).

## Validation plan

| Check | Tool / Command | Target |
|---|---|---|
| Comment placement review | manual read of `scripts/agent/config_dataclasses.py` around line 193 | comment present, distinct from line 165's `tool_definitions_strict` comment, does not alter field type/default |
| `ruff format --check` / `ruff check` | `uv run ruff format --check scripts/agent/config_dataclasses.py`, `uv run ruff check scripts/agent/config_dataclasses.py` | pass |
| `mypy` | `uv run mypy scripts/agent/config_dataclasses.py` | no new errors (comment-only) |
| Full suite | `uv run pytest` | no failures (comment-only, zero behavior change) |
