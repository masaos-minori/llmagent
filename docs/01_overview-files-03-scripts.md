
title: "Scripts File Structure: Agent Core & Memory (Part 1/5)"
category: overview
tags:
  - scripts
  - agent
  - mcp-server
  - file-structure
related:
  - 01_overview-files-03-scripts.md
  - 01_overview-files-03-scripts.md
  - 01_overview-files-03-scripts.md
  - 01_overview-files-03-scripts.md



# ファイル構成

アーキテクチャ概要 → [`01_overview-arch-01-process.md`](01_overview-arch-01-process.md), [`01_overview-arch-02-pipelines.md`](01_overview-arch-02-pipelines.md), [`01_overview-arch-03-features.md`](01_overview-arch-03-features.md)

## 3. ファイル構成

### 主要ディレクトリと責務

#### エージェント REPL パッケージ (`scripts/agent/`)

| 責務 | ファイル群 |
|---|---|
| エントリポイント | `__main__.py`, `repl.py` |
| 起動シーケンス | `startup.py`, `context.py` |
| 設定 | `config_builders.py`, `config_dataclasses.py` |
| セッション管理 | `session.py`, `session_message_repo.py` |
| ターン制御 | `orchestrator.py`, `llm_turn_runner.py` |
| ツール実行 | `tool_runner.py`, `tool_scheduler.py`, `tool_policy.py`, `tool_approval.py` |
| ツールガード | `tool_loop_guard.py` |
| ツール監査 | `security_audit_config.py`, `tool_audit.py` |
| 書き込み境界 | `repository_gateway.py` |
| 出力フォーマット | `output_tags.py`, `tool_output.py`, `tool_result_formatter.py` |
| エラー処理 | `llm_transport_errors.py`, `tool_exceptions.py`, `error_injection_service.py` |
| ライフサイクル | `lifecycle.py`, `lifecycle_protocol.py`, `http_lifecycle.py`, `repl_health.py` |
| CLI | `cli_view.py` |
| コンポーネント構築 | `factory.py` |
| 診断 | `diagnostic_store.py` |
| モード分類 | `mdq_rag_classifier.py`, `mode_classification.py` |
| 会話履歴 | `history.py`, `history_selection_policy.py` |
| ツール列挙型 | `tool_enums.py` |
| ツールデータモデル | `tool_models.py` |
| ツール引数検証 | `tool_arg_validator.py` |
| メッセージスキーマ | `message_schema.py` |
| ターン結果 | `turn_result.py` |

#### メモリサブパッケージ (`scripts/agent/memory/`)

| 責務 | ファイル群 |
|---|---|
| データモデル | `types.py`, `models.py`, `enums.py` |
| ストレージ | `store.py`, `jsonl_store.py` |
| 検索 | `retriever.py`, `fts_query.py` |
| 埋め込み | `embedding_client.py` |
| 取り込み | `ingestion.py` |
| 注入 | `injection.py` |
| マッピング | `mapper.py` |
| スコアリング | `scoring.py`, `rrf.py` |
| 操作 | `count_ops.py`, `write_ops.py`, `pin_ops.py`, `import_ops.py`, `rebuild_ops.py` |
| 定数 | `sql_constants.py` |

### 変更時の注意点

- セッション永続化のスキーマ変更時は `store.py` と `sql_constants.py` を併せて確認
- ツール承認フローの変更時は `tool_approval.py` と `repository_gateway.py` の両方を確認
- メモリ検索アルゴリズムの変更時は `retriever.py` と `scoring.py` を併せて確認

### 実装詳細の参照先

完全なファイル一覧はリポジトリの実装ツリーを参照する。

## Related Documents

- `01_overview-files-03-scripts.md`
- `01_overview-files-03-scripts.md`
- `01_overview-files-03-scripts.md`
- `01_overview-files-03-scripts.md`
- [01_overview.md](01_overview.md)

## Keywords

