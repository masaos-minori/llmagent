# Implementation: docs/04_mcp_05_05_mdq-enforcement-and-lockdown.md (add auth-token/allowed_dirs clarification section)

Source plan: `plans/20260716-132334_plan.md`

Note: a fourth distinct change targeting this doc, alongside the plan-02,
plan-04, and plan-06 docs already created for this file (see
`implementations/20260716-131159_...md`,
`implementations/20260716-131854_...md`,
`implementations/20260716-132619_...md`). This one adds a new
clarification section near the existing "mdq-mcp 自身の allowed_dirs 認可"
section rather than editing a known-issue bullet — apply all four.

Documentation-only change; no code, config, or test files are touched by
this plan.

## Goal

Add an explicit clarification stating that `mdq-mcp`'s empty `auth_token`
(`attach_auth_middleware(app, "")`) is deliberate, functioning, enforced
security behavior — not a dead/removable compatibility key like
`audit_log_path` or `enable_refresh` — so no contributor working through
the other 6 requirements in this 2026-07-16 MDQ cleanup batch mistakes it
for something to remove.

## Scope

**In:**
- Add a new subsection to
  `docs/04_mcp_05_05_mdq-enforcement-and-lockdown.md`, placed immediately
  after the existing "mdq-mcp 自身の allowed_dirs 認可（fail-closed）"
  section (current lines 54-71, ending right before the `---` separator at
  line 72), covering:
  1. `mdq-mcp` runs with `attach_auth_middleware(app, "")` — an
     intentionally empty Bearer token, meaning the HTTP layer performs no
     token check (cite `scripts/mcp_servers/server.py`'s
     `attach_auth_middleware()` docstring: "When token is empty, auth is
     skipped..."; and the actual call site
     `scripts/mcp_servers/mdq/server.py:308`:
     `attach_auth_middleware(cast(_FastAPIApp, app), "")`).
  2. This is not an oversight: `scripts/mcp_servers/mdq/server.py`'s
     `MdqMCPServer` class docstring (current lines 285-291) already states:
     `"auth_token: empty string (no auth required — mdq has its own
     authorization via allowed_dirs)"`.
  3. `allowed_dirs = []` (the config default) is fail-closed / deny-all —
     already stated in `config/mdq_mcp_server.toml:5-8`'s comment and
     `scripts/mcp_servers/mdq/auth.py`'s docstring ("An empty allowlist
     means fail-closed (deny all)"), and already documented in this same
     doc's existing `allowed_dirs` section immediately above.
  4. An explicit statement: empty `auth_token` is **current, intentional
     MDQ behavior** and must not be grouped with config keys removed
     elsewhere in the same 2026-07-16 batch (`audit_log_path`,
     `concurrency_limit`, `enable_refresh`, embedding/hybrid keys,
     summary-cache keys) — those were removed because they were
     read-but-unenforced; `auth_token=""` is the opposite case: read and
     its effect (skip HTTP auth) is fully enforced and intentional.
  5. A closing note: any future change to MDQ's HTTP authentication model
     (e.g., adding a real Bearer token) requires a separate security
     design issue, not a compatibility-cleanup change.

**Out:**
- No new `docs/security*.md` file is created — per the source plan's
  Design section, no such file exists anywhere in the repo and there is no
  established generic-security-doc naming convention (all docs use the
  numbered `NN_topic_...md` scheme); creating one would be a speculative
  addition. This existing, directly-relevant doc is the correct home.
- Any change to `scripts/mcp_servers/mdq/server.py`'s
  `attach_auth_middleware(...)` call, `auth.py`'s `authorize_path()`
  logic, or `config/mdq_mcp_server.toml`'s `allowed_dirs` default —
  explicit non-goals; this is a documentation-only plan.
- Any edit to the existing "mdq-mcp 自身の allowed_dirs 認可" section's
  existing content — only a new subsection is added after it; the
  existing section's text is untouched.
- Any edit to the three other companion docs' respective sections
  (`fts_consistency_check`/`fts_rebuild` bullet, MDQ-02 bullet, lock-model/
  `enable_refresh` bullets) — disjoint content, do not re-edit here.

## Assumptions

1. `attach_auth_middleware(app, "")`'s behavior with an empty token is
   fully defined and intentional platform-wide behavior (not MDQ-specific
   special-casing) — confirmed by direct read of
   `scripts/mcp_servers/server.py`'s docstring: "When token is non-empty,
   requests without a matching Authorization header receive a 401
   response. When token is empty, auth is skipped and the middleware only
   injects the X-Request-Id response header."
2. `scripts/mcp_servers/mdq/server.py:308` is the actual call site:
   `attach_auth_middleware(cast(_FastAPIApp, app), "")` — confirmed by
   direct read.
