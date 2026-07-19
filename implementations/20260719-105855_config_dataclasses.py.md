# Implementation procedure: `scripts/agent/config_dataclasses.py` (memory-layer default flip)

Source plan: `plans/20260719-095637_plan.md` ("Enable the persistent memory layer by default and add the
missing chunking step", requirement `requires/done/20260714_15_require.md`), Implementation step 3
(dataclass half).

No existing implementations doc under `implementations/` or `implementations/done/` matches this
specific change. Several `config_dataclasses.py`-named docs exist (e.g.
`implementations/20260717-230126_config_dataclasses.py.md` — a doc-comment addition on
`ToolConfig.tool_definitions`; `implementations/done/20260715-124841_config_dataclasses.md` — an
**invalid/archived** doc for a since-abandoned Memory-key-removal plan; `implementations/done/20260709-103716_config_dataclasses.py.md`,
`implementations/done/20260707-110400_config_dataclasses.py.md`, and others — unrelated fields/removals
from earlier batches). None proposes flipping `use_memory_layer`/`memory_embed_enabled` defaults to
`True`. Flagged as checked, not a genuine overlap.

## Goal

Flip `MemoryConfig.use_memory_layer` and `MemoryConfig.memory_embed_enabled` default values from
`False` to `True`, so a fresh checkout has the persistent memory layer and embedding-based retrieval
enabled without any config file edit.

## Scope

**In scope**
- `MemoryConfig.use_memory_layer: bool = False` → `True`.
- `MemoryConfig.memory_embed_enabled: bool = False` → `True`.

**Out of scope**
- `MemoryConfig.memory_local_only: bool = False` (current default) — **not changed**. It already matches
  the value `config/agent.toml` is being set to under Option B (`false`); the plan's Assumption already
  notes there is nothing to flip here, confirmed by direct read (see Assumptions).
- Every other `MemoryConfig` field (`memory_jsonl_dir`, `memory_max_inject_semantic`, `memory_max_content_chars`,
  etc.) — untouched.
- `AgentConfig`'s own `__post_init__` validation logic (`config_dataclasses.py:415-424`, the
  `use_memory_layer`+`memory_jsonl_dir` and `memory_embed_enabled`+`embed_url` checks) — untouched; this
  plan relies on those checks continuing to run as-is against the new defaults.

## Assumptions

1. **Re-located exact current line numbers** (as instructed by the plan's own Risks section, which
   flags that the requirement's cited `:243`/`:249` did not match the plan-authoring investigation's
   `:208`/`:214`): ran
   `grep -n "use_memory_layer\|memory_embed_enabled\|memory_local_only\|memory_max_content_chars" scripts/agent/config_dataclasses.py`
   directly in this cycle. **Confirmed current lines**: `use_memory_layer: bool = False` is at
   **line 208**, `memory_embed_enabled: bool = False` is at **line 214**, `memory_max_content_chars: int = 500`
   is at line 220, `memory_local_only: bool = False` is at line 232. These match the plan's own
   `:208`/`:214` read-out exactly, not the requirement's stale `:243`/`:249`. No further drift since the
   plan was authored.
2. `MemoryConfig` (`config_dataclasses.py:204-238`) is a plain `@dataclass` (not frozen); its
   `__post_init__` (`234-238`) only runs `_v_mem_fts`, `_v_mem_rrf`, `_v_mem_rec` — none of these three
   validators reference `use_memory_layer` or `memory_embed_enabled`, so flipping these two field
   defaults does not change `__post_init__`'s validation surface for `MemoryConfig` itself.