scripts
agent
mcp-server
file-structure

# ファイル構成

アーキテクチャ概要 → [`01_overview-arch-01-process.md`](01_overview-arch-01-process.md), [`01_overview-arch-02-pipelines.md`](01_overview-arch-02-pipelines.md), [`01_overview-arch-03-features.md`](01_overview-arch-03-features.md)

## 3a. ファイル構成

### 主要ディレクトリと責務

#### エージェント REPL パッケージ (`scripts/agent/`)

| 責務 | ファイル群 |
|---|---|
| エントリポイント | `__main__.py`, `repl.py` |
| 起動シーケンス | `startup.py`, `context.py` |
| 設定 | `config_builders.py`, `config_dataclasses.py` |
| セッション管理 | `session.py`, `session_message_repo.py` |
| ターン制御 | `orchestrator.py`, `llm_turn_runner.py` |
| ツール実行 | `tool_runner.py`, `tool_scheduler.py`, `tool_policy.py`, `tool_approval.py` |
| ツールガード | `tool_loop_guard.py` |
| ツール監査 | `security_audit_config.py`, `tool_audit.py` |
| 書き込み境界 | `repository_gateway.py` |
| 出力フォーマット | `output_tags.py`, `tool_output.py`, `tool_result_formatter.py` |
| エラー処理 | `llm_transport_errors.py`, `tool_exceptions.py`, `error_injection_service.py` |
| ライフサイクル | `lifecycle.py`, `lifecycle_protocol.py`, `http_lifecycle.py`, `repl_health.py` |
| CLI | `cli_view.py` |
| コンポーネント構築 | `factory.py` |
| 診断 | `diagnostic_store.py` |
| モード分類 | `mdq_rag_classifier.py`, `mode_classification.py` |
| 会話履歴 | `history.py`, `history_selection_policy.py` |
| ツール列挙型 | `tool_enums.py` |
| ツールデータモデル | `tool_models.py` |
| ツール引数検証 | `tool_arg_validator.py` |
| メッセージスキーマ | `message_schema.py` |
| ターン結果 | `turn_result.py` |

#### メモリサブパッケージ (`scripts/agent/memory/`)

| 責務 | ファイル群 |
|---|---|
| データモデル | `types.py`, `models.py`, `enums.py` |
| ストレージ | `store.py`, `jsonl_store.py` |
| 検索 | `retriever.py`, `fts_query.py` |
| 埋め込み | `embedding_client.py` |
| 取り込み | `ingestion.py` |
| 注入 | `injection.py` |
| マッピング | `mapper.py` |
| スコアリング | `scoring.py`, `rrf.py` |
| 操作 | `count_ops.py`, `write_ops.py`, `pin_ops.py`, `import_ops.py`, `rebuild_ops.py` |
| 定数 | `sql_constants.py` |

### 変更時の注意点

- セッション永続化のスキーマ変更時は `store.py` と `sql_constants.py` を併せて確認
- ツール承認フローの変更時は `tool_approval.py` と `repository_gateway.py` の両方を確認
- メモリ検索アルゴリズムの変更時は `retriever.py` と `scoring.py` を併せて確認

### 実装詳細の参照先

完全なファイル一覧はリポジトリの実装ツリーを参照する。

## Related Documents

- `01_overview-files-03-scripts.md`
- `01_overview-files-03-scripts.md`
- `01_overview-files-03-scripts.md`
- `01_overview-files-03-scripts.md`
- [01_overview.md](01_overview.md)

## Keywords

scripts
agent
mcp-server
file-structure




# ファイル構成

アーキテクチャ概要 → [`01_overview-arch-01-process.md`](01_overview-arch-01-process.md), [`01_overview-arch-02-pipelines.md`](01_overview-arch-02-pipelines.md), [`01_overview-arch-03-features.md`](01_overview-arch-03-features.md)

## 3b. ファイル構成

