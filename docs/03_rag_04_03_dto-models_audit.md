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

## 実装意図 (Implementation note) / 矛盾点

- `AuditLogRecord` / `ApprovalDecision` はいずれも `scripts/` 配下のどこからも import されていない(`grep -rn "from rag.models_audit\|rag.models_audit\." scripts/` で該当なし。Explicit in code、否定的事実)。
- 類似名の `ApprovalDecisionEvent`(`scripts/agent/shared/models.py`)や、ツール承認の実処理(`scripts/agent/tool_approval.py`、`scripts/agent/tool_audit.py`)は agent 層に別途独自実装されており、本ファイルの2クラスとは無関係(Explicit in code)。
- git履歴上は `f6a3d2db`(旧 `rag/models.py` 分割時)で現在の形になって以降、参照追加は行われていない(Explicit in code、`git log --oneline -- scripts/rag/models_audit.py`)。
- 以上より、本モジュールの2クラスは「RAGパイプラインのツール実行監査/承認ワークフロー用DTO」という説明どおりの用途では現状使われておらず、未使用コード(dead code)である可能性が高い(Needs confirmation — 将来の利用を見越した先行定義か、削除し忘れかは実装からは判別不能)。

## Related Documents

- [03_rag_04_05_dto-types.md](03_rag_04_05_dto-types.md)
- [03_rag_00_document-guide.md](03_rag_00_document-guide.md)

## Keywords

dto
data-model
unused-code