3. **Significant finding, load-bearing for this plan's Goal — verified by direct read and by running
   `build_agent_config()` interactively**: `config/agent.toml`'s `use_memory_layer` and
   `memory_embed_enabled` keys are **silently stripped before ever reaching this file's dataclass
   construction**:
   - `shared/config_loader.py:31-39` defines `_REMOVED_KEYS` containing exactly
     `use_memory_layer`, `memory_jsonl_dir`, `memory_embed_enabled`, `gitops_force_push_blocked`,
     `gitops_protected_branches`; `ConfigLoader.load()`/`load_all()` (`config_loader.py:77-119`) call
     `self._filter_removed_keys(...)` on every loaded file's dict before merging.
   - `agent/config_builders.py::_build_memory_config()` (lines 194-212) has `use_memory_layer=...` and
     `memory_embed_enabled=...` **commented out** (lines 197, 202, prefixed `# REMOVED:`) — it never
     reads these two keys from the config dict at all, regardless of what `config/agent.toml` contains.
   - Consequently, **`MemoryConfig.use_memory_layer` and `.memory_embed_enabled` are, today, controlled
     entirely and exclusively by this file's dataclass field defaults** — `config/agent.toml`'s text
     values for these two specific keys have zero runtime effect (confirmed empirically: ran
     `PYTHONPATH=scripts uv run python -c "from agent.config_builders import build_agent_config;
     print(build_agent_config().memory.use_memory_layer, build_agent_config().memory.memory_embed_enabled)"`
     against the current repo state — both keys in `config/agent.toml` are currently `false` and print
     `False`/`False`, consistent with the dataclass default rather than an independent toml read).
   - This means: **this file's edit is the entire, sufficient mechanism** by which the plan's Goal
     ("fresh checkout has `use_memory_layer = true` and `memory_embed_enabled = true` in effect by
     default") is achieved. The companion `config/agent.toml` edit (see the paired
     `config/agent.toml` implementation doc) for these same two keys is textually consistent with intent
     but functionally inert under the current `config_loader.py`/`config_builders.py` wiring — not a bug
     to fix under this plan (out of scope, not named in the plan's Implementation steps), but worth
     recording so a future reader does not assume the toml edit alone would suffice.
   - By contrast, `memory_local_only` is **not** on either removed-key list and **is** read live at
     `config_builders.py:211` (`memory_local_only=bool(cfg.get("memory_local_only", False))`) — so the
     paired `config/agent.toml` doc's `memory_local_only = false` edit is genuinely load-bearing and
     necessary (confirmed separately).
4. `agent/factory.py::_build_memory_services()` (line 263-268, `if not ctx.cfg.memory.use_memory_layer:
   return None`) still gates `MemoryServices` construction on the runtime `use_memory_layer` value — so
   flipping this file's default to `True` **does** actually change runtime behavior (memory services
   built at startup instead of skipped), it is not a dead flag. `factory.py::_build_embedding_client()`
   (line 331-344) similarly passes `enabled=ctx.cfg.memory.memory_embed_enabled` straight into the
   embedding client constructor.

## Implementation

### Target file

`scripts/agent/config_dataclasses.py`

### Procedure

1. Immediately before editing, re-run
   `grep -n "use_memory_layer\|memory_embed_enabled" scripts/agent/config_dataclasses.py` to reconfirm
   lines 208/214 have not shifted since this doc was written (only two matches expected inside
   `MemoryConfig`'s field declarations; the two additional matches inside `AgentConfig.__post_init__`
   at lines 415/422, per the plan's own text, are read-only condition checks, not field declarations,
   and are not edited).
2. Change line 208 from `use_memory_layer: bool = False` to `use_memory_layer: bool = True`.
3. Change line 214 from `memory_embed_enabled: bool = False` to `memory_embed_enabled: bool = True`.
4. Leave the inline comment on line 213 (`# Enable embedding generation and KNN search`) as-is — it
   already accurately describes the field's purpose regardless of default value.
5. Do not touch line 232 (`memory_local_only: bool = False`) — confirmed correct as-is per Assumption 3.

### Method

Two-line default-value edit on an existing plain dataclass. No new fields, no signature change, no new
abstractions.

### Details

No type or structural change: both fields remain `bool`. No `__post_init__` change required (Assumption
2). Downstream effect (informational, not part of this file's edit): with `use_memory_layer=True` and
`memory_local_only` becoming `False` via the paired `config/agent.toml` edit, `AgentConfig.__post_init__`'s
existing checks at lines 415-424 (`use_memory_layer` requires non-empty `memory_jsonl_dir` — already
non-empty by default at line 209 `"/opt/llm/memory"` — and `memory_embed_enabled` requires non-empty
`rag.embed_url` — already non-empty in `config/agent.toml` at line 10) should not raise on a fresh
checkout; this is exercised by the Validation plan's startup test, not by this file's edit in isolation.

## Validation plan

| Check | Command | Target |
|---|---|---|
| Format/lint | `uv run ruff format scripts/agent/config_dataclasses.py && uv run ruff check scripts/agent/config_dataclasses.py` | 0 errors |
| Type check | `uv run mypy scripts/agent/config_dataclasses.py` | 0 new errors vs baseline |
| Architecture | `PYTHONPATH=scripts uv run lint-imports` | 0 violations |
| Security | `uv run bandit -r scripts/agent/config_dataclasses.py -c pyproject.toml` | 0 high/medium |
| Diff scope | `rg -n "use_memory_layer: bool|memory_embed_enabled: bool|memory_local_only: bool" scripts/agent/config_dataclasses.py` | exactly the 3 field declarations; confirms `memory_local_only` untouched (`= False`) and the other two now `= True` |
| Factory/startup | `uv run pytest tests/test_agent_factory.py -v` | all pass — confirms no test hardcodes the old `False` defaults without explicitly overriding them, and no `ValueError` at construction |
| Memory layer/ingestion regression | `uv run pytest tests/test_memory_layer.py tests/test_memory_consistency.py tests/test_agent_cmd_memory.py -v` | all pass under the new `true` defaults |
| Runtime confirmation | `PYTHONPATH=scripts uv run python -c "from agent.config_builders import build_agent_config; c = build_agent_config(); print(c.memory.use_memory_layer, c.memory.memory_embed_enabled, c.memory.memory_local_only)"` | prints `True True False` after this file's edit and the paired `config/agent.toml` edit are both applied |
| Full suite | `uv run pytest -v` | no new failures vs pre-change baseline |