デプロイ先のディレクトリ構成:


``` text
│   │   ├─ commands/
│   │   │   # 主要なスラッシュコマンド (/help, /config, /stats 等) を実装。
│   │   │   # 責任ごとに 12 個の mixin クラスに分割されており、詳細は
│   │   │   # scripts/agent/commands/ を直接参照してください。
```

## Related Documents

- `01_overview-files-03-scripts.md`
- `01_overview-files-03-scripts.md`
- `01_overview-files-03-scripts.md`
- `01_overview-files-03-scripts.md`
- [01_overview.md](01_overview.md)

## Keywords

scripts
agent
mcp-server
file-structure

# ファイル構成

アーキテクチャ概要 → [`01_overview-arch-01-process.md`](01_overview-arch-01-process.md), [`01_overview-arch-02-pipelines.md`](01_overview-arch-02-pipelines.md), [`01_overview-arch-03-features.md`](01_overview-arch-03-features.md)

## 3c. ファイル構成

デプロイ先のディレクトリ構成:


``` text
│   │   ├─ commands/
│   │   │   # 主要なスラッシュコマンド (/help, /config, /stats 等) を実装。
│   │   │   # 責任ごとに 12 個の mixin クラスに分割されており、詳細は
│   │   │   # scripts/agent/commands/ を直接参照してください。
```

## Related Documents

- `01_overview-files-03-scripts.md`
- `01_overview-files-03-scripts.md`
- `01_overview-files-03-scripts.md`
- `01_overview-files-03-scripts.md`
- [01_overview.md](01_overview.md)

## Keywords

scripts
agent
mcp-server
file-structure




# ファイル構成

アーキテクチャ概要 → [`01_overview-arch-01-process.md`](01_overview-arch-01-process.md), [`01_overview-arch-02-pipelines.md`](01_overview-arch-02-pipelines.md), [`01_overview-arch-03-features.md`](01_overview-arch-03-features.md)

## 3d. ファイル構成

デプロイ先のディレクトリ構成:


``` text
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
│   │   │   ├─ mcp_tool_discovery.py        # McpToolDiscoveryService: /v1/tools からのライブツール検出、RuntimeToolRegistry 構築（startup.py から呼び出し済み — ToolExecutor.set_runtime_registry() で接続）
│   │   │   ├─ rag_maintenance_service.py   # RAG 保守サービス
│   │   │   ├─ session_restore.py           # セッション復元
│   │   │   ├─ session_title.py             # セッションタイトル生成
│   │   │   ├─ config_validators.py        # config_dataclasses.py __post_init__ から抽出された単一フィールド/クロスフィールド検証関数群
│   │   │   ├─ typed_validators.py          # 設定リロード用型境界抽出ヘルパー
│   │   │   └─ undo_service.py              # アンドゥサービス
│   │   ├─ shared/                          # agent パッケージ内共有型 (agent 層専用)
│   │   │    ├─ __init__.py                 # shared パッケージ初期化
│   │   │    ├─ enums.py                    # 空ファイル: カナonicalな列挙型は agent.memory.enums / agent.tool_enums
│   │   │    ├─ exceptions.py               # 空ファイル: カナonicalな例外は agent.commands/agent.services/agent.memory/agent.tool_exceptions
│   │   │    ├─ health_models.py            # ヘルスチェックモデル（ServiceWarning/HealthCheckResult/McpHealthProbeResult を集約）。詳細は scripts/agent/shared/health_models.py の定義を参照。
│   │   │    └─ models.py                   # エージェント共通データモデル（承認イベント・ツール実行イベントの監査データモデルを集約）。詳細は scripts/agent/shared/models.py の定義を参照。
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
│   │       ├─ validate.py                  # デプロイ時にworkflow定義JSONを検証するスタンドアロンCLI(エージェント/MCP/LLMは起動しない)
│   │       └─ __init__.py                  # workflow パッケージ初期化
```

