---
title: "Agent Configuration - MCPConfig, ApprovalConfig, ObservabilityConfig"
category: agent
tags:
  - agent
  - configuration
related:
  - 05_agent_00_document-guide.md
source:
  - 05_agent_08_01_configuration-loading-agent-config-part1.md
---

# エージェント設定

- 運用 → [05_agent_10_01_operations-and-observability-startup-and-health.md](05_agent_10_01_operations-and-observability-startup-and-health.md)

## Purpose

MCP設定、承認設定、観測設定の構造と制約について文書化する。

## Design Intent

### MCP設定

#### 所有権の責任分割

- `config/agent.toml`: エージェントプロセスのMCPライフサイクルおよびトランスポート設定のみ
- `config/*_mcp_server.toml`: 各MCPサーバーのアプリケーション設定（allowlists/denylists、リソース制限、監査パス、シークレット参照）

#### Agent-side MCPフィールド

- `startup_mode`: "none" / "persistent" / "subprocess"
- `transport`: TransportType.HTTP（"http"）
- `url`: HTTPサーバのベースURL
- `cmd`: subprocess起動コマンド

#### プロセス分離

各MCPサーバーは独立したプロセスであり、自身の設定ファイルのみを読み込む。

### 承認設定

#### Risk Rules

- `none`: デフォルトではなし
- `medium`: write_file, edit_file, create_directory, move_file, github_系操作
- `high`: delete_file, delete_directory, shell_run, github_push_files, github_merge_pull_request

#### エスカレーション

- `approval_protected_paths`: highへエスカレート（/opt/, /etc/, /boot/, /usr/, /bin/, /sbin/）
- `approval_high_risk_branches`: main, master

#### 自動承認

- `approval_shell_safe_prefixes`: shell_runの自動承認プレフィックス

#### Safety Tiers

- `tool_safety_tiers`: tool → READ_ONLY/WRITE_SAFE/WRITE_DANGEROUS/ADMIN

**CRITICAL**: `tool_safety_tiers`のキーはサーバーキーではなく、実際に登録されたツール名でなければならない。未知のキーは起動時に検出される: ローカル/開発環境では警告、本番環境では致命的なRuntimeError。

#### Dry Run

- `approval_dry_run_tools`: dry_run=Trueで事前実行されるツール

#### GitHub書き込み制御

- `approval_github_allowed_repos`: GitHub書き込み許可リスト（空 = すべて拒否）
- `gitops_push_blocked`: GitHubへの書き込みをグローバルにすべてブロック

#### ファイルパス制限

- `allowed_root`: ファイルパスジェイル（空 = 無効）

### 観測設定

- `otel_enabled`: OpenTelemetryを有効化
- `otel_endpoint`: OTLP HTTPエンドポイント（"" = ConsoleSpanExporter）
- `otel_service_name`: OTelサービス名
- `audit_log_file`: 監査ログのパス（JSON-lines）
- `structured_log`: agent.logにJSON-lines形式を使用

### 診断設定

- `encryption_key`: DiagnosticStore.save(encrypt=True)用のFernet対称鍵（空文字列 = 暗号化無効）
- `retention_days`: session_diagnosticsの行保持日数（0以下 = パージ無効）

## Responsibility Boundary

- **正典**: `config/agent.toml`のMCP/Approval/Observability/Diagnosticsセクション
- **バリデーション**: `agent/services/config_validators.py`
- **データクラス**: `agent/config_dataclasses.py`の`McpServerConfig` / `ApprovalConfig` / `ObservabilityConfig` / `DiagnosticsConfig`

## Key Constraints

- `tool_safety_tiers`のキーは実際に登録されたツール名でなければならない — 未知のキーは本番環境でfatal
- `allowed_tools=[]`（空）は「すべて許可」を意味する
- `approval_github_allowed_repos=[]`（空）は「すべて拒否」を意味する
- `/reload`で`cfg.diagnostics.*`は変更できない（未実装）

## Operational Notes

- 不明

## Known Limitations

- `/reload`で`cfg.diagnostics.*`は変更できない（未実装）

## Related Docs

- `05_agent_00_document-guide.md`
- `05_agent_08_01_configuration-loading-agent-config-part1.md`
- `05_agent_08_02_configuration-llm-rag.md`
- `05_agent_08_03_configuration-tools-memory.md`
- `05_agent_09_01_data-layer-session-db.md`

## Keywords

MCPConfig
ApprovalConfig
ObservabilityConfig
DiagnosticsConfig
