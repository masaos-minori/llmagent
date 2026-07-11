---
title: "Scripts File Structure: Agent Services & Workflow (Part 3/5)"
category: overview
tags:
  - scripts
  - agent
  - mcp-server
  - file-structure
related:
  - 01_overview-files-03-scripts-part1.md
  - 01_overview-files-03-scripts-part2.md
  - 01_overview-files-03-scripts-part4.md
  - 01_overview-files-03-scripts-part5.md
  - 01_overview.md
source:
  - 01_overview-files-03-scripts.md
---


# ファイル構成

アーキテクチャ概要 → [`01_overview-arch-01-process.md`](01_overview-arch-01-process.md), [`01_overview-arch-02-pipelines.md`](01_overview-arch-02-pipelines.md), [`01_overview-arch-03-features.md`](01_overview-arch-03-features.md)

## 3. ファイル構成

デプロイ先のディレクトリ構成:


```
│   │   ├─ services/                        # サービスレイヤー (agent/services/ ディレクトリ内)
│   │   │   └─ __init__.py                  # services パッケージ初期化
│   │   │   ├─ enums.py                     # McpTier / McpAvailability / ConversationActionType / ExportFormat
│   │   │   ├─ exceptions.py                # McpProbeError / SessionTitleGenerationError / ConfigReloadValidationError 等
│   │   │   ├─ models.py                    # SessionTitleResult / McpProbeResult / SessionRestoreResult / DbStats 等
│   │   │   ├─ config_reload.py             # 設定リロード
│   │   │   ├─ context_view.py              # コンテキストビュー
│   │   │   ├─ conversation_service.py      # 会話サービス
│   │   │   ├─ db_maintenance_service.py    # DB 保守サービス
│   │   │   ├─ export_formatter.py          # エクスポートフォーマット
│   │   │   ├─ io_ports.py                  # I/O ポート管理
│   │   │   ├─ mcp_status.py                # MCP サーバステータス
│   │   │   ├─ rag_maintenance_service.py   # RAG 保守サービス
│   │   │   ├─ session_restore.py           # セッション復元
│   │   │   ├─ session_title.py             # セッションタイトル生成
│   │   │   ├─ typed_validators.py          # 設定リロード用型境界抽出ヘルパー
│   │   │   └─ undo_service.py              # アンドゥサービス
│   │   ├─ shared/                          # agent パッケージ内共有型 (agent 層専用)
│   │   │    ├─ __init__.py                 # shared パッケージ初期化
│   │   │    ├─ enums.py                    # 空ファイル: カナonicalな列挙型は agent.memory.enums / agent.tool_enums
│   │   │    ├─ exceptions.py               # 空ファイル: カナonicalな例外は agent.commands/agent.services/agent.memory/agent.tool_exceptions
│   │   │    ├─ health_models.py            # ヘルスチェックモデル
│   │   │   │    ├─ ServiceWarning: label, url, message
│   │   │   │    ├─ HealthCheckResult: warnings, errors; has_issues (prop), warning_messages(), error_messages()
│   │   │   │    └─ McpHealthProbeResult: reachable, status_code, restart_recommended, operator_action_required, body
│   │   │    └─ models.py                   # エージェント共通データモデル
│   │   │       ├─ ToolApprovalEvent: event, task_id, tool, operation_type, resource_scope, risk, decision, args_preview, ts, workflow_id, session_id
│   │   │       ├─ ApprovalDecisionEvent: event, task_id, tool, risk_level, decision, escalation_reason, ts, workflow_id, session_id
│   │   │       └─ ToolExecEvent: event, task_id, tool, operation_type, resource_scope, mcp_request_id, is_error, args_preview, ts, source, error_type, workflow_id, session_id, artifact_uri
│   │   └─ workflow/                        # ワークフローエンジン
│   │       ├─ models.py                    # ワークフローデータモデル
│   │       ├─ state_store.py               # ワークフロー状態ストア
│   │       ├─ workflow_engine.py           # WorkflowEngine: ターン実行エンジン
│   │       ├─ workflow_loader.py           # ワークフローローダー
│   │       ├─ approval_ops.py              # 承認操作 (request, resolve, get_pending)
│   │       ├─ artifact_ops.py              # 成果物操作 (record_artifact)
│   │       ├─ attempt_ops.py               # アテンプト操作 (start, finish, count)
│   │       ├─ idempotency_ops.py           # 冪等性操作 (is_event_processed, begin_stage_if_new)
│   │       ├─ task_ops.py                  # タスク CRUD (create, update_status, get_by_id, list_pending)
│   │       └─ __init__.py                  # workflow パッケージ初期化
```

## Related Documents

- `01_overview-files-03-scripts-part1.md`
- `01_overview-files-03-scripts-part2.md`
- `01_overview-files-03-scripts-part4.md`
- `01_overview-files-03-scripts-part5.md`

## Keywords

scripts
agent
mcp-server
file-structure
