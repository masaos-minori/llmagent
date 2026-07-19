# Implementation procedure: `docs/05_agent_08_01_configuration-loading-agent-config-part1.md` (memory-default text update)

Source plan: `plans/20260719-095637_plan.md` ("Enable the persistent memory layer by default and add the
missing chunking step", requirement `requires/done/20260714_15_require.md`), Implementation step 4 /
Design step 6 (third of three target docs).

No existing implementations doc under `implementations/` or `implementations/done/` matches this
specific change. Several `05_agent_08_01`-named docs exist under `implementations/done/`
(e.g. `20260714-181038_...part2.md`, `20260714-181507_...workflow_definition_schema.md`,
`20260708-174000_docs_05_agent_08_l5.md`) but predate this batch and cover unrelated sections (workflow
schema, other config areas). None updates the memory-defaults text or the startup-only classification.
Flagged as checked, not a genuine overlap.

## Goal

Update this doc's "起動時のみの設定" list and any nearby default-value text so it reflects
`use_memory_layer=true`, `memory_embed_enabled=true`, `memory_local_only=false` as the new defaults, and
correct a pre-existing staleness discovered in the same section while investigating this change (see
Assumption 2).

## Scope

**In scope**
- The "起動時のみの設定" bullet list (current lines 85-90): update the `use_memory_layer` bullet's
  implied default and add `memory_embed_enabled` (see Assumption 3 for why it belongs here too).
- Correct the "`ConfigReloadService._detect_startup_only()`が`use_memory_layer`と共に2フィールドを
  比較する" claim (current lines 88-90), which is stale relative to current code (see Assumption 2).
- The `config/agent.toml` file-purpose table row (current line 68) that says
  "`use_memory_layer`は起動時のみ" — verify wording still holds (it does; only the underlying mechanism
  changed, not the classification) and extend to mention `memory_embed_enabled` for consistency with the
  bullet-list update above.

**Out of scope**
- Any other part of this doc (설정の読み込み overview, リロード実行パイプライン, Workflow Definition
  Schema sections, etc.) — untouched.
- Fixing `scripts/agent/services/config_reload.py` itself — this is a documentation-only correction; the
  code's current (dead-code-marked) state is not changed by this plan (not in the plan's Implementation
  steps or Affected areas).

## Assumptions

1. Confirmed by direct read: the "設定ファイルの所有関係とホットリロード可否" section spans current
   lines 59-100; the file-purpose table (line 66-69) has `config/agent.toml`'s Classification column
   reading "ホットリロード可能 (ほとんど); `use_memory_layer`は起動時のみ" (line 68); the "起動時のみの
   設定" bullet list is at lines 85-90.
2. **Pre-existing doc/code discrepancy, found while investigating this exact section (not introduced by
   this plan)**: the doc's current text (lines 88-90) claims
   "`ConfigReloadService._detect_startup_only()`が`use_memory_layer`と共に2フィールドを比較する"
   ("`_detect_startup_only()` compares 2 fields together with `use_memory_layer`"). Direct read of
   `scripts/agent/services/config_reload.py:422-437` shows `_detect_startup_only()` **only** actively
   compares `routing_drift_strict` (lines 434-436); the `use_memory_layer` comparison block is present
   only as dead, commented-out code (lines 429-432, each prefixed `# REMOVED: ... key removed from
   schema`). So the doc's "2 fields" claim about *how* `use_memory_layer` is tracked is currently false —
   only 1 field (`routing_drift_strict`) is actively compared inside that function today.
   Per `rules/coding.md`'s "Current behavior" classification table this is a **"Documentation fix
   required"** case (the doc is wrong, not the code) — however, the *outcome* the doc is trying to convey
   (`use_memory_layer` cannot be changed via `/reload`) remains **true**, just via a different mechanism:
   `use_memory_layer` (and `memory_embed_enabled`) are both members of
   `ConfigReloadService._REMOVED_KEYS`/`shared/config_loader.py`'s `_REMOVED_KEYS`
   (`config_reload.py:84-92`, `config_loader.py:31-39`) — any reload dict containing either key is
   rejected outright (`ConfigReloadValidationError`, `config_reload.py:127-132`) rather than being
   detected-and-skipped via `_detect_startup_only()`. Since this doc's own section is being edited for
   the default-value change anyway, this stale mechanism-description is corrected in the same pass rather
   than left to accumulate further (fixing it now avoids compounding the inaccuracy once `use_memory_layer`
   becomes `true` by default, which would make an unfixed stale claim more visible/misleading).
