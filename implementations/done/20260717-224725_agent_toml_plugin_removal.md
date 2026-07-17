# Implementation: config/agent.toml (remove plugin_tool_override/plugin_strict keys)

Source plan: `plans/done/20260717-123416_plan.md` (Implementation step 3, item 5)

Gap-filling note: matches the granularity of the existing `config_validators.py`
doc for this same plan step. Should land no earlier than
`config_dataclasses_py_plugin_removal.md` and `config_builders_py_plugin_removal.md`
(same commit-sized unit is fine) — those stop `ToolConfig`/`_build_tool_config()`
from reading these keys; removing them from `agent.toml` first would be
harmless too (unread keys are simply ignored by `cfg.get(key, default)`), so
strict ordering isn't required, but landing them together avoids a window
where the config file and the code disagree about what's configurable.

## Goal

`config/agent.toml` no longer declares `plugin_tool_override`/`plugin_strict`.

## Scope

**In scope**: `config/agent.toml` — delete the two lines
`plugin_tool_override = false` and `plugin_strict = false` (lines 79-80).

**Out of scope**: any other config key in this file, including the immediately
following `# ── Memory ──` section and `use_memory_layer` (already removed
per an earlier, unrelated change — do not touch it).

## Assumptions

1. Confirmed by direct read (2026-07-17): both keys are consecutive lines (79-80), immediately after `llm_stream_retry_on_malformed_chunk = false` and immediately before a blank line + `# ── Memory ────` section header.
2. `config/production_agent.toml` or any other environment-specific TOML overlay may also declare these keys — check for and remove them there too if such files exist (this repo may have profile-specific config overlays; confirm at implementation time via `ls config/*.toml` and `grep -l "plugin_tool_override\|plugin_strict" config/*.toml`).

## Implementation

### Target file

`config/agent.toml` (and any sibling `config/*.toml` overlay found per Assumption 2)

### Procedure

1. Delete:
   ```toml
   plugin_tool_override = false
   plugin_strict = false
   ```
2. Run `grep -l "plugin_tool_override\|plugin_strict" config/*.toml` to check for any other config file declaring these keys (e.g. a production overlay) and remove them there too if found.

### Method

Direct line deletion(s) from TOML config file(s) — no code change.

### Details

- Do not touch the `# ── Memory ──` section or any unrelated key in this file.
- If `_FORBIDDEN_KEYS`-style rejection lists exist elsewhere in this config-loading pipeline (e.g. `config_builders.py`'s `_FORBIDDEN_KEYS`, seen in this repo's history for other removed keys like `use_memory_layer`/`gitops_force_push_blocked`), consider whether `plugin_tool_override`/`plugin_strict` should be ADDED to such a list so a stale config file (e.g. someone's local copy still containing these keys) is rejected at load time rather than silently ignored — check `scripts/agent/config_builders.py`'s `_FORBIDDEN_KEYS` (or equivalent) for this pattern before deciding; if such a rejection-list mechanism exists and is the established convention for removed keys in this repo, add `plugin_tool_override`/`plugin_strict` to it as part of this change (this is a natural completion of the removal, not scope creep, since leaving them silently-ignorable rather than explicitly-rejected is inconsistent with how other removed keys were handled).

## Validation plan

| Check | Command | Expected |
|---|---|---|
| No plugin keys remain in any config file | `grep -rn "plugin_tool_override\|plugin_strict" config/` | 0 matches |
| Config still loads | `PYTHONPATH=scripts uv run python -c "from shared.config_loader import ConfigLoader; ConfigLoader().load('agent.toml')"` | no exception |
| Full suite (run only once all step-1/2/3/6 docs have landed) | `uv run pytest -q` | all pass |
