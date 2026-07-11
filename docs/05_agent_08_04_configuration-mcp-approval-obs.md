---
title: "Agent Configuration - MCPConfig, ApprovalConfig, ObservabilityConfig"
category: agent
tags:
  - agent
  - configuration
  - mcpconfig
  - approvalconfig
  - observabilityconfig
related:
  - 05_agent_00_document-guide.md
  - 05_agent_08_01_configuration-loading-agent-config.md
  - 05_agent_08_02_configuration-llm-rag.md
  - 05_agent_08_03_configuration-tools-memory.md
source:
  - 05_agent_08_01_configuration-loading-agent-config.md
---

# エージェント設定

- 運用 → [05_agent_10_01_operations-and-observability-startup-and-health.md](05_agent_10_01_operations-and-observability-startup-and-health.md)

## MCPConfig (`cfg.mcp.*`)

Source: `config/*_mcp_server.toml` (各ファイルの`[mcp_servers.<key>]`セクション)

| Field | Default | Description |
|---|---|---|
| `mcp_servers` | `{}` | サーバーキーごとの`McpServerConfig`のdict |
| `mcp_watchdog_interval` | `30.0` (PRODUCTION) / `0.0` (LOCAL) | ウォッチドッグのポーリング間隔 (秒; 0=無効); プロファイルに応じたデフォルト |
| `mcp_watchdog_max_restarts` | `3` | ウォッチドッグの最大再起動試行回数 |

GitHub MCPエンドポイントは`mcp_servers.github.url` (`McpServerConfig`のエントリ) のみを
通じて設定される — レガシーなトップレベルの`github_server_url`キーは削除されており、
存在する場合`build_agent_config()`によって`ConfigLoadError`で拒否される。

`McpServerConfig`のフィールドについては[04_mcp_03_routing_lifecycle_and_execution.md](04_mcp_03_routing_lifecycle_and_execution.md)を参照。

---

## ApprovalConfig (`cfg.approval.*`)

Source: `config/agent.toml`

| Field | Default | Description |
|---|---|---|
| `approval_risk_rules` | (下記参照) | tool → none/medium/high |
| `approval_protected_paths` | `[/opt/, /etc/, /boot/, /usr/, /bin/, /sbin/]` | highへエスカレート |
| `approval_high_risk_branches` | `[main, master]` | GitHubブランチのエスカレーション |
| `approval_shell_safe_prefixes` | `[ls, cat, echo, git log, ...]` | shell_runの自動承認プレフィックス |
| `approval_resource_keys` | `{path_keys: [...], branch_keys: [...]}` | リソース識別のための引数キー |
| `approval_dry_run_tools` | `[write_file, edit_file, delete_file, delete_directory, move_file]` | dry_run=Trueで事前実行 |
| `tool_safety_tiers` | `{}` | tool → READ_ONLY/WRITE_SAFE/WRITE_DANGEROUS/ADMIN |

`tool_safety_tiers`のキーはサーバーキーではなく、実際に登録されたツール名でなければならない。未知のキーは起動時に検出される: ローカル/開発環境では警告、本番環境では致命的な`RuntimeError` (`ProductionConfigValidator.validate_unknown_tool_safety_tiers()`経由)。
| `allowed_root` | `""` | ファイルパスジェイル (空 = 無効) |
| `approval_github_allowed_repos` | `[]` | GitHub書き込み許可リスト (空 = すべて拒否) |
| `gitops_push_blocked` | `False` | GitHubへの書き込みをグローバルにすべてブロック |
| `gitops_force_push_blocked` | `True` | force pushをブロック |
| `gitops_protected_branches` | `[main, master]` | 保護対象ブランチ (高リスク承認) |

**デフォルトの`approval_risk_rules`:**
- `none`: (デフォルトではなし)
- `medium`: write_file, edit_file, create_directory, move_file, github_create_branch, github_create_pull_request, github_update_pull_request, github_create_issue, github_add_issue_comment
- `high`: delete_file, delete_directory, shell_run, github_push_files, github_create_or_update_file, github_delete_file, github_merge_pull_request

---

## ObservabilityConfig (`cfg.obs.*`)

Source: `config/agent.toml`

| Field | Default | Description |
|---|---|---|
| `otel_enabled` | `False` | OpenTelemetryを有効化 |
| `otel_endpoint` | `""` | OTLP HTTPエンドポイント (`""` = ConsoleSpanExporter) |
| `otel_service_name` | `"llm-agent"` | OTelサービス名 |
| `audit_log_file` | `"/opt/llm/logs/audit.log"` | 監査ログのパス (JSON-lines) |
| `structured_log` | `False` | `agent.log`にJSON-lines形式を使用 |

## Related Documents

- `05_agent_00_document-guide.md`
- `05_agent_08_01_configuration-loading-agent-config.md`
- `05_agent_08_02_configuration-llm-rag.md`
- `05_agent_08_03_configuration-tools-memory.md`

## Keywords

MCPConfig
ApprovalConfig
ObservabilityConfig
