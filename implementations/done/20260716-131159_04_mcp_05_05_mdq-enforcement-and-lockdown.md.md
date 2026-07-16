# Implementation: docs/04_mcp_05_05_mdq-enforcement-and-lockdown.md (resolve the drift bullet under "既知の課題")

Source plan: `plans/20260716-123031_plan.md`

## Goal

Replace the "既知の課題" (known issues) bullet describing the
`fts_consistency_check`/`fts_rebuild` schema/dispatch drift with a
resolution note, matching the pattern already used for the resolved
`concurrency_limit` item immediately below it in the same section.

## Scope

**In:**
- The bullet at `docs/04_mcp_05_05_mdq-enforcement-and-lockdown.md:79-84`:
  ```
  - `scripts/mcp_servers/mdq/tools.py` の `TOOL_LIST` は `fts_consistency_check` と `fts_rebuild`
    を `status: "admin"` として定義しており、`config/agent.toml` の `mcp_servers.mdq.tool_names`
    にも両ツール名が列挙されている。しかし `scripts/mcp_servers/mdq/server.py` の
    `_DISPATCH_TABLE` にはこの2ツールのハンドラが登録されていない。呼び出すと
    `dispatch_tool()` が「Unknown tool」エラーを返す — ツールスキーマ・設定上は存在するが
    実行経路が未接続の状態(Explicit in code)。**矛盾点として明記**（後述）。
  ```

**Out:**
- The `MDQ-02` bullet immediately above (hybrid search embedding, unrelated
  issue — remains open, no change).
- The `concurrency_limit` bullet immediately below (lines 85-89) — already
  correctly worded as a resolution note; this doc's edit should match its
  style, not alter it.
- Any other section of this doc (Fail-open/Fail-closed table, path
  authorization section above).
- The "（後述）" forward-reference this bullet makes to a "矛盾点" section
  elsewhere in the doc — locate that referenced section during
  implementation (search for "矛盾点" in the full file) and remove/update
  its corresponding entry for this same drift issue in the same change, so
  no dangling forward-reference or duplicate contradiction entry remains.

## Assumptions

1. After the companion code-removal docs land (`tools.py`, `service.py`,
   `db_fts.py`, `tool_constants.py`, `config/agent.toml`,
   `audit_target.py`), the drift no longer exists — `TOOL_LIST` has no
   `"admin"`-status entries, `tool_names` no longer lists the two names, and
   there is nothing left to dispatch or fail to dispatch.
2. The `concurrency_limit` bullet's phrasing (`...ため、**2026-07-13 に設定
   ファイルから削除した**。...`) is the established house style for a
   "resolved" bullet in this section — the replacement bullet for this
   drift issue should follow the same structure (state what was found, state
   the resolution and date, cite the verification command/evidence).
3. This doc's forward-reference "（後述）" to a "矛盾点" section is real and
   resolvable within this same file — grep for "矛盾点" across the full
   file before finalizing the edit to find and update that companion
   section (do not leave a stale forward-reference pointing to now-outdated
   content).

## Implementation

### Target file

`docs/04_mcp_05_05_mdq-enforcement-and-lockdown.md`

### Procedure

1. Open `docs/04_mcp_05_05_mdq-enforcement-and-lockdown.md`.
2. Run `grep -n "矛盾点" docs/04_mcp_05_05_mdq-enforcement-and-lockdown.md`
   to locate the referenced "矛盾点として明記" section elsewhere in the
   file; read that section fully before editing either location.
3. Replace the bullet at lines 79-84 with a resolution note following the
   `concurrency_limit` bullet's style, e.g.:
   ```
   - `scripts/mcp_servers/mdq/tools.py` の `TOOL_LIST` に `fts_consistency_check` と `fts_rebuild`
     が `status: "admin"` として定義されていたが、`scripts/mcp_servers/mdq/server.py` の
     `_DISPATCH_TABLE` にハンドラが登録されておらず、呼び出すと「Unknown tool」エラーとなる
     スキーマ・設定・実行経路間の不整合があった。運用上この2ツールを呼び出すクライアントは
     存在せず、正式な配線（safety tier・serialization・audit・テスト整備）を行う積極的な
     要件もないため、**[実装日] に両ツールをスキーマ（`TOOL_LIST`）、モデル（`models.py`）、
     サービス層（`service.py`）、`db_fts.py`、レジストリ（`tool_constants.py`）、設定
     （`config/agent.toml`）から完全に削除した**。実装は git 履歴（`db_fts.py` 削除前の
     リビジョン）から復元可能(Explicit in code)。
   ```
   (Replace `[実装日]` with the actual implementation date.)
4. Update or remove the corresponding "矛盾点として明記" section found in
   step 2 so it no longer describes this issue as an active/current
   contradiction — either delete that entry if the section is a list of
   currently-open contradictions, or add a resolution note there too,
   matching whatever convention that section already uses for closed items
   (inspect the section's existing content before deciding, since its exact
   structure is not yet known from this plan alone).

### Method

Prose replacement of one "known issue" bullet, plus a follow-up edit to a
cross-referenced section within the same file — both edits target
`docs/04_mcp_05_05_mdq-enforcement-and-lockdown.md`, so both are covered
under this single implementation doc.

### Details

- Keep the "(Explicit in code)" / "(Strongly implied by code)" evidence
  annotations already used throughout this doc — apply the same annotation
  style to the resolution note.
- Do not delete the bullet outright — the source plan explicitly says
  "replace...with a resolution note", not "remove the bullet", matching how
  `concurrency_limit` was handled (kept as a bullet, reworded to describe
  the resolution).

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Bullet updated | `grep -n "fts_consistency_check\|fts_rebuild" docs/04_mcp_05_05_mdq-enforcement-and-lockdown.md` | shows only resolution-note wording, no "Unknown tool" / active-issue framing |
| No dangling forward-ref | `grep -n "矛盾点" docs/04_mcp_05_05_mdq-enforcement-and-lockdown.md` | the referenced section (if any) is also updated/consistent, no stale contradiction entry remains |
| Doc consistency | `uv run check-mcp-docs` | passes |
