## Goal

Simplify documentation by removing redundant code-derived tables in RAG ingestion pipeline docs and replacing them with pointers to implementation sources.

## Scope

- **In-Scope**:
  - Remove "Dataclass" table from part1.
  - Remove "公開メソッド" table from part1.
  - Keep §4.2.1 ("削除順序の不変条件") intact.
  - Remove "4.5 更新されるDBテーブル" table from part2.
  - Remove structured-field column from "4.7 ロギング" table in part2 (or entire table if appropriate).
  - Add prose pointers to source code or Reference API where tables were removed.
  - Maintain `embedding_dims` note in part2 §4.4.
- **Out-of-Scope**:
  - Modifying any source code.
  - Addressing ETag doc_id=0 issue.

## Assumptions

1. No external tools required beyond text editing.
2. Existing patterns in the codebase for prose-style references should be followed.

## Design decisions

- Replace tables with prose pointers rather than deleting sections entirely — preserves discoverability for readers who expect field/method listings.
- Keep design-relevant prose (e.g., invariant conditions) while removing mechanically derived tables.

## Alternatives considered

- Delete all derived tables without replacement: rejected because it loses useful lookup information for documentation readers.
- Link to a generated API reference page: not available yet; would require additional tooling.

## Compatibility considerations

- Readers relying on exact field names or method signatures will need to consult the source directly.
- Cross-references to deleted tables within other documents must be verified.

## Security considerations

N/A — documentation-only changes.

## Rollback considerations

- If prose pointers prove insufficient, re-insert the original tables as a temporary measure.
- If §4.2.1 or §4.4 content is accidentally modified during edits, restore from git history.

## Implementation

### Target file

`docs/03_rag_02_04_ingestion_pipeline-ingester-part1.md`

### Procedure

1. Delete "Dataclass" table (around line 39).
2. Delete "公開メソッド" table (around line 45).
3. Insert prose pointer to `scripts/rag/ingestion/ingester.py` for dataclass fields and method signatures.

### Method

Direct file edit using sed or manual editing.

### Details

- Line ~39: Remove the "Dataclass" Markdown table entirely.
- Line ~45: Remove the "公開メソッド" Markdown table entirely.
- After deletion, add prose such as: "For the complete list of dataclass fields and public methods, see `scripts/rag/ingestion/ingester.py`."

### Target file

`docs/03_rag_02_04_ingestion_pipeline-ingester-part2.md`

### Procedure

1. Delete "4.5 更新されるDBテーブル" table (around line 54).
2. Replace with prose pointer to schema definition or reference doc.
3. In "4.7 ロギング": remove structured-field column/table content and replace with prose pointer to `scripts/rag/ingestion/ingester.py`.

### Method

Direct file edit.

### Details

- Line ~54: Remove the "4.5 更新されるDBテーブル" Markdown table.
- Add prose: "For the current database schema, see the schema reference document."
- In "4.7 ロギング": delete the structured-field column from the logging table.
- Add prose: "For log message formats, see `scripts/rag/ingestion/ingester.py`."
- Ensure §4.4 (`embedding_dims` note) remains untouched.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `docs/03_rag_02_04_ingestion_pipeline-ingester-part1.md` | Manual review | `cat docs/03_rag_02_04_ingestion_pipeline-ingester-part1.md` | Tables removed, pointers added, §4.2.1 intact. |
| `docs/03_rag_02_04_ingestion_pipeline-ingester-part2.md` | Manual review | `cat docs/03_rag_02_04_ingestion_pipeline-ingester-part2.md` | Tables removed, pointers added, §4.4 intact. |

## Out of scope

- Source code modifications (`scripts/`).
- Changes to ETag/doc_id=0 behavior.
- Modifications to other RAG documentation not listed above.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260804-120000_plan_181423.md
- Source implementation procedure: N/A
- Generated at: 20260806-192254
- Related target files: docs/03_rag_02_04_ingestion_pipeline-ingester-part1.md, docs/03_rag_02_04_ingestion_pipeline-ingester-part2.md
