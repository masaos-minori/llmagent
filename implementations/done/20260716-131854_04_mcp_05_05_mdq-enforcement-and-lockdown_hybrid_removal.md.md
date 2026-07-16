# Implementation: docs/04_mcp_05_05_mdq-enforcement-and-lockdown.md (remove/resolve MDQ-02 known-issue bullet)

Source plan: `plans/20260716-131500_plan.md`

Note: distinct from `implementations/20260716-131159_04_mcp_05_05_mdq-enforcement-and-lockdown.md.md`
(plan 02, resolves the `fts_consistency_check`/`fts_rebuild` drift bullet).
Both target the same "既知の課題" (known issues) list but different
bullets — apply both.

## Goal

Remove or resolve the "MDQ-02: ハイブリッド検索の埋め込み統合（`mode=hybrid`）
は未実装" known-issue bullet — per the source plan, this issue becomes moot
once the hybrid-search placeholder is fully removed, rather than merely
staying undocumented as a known limitation.

## Scope

**In:**
- The bullet at `docs/04_mcp_05_05_mdq-enforcement-and-lockdown.md:78`:
  ```
  - MDQ-02: ハイブリッド検索の埋め込み統合（`mode=hybrid`）は未実装 — BM25 とベクトルモードのみ利用可能。
  ```

**Out:**
- The `fts_consistency_check`/`fts_rebuild` bullet immediately below
  (lines 79-84) — already handled by the companion plan-02 doc
  (`implementations/20260716-131159_...md`); do not re-edit it here.
- The `concurrency_limit` bullet (lines 85-89) — already resolved, no
  change.
- Any other section of this doc.
- Any other "MDQ-NN" issue ID referenced elsewhere in the codebase/docs —
  check via `rg -n "MDQ-02"` across `docs/` before finalizing, since other
  docs might cross-reference this issue ID and need a consistent
  resolution note too (if found, note this as a follow-up rather than
  silently leaving a dangling reference — see Details).

## Assumptions

1. Per the source plan's own framing: "it becomes moot once the
   placeholder is removed rather than merely undocumented" — meaning the
   correct action is to state resolution (bullet reworded to a past-tense
   resolution note, matching the `concurrency_limit` bullet's established
   style immediately below it), not to silently delete the bullet with no
   trace, since a future reader might search for "MDQ-02" and should find
   an explanation of what happened to it.
2. This edit must land after (or together with) the companion code-removal
   docs (`models.py`, `search.py`, `service.py`, `db_schema.py`,
   `config/mdq_mcp_server.toml`) for this same plan — otherwise the doc
   would claim resolution while the hybrid code/config still exists.
3. `check-mcp-docs`'s "Active MCP issue cross-references (MCP-01 through
   MCP-08)" check (per `rules/toolchain.md`) validates a different issue
   numbering namespace (`MCP-NN`, generic MCP-layer issues) — `MDQ-02` is a
   distinct, MDQ-specific issue ID scheme used only within this doc file;
   confirm this doesn't trip the `check-mcp-docs --skip active` validation
   unexpectedly (if it does, note the finding but do not silently add
   `--skip active` to the validation command without justification per
   `rules/coding.md`'s suppression-governance rule).

## Implementation

### Target file

`docs/04_mcp_05_05_mdq-enforcement-and-lockdown.md`

### Procedure

1. Open `docs/04_mcp_05_05_mdq-enforcement-and-lockdown.md`.
2. Run `rg -n "MDQ-02"` across `docs/` to find any other file referencing
   this issue ID; read each hit before editing to decide whether a
   matching update is needed there too (out of this doc's Scope, but worth
   flagging in the commit message if found).
3. Locate line 78:
   ```
   - MDQ-02: ハイブリッド検索の埋め込み統合（`mode=hybrid`）は未実装 — BM25 とベクトルモードのみ利用可能。
   ```
4. Replace with a resolution note matching the `concurrency_limit` bullet's
   style (state what was found, cite the resolution date and evidence):
   ```
   - MDQ-02（解決済み）: ハイブリッド検索の埋め込み統合（`mode=hybrid`）は実装されたことのない
     永続的なプレースホルダーだった（`_search_vector()` は常に空リストを返していた）ため、
     **[実装日] に `mode` パラメータを `bm25` のみに制限し、関連コード（`_search_vector()`,
     `_merge_hybrid()`, `_RRF_K`）と設定項目（`use_embedding`, `embedding_dims`,
     `vector_table`, `embedding_model`）を完全に削除した**(Explicit in code)。
     セマンティック検索が必要な場合は RAG パイプラインを使用する。
   ```
   (Replace `[実装日]` with the actual implementation date.)

### Method

Single bullet replacement in a Markdown list — no structural change to the
既知の課題 section beyond this one bullet's wording.

### Details

- Keep the "(Explicit in code)" evidence-annotation style already used
  throughout this doc.
- Do not delete the bullet outright — per Assumption 1, a resolution note
  is preferred over silent removal, matching this section's existing
  pattern for the `concurrency_limit` item.
- If step 2's cross-reference search finds other docs mentioning
  "MDQ-02" or "mode=hybrid", list them in the commit message as
  candidates for a follow-up doc pass — do not silently leave them
  inconsistent, but also do not expand this implementation's scope beyond
  this one target file without a separate plan/doc.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Bullet updated | `grep -n "MDQ-02" docs/04_mcp_05_05_mdq-enforcement-and-lockdown.md` | shows resolution-note wording, not "は未実装" framing |
| Cross-reference sweep | `rg -n "MDQ-02\|mode=hybrid" docs/` | any remaining hits outside this file are noted for follow-up, not silently ignored |
| Doc consistency | `uv run check-mcp-docs` | passes |
