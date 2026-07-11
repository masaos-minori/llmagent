# Implementation: Fix stale field name, bypass wording, and add strict-mode aggregation note (docs/90_shared_03_02_runtime_and_execution-plugin-and-tool-runtime.md)

## Goal

Fix three documentation gaps in `docs/90_shared_03_02_runtime_and_execution-plugin-and-tool-runtime.md`'s `plugin_registry` section:
1. Stale field name `command_shadows` in the `PluginLoadResult` code sample (actual field is `command_shadows_rejected`)
2. Under-specified "bypass" sentence naming only "cache and MCP routing" instead of the full list of mechanisms plugin tools skip
3. Missing statement of the strict-mode "attempt all, then aggregate" timing behavior of `PluginLoadError`

## Scope

**In-Scope:**
- `docs/90_shared_03_02_runtime_and_execution-plugin-and-tool-runtime.md`, section "## 4. `plugin_registry` (`shared/plugin_registry.py`)" only:
  - The `PluginLoadResult` code sample's `command_shadows: int` line
  - The "優先順位" (priority/bypass) sentence describing `@register_tool` handler dispatch order
  - Addition of one new sentence near the `PluginLoadError` description covering strict-mode aggregation timing

**Out-of-Scope:**
- `90_99.md` — confirmed non-existent in this plan's Out-of-Scope; not created or touched
- Any other section of this doc file (sections 5+, e.g. `token_counter`)
- Any Python source file — `plugin_registry.py`, `plugin_auto_discover.py`, `plugin_tool_invoker.py` are not modified; their existing behavior is already correct and is only being documented more precisely
- `docs/90_shared_03_runtime_and_execution_md.md`-equivalent implementation docs already in `implementations/done/` (a different, older pre-split doc file — not this target)

## Assumptions

1. Current content of the `PluginLoadResult` code sample (confirmed by direct read, doc lines ~63-77):
   ```python
   @dataclass(frozen=True)
   class PluginLoadResult:
       loaded_count: int
       failed: tuple[PluginFailure, ...]
       tool_conflicts_shadowed: int
       tool_conflicts_allowed: int
       command_shadows: int
   ```
   `scripts/shared/plugin_result.py::PluginLoadResult` (confirmed by direct read) actually has `command_shadows_rejected: int = 0` — there is no `command_shadows` field under any name. This is a direct, unambiguous doc/code mismatch.
2. Current bypass sentence (doc, in the "優先順位" line): "`@register_tool` ハンドラは `ToolExecutor.execute()` によってキャッシュ・MCPルーティングより**先に**チェックされる。" — names only "cache" and "MCP routing" as an umbrella. The plan's Design section specifies the expanded English replacement sentence to use instead (see Method below); this changes both the language and precision of that sentence per the plan's explicit Design text.
3. `scripts/shared/plugin_auto_discover.py::load_plugins()`'s docstring (confirmed by direct read, lines 36-37) already documents and the code already implements: "When strict_mode is True, all plugins are attempted first, then a single PluginLoadError is raised with aggregated failure details." The target doc currently only describes the return-type shape of `PluginLoadResult`/`PluginLoadError`, not this timing/aggregation behavior — this is a pure doc addition, no code change needed.
4. The doc file is partly in Japanese (e.g. the "プラグイン読込フロー" flow diagram and "優先順位" sentence use Japanese prose) with English code samples. The plan's Design section gives the replacement bypass sentence and the new aggregation sentence in English; follow the plan's Design section text for these two specific sentences as authoritative (do not translate them to Japanese), since the plan itself specifies the exact English wording to insert.
5. No other content in the file changes; sections outside `## 4. plugin_registry` are untouched.

## Implementation

### Target file

`docs/90_shared_03_02_runtime_and_execution-plugin-and-tool-runtime.md`

### Procedure

1. Open the file and locate section `## 4. plugin_registry (shared/plugin_registry.py)`.
2. In the `PluginLoadResult` code sample, replace the line `    command_shadows: int` with `    command_shadows_rejected: int  # commands rejected due to strict-mode conflict with a builtin`.
3. Locate the "優先順位" sentence describing `@register_tool` handler dispatch order (currently: "`@register_tool` ハンドラは `ToolExecutor.execute()` によってキャッシュ・MCPルーティングより**先に**チェックされる。"). Expand/replace it per the plan's Design section to explicitly name each bypassed mechanism: `ToolRegistry` route resolution, the tool-result cache, the health gate, lifecycle `ensure_ready()`, and `HttpTransport`.
4. Near the `PluginLoadError` description (the bullet list under "戻り値の型" / "- `PluginLoadError` は..."), add one new sentence stating the strict-mode "attempt all, then aggregate" timing behavior, per the plan's Design section wording.
5. Save the file.
6. Run `grep -n "command_shadows\b" docs/*.md` afterward and confirm no bare (non-`_rejected`) match remains anywhere in `docs/`.

### Method

**Step 2 replacement** (in the `PluginLoadResult` code block):

Replace:
```
    command_shadows: int
```
with:
```
    command_shadows_rejected: int  # commands rejected due to strict-mode conflict with a builtin
```

**Step 3 replacement** — expand the bypass sentence to (per plan Design section, verbatim):

"`@register_tool` handlers are checked by `ToolExecutor.execute()` **before** `ToolRegistry` route resolution, the tool-result cache, the health gate, lifecycle `ensure_ready()`, and `HttpTransport` — a plugin tool never reaches any of these MCP-routing mechanisms."

This replaces (or is placed adjacent to, superseding) the existing Japanese sentence: "`@register_tool` ハンドラは `ToolExecutor.execute()` によってキャッシュ・MCPルーティングより**先に**チェックされる。" The `@register_command` / `CommandRegistry` sentence that follows it is untouched (out of scope — the plan's Tasks concern only the `@register_tool` MCP-routing bypass list, not command dispatch order).

**Step 4 addition** — add this new sentence near the `PluginLoadError` bullet list (per plan Design section, verbatim):

"In `strict_mode=True`, **all** plugins are attempted first; a single aggregated `PluginLoadError` (naming every load failure, tool-conflict rejection, and command-conflict rejection together) is raised only after every plugin has had a chance to load — not on the first failure."

### Details

- Preserve the existing Markdown structure (headings, code fences, bullet list formatting) around each edit; only the specific sentence/line content changes.
- Do not touch the "プラグイン読込フロー" ASCII flow diagram — it already correctly states "全読込後" (after all loads) for the conflict-validation step; this is consistent with, and does not need updating for, the new aggregation sentence.
- Do not modify the `related`/`tags`/`source` YAML frontmatter at the top of the file.
- This is a docs-only change; no `deploy.sh` update needed (per plan's Affected areas: "deploy.sh: n/a").

## Validation plan

Relevant subset of the plan's Validation plan table, filtered to this target file:

| Check | Tool | Target |
|---|---|---|
| Docs | `uv run python tools/check_docs_consistency.py` | Passes |
| Manual grep | `grep -n "command_shadows\b" docs/*.md` (exact word, not `command_shadows_rejected`) | No matches remain |

No lint/mypy/test run applies to this file (Markdown, not Python) beyond the general full-suite run at the end of all phases.
