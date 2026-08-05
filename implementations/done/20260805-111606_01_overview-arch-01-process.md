## Goal

Correct the inaccurate hardcoded MCP server count in the process-architecture diagram caption
and add two disclaimers in `docs/01_overview-arch-01-process.md`: (1) `config/agent.toml` is the
authoritative source for MCP server count/ports, not the service table; (2) port 8011 is retired
(formerly `sqlite-mcp`).

## Scope

- In scope: `docs/01_overview-arch-01-process.md` — diagram caption line (~line 46), disclaimer
  above the service table (~line 69), note near the port information (~lines 85-88).
- Out of scope: `config/agent.toml` content changes; consolidating port tables into other docs;
  changing the service table's existing row content/order.

## Assumptions

- `config/agent.toml` `[mcp_servers.*]` sections are the single source of truth for MCP server
  count and ports (per plan Assumption and confirmed by evidence below).
- Port 8011 is officially retired following removal of `sqlite-mcp` (per plan Assumption; no
  direct evidence of the historical `sqlite-mcp` entry was found in the current repo — treat the
  retirement fact as inherited from the source requirement/issue, not re-derived here).

## Design decisions

- Keep the diagram as a lightweight ASCII sketch: replace the hardcoded `11 サーバ` with prose
  that defers to `config/agent.toml` rather than trying to keep a second numeric count in sync.
- Place the "representative example" disclaimer directly above the service table (not in a
  footnote) so a reader hits it before reading specific port numbers.
- Add the port-8011-retired note next to the existing "実装上の補足" note at line 85-88 (which
  already explains that `8004`〜`8015` map to `agent.toml`), rather than creating a new subsection,
  to keep related caveats co-located.

## Alternatives considered

- Auto-generate the server count from `config/agent.toml` at doc-build time — rejected: this repo
  has no doc-generation pipeline for `docs/*.md`; would be disproportionate for a one-line caption.
- Remove the service table entirely and point only to `agent.toml` — rejected: plan explicitly
  keeps the table's content unchanged (out of scope) since it still has documentation value as a
  representative example.

## Implementation

### Target file

`docs/01_overview-arch-01-process.md`

### Procedure

1. Diagram caption fix (~line 46): replace the hardcoded `11 サーバ (:8004〜:8014)` text with
   wording that does not assert a fixed count/range, and instead refers the reader to
   `config/agent.toml` as authoritative (e.g. "MCP サーバ群 (件数・ポートは `config/agent.toml`
   の `[mcp_servers.*]` を参照)").
2. Service-table disclaimer (insert before ~line 69, i.e. immediately above the `| サービス |
   ポート | モデル | 役割 |` table header): add a one- to two-line note stating the table is a
   representative example and `config/agent.toml` is authoritative for the current server set and
   ports.
3. Port 8011 retirement note (near ~lines 85-88, alongside the existing "実装上の補足(LLMサービ
   スのURL/ポート)" paragraph): add a sentence noting port 8011 is retired (formerly `sqlite-mcp`)
   and is intentionally absent from the current table/config.
4. Manual re-read of the full updated section (lines ~30-101) to confirm wording is consistent
   with the existing evidence-citation style used elsewhere in the file (e.g. "(根拠: ...)",
   "(Explicit in code)").

### Method

- Direct Markdown edit of the three call-out locations; no code, scripts, or generated content
  involved. No test suite applies (this is a documentation-only file).

### Details

- Evidence gathered for this procedure (`grep`-based, not full-file read):
  - `docs/01_overview-arch-01-process.md:46` currently reads
    `(RAG 検索時)                       11 サーバ (:8004〜:8014)`.
  - `docs/01_overview-arch-01-process.md:69-83` service table currently lists 10 MCP-server rows
    (`web-search-mcp` 8004, `file-read-mcp` 8005, `github-mcp` 8006, `file-write-mcp` 8007,
    `file-delete-mcp` 8008, `shell-mcp` 8009, `rag-pipeline-mcp` 8010, `cicd-mcp` 8012, `mdq-mcp`
    8013, `git-mcp` 8014) plus `agent-llm`/`embed-llm` rows and a separate `eventbus` row (8015).
    Port 8011 is already absent from the table but not explained.
  - `config/agent.toml` currently defines exactly 10 `[mcp_servers.*]` sections (`shell`, `git`,
    `web_search`, `file_delete`, `file_write`, `file_read`, `github`, `cicd`, `rag_pipeline`,
    `mdq`), confirming the diagram's "11 サーバ" figure is stale (actual current count is 10, and
    even that is subject to change — hence pointing to `agent.toml` instead of hardcoding a
    number is the correct fix).
  - `docs/01_overview-arch-01-process.md:85-88` already contains a related "実装上の補足" note
    that `8004`〜`8015` map to `agent.toml`'s `[mcp_servers.*].url` — the new port-8011 note
    should be appended near this existing note, not duplicate it.

## Compatibility considerations

- Documentation-only change; no API, schema, or runtime behavior affected.
- Existing internal links to this file (checked via `grep -rl "01_overview-arch-01-process.md"`
  during implementation) are unaffected since no headings or anchors are removed/renamed.

## Security considerations

N/A — no code, secrets, or configuration values are introduced or modified.

## Rollback considerations

- Single-file Markdown edit; revert via `git checkout -- docs/01_overview-arch-01-process.md` or
  a follow-up commit reverting the three edited spans if the wording needs adjustment.

## Validation plan

- Manual read-through of the edited sections (diagram caption, table preamble, port note) to
  confirm they read naturally alongside surrounding text and evidence-citation style.
- `grep -n "サーバ\|8011\|config/agent.toml" docs/01_overview-arch-01-process.md` to confirm the
  new wording is present and the old hardcoded `11 サーバ (:8004〜:8014)` string is gone.
- Confirm no other file references the now-removed exact count string (`grep -rn "11 サーバ"
  docs/`) so no inconsistency is introduced elsewhere.
- No automated test suite applies to `docs/*.md`; `uv run check-mcp-docs` (see
  `rules/toolchain.md` §MCP documentation consistency) may optionally be run to confirm no new
  port/tool-name drift was introduced, though this file was already passing before the edit.

## Out of scope

- Any change to `config/agent.toml`.
- Consolidating the port/service table into another document.
- Changing existing service-table row content, order, or column set.
- Broader reformatting of `docs/01_overview-arch-01-process.md` beyond the three call-outs above.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260803-141113_plan.md
- Source implementation procedure: N/A
- Generated at: 20260805-111606
- Related target files: 01_overview-arch-01-process.md
