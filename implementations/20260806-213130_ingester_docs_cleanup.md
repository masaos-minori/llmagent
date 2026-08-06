## Goal

Clean up redundant, code-derived tables in ChunkSplitter ingestion documentation by replacing them with concise prose pointers to the implementation source, while preserving essential design-intent information.

## Scope

- **In-Scope**:
  - `docs/03_rag_02_04_ingestion_pipeline-ingester-part1.md`: Remove Dataclass and Public Methods tables; add prose pointers. Preserve §4.2.1.
  - `docs/03_rag_02_04_ingestion_pipeline-ingester-part2.md`: Remove DB tables and structured-field columns; add prose pointers. Preserve §4.4.
- **Out-of-Scope**:
  - Any modification to `scripts/rag/ingestion/document_manager.py` or `scripts/mcp_servers/rag_pipeline/document_manager.py`.
  - Modification of any other documentation files.

## Assumptions

1. The replacement text will use English/Japanese appropriately to match the existing document style.
2. Prose pointers should direct readers to the most relevant implementation source (e.g., `scripts/rag/ingestion/ingester.py`).

## Design decisions

- Treat additions as insert-only — do not modify existing text outside the target section.
- Use grep-based verification rather than Markdown AST parsing since we only need string-level comparison.

## Alternatives considered

- Rewrite the entire Ingester doc: rejected because scope is limited to removing redundancy.
- Create a separate document for ingester rationale: rejected because scope is limited to these two docs.

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

`docs/03_rag_02_04_ingestion_pipeline-ingester-part1.md`

### Procedure

1. Locate the "Dataclass" and "公開メソッド" tables in Part 1.
2. Identify insertion points for:
   - Prose description replacing the Dataclass table.
   - Prose description replacing the Public Methods table.
3. Remove the two tables and add prose descriptions.

### Method

Direct file edit using sed or manual editing.

### Details

```bash
# Find the Dataclass table
grep -n "Dataclass\|dataclass" docs/03_rag_02_04_ingestion_pipeline-ingester-part1.md

# Find the Public Methods table
grep -n "公開メソッド\|Public.*Method" docs/03_rag_02_04_ingestion_pipeline-ingester-part1.md

# Verify protected section exists
grep -c "§4\.2\.1\|削除順序.*不変条件" docs/03_rag_02_04_ingestion_pipeline-ingester-part1.md
```

Insertion pattern:
- After Dataclass table header, add prose: "For the complete list of dataclass fields, see `scripts/rag/ingestion/ingester.py`."
- After Public Methods table header, add prose: "For the complete list of public methods, see `scripts/rag/ingestion/ingester.py`."

### Target file

`docs/03_rag_02_04_ingestion_pipeline-ingester-part2.md`

### Procedure

1. Locate the "4.5 更新されるDBテーブル" table and the structured-field part of the "4.7 ロギング" table in Part 2.
2. Identify insertion points for:
   - Prose description replacing the DB tables table.
   - Prose description replacing the structured-field column.
3. Remove the two sections and add prose descriptions.

### Method

Direct file edit using sed or manual editing.

### Details

```bash
# Find the DB tables section
grep -n "4\.5.*更新されるDBテーブル\|4\.5.*DB.*Table" docs/03_rag_02_04_ingestion_pipeline-ingester-part2.md

# Find the structured-field section
grep -n "4\.7.*ロギング\|structured.*field\|構造化.*フィールド" docs/03_rag_02_04_ingestion_pipeline-ingester-part2.md

# Verify protected section exists
grep -c "§4\.4\|embedding_dims" docs/03_rag_02_04_ingestion_pipeline-ingester-part2.md
```

Insertion pattern:
- After DB tables table header, add prose: "For the current database schema, see the schema reference document."
- After structured-field column, add prose: "For log message formats, see `scripts/rag/ingestion/ingester.py`."

### Target file

Verification

### Procedure

1. Manually verify that protected sections (§4.2.1 in P1, §4.4 in P2) are intact.
2. Verify both files still render correctly as Markdown.
3. Run lint check on modified files.

### Method

Manual verification + tool execution.

### Details

```bash
# Verify protected sections preserved
grep -c "§4\.2\.1\|削除順序.*不変条件" docs/03_rag_02_04_ingestion_pipeline-ingester-part1.md
grep -c "§4\.4\|embedding_dims" docs/03_rag_02_04_ingestion_pipeline-ingester-part2.md

# Verify tables removed
grep -c "Dataclass.*Table\|公開メソッド.*Table" docs/03_rag_02_04_ingestion_pipeline-ingester-part1.md
grep -c "4\.5.*更新されるDBテーブル\|4\.7.*ロギング.*Table" docs/03_rag_02_04_ingestion_pipeline-ingester-part2.md

# Verify prose pointers added
grep -c "ingester\.py" docs/03_rag_02_04_ingestion_pipeline-ingester-part*.md

# Run lint check
ruff check docs/03_rag_02_04_ingestion_pipeline-ingester-part*.md
```

Expected outcomes:
- Two tables removed from Part 1, replaced with prose pointers
- Two sections removed from Part 2, replaced with prose pointers
- Protected sections (§4.2.1 in P1, §4.4 in P2) preserved
- Zero lint errors on both files

## Validation plan

| Check | Tool | Target | Expected Outcome |
|---|---|---|---|
| Lint | `ruff check docs/03_rag_02_*` | Docs files | 0 errors |
| Manual | Visual/Grep | Table removal & preservation | Tables gone where requested; key info preserved |

## Out of scope

- Modifications to `scripts/rag/ingestion/document_manager.py` or `scripts/mcp_servers/rag_pipeline/document_manager.py`.
- Removal of protected sections (§4.2.1 in P1, §4.4 in P2).
- Modifications to any other documentation files.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: requires/20260802-181423_require.md
- Source plan: plans/20260805-122845_plan.md
- Source implementation procedure: N/A
- Generated at: 20260806-213130
- Related target files: docs/03_rag_02_04_ingestion_pipeline-ingester-part1.md, docs/03_rag_02_04_ingestion_pipeline-ingester-part2.md
