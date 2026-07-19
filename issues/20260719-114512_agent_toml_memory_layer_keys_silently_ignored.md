# `config/agent.toml`'s `use_memory_layer`/`memory_embed_enabled` are silently ignored

**RESOLVED (2026-07-19).** Fixed by restoring the three commented-out lines
in `_build_memory_config()` (`scripts/agent/config_builders.py`):
`use_memory_layer`, `memory_embed_enabled`, and `memory_jsonl_dir` (a third
field found to have the identical bug during the fix) are now genuinely read
from the config dict, defaulting to the current dataclass defaults (`True`,
`True`, `"/opt/llm/memory"`) when absent — option (b) from "Recommended
action" below. Verified directly: `_build_memory_config({"use_memory_layer":
False, "memory_embed_enabled": False, "memory_jsonl_dir": "/tmp/x"})` now
returns those exact values instead of the old dataclass-only defaults.
Regression test added: `tests/test_config_builders.py::TestBuildMemoryConfig::test_overrides_are_applied`
(the prior test only checked the empty-dict/defaults case, which is exactly
why this bug went unnoticed — it never exercised an actual override).
`docs/05_agent_08_01_configuration-loading-agent-config-part1.md`'s two
affected bullets no longer apply as written and should be revised to state
these keys are now live config again (not done as part of this fix — see
that doc directly).

Discovered while implementing `plans/done/20260719-095637_plan.md` (memory-layer
chunking + defaults, requirement `requires/done/20260714_15_require.md`).

**Status update (2026-07-19, post-verification):** commit `9711ca96`
("refactor: remove redundant _FORBIDDEN_KEYS/_REMOVED_KEYS validation")
removed the `_REMOVED_KEYS`/`_FORBIDDEN_KEYS` stripping mechanisms entirely
from `config_loader.py`, `config_builders.py`, and `config_reload.py` — but
this did **not** fix the bug described below. `_build_memory_config()` still
never reads `use_memory_layer`/`memory_embed_enabled` from the parsed config
dict at all (the two lines are still present, commented out as
`# REMOVED: ...`); the stripping step was simply redundant with that, not the
cause. **Re-verified directly**: calling `_build_memory_config()` with an
explicit dict containing `use_memory_layer=False`/`memory_embed_enabled=False`
still returns `MemoryConfig(use_memory_layer=True, memory_embed_enabled=True)`
— the dataclass defaults are still the sole authority. This issue remains
open; only the root-cause mechanism description below is now stale (see
Reproduction for the corrected explanation).

## Problem

`config/agent.toml` has `use_memory_layer` and `memory_embed_enabled` keys that
look like normal, settable configuration — but they have **zero runtime
effect**:

- `scripts/agent/config_builders.py:194-202`'s `_build_memory_config()` has
  both fields **commented out** as `# REMOVED: use_memory_layer=bool(cfg.get(...))`
  and `# REMOVED: memory_embed_enabled=bool(cfg.get(...))` — meaning
  `MemoryConfig`'s dataclass field defaults (`scripts/agent/config_dataclasses.py`)
  are used unconditionally, regardless of what `config/agent.toml` says. This
  is the entire cause — no other layer needs to reject or strip the keys for
  them to be ignored; `_build_memory_config()` simply never looks at them.
- (Historical, no longer true as of `9711ca96`: `scripts/shared/config_loader.py`
  used to additionally strip these two keys via a `_REMOVED_KEYS` frozenset
  before the dict reached config construction. That mechanism has since been
  removed as redundant, since `_build_memory_config()` never read the keys in
  the first place — removing the stripping layer changes nothing observable.)

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

- `grep -n "_build_memory_config" -A 10 scripts/agent/config_builders.py` shows
  both fields commented out with `# REMOVED:` prefixes.
- Set `config/agent.toml`'s `use_memory_layer = false` (or any value) and
  confirm via `build_agent_config()` that `cfg.memory.use_memory_layer` always
  equals the dataclass default (`config_dataclasses.py`), never the toml value.
- Re-verified directly (2026-07-19) by calling
  `agent.config_builders._build_memory_config({"use_memory_layer": False,
  "memory_embed_enabled": False, ...})` — returns `True`/`True` regardless.

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

Decide (a) or (b) above. If (b): simply un-comment the two lines in
`_build_memory_config()` (`memory=MemoryConfig(use_memory_layer=bool(cfg.get("use_memory_layer", True)), memory_embed_enabled=bool(cfg.get("memory_embed_enabled", True)), ...)`,
defaulting to `True` to match the current dataclass defaults) — this is now a
purely additive, low-risk change since the `_REMOVED_KEYS`/`_FORBIDDEN_KEYS`
stripping mechanisms that might have once fought against this are gone
(`9711ca96`). Also update
`docs/05_agent_08_01_configuration-loading-agent-config-part1.md`'s
`use_memory_layer`/`memory_embed_enabled` bullets, which still describe the
now-removed `_REMOVED_KEYS` mechanism as the reason these keys are ignored —
that description is stale post-`9711ca96` even though its conclusion (dataclass
default is authoritative) remains correct.
