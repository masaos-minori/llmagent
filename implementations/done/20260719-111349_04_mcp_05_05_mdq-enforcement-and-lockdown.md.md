# Implementation: `docs/04_mcp_05_05_mdq-enforcement-and-lockdown.md` (tags_json/token_count closure note)

Source plan: `plans/20260719-100727_plan.md` ("Implement `tags_json`/`token_count` in mdq-mcp;
reconcile stale MDQ known-issue docs"), Implementation step 5 (closure-note half, this file's
share — the stale-entry deletion half targets `docs/04_mcp_90_...`, and the sibling closure note
for `docs/04_mcp_04_04_mdq.md` is covered by a separate doc).

Multiple existing implementations docs (under `implementations/done/`) also target this same
file — `20260716-131159_04_mcp_05_05_mdq-enforcement-and-lockdown.md.md`,
`20260716-131854_04_mcp_05_05_mdq-enforcement-and-lockdown_hybrid_removal.md.md`,
`20260716-132619_04_mcp_05_05_mdq-enforcement-and-lockdown_lock_model_and_enable_refresh.md.md`,
`20260716-132819_04_mcp_05_05_mdq-enforcement-and-lockdown_auth_token_clarification.md.md`. All
read by filename/topic and confirmed **not a genuine overlap**: they cover hybrid-search
removal, lock-model/enable_refresh removal, and auth-token wording clarification — none mentions
`tags_json`/`token_count` (confirmed via `grep -n "tags_json\|token_count"
docs/04_mcp_05_05_mdq-enforcement-and-lockdown.md` returning zero matches in the live file
today). Flagged as checked, not a genuine overlap, matching the convention in
`implementations/20260717-224725_repl_health.py.md`.

## Goal

Add one new bullet to this file's existing `### 既知の課題` ("known issues") section
(`docs/04_mcp_05_05_mdq-enforcement-and-lockdown.md:104-140`) stating that `tags_json` and
`token_count` — previously hardcoded placeholders — are now populated with real data, following
the same dated, "(Explicit in code)"-tagged style already used by the section's 5 existing
bullets (fts-tools removal, hybrid-search removal, concurrency_limit removal, serialization
detail, enable_refresh removal).

## Scope

**In scope**
- Insert one new bullet into the `### 既知の課題` section, immediately after the existing 5th
  bullet (enable_refresh removal, ending line 139) and before the section's closing `---`
  (line 141), per Assumption 2's exact boundary.

**Out of scope**
- Any change to the 5 existing bullets in this section (fts-tools/hybrid-search/
  concurrency_limit/serialization/enable_refresh) — all already accurate per the source plan's
  own Assumption 2 (verified: this file already correctly documents the fts-tools and
  summary-cache-era removals with the 2026-07-16 date and rationale).