### 変更時の注意点

- `AgentConfig` のフィールド変更時は `config_dataclasses.py`、`config_builders.py`、`services/config_validators.py` を併せて確認 — フィールドの定義・構築・検証ロジックが三者に分散しているため
- `attempts` テーブルへの INSERT ロジック変更時は `idempotency_ops.py` と `attempt_ops.py` の両方を確認 — 両ファイルが同一テーブルのスキーマ/生成ロジックに依存しているため

## Related Documents

- `01_overview-files-03-scripts.md`
- `01_overview-files-03-scripts.md`
- `01_overview-files-03-scripts.md`
- `01_overview-files-03-scripts.md`
- [01_overview.md](01_overview.md)

## Keywords

scripts
agent
mcp-server
file-structure

# ファイル構成

アーキテクチャ概要 → [`01_overview-arch-01-process.md`](01_overview-arch-01-process.md), [`01_overview-arch-02-pipelines.md`](01_overview-arch-02-pipelines.md), [`01_overview-arch-03-features.md`](01_overview-arch-03-features.md)

## 3e. ファイル構成

デプロイ先のディレクトリ構成:


``` text
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
│   │   │   ├─ mcp_tool_discovery.py        # McpToolDiscoveryService: /v1/tools からのライブツール検出、RuntimeToolRegistry 構築（startup.py から呼び出し済み — ToolExecutor.set_runtime_registry() で接続）
│   │   │   ├─ rag_maintenance_service.py   # RAG 保守サービス
│   │   │   ├─ session_restore.py           # セッション復元
│   │   │   ├─ session_title.py             # セッションタイトル生成
│   │   │   ├─ config_validators.py        # config_dataclasses.py __post_init__ から抽出された単一フィールド/クロスフィールド検証関数群
│   │   │   ├─ typed_validators.py          # 設定リロード用型境界抽出ヘルパー
│   │   │   └─ undo_service.py              # アンドゥサービス
│   │   ├─ shared/                          # agent パッケージ内共有型 (agent 層専用)
│   │   │    ├─ __init__.py                 # shared パッケージ初期化
│   │   │    ├─ enums.py                    # 空ファイル: カナonicalな列挙型は agent.memory.enums / agent.tool_enums
│   │   │    ├─ exceptions.py               # 空ファイル: カナonicalな例外は agent.commands/agent.services/agent.memory/agent.tool_exceptions
│   │   │    ├─ health_models.py            # ヘルスチェックモデル（ServiceWarning/HealthCheckResult/McpHealthProbeResult を集約）。詳細は scripts/agent/shared/health_models.py の定義を参照。
│   │   │    └─ models.py                   # エージェント共通データモデル（承認イベント・ツール実行イベントの監査データモデルを集約）。詳細は scripts/agent/shared/models.py の定義を参照。
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
│   │       ├─ validate.py                  # デプロイ時にworkflow定義JSONを検証するスタンドアロンCLI(エージェント/MCP/LLMは起動しない)
│   │       └─ __init__.py                  # workflow パッケージ初期化
```

### 変更時の注意点

- `AgentConfig` のフィールド変更時は `config_dataclasses.py`、`config_builders.py`、`services/config_validators.py` を併せて確認 — フィールドの定義・構築・検証ロジックが三者に分散しているため
- `attempts` テーブルへの INSERT ロジック変更時は `idempotency_ops.py` と `attempt_ops.py` の両方を確認 — 両ファイルが同一テーブルのスキーマ/生成ロジックに依存しているため

## Related Documents

- `01_overview-files-03-scripts.md`
- `01_overview-files-03-scripts.md`
- `01_overview-files-03-scripts.md`
- `01_overview-files-03-scripts.md`
- [01_overview.md](01_overview.md)

## Keywords

scripts
agent
mcp-server
file-structure




# ファイル構成

