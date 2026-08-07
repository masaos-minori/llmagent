## Goal

Split the single `SearchDiagnostics` field table in `docs/03_rag_04_02_dto-models_result.md` into two distinct groups: "Local-execution counters" and "HTTP-integration-added fields", to clarify which fields are meaningful in different execution modes.

## Scope

- **In-Scope**: Modifying `docs/03_rag_04_02_dto-models_result.md` to reorganize the `SearchDiagnostics` field table into two subsections/tables as specified.
- **Out-of-Scope**:
  - Modifying `scripts/rag/models_result.py`.
  - Modifying any other documentation files.

## Assumptions

1. The current `SearchDiagnostics` table has 8 rows: `embed_ok`, `embed_failed`, `fts_errors`, `result_source`, `http_result_kind`, `remote_status_code`, `remote_latency_ms`, and `fallback_reason`.
2. The goal is to preserve all existing Type/Default/Description values exactly.

## Design decisions

- Treat additions as insert-only — do not modify existing text outside the target section.
- Use grep-based verification rather than Markdown AST parsing since we only need string-level comparison.

## Alternatives considered

- Rewrite the entire dto-models doc: rejected because scope is limited to splitting one table.
- Create a separate document for SearchDiagnostics: rejected because scope is limited to this doc.

## Compatibility considerations

- Added sentences must use existing Japanese terminology conventions.
- Cross-references must use existing Markdown conventions within the document.

## Security considerations

N/A — documentation-only changes.

## Rollback considerations

- If added sentences cause formatting issues, revert to git history before edit.

## Implementation

### Target file

`docs/03_rag_04_02_dto-models_result.md`

### Procedure

1. Verify existence of the target file.
2. Locate the `SearchDiagnostics` section in the document.
3. Remove the existing single flat table.
4. Insert a brief introductory sentence explaining the split between local and HTTP-mode fields.
5. **Group 1: Local-execution counters**
   - Create a sub-table containing: `embed_ok`, `embed_failed`, `fts_errors`.
   - Ensure Type/Default/Description values are identical to original.
6. **Group 2: HTTP-integration-added fields**
   - Create a sub-table containing: `result_source`, `http_result_kind`, `remote_status_code`, `remote_latency_ms`, `fallback_reason`.
   - Ensure Type/Default/Description values are identical to original.
   - Add a note stating these are meaningful only during remote/HTTP-delegated execution.

### Method

Direct file edit using sed or manual editing.

### Details

```bash
# Find the SearchDiagnostics section
grep -n "SearchDiagnostics\|検索診断情報" docs/03_rag_04_02_dto-models_result.md

# Find the current table headers
grep -n "Field.*Type.*Default\|フィールド.*型.*デフォルト" docs/03_rag_04_02_dto-models_result.md

# Verify embed_ok exists
grep -rn "embed_ok" scripts/rag/models_result.py

# Verify embed_failed exists
grep -rn "embed_failed" scripts/rag/models_result.py

# Verify fts_errors exists
grep -rn "fts_errors" scripts/rag/models_result.py

# Verify result_source exists
grep -rn "result_source" scripts/rag/models_result.py

# Verify http_result_kind exists
grep -rn "http_result_kind" scripts/rag/models_result.py

# Verify remote_status_code exists
grep -rn "remote_status_code" scripts/rag/models_result.py

# Verify remote_latency_ms exists
grep -rn "remote_latency_ms" scripts/rag/models_result.py

# Verify fallback_reason exists
grep -rn "fallback_reason" scripts/rag/models_result.py
```

Insertion pattern:
- After the "SearchDiagnostics" section header, replace the single table with:
  ```markdown
  ### Local-execution counters
  
  | フィールド | 型 | デフォルト値 | 説明 |
  |---|---|---|---|
  | embed_ok | int | 0 | Embedding に成功した数 |
  | embed_failed | int | 0 | Embedding に失敗した数 |
  | fts_errors | int | 0 | FTS5 クエリエラーの数 |
  
  ### HTTP-integration-added fields
  
  | フィールド | 型 | デフォルト値 | 説明 |
  |---|---|---|---|
  | result_source | str | "local" | 結果のソース |
  | http_result_kind | Optional[str] | null | HTTPモードの結果種別 |
  | remote_status_code | Optional[int] | null | リモートサーバーのステータスコード |
  | remote_latency_ms | Optional[float] | null | リモートサーバーへのレイテンシ（ミリ秒） |
  | fallback_reason | Optional[str] | null | フォールバック理由 |
  
  > Note: These fields are meaningful only during remote/HTTP-delegated execution.
  ```

### Target file

Verification

### Procedure

1. Manually verify the reorganized structure and content accuracy.
2. Confirm that the "実装意図 (Implementation note)" section still aligns with the new layout.
3. Run lint check on modified file.

### Method

Manual verification + tool execution.

### Details

```bash
# Verify local-execution counters table present
grep -c "embed_ok\|embed_failed\|fts_errors" docs/03_rag_04_02_dto-models_result.md

# Verify HTTP-integration-added fields table present
grep -c "result_source\|http_result_kind\|remote_status_code\|remote_latency_ms\|fallback_reason" docs/03_rag_04_02_dto-models_result.md

# Verify no single flat table remains
grep -c "SearchDiagnostics.*Table\|検索診断情報.*Table" docs/03_rag_04_02_dto-models_result.md

# Verify implementation note preserved
grep -c "実装意図\|Implementation.*note" docs/03_rag_04_02_dto-models_result.md

# Run lint check
ruff check docs/03_rag_04_02_dto-models_result.md
```

Expected outcomes:
- Single SearchDiagnostics table replaced with two grouped tables
- Local-execution counters group contains: embed_ok, embed_failed, fts_errors
- HTTP-integration-added fields group contains: result_source, http_result_kind, remote_status_code, remote_latency_ms, fallback_reason
- All Type/Default/Description values preserved from original
- Note about HTTP-mode meaningfulness added
- Zero lint errors on the file
- Document structure preserved (no accidental restructuring)

## Validation plan

| Check | Tool | Target | Expected Outcome |
|---|---|---|---|
| Lint | `ruff check docs/03_rag_04_*.md` | Docs files | 0 errors |
| Manual | Visual/Grep | Table structure | Two clearly labeled groups with correct field counts |

## Out of scope

- Modifications to `scripts/rag/pipeline.py`, `scripts/mcp_servers/rag_pipeline/`.
- Modifications to any other documentation files.
- Creating new documentation files.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: requires/20260802-182923_require.md
- Source plan: plans/20260805-123500_plan.md
- Source implementation procedure: N/A
- Generated at: 20260806-215254
- Related target files: docs/03_rag_04_02_dto-models_result.md
