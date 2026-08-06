## Goal

Update `docs/04_mcp_05_04_mdq-rag-boundary.md` with current RAG tool names and a note about the lack of a standalone search tool, and consolidate MDQ-vs-RAG decision criteria into `05_04` by removing the redundant table from `docs/04_mcp_04_04_mdq.md`.

## Scope

- **In-Scope**:
  - `docs/04_mcp_05_04_mdq-rag-boundary.md`: Replace stale tool names (`ingest`, `search`, etc.) with current ones (`rag_run_pipeline`, `rag_debug_pipeline`, `rag_list_documents`, `rag_delete_document`) and add a note about the absence of a standalone search tool.
  - `docs/04_mcp_04_04_mdq.md`: Remove the redundant "MDQ FTS5 対 RAG の判断基準" table, leaving only a single-line reference to `05_04`.
- **Out-of-Scope**:
  - Modifying any source code.
  - Creating new documentation files.

## Assumptions

1. The current tool names are `rag_run_pipeline`, `rag_debug_pipeline`, `rag_list_documents`, and `rag_delete_document`.
2. `docs/04_mcp_05_04_mdq-rag-boundary.md` is the intended canonical source for the boundary.

## Design decisions

- Treat additions as insert-only — do not modify existing text outside the target section.
- Use grep-based verification rather than Markdown AST parsing since we only need string-level comparison.

## Alternatives considered

- Rewrite the entire mdq-rag-boundary doc: rejected because scope is limited to updating tool names.
- Create a separate document for MDQ vs RAG criteria: rejected because scope is limited to these two docs.

## Compatibility considerations

- Added sentences must use existing Japanese terminology conventions.
- Cross-references must use existing Markdown conventions within the document.

## Security considerations

N/A — documentation-only changes.

## Rollback considerations

- If added sentences cause formatting issues, revert to git history before edit.
- If table removal breaks downstream references, restore table.

## Implementation

### Target file

`docs/04_mcp_05_04_mdq-rag-boundary.md`

### Procedure

1. Verify existence of the target file.
2. Locate the "RAG を使用する場面" section in the document.
3. Replace the stale tool list with:
   - `rag_run_pipeline` (pipeline execution)
   - `rag_debug_pipeline` (debug execution with intermediate outputs)
   - `rag_list_documents` (listing documents)
   - `rag_delete_document` (deleting documents)
4. Add a note explaining that no standalone search-only tool exists, as search is an inseparable stage within the pipeline tools.

### Method

Direct file edit using sed or manual editing.

### Details

```bash
# Find the RAG usage scene section
grep -n "RAG.*使用.*場面\|RAG.*Usage.*Scene" docs/04_mcp_05_04_mdq-rag-boundary.md

# Find the stale tool mentions
grep -n "ingest\|search.*tool\|検索ツール" docs/04_mcp_05_04_mdq-rag-boundary.md

# Verify current tool names exist
grep -rn "rag_run_pipeline\|rag_debug_pipeline\|rag_list_documents\|rag_delete_document" scripts/mcp_servers/rag_pipeline/
```

Insertion pattern:
- After the "RAG を使用する場面" section header, replace the stale tool list with:
  ```markdown
  - `rag_run_pipeline`: パイプライン実行
  - `rag_debug_pipeline`: デバッグ実行（中間出力付き）
  - `rag_list_documents`: ドキュメント一覧取得
  - `rag_delete_document`: ドキュメント削除
  
  ※ 単独の検索ツールは存在しません。検索はパイプラインツールの不可欠なステージです。
  ```

### Target file

`docs/04_mcp_04_04_mdq.md`

### Procedure

1. Verify existence of the target file.
2. Locate the "MDQ FTS5 対 RAG の判断基準" table in the document.
3. Remove the table entirely.
4. Ensure a single-line reference pointing to `05_04` remains (merging with/replacing the table while preserving the existing cross-reference context).

### Method

Direct file edit using sed or manual editing.

### Details

```bash
# Find the MDQ FTS5 vs RAG criteria table
grep -n "MDQ.*FTS5.*対.*RAG.*判断基準\|MDQ.*FTS5.*vs.*RAG.*Criteria" docs/04_mcp_04_04_mdq.md

# Find the 05_04 cross-reference
grep -n "05_04\|mdq-rag-boundary" docs/04_mcp_04_04_mdq.md
```

Delete the "MDQ FTS5 対 RAG の判断基準" table content. Keep a single-line reference like:
```markdown
詳細は `docs/04_mcp_05_04_mdq-rag-boundary.md` を参照してください。
```

### Target file

Verification

### Procedure

1. Manually verify that `05_04` has the correct tools and the search-only note.
2. Manually verify that `04_04` has removed the table and correctly points to `05_04`.
3. Check for broken links or formatting errors.
4. Run lint check on modified files.

### Method

Manual verification + tool execution.

### Details

```bash
# Verify new tool names present in 05_04
grep -c "rag_run_pipeline\|rag_debug_pipeline\|rag_list_documents\|rag_delete_document" docs/04_mcp_05_04_mdq-rag-boundary.md

# Verify search-only note present in 05_04
grep -c "単独.*検索.*ツール.*存在.*しない\|standalone.*search.*only.*tool.*does.*not.*exist" docs/04_mcp_05_04_mdq-rag-boundary.md

# Verify stale tools removed from 05_04
grep -c "ingest.*tool\|search.*tool" docs/04_mcp_05_04_mdq-rag-boundary.md

# Verify table removed from 04_04
grep -c "MDQ.*FTS5.*対.*RAG.*判断基準\|MDQ.*FTS5.*vs.*RAG.*Criteria" docs/04_mcp_04_04_mdq.md

# Verify 05_04 reference in 04_04
grep -c "05_04\|mdq-rag-boundary" docs/04_mcp_04_04_mdq.md

# Run lint check
ruff check docs/04_mcp_05_04_mdq-rag-boundary.md docs/04_mcp_04_04_mdq.md
```

Expected outcomes:
- Stale tool names replaced with current ones in `05_04`
- Search-only note added to `05_04`
- Redundant table removed from `04_04`
- Single-line reference to `05_04` preserved in `04_04`
- Zero lint errors on both files
- Document structure preserved (no accidental restructuring)

## Validation plan

| Check | Tool | Target | Expected Outcome |
|---|---|---|---|
| Lint | `ruff check docs/04_mcp_*.md` | Docs files | 0 errors |
| Manual | Visual/Grep | Content accuracy | Correct tools in `05_04`; Table gone from `04_04` |

## Out of scope

- Modifications to `scripts/rag/pipeline.py`, `scripts/mcp_servers/rag_pipeline/`.
- Modifications to any other documentation files.
- Creating new documentation files.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: requires/20260802-153401_require.md
- Source plan: plans/20260805-123100_plan.md
- Source implementation procedure: N/A
- Generated at: 20260806-214346
- Related target files: docs/04_mcp_05_04_mdq-rag-boundary.md, docs/04_mcp_04_04_mdq.md
