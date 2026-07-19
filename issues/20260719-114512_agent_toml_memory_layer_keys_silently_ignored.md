# `config/agent.toml`'s `use_memory_layer`/`memory_embed_enabled` are silently ignored

Discovered while implementing `plans/done/20260719-095637_plan.md` (memory-layer
chunking + defaults, requirement `requires/done/20260714_15_require.md`).

## Problem

`config/agent.toml` has `use_memory_layer` and `memory_embed_enabled` keys that
look like normal, settable configuration — but they have **zero runtime
effect**:

- `scripts/shared/config_loader.py:31-35`'s `_REMOVED_KEYS` frozenset includes
  both `"use_memory_layer"` and `"memory_embed_enabled"` — both are stripped
  from the parsed TOML dict before it ever reaches config construction
  (`config_loader.py:169`: `{k: v for k, v in data.items() if k not in
  _REMOVED_KEYS}`).
- `scripts/agent/config_builders.py:194-202`'s `_build_memory_config()` has
  both fields **commented out** as `# REMOVED: use_memory_layer=bool(cfg.get(...))`
  and `# REMOVED: memory_embed_enabled=bool(cfg.get(...))` — meaning
  `MemoryConfig`'s dataclass field defaults (`scripts/agent/config_dataclasses.py`)
  are used unconditionally, regardless of what `config/agent.toml` says.

An operator editing either key in `config/agent.toml` (setting it to `true` or
`false`) has no effect whatsoever — the only way to change these two flags'
actual behavior is editing the Python dataclass default. This is silently
misleading: the config file's own comments/keys imply they are the
configuration surface, and nothing warns that they are dead.

By contrast, the third memory-related flag in the same section,
`memory_local_only`, is NOT in `_REMOVED_KEYS` and IS wired in
`_build_memory_config()` — it behaves normally. So the inconsistency is
specific to these two keys, not the whole memory config section.

## Reproduction

- `grep -n "_REMOVED_KEYS" scripts/shared/config_loader.py` shows
  `use_memory_layer`/`memory_embed_enabled` in the frozenset.
- `grep -n "_build_memory_config" -A 10 scripts/agent/config_builders.py` shows
  both fields commented out with `# REMOVED:` prefixes.
- Set `config/agent.toml`'s `use_memory_layer = false` (or any value) and
  confirm via `build_agent_config()` that `cfg.memory.use_memory_layer` always
  equals the dataclass default (`config_dataclasses.py`), never the toml value.

## Why this wasn't fixed inline

Fixing this requires a product decision this repo's own convention (see
`rules/coding.md`'s "Current behavior" classification table) says should not
be made silently:

- (a) **Remove the dead keys from `config/agent.toml` entirely** (and its
  comments), since they're vestigial and only the dataclass default matters —
  simplest, but removes the *appearance* of runtime configurability that
  might be intentional (e.g. these keys may have been left in deliberately as
  a paper trail of "we used to support per-deployment overrides here").
- (b) **Restore the wiring in `_build_memory_config()`** so `config/agent.toml`
  becomes authoritative again for these two keys, matching every other memory
  config field's pattern (`memory_local_only`, `memory_max_content_chars`,
  etc.) and matching how every other boolean/config flag in this codebase
  works. This re-introduces per-deployment override capability without a code
  change, which may or may not be desired.

`plans/done/20260719-095637_plan.md` (which enables the memory layer by
default via the dataclass default alone) does not require either fix to
achieve its own goal — the dataclass default change is sufficient and
sufficient on its own for the plan's Acceptance Criteria. This issue is filed
separately so the discovery isn't lost, per this repo's own "file, don't
silently patch" convention for exactly this class of finding.

## Recommended action

Decide (a) or (b) above. If (b), also decide whether the `_REMOVED_KEYS`
history (why these were removed originally) should be checked via `git log
-p -- scripts/agent/config_builders.py` before re-wiring them, in case the
removal was itself deliberate for a reason not yet understood (e.g. related
to the `use_memory_layer` startup-only/hot-reload distinction documented in
`docs/05_agent_08_01_configuration-loading-agent-config-part1.md`).
