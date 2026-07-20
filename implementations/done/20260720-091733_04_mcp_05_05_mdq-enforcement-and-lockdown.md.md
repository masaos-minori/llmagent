# Implementation: docs/04_mcp_05_05_mdq-enforcement-and-lockdown.md (correct the
"read-time tools bypass authorize_path()" paragraph)

Source plan: `plans/20260719-205532_plan.md`, Implementation steps Phase 4, item 2.

## Goal

Correct the paragraph at `docs/04_mcp_05_05_mdq-enforcement-and-lockdown.md:69-72` that
currently states `search_docs`/`get_chunk`/`grep_docs`/`stats` "do not go through
`authorize_path()`" — this becomes factually wrong once this plan's read-time authorization
changes (companion `search.py`/`mdq_service.py`/`db_grep.py` docs) land for three of those four
tools.

## Scope

**In scope:**
- `docs/04_mcp_05_05_mdq-enforcement-and-lockdown.md:65-72` (the bullet describing which
  methods apply `authorize_path()` checks): update to list `search_docs`/`get_chunk`/
  `grep_docs` alongside `outline`/`index_paths`/`refresh_index` as authorization-enforcing,
  and keep `stats` as the one tool that still does not (it returns aggregate counts only, no
  per-path content — unchanged, explicitly out of scope per the plan).

**Out of scope:**
- The `### 既知の課題` section (lines 104-148) — the plan's own Design step 4 says "No
  `routing.md` change needed (no new module)"; this known-issues section is a separate list of
  already-closed/still-open items unrelated to this specific stale-statement correction. Do
  not add a new bullet there for this change unless a future doc-sync pass decides a
  known-issues entry is also warranted — this document's narrow scope is the one stale
  paragraph at lines 65-72.
- `#### HTTP レベル認証（auth_token）は意図的に無効` section (lines 74-100) — unrelated,
  describes a deliberately-different, unchanged design decision (empty Bearer token).
- Any change to the companion `docs/04_mcp_04_04_mdq.md` パス制御 table — covered by its own
  separate implementation document.

## Assumptions

1. Direct read of the current file (284 lines) confirms the exact stale paragraph at
   lines 65-72:
   ```
   - 認可チェックの適用箇所は `MdqService.outline()`（`outline` ツール）と
     パス検証関数（`index_paths`/`refresh_index` ツールが使用）の2箇所。
     違反時は `MdqAuthorizationError` を送出し、HTTP 層では 403 に変換される
     (`scripts/mcp_servers/mdq/server.py` の例外ハンドラ) (Explicit in code)。
   - `search_docs`・`get_chunk`・`grep_docs`・`stats` は既にインデックス済みの DB レコードのみを
     参照するため、`authorize_path()` によるパス認可チェックを経由しない。これらのツールが
     未許可ディレクトリの内容を返さないことは、そのディレクトリが事前に `index_paths`/`refresh_index`
     で認可済みパスとしてインデックスされていないことに依存する(Strongly implied by code)。
   ```
2. Per `rules/coding.md`'s "Current behavior" classification table, this is squarely
   "Documentation fix required": the doc's own prior statement was accurate *at the time it
   was written*, but this plan's code change makes it stale/wrong — correct the doc directly
   rather than leaving the old "(Strongly implied by code)" wording in place once the new code
   makes the claim actively false. Do not silently patch the doc to match a bug; there is no
   bug here — this is planned, intentional new behavior superseding old accurate-then, wrong-now
   prose.
3. The file's established convention for citing verified-against-code claims is the
   `(Explicit in code)` / `(Strongly implied by code)` suffix tags (seen throughout this
   section and the `### 既知の課題` section) — the corrected paragraph should use
   `(Explicit in code)` once the companion code changes land, since the new authorization
   calls will be directly greppable/verifiable, same as the `outline()`/`index_paths`/
   `refresh_index` bullet already does.
4. This doc update must land only after (or together with) the companion `search.py`/
   `mdq_service.py`/`db_grep.py` code changes — landing the doc first would make its
   "(Explicit in code)" claim false at merge time, mirroring the same ordering discipline used
   elsewhere in this file (e.g. the tags_json/token_count closure-note precedent in
   `implementations/done/20260719-111349_04_mcp_05_05_mdq-enforcement-and-lockdown.md.md`).