3. `MdqMCPServer`'s class docstring (current lines 285-291) already states
   the rationale ("mdq has its own authorization via allowed_dirs") —
   confirmed by direct read; this doc change surfaces that same rationale
   in the enforcement-and-lockdown doc where a security reviewer would
   naturally look, rather than requiring them to read `server.py`'s class
   docstring directly.
4. None of the other 6 requirement plans in this 2026-07-16 batch (01, 02,
   03, 04, 05, 06) propose any change to `auth_token`, `allowed_dirs`, or
   `attach_auth_middleware` — per the source plan's Assumption 4, verified
   by reviewing each plan's Scope section (all now exist as companion
   implementation docs already created in this same batch); no conflict to
   guard against beyond this clarification itself.

## Implementation

### Target file

`docs/04_mcp_05_05_mdq-enforcement-and-lockdown.md`

### Procedure

1. Open `docs/04_mcp_05_05_mdq-enforcement-and-lockdown.md`.
2. Locate the end of the existing "mdq-mcp 自身の allowed_dirs 認可
   （fail-closed）" section (current lines 54-71), specifically the
   bullet ending "...インデックスされていないことに依存する(Strongly
   implied by code)." immediately followed by a `---` separator (line 72).
3. Insert a new subsection immediately before that `---` separator (i.e.,
   as a continuation of the same section, or as its own `####`-level
   subsection — match whichever heading depth this doc uses for closely
   related sub-topics; inspect the doc's existing heading hierarchy before
   choosing `###` vs `####`), e.g.:
   ```markdown
   #### HTTP レベル認証（auth_token）は意図的に無効

   mdq-mcp は `attach_auth_middleware(app, "")` という空の Bearer トークンで起動する
   ため、HTTP 層でのトークン検証は行われない（`scripts/mcp_servers/server.py` の
   `attach_auth_middleware()` docstring: "When token is empty, auth is skipped..."）
   (Explicit in code)。

   これは見落としではない。`scripts/mcp_servers/mdq/server.py` の `MdqMCPServer`
   クラスの docstring には次のように明記されている:
   `"auth_token: empty string (no auth required — mdq has its own authorization
   via allowed_dirs)"`(Explicit in code)。実際の呼び出しは
   `scripts/mcp_servers/mdq/server.py:308`: `attach_auth_middleware(cast(_FastAPIApp, app), "")`。

   代わりに、上記の `allowed_dirs`（デフォルト `[]`）ベースのパス認可が実際のセキュリティ
   境界として機能する。`allowed_dirs = []` は fail-closed（全パスアクセス拒否）である
   (Explicit in code、上記セクション参照)。

   > **重要:** 空の `auth_token` は、この 2026-07-16 の MDQ 互換性クリーンアップ一式
   > （`audit_log_path`, `concurrency_limit`, `enable_refresh`, embedding/hybrid
   > 関連キー, summary-cache 関連キー）で削除された「読み込まれるが強制されない」
   > 設定キーとは正反対のケースである。これらは未強制のため削除されたが、
   > `auth_token=""` は読み込まれ、その効果（HTTP 認証のスキップ）が完全に強制・
   > 意図されている**現行の仕様**であり、削除・「修正」の対象ではない。
   >
   > 将来 MDQ の HTTP 認証モデルを変更する場合（例: 実際の Bearer トークンを追加する
   > 等）は、独立したセキュリティ設計課題として扱うべきであり、互換性クリーンアップ
   > の一部として行ってはならない。
   ```
4. Confirm the new subsection reads as a natural continuation before the
   `---` separator, and that no existing content in the "mdq-mcp 自身の
   allowed_dirs 認可" section above it is altered.

### Method

Single new subsection insertion — no edits to existing prose anywhere in
this doc, no code changes (this plan is documentation-only per its own
Scope).

### Details

- Keep the "(Explicit in code)" evidence-annotation style already used
  throughout this doc.
- Cite concrete file:line references (`server.py:308`,
  `scripts/mcp_servers/server.py`'s `attach_auth_middleware()` docstring,
  `MdqMCPServer`'s class docstring) so a future reader can verify each
  claim independently, matching this doc's existing citation density.
- Do not create `docs/security*.md` or any other new file — per Design in
  the source plan, this exact doc is the correct, evidence-based home.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Section present | `grep -n "auth_token\|HTTP レベル認証" docs/04_mcp_05_05_mdq-enforcement-and-lockdown.md` | new subsection found |
| Doc consistency | `uv run check-mcp-docs` | passes |
| Manual cross-check | review the 6 other companion implementation docs' Scope sections in this batch | none reference `auth_token`/`allowed_dirs`/`attach_auth_middleware` removal |
| Pre-commit | `uv run pre-commit run --all-files` | pass (markdown lint if configured) |
