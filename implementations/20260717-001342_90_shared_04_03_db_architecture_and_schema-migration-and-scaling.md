# Implementation Procedure: Document MDQ Migration Pattern, Resolve Section 8a Contradiction, Add RAG/Session-Vector Clarification, Add Schema-Change Checklist

Source plan: `plans/20260716-144747_plan.md`
Source requirement: `requires/20260716_10_require.md`

## Goal

`docs/90_shared_04_03_db_architecture_and_schema-migration-and-scaling.md` documents all three existing DB migration/recreation patterns in this codebase (rag/session/eventbus manual recreation, workflow incremental ALTER-TABLE migration, and MDQ's previously-undocumented automatic legacy-schema detect-and-rebuild pattern), resolves its own self-flagged Section 8a contradiction, clarifies that RAG/session vector tables are unaffected by MDQ work, and adds a schema-change checklist section for future schema work.

## Scope

**In scope**
- Add a new "8c. mdq.sqlite-only automatic legacy schema detection" subsection to Section 8, documenting `scripts/mcp_servers/mdq/db_schema.py::create_production_tables()` (lines 33-44).
- Reword Section 8's opening statement so it scopes the "no incompatible migration support" claim to rag/session/eventbus only, removing the basis for Section 8a's "矛盾（要修正）" flag.
- Remove or reword the "矛盾（要修正）" flag on Section 8a now that it is no longer a contradiction.
- Add one clarifying sentence (Section 8 or 10) stating `chunks_vec`/`memories_vec` (`db/schema_sql.py`) are unrelated to and unaffected by MDQ schema/hybrid-search work.
- Add a new "スキーマ変更チェックリスト" section (numbered after the existing last section, e.g. §12), built from the requirement's "Required checklist for future schema issues" list, formatted as Markdown checkboxes matching `docs/04_mcp_06_15_new-mcp-server-addition-checklist.md`'s convention.
- Add an `mdq.sqlite` row to the §10 "正典（Source of Truth）" table.

**Out of scope**
- No migration framework implementation.
- No changes to any vector table.
- No changes to `create_schema.py`, `schema_sql.py`, or `mdq/db_schema.py` — read-only references only.

## Assumptions

1. `docs/90_shared_04_03_db_architecture_and_schema-migration-and-scaling.md` is the correct existing home for this content; no new file is created.
2. No developer checklist for DB schema-changing work exists anywhere in the repo today (`04_mcp_06_15_...` and `04_mcp_06_16_...` are MCP-server-scoped, not DB-schema-scoped).
3. MDQ's `create_production_tables()` (`scripts/mcp_servers/mdq/db_schema.py:33-44`) is a third, distinct migration pattern: detects an old `chunks` shape via `PRAGMA table_info(chunks)` and `DROP`s + lets `CREATE TABLE IF NOT EXISTS` recreate it — no version tracking, no explicit migration list, runs automatically at every service startup.
4. `chunks_vec`/`memories_vec` in `db/schema_sql.py` are unrelated to MDQ (already confirmed in `plans/done/20260716-131500_plan.md`).

## Implementation

### Target file

`docs/90_shared_04_03_db_architecture_and_schema-migration-and-scaling.md` (documentation only — no source code changes)

### Procedure

1. Read the current file in full; locate Section 8 (migration policy), Section 8a (self-flagged contradiction), Section 10 (正典 table), and the last numbered section (to determine the new checklist section's number).
2. Reword Section 8's opening sentence: change the unqualified "互換マイグレーションは非対応" (blanket rule) to explicitly scope it to rag.sqlite / session.sqlite / eventbus.sqlite.
3. Insert a new "8c. mdq.sqlite限定の自動レガシースキーマ検出" subsection immediately after 8a/8b (matching their heading level and style), describing:
   - Trigger: `create_production_tables()` runs at every MDQ service startup.
   - Detection: `PRAGMA table_info(chunks)` checks for the legacy shape (`id INTEGER PRIMARY KEY` + `chunk_id TEXT UNIQUE`).
   - Action: unconditional `DROP TABLE` followed by `CREATE TABLE IF NOT EXISTS` in the current shape (`chunk_id TEXT PRIMARY KEY`).
   - Contrast: no version tracking column, no explicit ALTER-TABLE migration list, unlike workflow.sqlite's 8a pattern.
   - Citation: `scripts/mcp_servers/mdq/db_schema.py:33-44`.
4. On Section 8a, remove or reword the "矛盾（要修正）" flag/callout, since after step 2's rewording it is a named exception in a three-pattern list rather than a contradiction of a blanket rule.
5. Add one sentence to Section 8 (or 10) stating that `chunks_vec` and `memories_vec` (defined in `db/schema_sql.py`) are unrelated to and unaffected by MDQ schema or hybrid-search cleanup work.
6. In Section 10's 正典（Source of Truth）table, add a row for `mdq.sqlite` pointing to `scripts/mcp_servers/mdq/db_schema.py::create_production_tables()`.
7. Add a new final section (numbered to follow the doc's existing sequence, e.g. §12) titled "スキーマ変更チェックリスト", containing a Markdown checkbox list built directly from the requirement's checklist items: affected DB, affected schema source file, new-install-only vs. existing-DB migration, recreation requirement, data-loss risk, test updates, and which subsystem (RAG/session/workflow/eventbus/MDQ) is affected. Match the checkbox formatting style of `docs/04_mcp_06_15_new-mcp-server-addition-checklist.md`.

### Method

- Direct Markdown text editing of the single target file; no code changes.
- Preserve existing heading numbering scheme and Japanese prose style used elsewhere in the file.
- Keep all substantive guidance for rag/session/eventbus unchanged — only the scoping qualifier in Section 8's opening sentence changes.

### Details

- Do not touch any file under `scripts/` — this is a documentation-only change.
- Do not create a new doc file; all changes land in the single existing target file.
- Cross-check that the §11 recreation-procedure cross-reference (if any) still reads correctly after Section 8's rewording.

## Validation plan

- Manual Markdown review: confirm new sections render correctly and the checklist renders as checkboxes.
- `rg -n "90_shared_04_03" docs/` — confirm any doc cross-referencing this file still makes sense after the new sections are added.
- `uv run check-mcp-docs` — confirms no regression (this doc is outside its direct scope).
- `uv run pre-commit run --all-files` — markdown lint if configured.
