# Implementation: M-1 — Remove use_tool_summarize/tool_summarize_threshold from config/agent.toml

## Goal

Remove the `use_tool_summarize` and `tool_summarize_threshold` keys from `config/agent.toml`.
**This is a mandatory, must-land-together change** — once
`implementations/20260708-171134_config_builders.py.md` adds these keys to `_FORBIDDEN_KEYS`,
this repository's config file (which explicitly sets both keys) would otherwise fail
`build_agent_config()` on every agent startup with `ConfigLoadError`.

## Scope

**Target**: `config/agent.toml`

**Depends on / must land in the SAME commit as**:
`implementations/20260708-171057_config_dataclasses.py.md` (field removal) and
`implementations/20260708-171134_config_builders.py.md` (`_FORBIDDEN_KEYS` addition). This doc
was discovered as a necessary addition while writing that doc's Risks section — the original
M-1 plan's Affected Areas table did not list `config/agent.toml` itself, only the Python source
files, but the plan's own chosen backward-compatibility policy (fail-closed via
`_FORBIDDEN_KEYS`) makes this edit unconditionally required for THIS repository's agent to keep
starting.

**Out of scope**: every other key in `config/agent.toml`.

## Assumptions

1. `config/agent.toml` currently has both keys set to their existing defaults
   (`use_tool_summarize = false`, `tool_summarize_threshold = 3000`) — removing them causes no
   behavior change today (the values were already the same as `ToolConfig`'s dataclass defaults
   before their removal), since nothing reads them anymore once the M-1 rollout's other docs land.

## Implementation

### Target file

`config/agent.toml`

### Procedure

#### Step 1: Confirm the current lines

```bash
grep -n "use_tool_summarize\|tool_summarize_threshold" config/agent.toml
```

Expected: two matches in the `# ── Tools ──` section (lines ~70-71).

#### Step 2: Remove both lines

Current (within the `# ── Tools ──` section):

```toml
tool_cache_ttl = 300
serial_tool_calls = false
use_tool_dag = true
use_tool_summarize = false
tool_summarize_threshold = 3000
tool_dedup_max_repeats = 3
```

Replace with:

```toml
tool_cache_ttl = 300
serial_tool_calls = false
use_tool_dag = true
tool_dedup_max_repeats = 3
```

### Method

- Two-line TOML key removal; no other keys in the `# ── Tools ──` section change.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| TOML syntax | `python3 -c "import tomllib; tomllib.load(open('config/agent.toml','rb')); print('OK')"` | prints `OK` |
| Grep (keys removed) | `grep -n "use_tool_summarize\|tool_summarize_threshold" config/agent.toml` | no matches |
| Agent startup smoke test | start the agent (or run `build_agent_config()` against the real file) | no `ConfigLoadError` |
| Tests (full) | `uv run pytest -v` | no new failures once `config_dataclasses.py` and `config_builders.py`'s M-1 docs land together |

## Risks

- If this doc is applied WITHOUT `config_builders.py`'s `_FORBIDDEN_KEYS` extension also landing,
  nothing breaks (the keys simply stop being read, same as any other unset-with-default field) —
  safe on its own. The DANGEROUS direction is the reverse: landing `_FORBIDDEN_KEYS` without this
  doc. Always land both together, and if only one can land first, land THIS doc first.
