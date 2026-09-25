Source plan: `plans/20260719-093757_plan.md` ("Add `/diff` slash command to review files the agent
wrote/edited this session"), Implementation step 4 (Design step 3).

No existing implementations doc (under `implementations/` or `implementations/done/`) targets this
exact file. A broader grep for `agent_07_10` across both directories only matches unrelated docs
that merely *reference* this doc in passing (e.g. `implementations/done/20260714-213701_04_mcp_02_03_
dead-rag-settings-and-unused-commands.md`, `implementations/done/20260715-130000_docs_update.md`,
`implementations/done/20260712-164711_docs_front_matter_dead_reference_cleanup.md`,
`implementations/done/20260711-172657_docs_approve_reject_syntax_and_db_fallback_fix.md`) — none of
these is itself a procedure for editing this file's content to add a `/diff` entry. Flagged as checked,
not a genuine overlap.

## Goal

Add a new `/diff` entry to
`docs/agent_07_10_cli-and-commands-slash-commands-workflow-debug.md`, documenting the command's
behavior, its `ctx.conv.history`-only scope limitation (does not see activity from before a `/compact`
or `/clear`), and the `config/git_mcp_server.toml` `allowed_repo_paths` prerequisite — matching the
doc's existing 3-column table format and frontmatter/footer conventions.

## Scope

**In scope**
- Add a new `### Git/Diffカテゴリ` (or similarly named) section with a 3-column
  (`Command | 副作用 | 関連する状態`) table row for `/diff`, placed after the existing `### Debug /
  auditカテゴリ` section and before `### Exportカテゴリ` (or after Export — order is a minor stylistic
  choice, see Procedure), including the two explicit caveats from the plan's Design step 3.
- Update the "Keywords" footer (lines 91-96 of the current file) to add a line for the new category,
  matching its existing one-category-per-line convention.

**Out of scope**
- The `related`/frontmatter list (lines 11-22) and "Related Documents" section (lines 77-89) — both
  list *other numbered docs* (`agent_07_01` through `agent_07_11`), not command categories within
  this doc; the plan's own Affected areas note says to update these "if that doc's convention requires
  it" — direct inspection (below) confirms it does **not**: this doc's own frontmatter categories
  (Workflow, Debug/audit, Export) are not separately listed in `related`/"Related Documents" anywhere in
  the file, since those lists are for cross-document links, not intra-document section names. No change
  needed here.
- No change to `command_defs_list.py` or `cmd_context.py` themselves (paired docs).

## Assumptions

1. Current file structure, re-verified by direct read of `docs/05_agent_07_10_cli-and-commands-slash-
   commands-workflow-debug.md` (96 lines total):
   - Frontmatter (lines 1-23): `title`, `category: agent`, `tags` (list), `related` (list of other doc
     filenames).
   - `### Workflowカテゴリ` (line 29): table (lines 31-34) + a blockquote note (line 36-38) +
     `#### 起動時のリカバリ` subsection (lines 40-55).
   - `### Debug / auditカテゴリ` (line 57): table (lines 59-63), 3 rows (`/debug`, `/debug
     verbose|normal`, `/audit ...`).
   - `### Exportカテゴリ` (line 65): explanatory paragraph (lines 67-70) + table (lines 72-75), 2 rows
     (`/compact`, `/export ...`).
   - `## Related Documents` (line 77): bullet list of other doc filenames, lines 79-89.
   - `## Keywords` (line 91): one line per category, lowercase, lines 93-96 read exactly:
     ```
     workflow category
     startup recovery
     debug/audit category
     RAG/export category
     ```
2. Every existing category table uses the exact header `| Command | 副作用 | 関連する状態 |` followed
   by `|---|---|---|` (re-verified: lines 31-32, 59-60, 72-73 are byte-identical in this pattern). The
   new `/diff` row must match this header exactly.
3. `tools/check_agent_docs_consistency.py`'s `check_command_drift` function (re-verified:
   `tools/check_agent_docs_consistency.py:189-233`) scans doc files for `` `/word ...` `` inline-code
   patterns that look like slash commands and flags (WARNING, not ERROR) any name not present in
   `_COMMANDS` from `command_defs_list.py`. Since the paired
   `implementations/20260719-104306_command_defs_list.py.md` adds a matching `/diff` `CommandDef` entry,
   this doc's new `` `/diff` `` reference will resolve cleanly — but only if that paired doc's change is
   applied at or before this doc's change (or in the same commit); the plan's own Implementation step
   order already places the `CommandDef` addition (step 1) before the docs update (step 4), consistent
   with this ordering requirement.
