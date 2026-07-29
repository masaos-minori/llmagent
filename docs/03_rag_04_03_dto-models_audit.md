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

**Status**: deleted — `AuditLogRecord` と `ApprovalDecision` の両クラスはデッドコードとして削除済み。

- `scripts/rag/models_audit.py` はゼロの外部呼び出し元を確認後、2026-07-29 に削除された。
- 類似名の `ApprovalDecisionEvent`(`scripts/agent/shared/models.py`)や `ApprovalDecisionType`(`scripts/agent/tool_enums.py`)はエージェント層の独立した実装であり、本ファイルのクラスとは無関係。

## Related Documents

- [03_rag_04_05_dto-types.md](03_rag_04_05_dto-types.md)
- [03_rag_00_document-guide.md](03_rag_00_document-guide.md)

## Keywords

dto
data-model
unused-code