- Any change to other sections of this file (e.g. `## Fail-open 対 Fail-closed のデフォルト`,
  which begins immediately after this section's closing `---` at line 143).
- `docs/04_mcp_90_...` deletion or `docs/04_mcp_04_04_mdq.md` closure note — separate docs cover
  those.

## Assumptions

1. Verified via `grep -n "tags_json\|token_count" docs/04_mcp_05_05_mdq-enforcement-and-lockdown.md`:
   zero matches — this file currently says nothing about `tags_json`/`token_count` being
   placeholders or gaps. This is a pure addition, not a correction.
2. Verified by direct read: the `### 既知の課題` section spans lines **104-140**
   (heading at 104; 5 existing bullets at lines 106-111, 112-120, 121-125, 126-132, 133-139;
   blank line 140; closing `---` at line 141). The next section, `## Fail-open 対 Fail-closed の
   デフォルト`, starts at line 143. Inserting the new bullet after line 139 (the end of the
   5th/enable_refresh bullet) and before the blank line 140 keeps it inside this section, as the
   6th bullet, without disturbing the section's closing `---` or the following section.
3. Each existing bullet in this section follows a consistent shape: a factual statement, a
   **2026-07-DD に...した** (bolded, dated action) clause describing what was done and why, and
   an `(Explicit in code)` tag at the end signaling the claim is directly verifiable against
   current source (not an inference). The new bullet follows this same shape, citing
   `2026-07-19` (today, per this session) as the closure date, contingent on the paired
   `parser.py`/`indexer.py` changes actually landing first (see Implementation step 2's ordering
   note).
4. The source plan's own Assumption 2 states this file's "既知の課題" section "already describes
   the fts-tools/summary-cache removal accurately ... no correction needed there for those two
   items; only the still-open tags_json/token_count gap needs a closure update once items 2/3
   land" — this doc is exactly that narrowly-scoped closure update, adding one bullet, not
   touching the other 5.

## Implementation

### Target file

`docs/04_mcp_05_05_mdq-enforcement-and-lockdown.md`

### Procedure

1. Open `docs/04_mcp_05_05_mdq-enforcement-and-lockdown.md`.
2. After line 139 (the end of the existing enable_refresh-removal bullet: `...一方のみが実際の
   挙動に接続されている(Explicit in code)。`) and before the blank line 140 / closing `---` at
   line 141, insert one new bullet:
   ```
   - `chunks` テーブルの `tags_json` と `token_count` は、これまで `scripts/mcp_servers/mdq/indexer.py`
     の `_index_single_file()` 内で常に `""` / `None` としてハードコードされたプレースホルダー
     だったが、**2026-07-19 に実データを格納するよう変更した**。`tags_json` は
     `scripts/mcp_servers/mdq/parser.py` の `parse_markdown()` が YAML frontmatter の `tags:`
     フィールド（リスト形式・カンマ区切り文字列形式のどちらも可）を抽出した結果を JSON 配列と
     して格納する。`token_count` はローカルなヒューリスティック（`len(content) // 4`）による
     概算値であり、正確なトークナイザーによる値ではない。`search_docs` の `tag_filter` は
     `scripts/mcp_servers/mdq/search.py` の既存の `tags_json LIKE` 条件により、この実データに
     対して照合されるようになった(Explicit in code)。
   ```
3. Confirm the section still ends with the same blank line and closing `---` (now after 6
   bullets instead of 5), and that `## Fail-open 対 Fail-closed のデフォルト` at line 143 (or its
   shifted equivalent) is untouched.

### Method

Direct Markdown insertion of one new bullet, matching the section's existing 5-bullet style
exactly (factual claim → bolded dated action → `(Explicit in code)` tag).

### Details

- Do not insert this bullet before this session's paired code changes
  (`implementations/20260719-110818_parser.py.md`,
  `implementations/20260719-110900_indexer.py.md`) actually land — the `(Explicit in code)` tag
  is this file's own convention for "independently verifiable against current source," so
  landing the doc bullet ahead of the code would make that tag false.
- Keep the bullet's wording aligned with the actual landed design (tuple return from
  `parse_markdown`, local `_estimate_token_count` heuristic in `indexer.py`) — if the
  implementer chooses a different concrete shape (e.g. a typed result object instead of a tuple,
  or a separate `token_estimate.py` module instead of an in-`indexer.py` function), update this
  bullet's file/function references to match the actually-landed code, not the paired docs'
  suggested defaults.

## Validation plan

| Check | Command | Target |
|---|---|---|
| Note present | `grep -n "tags_json\|token_count" docs/04_mcp_05_05_mdq-enforcement-and-lockdown.md` | ≥1 match, describing both fields as now real (not placeholder) |
| Section boundary intact | `grep -n "^### 既知の課題\|^---\|^## " docs/04_mcp_05_05_mdq-enforcement-and-lockdown.md` | section still opens/closes with the same headings/rules, now with 6 bullets |
| No unrelated change | `git diff docs/04_mcp_05_05_mdq-enforcement-and-lockdown.md` | only the one new bullet added; none of the existing 5 bullets modified |
| Docs consistency | `uv run check-mcp-docs` | no new ERROR/WARNING |
| Landing-order check | Manual: confirm `scripts/mcp_servers/mdq/indexer.py`'s `tags_json`/`token_count` hardcoding is actually gone before/at the same time this bullet lands | `rg -n 'tags_json = \"\"\|token_count.*None,$' scripts/mcp_servers/mdq/indexer.py` → 0 matches, confirming the `(Explicit in code)` claim is true at merge time |
