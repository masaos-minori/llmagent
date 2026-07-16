# Implementation: docs/04_mcp_05_05_mdq-enforcement-and-lockdown.md (document lock-based serialization model; add `enable_refresh` removal note)

Source plan: `plans/20260716-131759_plan.md`

Note: a third distinct change targeting this doc's "既知の課題"/config
-note area, alongside the plan-02 doc
(`implementations/20260716-131159_...md`, resolves the
`fts_consistency_check`/`fts_rebuild` bullet) and the plan-04 doc
(`implementations/20260716-131854_...md`, resolves the MDQ-02 hybrid-search
bullet). This doc adds new explanatory content near the existing
`concurrency_limit` note rather than resolving another known-issue bullet —
apply all three.

## Goal

Explicitly document `MdqService._index_lock` as the production
serialization mechanism for `index_paths`/`refresh_index` (already
mentioned in passing in the existing `concurrency_limit` removal note, but
not as a standalone explained model), add a removal note for
`enable_refresh` matching the existing note style, and clarify the
distinction between `enable_refresh` (removed, never enforced) and
`enable_grep` (kept, enforced).

## Scope

**In:**
- Expand on the existing brief mention of `_index_lock` at
  `docs/04_mcp_05_05_mdq-enforcement-and-lockdown.md:85-89` (currently part
  of the `concurrency_limit` removal-note bullet) into a clearer,
  standalone explanation of the lock-based serialization model — stating
  explicitly that `index_paths`/`refresh_index` both acquire this lock,
  and that this is distinct from (but complementary to) the
  `requires_serial`/`ToolScheduler` mechanism at the agent-turn level.
- Add a new bullet (or extend the existing "既知の課題"/note area)
  documenting `enable_refresh`'s removal, alongside the existing
  `concurrency_limit` removal note.
- Add a short clarifying line distinguishing `enable_grep` (enforced,
  kept) from the removed `enable_refresh` (never enforced) — per the
  source plan's Scope item "enable_grep gate classification."

**Out:**
- The `fts_consistency_check`/`fts_rebuild` bullet (already resolved by
  the plan-02 companion doc) and the `MDQ-02` hybrid-search bullet
  (already resolved by the plan-04 companion doc) — do not re-edit either.
- Any other section of this doc (path authorization, fail-open/fail-closed
  table).

## Assumptions

1. `requires_serial` at the `tools.py`/`MCPToolSchema` level is a
   *different* serialization mechanism from `MdqService._index_lock`: the
   former is consumed by `scripts/agent/tool_scheduler.py` as a global
   barrier across concurrent tool calls *within one agent turn* (verified
   in the source plan's Assumption 5 — `tool_scheduler.py:75,131,133`);
   the latter is an in-process lock inside `MdqService` that protects
   against any overlapping `index_paths`/`refresh_index` execution
   regardless of caller. Both are legitimate and complementary — this doc
   change documents the distinction rather than merging or removing
   either.
2. This doc change should reference the companion
   `tests/test_mdq_index_serialization.py` doc as the proof of the
   lock-based claim, so a future reader can find the test that verifies
   this behavior.
3. This edit must land after (or together with) the companion `service.py`
   and `config/mdq_mcp_server.toml` docs (remove `enable_refresh`) —
   otherwise the "removed" framing would be premature.

## Implementation

### Target file

`docs/04_mcp_05_05_mdq-enforcement-and-lockdown.md`

### Procedure

1. Open `docs/04_mcp_05_05_mdq-enforcement-and-lockdown.md`.
2. Locate the existing `concurrency_limit` bullet (current lines 85-89):
   ```
   - `mdq_mcp_server.toml` の `concurrency_limit` は、`scripts/mcp_servers/mdq/` 配下および
     リポジトリ全体のどこからも参照されていないことを確認した（`grep -rn '"concurrency_limit"'`
     でヒットなし）ため、**2026-07-13 に設定ファイルから削除した**。実際の直列化は `MdqService`
     内の `asyncio.Lock`（`_index_lock`）により `index_paths`/`refresh_index` に対してのみ
     達成されており、設定値には依存しない(Explicit in code)。
   ```
3. Immediately after this bullet, add a new subsection expanding on the
   lock model and adding the `enable_refresh` removal note, e.g.:
   ```markdown
   - **直列化モデルの詳細:** `index_paths` と `refresh_index` はいずれも
     `MdqService._index_lock`（遅延生成される `asyncio.Lock`）を実行前に取得し、
     同時実行を防ぐ(Explicit in code)。これは `tools.py` の `requires_serial: True`
     （`scripts/agent/tool_scheduler.py` が1エージェントターン内の同時ツール呼び出しに対して
     適用するグローバルなバリア）とは別の、独立した直列化機構である。両者は補完的であり、
     いずれも削除・統合の対象ではない。この直列化が実際に機能することは
     `tests/test_mdq_index_serialization.py` で検証されている。
   - `mdq_mcp_server.toml` の `enable_refresh` は、`refresh_index()` にゲートチェックが
     一度も実装されなかった（読み込まれるが常に無視される）ため、
     **[実装日] に `service.py` と設定ファイルから削除した**。対照的に `enable_grep` は
     `grep_docs()` 内で実際に強制されており（`not self.enable_grep` の場合
     `MdqValidationError` を発生させる）、`tests/test_mdq_service.py`
     の `TestGrepDocsConfigGate` でテストされている — 両者は設定上似ているが、
     一方のみが実際の挙動に接続されている(Explicit in code)。
   ```
   (Replace `[実装日]` with the actual implementation date.)

### Method

Insert one new explanatory bullet (lock model) and one new removal-note
bullet (enable_refresh vs enable_grep) immediately after the existing
`concurrency_limit` bullet — no edits to the `concurrency_limit` bullet
itself, no edits to the two already-resolved known-issue bullets above it.

### Details

- Keep the "(Explicit in code)" evidence-annotation style already used
  throughout this doc.
- Reference the companion test file by name
  (`tests/test_mdq_index_serialization.py`) so a future reader can verify
  the claim independently.
- Replace `[実装日]` with the actual implementation date when this doc
  change lands.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Lock model documented | `grep -n "_index_lock\|直列化モデル" docs/04_mcp_05_05_mdq-enforcement-and-lockdown.md` | shows expanded explanation referencing both `index_paths`/`refresh_index` and the `requires_serial` distinction |
| `enable_refresh` removal noted | `grep -n "enable_refresh" docs/04_mcp_05_05_mdq-enforcement-and-lockdown.md` | shows removal-note wording, references `enable_grep` distinction |
| Doc consistency | `uv run check-mcp-docs` | passes |