3. `memory_embed_enabled` was previously never listed in the "起動時のみの設定" bullet list at all, even
   though it is (per Assumption 2 and the paired `config_dataclasses.py`/`config/agent.toml` docs) subject
   to the exact same mechanism as `use_memory_layer`: both are in `_REMOVED_KEYS`/`_FORBIDDEN_KEYS`, both
   are controlled solely by the `MemoryConfig` dataclass default (not read from `config/agent.toml` at
   load time), and neither can be changed via `/reload`. Since this plan flips `memory_embed_enabled`'s
   default to `true` (making it as operationally significant as `use_memory_layer`), adding it to this
   list now — rather than leaving the omission — keeps the doc consistent with its own stated purpose
   (documenting which fields are startup-only).
4. `memory_local_only` is genuinely hot-reloadable (confirmed: `config_reload.py:450-451`,
   `if (vb := _get_bool(new_cfg, "memory_local_only")) is not None: ctx.cfg.memory.memory_local_only =
   vb`, inside `_reload_approval_settings()`, not gated by `_REMOVED_KEYS`) — it must **not** be added to
   the startup-only list; this doc's silence on `memory_local_only` today is already correct and needs
   no change beyond the default-value mention elsewhere (see Procedure step 3).

## Implementation

### Target file

`docs/05_agent_08_01_configuration-loading-agent-config-part1.md`

### Procedure

1. In the file-purpose table (current line 68), change:
   `ホットリロード可能 (ほとんど); \`use_memory_layer\`は起動時のみ`
   to:
   `ホットリロード可能 (ほとんど); \`use_memory_layer\`/\`memory_embed_enabled\`は起動時のみ`
2. In the "起動時のみの設定" bullet list (current lines 85-90):
   - Keep the `use_memory_layer` bullet (line 86), wording unchanged (`起動時にメモリサブシステムを
     有効/無効にする` remains accurate regardless of default value).
   - Add a new bullet for `memory_embed_enabled` — `起動時に埋め込み生成・KNN検索を有効/無効にする`
     (mirrors the inline code comment at `config_dataclasses.py:213`,
     `# Enable embedding generation and KNN search`).
   - Replace the `routing_drift_strict` bullet's parenthetical (current lines 88-90) so it no longer
     claims `_detect_startup_only()` compares "2 fields... と共に" `use_memory_layer`. New wording should
     state: `_detect_startup_only()` actively compares `routing_drift_strict` only
     (`agent/services/config_reload.py::_detect_startup_only()`); `use_memory_layer` and
     `memory_embed_enabled` are instead unconditionally rejected if present in a reload request, via
     `_REMOVED_KEYS` (`config_reload.py`, `shared/config_loader.py`) — both mechanisms result in the same
     practical outcome (neither field is changeable via `/reload`), so both are listed under
     "起動時のみ" here.
3. No change needed for `memory_local_only` mentions elsewhere in this doc (confirmed none exist outside
   the file-purpose table, which does not currently mention it) — the plan's instruction to reflect
   `memory_local_only=false` is satisfied by the paired `config/agent.toml` doc; this file has no
   default-value table naming `memory_local_only` to update (verified by
   `rg -n "memory_local_only" docs/05_agent_08_01_configuration-loading-agent-config-part1.md` finding no
   matches).

### Method

Prose/table-cell edits only. No new sections, no new tables.

### Details

No structural change. This is the only one of the three target docs where a genuine pre-existing
inaccuracy was found in the immediate vicinity of the requested edit; the correction is scoped tightly
to the sentence making the false "2 fields" claim and does not touch the surrounding
ホットリロード実行パイプライン or Workflow Definition Schema sections.

## Validation plan

| Check | Command | Target |
|---|---|---|
| Docs consistency | `uv run python tools/check_agent_docs_consistency.py` | no new ERROR/WARNING |
| No stale "2 fields" claim | `rg -n "2フィールド" docs/05_agent_08_01_configuration-loading-agent-config-part1.md` | 0 matches after the edit (or replaced with accurate wording) |
| `memory_embed_enabled` now listed as startup-only | `rg -n "memory_embed_enabled" docs/05_agent_08_01_configuration-loading-agent-config-part1.md` | at least one match inside the "起動時のみの設定" bullet list |
| `memory_local_only` not miscategorized | `rg -n "memory_local_only" docs/05_agent_08_01_configuration-loading-agent-config-part1.md` | 0 matches, or any match present is outside the startup-only list |
| Manual review | Read updated lines 66-90 alongside `scripts/agent/services/config_reload.py:84-92,422-437` and `shared/config_loader.py:31-39` | prose matches current code exactly |
