## Goal

Clean up `docs/03_rag_02_09_ingestion_pipeline-shared-utilities.md` by removing several mechanical, code-derived tables and documenting the unconfirmed rationale for the `MIN_TEXT_LENGTH_FOR_DETECTION` constant as prose.

## Scope

- **In-Scope**:
  - `docs/03_rag_02_09_ingestion_pipeline-shared-utilities.md`: Removal of five specific tables and addition of a prose section for `MIN_TEXT_LENGTH_FOR_DETECTION`.
- **Out-of-Scope**:
  - Any modification to `scripts/rag/utils.py`, `scripts/rag/ingestion/crawler_utils.py`, or `scripts/rag/ingestion/crawler.py`.
  - Modification of any other documentation files.

## Assumptions

1. The new prose section will follow the existing document style and language (Japanese/English mix as appropriate).
2. The rationale for `MIN_TEXT_LENGTH_FOR_DETECTION` will clearly state it is "Needs Confirmation" based on the provided investigation findings.

## Design decisions

- Treat additions as insert-only — do not modify existing text outside the target section.
- Use grep-based verification rather than Markdown AST parsing since we only need string-level comparison.

## Alternatives considered

- Rewrite the entire shared utilities doc: rejected because scope is limited to removing redundancy.
- Create a separate document for MIN_TEXT_LENGTH_FOR_DETECTION rationale: rejected because scope is limited to this doc.

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

`docs/03_rag_02_09_ingestion_pipeline-shared-utilities.md`

### Procedure

1. Locate the five tables to remove:
   - "関数 / シグネチャ / 戻り値 / 説明" table.
   - "定数" table (containing `MIN_TEXT_LENGTH_FOR_DETECTION`).
   - "プロンプトインジェクションパターン" table.
   - "構造化ログキー" table.
   - "利用元" table.
2. Identify insertion points for:
   - Prose description replacing the constants table, specifically detailing `MIN_TEXT_LENGTH_FOR_DETECTION = 100` and its "Needs Confirmation" status.
3. Remove the five tables and add prose descriptions.

### Method

Direct file edit using sed or manual editing.

### Details

```bash
# Find the function/signature table
grep -n "関数.*シグネチャ\|Function.*Signature" docs/03_rag_02_09_ingestion_pipeline-shared-utilities.md

# Find the constants table
grep -n "定数\|CONSTANT\|MIN_TEXT_LENGTH_FOR_DETECTION" docs/03_rag_02_09_ingestion_pipeline-shared-utilities.md

# Find the prompt injection patterns table
grep -n "プロンプトインジェクション\|prompt.*injection" docs/03_rag_02_09_ingestion_pipeline-shared-utilities.md

# Find the structured log keys table
grep -n "構造化ログキー\|structured.*log.*key" docs/03_rag_02_09_ingestion_pipeline-shared-utilities.md

# Find the usage sources table
grep -n "利用元\|usage.*source\|utilization" docs/03_rag_02_09_ingestion_pipeline-shared-utilities.md
```

Insertion pattern:
- After constants table header, add prose: "このモジュールは以下の定数を定義しています。詳細はソースコードを参照してください。特に、`MIN_TEXT_LENGTH_FOR_DETECTION = 100` の根拠は未確認です（Needs Confirmation）。"

### Target file

Verification

### Procedure

1. Manually verify that all requested tables were removed and the prose description is present.
2. Ensure no other parts of the document were accidentally deleted.
3. Run lint check on modified file.

### Method

Manual verification + tool execution.

### Details

```bash
# Verify tables removed
grep -c "関数.*シグネチャ.*Table\|定数.*Table\|プロンプトインジェクション.*Table\|構造化ログキー.*Table\|利用元.*Table" docs/03_rag_02_09_ingestion_pipeline-shared-utilities.md

# Verify prose added
grep -c "MIN_TEXT_LENGTH_FOR_DETECTION.*100\|Needs Confirmation" docs/03_rag_02_09_ingestion_pipeline-shared-utilities.md

# Verify document integrity (no accidental deletions)
wc -l docs/03_rag_02_09_ingestion_pipeline-shared-utilities.md

# Run lint check
ruff check docs/03_rag_02_09_ingestion_pipeline-shared-utilities.md
```

Expected outcomes:
- Five tables removed from the document
- Prose description for `MIN_TEXT_LENGTH_FOR_DETECTION` with "Needs Confirmation" status present
- Zero lint errors on the file
- Document structure intact (no accidental deletions)

## Validation plan

| Check | Tool | Target | Expected Outcome |
|---|---|---|---|
| Lint | `ruff check docs/03_rag_02_09_*.md` | Docs files | 0 errors |
| Manual | Visual/Grep | Table removal & prose presence | Tables gone, `MIN_TEXT_LENGTH_FOR_DETECTION` prose exists |

## Out of scope

- Modifications to `scripts/rag/utils.py`, `scripts/rag/ingestion/crawler_utils.py`, or `scripts/rag/ingestion/crawler.py`.
- Modifications to any other documentation files.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: requires/20260802-181753_require.md
- Source plan: plans/20260805-122855_plan.md
- Source implementation procedure: N/A
- Generated at: 20260806-213314
- Related target files: docs/03_rag_02_09_ingestion_pipeline-shared-utilities.md