## Implementation

### Target file

`docs/04_mcp_05_05_mdq-enforcement-and-lockdown.md`

### Procedure

1. Locate lines 65-72 (quoted in full in Assumption 1 above).
2. Replace the two bullets with:
   ```
   - 認可チェックの適用箇所は `MdqService.outline()`（`outline` ツール）、
     パス検証関数（`index_paths`/`refresh_index` ツールが使用）、および
     `search_docs`・`get_chunk`・`grep_docs`（**2026-07-20 に読み取り時の再チェックを追加**、
     下記参照）の計5ツール。違反時は `MdqAuthorizationError` を送出し、HTTP 層では 403 に
     変換される(`scripts/mcp_servers/mdq/server.py` の例外ハンドラ) (Explicit in code)。
   - `search_docs`・`get_chunk`・`grep_docs` は、返却前にインデックス済みチャンクの
     `source_path` を現在の `allowed_dirs` に対して `authorize_path()` で再チェックする。
     `search_docs` と `grep_docs`（`paths` 未指定時）は未認可の行を無音で除外し件数にも
     計上しない（fail-closed、未認可結果の存在自体を漏らさない）。`get_chunk` と
     `grep_docs`（`paths` 明示指定時）は未認可対象が含まれる場合、呼び出し全体を
     `MdqAuthorizationError` で拒否する(Explicit in code)。
   - `stats` は集計件数のみを返しパス単位のコンテンツを含まないため、
     引き続き `authorize_path()` を経由しない(Explicit in code)。
   ```
3. Confirm the surrounding section structure (`### mdq-mcp 自身の allowed_dirs 認可
   （fail-closed）`, lines 54-72, followed by the `---`/`#### HTTP レベル認証` subsection at
   line 74) is otherwise unchanged.

### Method

Direct Markdown replacement of two stale bullets with three corrected, more granular bullets
that (a) add the three newly-enforcing tools to the "applies `authorize_path()`" list,
(b) describe the two distinct enforcement behaviors (silent-drop vs. hard-reject) precisely,
and (c) explicitly keep `stats` as the one remaining non-enforcing tool with its rationale
intact.

### Details

- Do not remove the `(Explicit in code)`/`(Strongly implied by code)` tag convention — keep
  using `(Explicit in code)` for claims directly verifiable via `grep`/read of the companion
  code changes.
- Distinguish silent-drop (`search_docs`, `grep_docs` no-filter case) from hard-reject
  (`get_chunk`, `grep_docs` explicit-paths case) explicitly in the new bullet — this mirrors
  the same distinction required in the companion `docs/04_mcp_04_04_mdq.md` パス制御 table
  update; keep the two docs consistent with each other on this point.
- Use `2026-07-20` as the landing date in the bullet (today's date per this session) — adjust
  if the actual implementation lands on a different date, matching this file's existing
  convention of dating each behavior-change bullet precisely (e.g. the existing
  `**2026-07-16 に...`/`**2026-07-19 に...` bolded-date phrasing used throughout this section
  and the `### 既知の課題` section).

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Stale claim removed | `grep -n "認可チェックを経由しない" docs/04_mcp_05_05_mdq-enforcement-and-lockdown.md` | either 0 matches, or only present in a corrected form scoped to `stats` alone, not `search_docs`/`get_chunk`/`grep_docs` |
| Corrected claim present | `grep -n "authorize_path()で再チェック\|再チェックする" docs/04_mcp_05_05_mdq-enforcement-and-lockdown.md` | ≥1 match |
| `stats` still excluded | `grep -n "stats" docs/04_mcp_05_05_mdq-enforcement-and-lockdown.md` | still described as not going through `authorize_path()` |
| No unrelated change | `git diff docs/04_mcp_05_05_mdq-enforcement-and-lockdown.md` | only lines 65-72 (or their replacement range) modified; `### 既知の課題` and `auth_token` sections untouched |
| Docs consistency | `uv run check-mcp-docs` | no new ERROR/WARNING |
| Landing-order check | Manual: confirm companion `search.py`/`mdq_service.py`/`db_grep.py` code changes have landed before/with this doc update | `(Explicit in code)` claim is true at merge time |
