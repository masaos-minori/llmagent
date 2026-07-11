---
title: "6.4 models_audit.py (`scripts/rag/models_audit.py`)"
category: rag
tags:
  - rag
  - dto
  - data-model
related:
  - 03_rag_00_document-guide.md
  - 03_rag_04_05_dto-types.md
source:
  - 03_rag_04_05_dto-types.md
---

# 6.4 models_audit.py (`scripts/rag/models_audit.py`)

### 6.4 models_audit.py (`scripts/rag/models_audit.py`)

**AuditLogRecord** — 承認ワークフロー用のツール実行監査レコード。

| Field | Type | Description |
|---|---|---|
| `tool_name` | `str` | 実行されたツール名 |
| `args_masked` | `str` | マスクされた引数 (機密データは伏字化) |
| `result_summary` | `str` | 実行結果の概要 |
| `is_error` | `bool` | 実行がエラーになったか |
| `session_id` | `int \| None` | 関連するセッションID |

**ApprovalDecision** — ツール承認ワークフローからの判定結果。

| Field | Type | Description |
|---|---|---|
| `approved` | `bool` | ツール実行が承認されたか |
| `reason` | `str` | 判定の理由 |
| `risk_level` | `str` | リスクレベルの分類 |


## Related Documents

- [03_rag_04_05_dto-types.md](03_rag_04_01_dto-models_data.md)

## Keywords

dto
data-model
