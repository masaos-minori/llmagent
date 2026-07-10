---
title: "6.4 models_audit.py (`scripts/rag/models_audit.py`)"
category: rag
tags:
  - rag
  - dto
  - data-model
related:
  - 03_rag_00_document-guide.md
  - 03_rag_04_dto-types.md
source:
  - 03_rag_04_dto-types.md
---

# 6.4 models_audit.py (`scripts/rag/models_audit.py`)

### 6.4 models_audit.py (`scripts/rag/models_audit.py`)

**AuditLogRecord** — Tool execution audit record for approval workflows.

| Field | Type | Description |
|---|---|---|
| `tool_name` | `str` | Name of the tool executed |
| `args_masked` | `str` | Masked arguments (sensitive data redacted) |
| `result_summary` | `str` | Summary of the execution result |
| `is_error` | `bool` | Whether the execution resulted in an error |
| `session_id` | `int \| None` | Associated session ID |

**ApprovalDecision** — Decision from tool approval workflow.

| Field | Type | Description |
|---|---|---|
| `approved` | `bool` | Whether the tool execution is approved |
| `reason` | `str` | Reason for the decision |
| `risk_level` | `str` | Risk level classification |


## Related Documents

- [03_rag_04_dto-types.md](03_rag_04_dto-models_data.md)

## Keywords

dto
data-model
