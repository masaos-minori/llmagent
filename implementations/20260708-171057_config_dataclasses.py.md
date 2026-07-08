# Implementation: M-1 — Remove use_tool_summarize/tool_summarize_threshold from ToolConfig

## Goal

Delete the `use_tool_summarize` and `tool_summarize_threshold` fields from `ToolConfig`. The
summarization feature's execution-layer code path was already removed by H-1
(`implementations/20260708-162748_tool_runner_h1.py.md`); this completes the cleanup at the
config layer.

## Scope

**Target**: `scripts/agent/config_dataclasses.py`

**Depends on / must land together with**: `implementations/*_config_builders.py.md` (M-1),
`implementations/*_config_reload_m1.py.md` (M-1), `implementations/*_cmd_config_display.py.md`
(M-1), and `implementations/*_tool_result_formatter_m1.py.md` (M-1) — all read or write these
two fields and will raise `AttributeError` if this doc lands without them, or vice versa. Land
all M-1 docs in the same commit.

**Out of scope**: every other field on `ToolConfig` — `tool_cache_ttl`, `tool_cache_max_size`,
`serial_tool_calls`, `tool_definitions_strict`, `routing_drift_strict`,
`tool_dedup_max_repeats`, `tool_result_max_llm_chars`, `tool_results_turn_max_chars`, etc. — all
unchanged.

## Assumptions

1. `ToolConfig.__post_init__` (if it exists) does not validate `use_tool_summarize` or
   `tool_summarize_threshold` — confirmed by the plan's own analysis; no validator removal
   needed.

## Implementation

### Target file

`scripts/agent/config_dataclasses.py`

### Procedure

#### Step 1: Confirm the current field definitions

```bash
grep -n "use_tool_summarize\|tool_summarize_threshold" scripts/agent/config_dataclasses.py
```

Expected: two field definitions inside `ToolConfig` (lines ~192-194):

```python
    # Replace truncation with LLM summary above threshold
    use_tool_summarize: bool = False
    tool_summarize_threshold: int = 3000
```

#### Step 2: Remove both fields and their comment

Remove the three lines shown above entirely. The preceding `serial_tool_calls: bool = False`
field and the following `# Compare tool_definitions against /v1/tools at startup` /
`tool_definitions_strict: bool = False` fields become adjacent.

### Method

- Two-field deletion (plus their explanatory comment) from a dataclass; no other fields,
  `__post_init__` logic, or class structure changes.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Lint | `ruff check scripts/agent/config_dataclasses.py` | 0 errors |
| Type check | `mypy scripts/` | no new errors (confirms no remaining code reads `ToolConfig.use_tool_summarize`/`.tool_summarize_threshold` as typed attributes) |
| Grep (fields removed) | `grep -n "use_tool_summarize\|tool_summarize_threshold" scripts/agent/config_dataclasses.py` | no matches |
| Tests (full) | `uv run pytest -v` | no new failures once every M-1 companion doc lands together |
| Pre-commit | `pre-commit run --all-files` | pass |

## Risks

- Landing this field removal WITHOUT `config_builders.py`'s companion change
  (`_build_tool_config()` still passing `use_tool_summarize=...`/`tool_summarize_threshold=...`
  as constructor kwargs to `ToolConfig(...)`) would raise `TypeError: unexpected keyword
  argument`. Apply both in the same commit.