アーキテクチャ概要 → [`01_overview-arch-01-process.md`](01_overview-arch-01-process.md), [`01_overview-arch-02-pipelines.md`](01_overview-arch-02-pipelines.md), [`01_overview-arch-03-features.md`](01_overview-arch-03-features.md)

## 3f. ファイル構成

デプロイ先のディレクトリ構成:


``` text
│   ├─ mcp_servers/                           # MCP サーバパッケージ
│   │   └─ __init__.py                      # MCP パッケージ初期化
│   │   ├─ models.py                        # /v1/call_tool 統合エンドポイント共通 Pydantic モデル
│   │   ├─ server.py                        # MCP サーバ HTTP 起動共通基底クラス
│   │   ├─ audit.py                         # MCP ツール実行監査ログ (JSON-lines 1 行/実行)
│   │   ├─ dispatch.py                      # dispatch_tool(): DispatchResult を返すツールルーティングヘルパー
│   │   ├─ health_response.py               # make_health_response(): /health エンドポイント共通レスポンス生成
│   │   ├─ tool_validators.py               # @register_validator: git_commit / git_push / trigger_workflow / shell_run 等の入力バリデータ
│   │   ├─ web_search/                      # Web 検索 MCP サーバ (DuckDuckGo, :8004)
│   │   │   # 各サービス固有のファイル (例: web_search_server.py 等) は、
│   │   │   # mcp_servers/ の共有基盤の上に構築されています。詳細は
│   │   │   # scripts/mcp_servers/web_search/ を直接参照してください。
│   │   ├─ github/                          # GitHub MCP サーバ (:8006)
│   │   │   # 各ドメイン (file/issues/PR/repo) ごとの実装は、
│   │   │   # mcp_servers/ の共有基盤の上に構築されています。詳細は
│   │   │   # scripts/mcp_servers/github/ を直接参照してください。
```

## Related Documents

- `01_overview-files-03-scripts.md`
- `01_overview-files-03-scripts.md`
- `01_overview-files-03-scripts.md`
- `01_overview-files-03-scripts.md`
- [01_overview.md](01_overview.md)

## Keywords

scripts
agent
mcp-server
file-structure

# ファイル構成

アーキテクチャ概要 → [`01_overview-arch-01-process.md`](01_overview-arch-01-process.md), [`01_overview-arch-02-pipelines.md`](01_overview-arch-02-pipelines.md), [`01_overview-arch-03-features.md`](01_overview-arch-03-features.md)

## 3g. ファイル構成

デプロイ先のディレクトリ構成:


``` text
│   ├─ mcp_servers/                           # MCP サーバパッケージ
│   │   └─ __init__.py                      # MCP パッケージ初期化
│   │   ├─ models.py                        # /v1/call_tool 統合エンドポイント共通 Pydantic モデル
│   │   ├─ server.py                        # MCP サーバ HTTP 起動共通基底クラス
│   │   ├─ audit.py                         # MCP ツール実行監査ログ (JSON-lines 1 行/実行)
│   │   ├─ dispatch.py                      # dispatch_tool(): DispatchResult を返すツールルーティングヘルパー
│   │   ├─ health_response.py               # make_health_response(): /health エンドポイント共通レスポンス生成
│   │   ├─ tool_validators.py               # @register_validator: git_commit / git_push / trigger_workflow / shell_run 等の入力バリデータ
│   │   ├─ web_search/                      # Web 検索 MCP サーバ (DuckDuckGo, :8004)
│   │   │   # 各サービス固有のファイル (例: web_search_server.py 等) は、
│   │   │   # mcp_servers/ の共有基盤の上に構築されています。詳細は
│   │   │   # scripts/mcp_servers/web_search/ を直接参照してください。
│   │   ├─ github/                          # GitHub MCP サーバ (:8006)
│   │   │   # 各ドメイン (file/issues/PR/repo) ごとの実装は、
│   │   │   # mcp_servers/ の共有基盤の上に構築されています。詳細は
│   │   │   # scripts/mcp_servers/github/ を直接参照してください。
```

