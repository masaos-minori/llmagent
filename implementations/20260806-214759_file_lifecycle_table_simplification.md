## Goal

Simplify the "ファイルのライフサイクル" (File Lifecycle) table in `docs/03_rag_02_01_ingestion_pipeline-overview.md` to reduce redundancy by removing exact filename patterns and content descriptions, instead providing high-level summaries and references to detailed documentation.

## Scope

- **In-Scope**: Modifying `docs/03_rag_02_01_ingestion_pipeline-overview.md` to shorten the lifecycle table and add pointers to stage-specific detail docs.
- **Out-of-Scope**:
  - Modifying any source code.
  - Modifying the actual detail documents (`03_rag_02_02`, `03_rag_02_03`, `03_rag_02_04`).

## Assumptions

1. The goal is to maintain a summary view in the overview while delegating details to the specific part documents.
2. The existing "Related Documents" list in the overview will be preserved.

## Design decisions

- Treat additions as insert-only — do not modify existing text outside the target section.
- Use grep-based verification rather than Markdown AST parsing since we only need string-level comparison.

## Alternatives considered

- Rewrite the entire ingestion pipeline doc: rejected because scope is limited to simplifying the lifecycle table.
- Create a separate document for file lifecycle: rejected because scope is limited to this doc.

## Compatibility considerations

- Added sentences must use existing Japanese terminology conventions.
- Cross-references must use existing Markdown conventions within the document.

## Security considerations

N/A — documentation-only changes.

## Rollback considerations

- If added sentences cause formatting issues, revert to git history before edit.

## Implementation

### Target file

`docs/03_rag_02_01_ingestion_pipeline-overview.md`

### Procedure

1. Verify existence of the target file.
2. Locate the "### ファイルのライフサイクル" section in the document.
3. Rewrite the table to include only:
   - Stage name (Crawl, Split, Ingest).
   - Producing module (`crawler.py`, `chunk_splitter.py`, `ingester.py`).
   - General output directory (e.g., `{rag_src_dir}`, `{rag_src_dir}/chunk/`, `{rag_src_dir}/registered/`).
4. Remove columns for "exact filename pattern" and "detailed content description".
5. Add an explicit text note below the table: "ファイル名や詳細な内容は、各ステージの詳細ドキュメント（`03_rag_02_02`, `03_rag_02_03`, `03_rag_02_04`）を参照してください。" (referencing the appropriate docs).

### Method

Direct file edit using sed or manual editing.

### Details

```bash
# Find the file lifecycle section
grep -n "ファイル.*ライフサイクル\|File.*Lifecycle" docs/03_rag_02_01_ingestion_pipeline-overview.md

# Find the current table headers
grep -n "Stage\|Module\|Filename\|Content\|出力ディレクトリ" docs/03_rag_02_01_ingestion_pipeline-overview.md

# Verify crawler.py location
grep -rn "class Crawler\|def crawl" scripts/rag/ingestion/crawler.py

# Verify chunk_splitter.py location
grep -rn "class ChunkSplitter\|def split" scripts/rag/chunk_splitter.py

# Verify ingester.py location
grep -rn "class Ingester\|def ingest" scripts/rag/ingester.py
```

Insertion pattern:
- After the "### ファイルのライフサイクル" section header, replace the table with:
  ```markdown
  | ステージ | モジュール | 出力ディレクトリ |
  |---|---|---|
  | Crawl | crawler.py | {rag_src_dir} |
  | Split | chunk_splitter.py | {rag_src_dir}/chunk/ |
  | Ingest | ingester.py | {rag_src_dir}/registered/ |
  
  > ファイル名や詳細な内容は、各ステージの詳細ドキュメント（`03_rag_02_02`, `03_rag_02_03`, `03_rag_02_04`）を参照してください。
  ```

### Target file

Verification

### Procedure

1. Manually verify that the table is simplified and the references are correct.
2. Check for any broken formatting in the markdown.
3. Run lint check on modified file.

### Method

Manual verification + tool execution.

### Details

```bash
# Verify simplified table present
grep -c "Crawl.*crawler\.py\|Split.*chunk_splitter\.py\|Ingest.*ingester\.py" docs/03_rag_02_01_ingestion_pipeline-overview.md

# Verify references added
grep -c "03_rag_02_02\|03_rag_02_03\|03_rag_02_04" docs/03_rag_02_01_ingestion_pipeline-overview.md

# Verify old columns removed
grep -c "Filename.*Pattern\|Content.*Description" docs/03_rag_02_01_ingestion_pipeline-overview.md

# Run lint check
ruff check docs/03_rag_02_01_ingestion_pipeline-overview.md
```

Expected outcomes:
- File lifecycle table simplified to three columns (Stage, Module, Directory)
- Filename pattern and content description columns removed
- Reference note added pointing to stage-specific detail docs
- Zero lint errors on the file
- Document structure preserved (no accidental restructuring)

## Validation plan

| Check | Tool | Target | Expected Outcome |
|---|---|---|---|
| Lint | `ruff check docs/03_rag_02_*.md` | Docs files | 0 errors |
| Manual | Visual/Grep | Content accuracy | Simplified table with correct modules and directories; proper cross-references |

## Out of scope

- Modifications to `scripts/rag/pipeline.py`, `scripts/mcp_servers/rag_pipeline/`.
- Modifications to any other documentation files.
- Creating new documentation files.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: requires/20260802-175047_require.md
- Source plan: plans/20260805-123300_plan.md
- Source implementation procedure: N/A
- Generated at: 20260806-214759
- Related target files: docs/03_rag_02_01_ingestion_pipeline-overview.md
