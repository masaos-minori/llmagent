## Goal

Clean up redundant, code-derived tables in `RagPipeline` class documentation by replacing them with concise prose where necessary, while ensuring critical design-intent information (like `module_cfg` bypass and `http_result_kind` semantics) is preserved.

## Scope

- **In-Scope**:
  - `docs/03_rag_03_02_query_pipeline-rag-pipeline-class-part1.md`: Replace constructor/attributes/methods tables with prose; preserve `module_cfg` bypass detail.
  - `docs/03_rag_03_02_query_pipeline-rag-pipeline-class-part2.md`: Remove "HTTP RAGリクエストの詳細" table; preserve all other semantic/design tables.
- **Out-of-Scope**:
  - Any modification to `scripts/rag/pipeline.py`, `scripts/rag/pipeline_service.py`, or `scripts/rag/http_augment.py`.
  - Modification of any other documentation files.

## Assumptions

1. The replacement prose for `module_cfg` will be integrated naturally into the existing document structure.
2. All remaining tables in Part 2 are confirmed essential for understanding the design semantics.

## Design decisions

- Treat additions as insert-only — do not modify existing text outside the target section.
- Use grep-based verification rather than Markdown AST parsing since we only need string-level comparison.

## Alternatives considered

- Rewrite the entire RagPipeline doc: rejected because scope is limited to removing redundancy.
- Create a separate document for module_cfg rationale: rejected because scope is limited to these two docs.

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

`docs/03_rag_03_02_query_pipeline-rag-pipeline-class-part1.md`

### Procedure

1. Locate the constructor section ("### コンストラクタ") and extract the `module_cfg` bypass description.
2. Delete the "### コンストラクタ" heading, its table, and the associated Python code block.
3. Insert the extracted `module_cfg` description as a prose sentence under the "## 2. RagPipeline クラス" section.
4. Delete the "### 公開属性" heading and its table.
5. Delete the "### 公開メソッド" heading and its table.

### Method

Direct file edit using sed or manual editing.

### Details

```bash
# Find the constructor section
grep -n "コンストラクタ\|constructor\|__init__" docs/03_rag_03_02_query_pipeline-rag-pipeline-class-part1.md

# Find the module_cfg mention
grep -n "module_cfg.*bypass\|bypass.*module_cfg" docs/03_rag_03_02_query_pipeline-rag-pipeline-class-part1.md

# Find the public attributes section
grep -n "公開属性\|public.*attribute\|Attribute" docs/03_rag_03_02_query_pipeline-rag-pipeline-class-part1.md

# Find the public methods section
grep -n "公開メソッド\|public.*method\|Method" docs/03_rag_03_02_query_pipeline-rag-pipeline-class-part1.md
```

Insertion pattern:
- After "## 2. RagPipeline クラス" header, add prose: "このクラスのコンストラクタは `module_cfg` をバイパスして設定します。詳細はソースコードを参照してください。"
- After constructor section, delete the heading, table, and code block entirely.
- After public attributes section, delete the heading and table entirely.
- After public methods section, delete the heading and table entirely.

### Target file

`docs/03_rag_03_02_query_pipeline-rag-pipeline-class-part2.md`

### Procedure

1. Locate the "#### HTTP RAGリクエストの詳細" heading and its table.
2. Delete the heading and table.
3. Verify that "HTTPモード (`rag_service_url`)" and `http_result_kind` sections remain untouched.

### Method

Direct file edit using sed or manual editing.

### Details

```bash
# Find the HTTP request details section
grep -n "HTTP.*RAGリクエスト.*詳細\|HTTP.*RAG.*Request.*Detail" docs/03_rag_03_02_query_pipeline-rag-pipeline-class-part2.md

# Verify protected sections exist
grep -c "HTTPモード.*rag_service_url\|http_result_kind" docs/03_rag_03_02_query_pipeline-rag-pipeline-class-part2.md
```

Delete the "#### HTTP RAGリクエストの詳細" heading and its table content.

### Target file

Verification

### Procedure

1. Manually verify that the `module_cfg` detail was successfully converted to prose and that no prohibited tables remain.
2. Check for broken links or empty sections caused by deletions.
3. Run lint check on modified files.

### Method

Manual verification + tool execution.

### Details

```bash
# Verify module_cfg prose added
grep -c "module_cfg.*バイパス\|bypass.*module_cfg" docs/03_rag_03_02_query_pipeline-rag-pipeline-class-part1.md

# Verify constructor table removed
grep -c "コンストラクタ.*Table\|constructor.*Table" docs/03_rag_03_02_query_pipeline-rag-pipeline-class-part1.md

# Verify public attributes table removed
grep -c "公開属性.*Table\|public.*attribute.*Table" docs/03_rag_03_02_query_pipeline-rag-pipeline-class-part1.md

# Verify public methods table removed
grep -c "公開メソッド.*Table\|public.*method.*Table" docs/03_rag_03_02_query_pipeline-rag-pipeline-class-part1.md

# Verify HTTP request details table removed
grep -c "HTTP.*RAGリクエスト.*詳細.*Table\|HTTP.*RAG.*Request.*Detail.*Table" docs/03_rag_03_02_query_pipeline-rag-pipeline-class-part2.md

# Verify protected sections intact
grep -c "HTTPモード.*rag_service_url\|http_result_kind" docs/03_rag_03_02_query_pipeline-rag-pipeline-class-part2.md

# Run lint check
ruff check docs/03_rag_03_02_query_pipeline-rag-pipeline-class-part*.md
```

Expected outcomes:
- Constructor/attributes/methods tables replaced with prose in Part 1
- `module_cfg` bypass detail preserved as prose
- HTTP RAGリクエストの詳細 table removed from Part 2
- Protected sections (HTTPモード, http_result_kind) preserved in Part 2
- Zero lint errors on both files

## Validation plan

| Check | Tool | Target | Expected Outcome |
|---|---|---|---|
| Lint | `ruff check docs/03_rag_03_*.md` | Docs files | 0 errors |
| Manual | Visual/Grep | Table removal & preservation | Tables gone where requested; key details preserved |

## Out of scope

- Modifications to `scripts/rag/pipeline.py`, `scripts/rag/pipeline_service.py`, or `scripts/rag/http_augment.py`.
- Modifications to any other documentation files.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: requires/20260802-182043_require.md
- Source plan: plans/20260805-122915_plan.md
- Source implementation procedure: N/A
- Generated at: 20260806-213601
- Related target files: docs/03_rag_03_02_query_pipeline-rag-pipeline-class-part1.md, docs/03_rag_03_02_query_pipeline-rag-pipeline-class-part2.md