## Related Documents

- `01_overview-files-03-scripts.md`
- `01_overview-files-03-scripts.md`
- `01_overview-files-03-scripts.md`
- `01_overview-files-03-scripts.md`
- [01_overview.md](01_overview.md)

## Keywords

scripts
agent
mcp-server
file-structure




# ファイル構成

アーキテクチャ概要 → [`01_overview-arch-01-process.md`](01_overview-arch-01-process.md), [`01_overview-arch-02-pipelines.md`](01_overview-arch-02-pipelines.md), [`01_overview-arch-03-features.md`](01_overview-arch-03-features.md)

## 3h. ファイル構成

デプロイ先のディレクトリ構成:


各サーバのコアな4点セット（`<service>_server.py`, `<service>_service.py`, `<service>_tools.py`, `<service>_models.py`）には、サービス名が接頭辞として付与されています。補助的なモジュールやヘルパーは、接頭辞なしまたは部分的な接頭辞を持つ場合があります。詳細なファイル構成については、以下の各ディレクトリを参照してください：
- `scripts/mcp_servers/shell/` (# シェル MCP サーバ :8009)
- `scripts/mcp_servers/rag_pipeline/` (# RAG パイプライン MCP サーバ :8010)
- `scripts/mcp_servers/cicd/` (# GitHub Actions CI/CD MCP サーバ :8012)
- `scripts/mcp_servers/mdq/` (# Markdown Context Compression Engine MCP サーバ :8013)
  ※ FTS 管理ツールはコミット `74906389b` により廃止されました（後継ファイルなし）。`db_grep.py` および `db_schema.py` はこれとは無関係な既存モジュールです。
- `scripts/mcp_servers/git/` (# ローカル git 操作 MCP サーバ :8014)

## Related Documents

- `01_overview-files-03-scripts.md`
- `01_overview-files-03-scripts.md`
- `01_overview-files-03-scripts.md`
- `01_overview-files-03-scripts.md`
- [01_overview.md](01_overview.md)

## Keywords

scripts
agent
mcp-server
file-structure

# ファイル構成

アーキテクチャ概要 → [`01_overview-arch-01-process.md`](01_overview-arch-01-process.md), [`01_overview-arch-02-pipelines.md`](01_overview-arch-02-pipelines.md), [`01_overview-arch-03-features.md`](01_overview-arch-03-features.md)

## 3i. ファイル構成

デプロイ先のディレクトリ構成:


各サーバのコアな4点セット（`<service>_server.py`, `<service>_service.py`, `<service>_tools.py`, `<service>_models.py`）には、サービス名が接頭辞として付与されています。補助的なモジュールやヘルパーは、接頭辞なしまたは部分的な接頭辞を持つ場合があります。詳細なファイル構成については、以下の各ディレクトリを参照してください：
- `scripts/mcp_servers/shell/` (# シェル MCP サーバ :8009)
- `scripts/mcp_servers/rag_pipeline/` (# RAG パイプライン MCP サーバ :8010)
- `scripts/mcp_servers/cicd/` (# GitHub Actions CI/CD MCP サーバ :8012)
- `scripts/mcp_servers/mdq/` (# Markdown Context Compression Engine MCP サーバ :8013)
  ※ FTS 管理ツールはコミット `74906389b` により廃止されました（後継ファイルなし）。`db_grep.py` および `db_schema.py` はこれとは無関係な既存モジュールです。
- `scripts/mcp_servers/git/` (# ローカル git 操作 MCP サーバ :8014)

## Related Documents

- `01_overview-files-03-scripts.md`
- `01_overview-files-03-scripts.md`
- `01_overview-files-03-scripts.md`
- `01_overview-files-03-scripts.md`
- [01_overview.md](01_overview.md)

## Keywords

scripts
agent
mcp-server
file-structure