4. No other doc under `docs/` currently documents `/diff` (verified: `rg -n "/diff" docs/` was run and
   returned no matches referring to a slash command — confirming this is a net-new addition, not an
   update to a stale existing mention).

## Implementation

### Target file

`docs/agent_07_10_cli-and-commands-slash-commands-workflow-debug.md`.

### Procedure

1. Insert a new section between `### Debug / auditカテゴリ` (ending at line 63) and
   `### Exportカテゴリ` (starting at line 65):
   ```markdown
   ### Git/Diffカテゴリ

   | Command | 副作用 | 関連する状態 |
   |---|---|---|
   | `/diff` | なし（読み取り専用；`git_diff` MCPツールを呼び出す） | `ctx.conv.history`内の`write_file`/`edit_file`ツール呼び出しをスキャンして対象パスを収集 |

   > **既知の制限:** `/diff`は現在のセッションの`ctx.conv.history`に残っているツール呼び出ししか見えない。
   > セッション中に`/compact`または`/clear`を実行すると、それ以前に書き込み/編集されたファイルは
   > `/diff`の対象から外れる（設計上の割り切り。DBベースの変更追跡は行わない）。
   >
   > **前提条件:** `git_diff`は`config/git_mcp_server.toml`の`allowed_repo_paths`にリポジトリの絶対パスが
   > 含まれている場合のみ実際の diff を返す。デフォルトは空リスト（`[]`）— fail-closed設計のため、
   > 未設定の状態では全てのリポジトリで `[DENIED] repo_path ... is not in allowed_repo_paths` という
   > 明確な拒否メッセージが表示される（エラーやクラッシュではない）。
   ```
   (Japanese phrasing above follows this doc's existing register/terminology, e.g. the `/approve`/
   `/reject` blockquote at lines 36-38 uses the same `> **ラベル:** 説明` convention; adjust exact
   wording at implementation time to match reviewer preference, but keep both the compact/clear
   limitation and the `allowed_repo_paths` prerequisite as two distinct, explicit points — both are
   required per the plan's Design step 3(a)/3(b).)
2. Update the `## Keywords` section (currently lines 91-96) to append one line:
   ```
   workflow category
   startup recovery
   debug/audit category
   RAG/export category
   git/diff category
   ```
3. Do not modify the frontmatter `related` list or `## Related Documents` section (per Scope/Out of
   scope — confirmed unnecessary, see Assumption 1's inventory: no other doc's own category names
   appear there today, so `/diff`'s category name should not either).
4. Run `uv run python tools/check_agent_docs_consistency.py` after this edit **and** after the paired
   `command_defs_list.py` doc's change have both landed, to confirm no drift warning.

### Method

Pure Markdown content insertion (new `###` section + one footer line). No code change, no schema
change. Matches the file's existing table/blockquote conventions exactly (Assumption 2).

### Details

- No new frontmatter fields introduced; `tags`/`category`/`related` all remain as-is (Scope/Out of
  scope).
- The new table row's wording deliberately avoids promising path-level filtering from `git_diff` itself
  (since `git_diff` has no such parameter — confirmed in the paired `cmd_context.py` doc's Assumption 2)
  — the "関連する状態" column instead describes `/diff`'s own client-side scan/grouping behavior, which
  is the part of the design unique to this command (the MCP tool call itself is a plain, whole-repo
  diff).

## Validation plan

| Check | Command | Target |
|---|---|---|
| Doc consistency | `uv run python tools/check_agent_docs_consistency.py` | no new ERROR/WARNING once this doc and the paired `command_defs_list.py` doc have both landed |
| New section present | `rg -n "Git/Diffカテゴリ" docs/agent_07_10_cli-and-commands-slash-commands-workflow-debug.md` | 1 match |
| New command row present | `rg -n '\`/diff\`' docs/agent_07_10_cli-and-commands-slash-commands-workflow-debug.md` | at least 1 match, inside the new table |
| Keywords updated | `rg -n "git/diff category" docs/agent_07_10_cli-and-commands-slash-commands-workflow-debug.md` | 1 match |
| Table format matches existing convention | `rg -n '\| Command \| 副作用 \| 関連する状態 \|' docs/agent_07_10_cli-and-commands-slash-commands-workflow-debug.md` | 4 matches (3 existing + 1 new) |
| No broken internal links introduced | `uv run python tools/check_agent_docs_consistency.py` (covers `check_broken_internal_links`/`check_removed_file_references`) | no new findings (this doc's edit adds no new links) |
