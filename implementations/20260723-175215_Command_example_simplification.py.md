## Goal

Simplify long command examples and JSON examples in eight design documents by keeping only representative examples that clarify design intent, operational boundaries, failure behavior, compatibility, or data lifecycle, while moving or compressing procedural details better confirmed through execution guides, command help, source code, or generated schemas.

## Scope

**In**:
- Simplify long command and JSON examples in 8 documents
- Classify each example before editing (required for design understanding, required for operational safety, representative minimal example, procedural detail, implementation-derived payload copy, removable duplicate)
- Replace full copied JSON payloads with minimal examples where possible
- Ensure remaining examples are properly formatted as Markdown code blocks (`bash` for shell, `json` for JSON)

**Out**:
- Modifying source code
- Creating ADR documents
- Modifying `00_index.md`
- Resolving any individual NC items
- Removing startup-critical commands, failure-mode guidance, or compatibility-sensitive JSON fields

## Assumptions

1. All eight target documents exist at their expected paths.
2. The existing command/JSON examples can be safely compressed without losing operational safety information.

## Design decisions

- Classify each example using six categories before editing.
- Keep one representative minimal example per operation type; remove duplicates.
- Use exact Japanese section headings as specified in the requirement where they improve clarity.
- Preserve all operational safety content including: startup-critical commands, failure-mode guidance, and compatibility-sensitive JSON fields.

## Alternatives considered

- Delete command examples entirely: loses operator-facing contract information.
- Create separate command reference documents: fragments documentation unnecessarily.
- Keep full examples but add navigation links: doesn't reduce cognitive load.

## Implementation

### Target file

8 documents: `docs/02_deployment-part1.md`, `docs/02_deployment-part2.md`, `docs/03_rag_02_01_ingestion_pipeline-overview.md`, `docs/03_rag_02_02_ingestion_pipeline-crawler-part2.md`, `docs/03_rag_02_03_ingestion_pipeline-chunksplitter-part2.md`, `docs/03_rag_02_04_ingestion_pipeline-ingester-part2.md`, `docs/03_rag_05_2-execution-guide.md`, `docs/03_rag_05_6-local-file-re-ingestion.md`

### Procedure

1. Verify all eight target documents exist at expected paths; record any not found
2. For each document:
   a. Read the document and identify the command/JSON example sections
   b. Classify each example using the six-category classification scheme
   c. Keep examples that clarify design or operational behavior
   d. Compress repeated examples and replace full copied JSON payloads with minimal examples
   e. Ensure remaining examples are properly formatted as Markdown code blocks
3. Verify preservation of operational safety content listed in scope

### Method

Replace full command examples with minimal representative examples; remove duplicates.

### Details

Classification scheme:

| カテゴリ | 判定基準 | 対応 |
|---|---|---|
| デザイン理解必須 | 設計意図やアーキテクチャ判断を理解するために必要な例 | 保持 |
| 運用安全必須 | 起動失敗や障害復旧に直結するコマンド | 保持 |
| 代表的最小例 | 同じ操作の複数例のうち一つを残す | 最小化して保持 |
| 手順詳細 | 実行ガイドで確認可能な手順 | 圧縮または削除 |
| 実装由来ペイロードコピー | コードから直接コピーしたJSONペイロード | 最小例に置換 |
| 重複 | 同じ内容の別例 | 削除 |

For `03_rag_05_2-execution-guide.md`, simplify the example sections:

```markdown
# 2. 実行ガイド

## 2.1 前提条件

```bash
# embed-llmのヘルスチェック
curl -s http://127.0.0.1:8081/health

# 設定ファイルの確認
ls config/crawler.toml config/chunk_splitter.toml config/ingester.toml
```

## 2.2 クロール

```bash
# crawler.tomlの全URLクロール
uv run python scripts/rag/ingestion/crawler.py

# 単一URLクロール
uv run python scripts/rag/ingestion/crawler.py --url "https://example.com/" --lang en
```

## 2.3 チャンク分割

```bash
# 未処理ファイル一括分割
uv run python scripts/rag/ingestion/chunk_splitter.py

# 既存チャンクの再生成
uv run python scripts/rag/ingestion/chunk_splitter.py --force
```

## 2.4 埋め込みと保存

```bash
# 埋め込みとDB保存
uv run python scripts/rag/ingestion/ingester.py

# 強制再登録
uv run python scripts/rag/ingestion/ingester.py --force
```

## 2.5 RAG整合性チェック

```python
from db.rag_consistency import check_rag_consistency, is_consistent, summarize_issues
from db.helper import SQLiteHelper

with SQLiteHelper("rag").open() as db:
    report = check_rag_consistency(db)
    if not is_consistent(report):
        for issue in summarize_issues(report):
            print(issue)
```
```

Apply similar simplification to remaining seven documents following the same pattern, classifying each example before editing.

## Compatibility considerations

None — documentation-only change; no behavioral impact.

## Security considerations

N/A — documentation-only change.

## Rollback considerations

Restore original command/JSON examples from git history; no data migration or config changes required.

## Validation plan

| Check | Tool | Target |
|---|---|---|
| Markdown rendering | Manual review | Correct rendering |
| Content preservation | Manual review | No operational safety content loss |
| Example reduction | Manual review | Significant reduction achieved |
| Operational safety verification | Manual review | All startup-critical commands, failure-mode guidance preserved |

## Out of scope

- Modifying source code
- Creating ADR documents
- Modifying `00_index.md`
- Resolving any individual NC items
- Removing startup-critical commands, failure-mode guidance, or compatibility-sensitive JSON fields

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260723-170051_plan.md
- Source implementation procedure: N/A
- Generated at: 20260723-175215
- Related target files: Implementation-dependent — design documents
