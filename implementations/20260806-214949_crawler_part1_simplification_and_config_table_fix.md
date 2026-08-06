## Goal

Simplify `docs/03_rag_02_02_ingestion_pipeline-crawler-part1.md` by removing redundant method/utility tables and refining the configuration table to distinguish between code-fallback defaults and actual operational values from `config/crawler.toml`.

## Scope

- **In-Scope**: Modifying `docs/03_rag_02_02_ingestion_pipeline-crawler-part1.md` to:
  - Remove "公開メソッド" (public methods) and "モジュールレベルのユーティリティ" (module-level utility) tables.
  - Refine the §2.1.1 configuration table to only include `max_depth`, `max_pages`, and `skip_nofollow`.
  - Update those 3 rows to show both the code-fallback value and the operational value from `config/crawler.toml`.
  - Add a link to `docs/03_rag_05_1-configuration-reference.md` for the full parameter list.
- **Out-of-Scope**:
  - Modifying `docs/03_rag_05_1-configuration-reference.md`.
  - Modifying `scripts/rag/ingestion/crawler.py` or `config/crawler.toml`.

## Assumptions

1. Current verified values for the 3 parameters are:
   - `max_depth`: no fallback; operational = `3`.
   - `max_pages`: fallback = `500`; operational = `200`.
   - `skip_nofollow`: fallback = `False`; operational = `true`.
2. The existing BFS-strategy/concurrency-control prose should be kept.
3. The `CrawlPayload` TypedDict table should be kept.

## Design decisions

- Treat additions as insert-only — do not modify existing text outside the target section.
- Use grep-based verification rather than Markdown AST parsing since we only need string-level comparison.

## Alternatives considered

- Rewrite the entire crawler part1 doc: rejected because scope is limited to simplifying tables.
- Create a separate document for config values: rejected because scope is limited to this doc.

## Compatibility considerations

- Added sentences must use existing Japanese terminology conventions.
- Cross-references must use existing Markdown conventions within the document.

## Security considerations

N/A — documentation-only changes.

## Rollback considerations

- If added sentences cause formatting issues, revert to git history before edit.
- If table removal breaks downstream references, restore tables.

## Implementation

### Target file

`docs/03_rag_02_02_ingestion_pipeline-crawler-part1.md`

### Procedure

1. Verify existence of the target file.
2. Confirm current values in `scripts/rag/ingestion/crawler.py` and `config/crawler.toml` to ensure requirements haven't gone stale.
3. Locate §2.1 in the document.
4. Delete the "公開メソッド" and "モジュールレベルのユーティリティ" tables.
5. Locate the §2.1.1 "設定パラメータ" table.
6. Replace its contents with a new table containing only:
   - `max_depth`: (No fallback / Operational: 3)
   - `max_pages`: (Fallback: 500 / Operational: 200)
   - `skip_nofollow`: (Fallback: False / Operational: true)
7. Append a pointer to `docs/03_rag_05_1-configuration-reference.md` §1.1 for the full list.

### Method

Direct file edit using sed or manual editing.

### Details

```bash
# Find the public methods section
grep -n "公開メソッド\|public.*method" docs/03_rag_02_02_ingestion_pipeline-crawler-part1.md

# Find the module-level utilities section
grep -n "モジュールレベル.*ユーティリティ\|module.*utility" docs/03_rag_02_02_ingestion_pipeline-crawler-part1.md

# Find the configuration table
grep -n "設定パラメータ\|Configuration.*Parameter" docs/03_rag_02_02_ingestion_pipeline-crawler-part1.md

# Verify current values in crawler.py
grep -rn "max_depth\|max_pages\|skip_nofollow" scripts/rag/ingestion/crawler.py

# Verify current values in crawler.toml
grep -rn "max_depth\|max_pages\|skip_nofollow" config/crawler.toml

# Verify configuration reference doc exists
ls -la docs/03_rag_05_1-configuration-reference.md
```

Insertion pattern:
- After §2.1 header, delete the "公開メソッド" and "モジュールレベルのユーティリティ" tables entirely.
- Replace the §2.1.1 "設定パラメータ" table with:
  ```markdown
  | パラメータ | コードフォールバック値 | 本番環境値 (config/crawler.toml) |
  |---|---|---|
  | max_depth | なし | 3 |
  | max_pages | 500 | 200 |
  | skip_nofollow | False | true |
  
  > 全パラメータ一覧は [§1.1 Configuration Reference](../03_rag_05_1-configuration-reference.md) を参照してください。
  ```

### Target file

Verification

### Procedure

1. Manually verify the simplified structure and accurate values.
2. Ensure the `CrawlPayload` table and BFS prose remain intact.
3. Run lint check on modified file.

### Method

Manual verification + tool execution.

### Details

```bash
# Verify public methods table removed
grep -c "公開メソッド.*Table\|public.*method.*Table" docs/03_rag_02_02_ingestion_pipeline-crawler-part1.md

# Verify module-level utilities table removed
grep -c "モジュールレベル.*ユーティリティ.*Table\|module.*utility.*Table" docs/03_rag_02_02_ingestion_pipeline-crawler-part1.md

# Verify config table updated
grep -c "max_depth.*3\|max_pages.*200\|skip_nofollow.*true" docs/03_rag_02_02_ingestion_pipeline-crawler-part1.md

# Verify configuration reference link added
grep -c "03_rag_05_1-configuration-reference.md" docs/03_rag_02_02_ingestion_pipeline-crawler-part1.md

# Verify CrawlPayload table preserved
grep -c "CrawlPayload" docs/03_rag_02_02_ingestion_pipeline-crawler-part1.md

# Verify BFS prose preserved
grep -c "BFS\|breadth-first" docs/03_rag_02_02_ingestion_pipeline-crawler-part1.md

# Run lint check
ruff check docs/03_rag_02_02_ingestion_pipeline-crawler-part1.md
```

Expected outcomes:
- Public methods and module-level utilities tables removed
- Configuration table refined to three columns (parameter, fallback, operational)
- Only three parameters shown (max_depth, max_pages, skip_nofollow)
- Link to configuration reference added
- CrawlPayload table and BFS prose preserved
- Zero lint errors on the file
- Document structure preserved (no accidental restructuring)

## Validation plan

| Check | Tool | Target | Expected Outcome |
|---|---|---|---|
| Lint | `ruff check docs/03_rag_02_*.md` | Docs files | 0 errors |
| Manual | Visual/Grep | Content accuracy | Tables removed/refined correctly; correct values shown |

## Out of scope

- Modifications to `scripts/rag/pipeline.py`, `scripts/mcp_servers/rag_pipeline/`.
- Modifications to any other documentation files.
- Creating new documentation files.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: requires/20260802-175218_require.md
- Source plan: plans/20260805-123400_plan.md
- Source implementation procedure: N/A
- Generated at: 20260806-214949
- Related target files: docs/03_rag_02_02_ingestion_pipeline-crawler-part1.md
