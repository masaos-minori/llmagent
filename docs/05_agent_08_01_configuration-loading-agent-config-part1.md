---
title: "Agent Configuration - Loading and AgentConfig Structure (Part 1)"
category: agent
tags:
  - agent
  - configuration
  - config-loading
  - agentconfig
  - hot-reload
related:
  - 05_agent_00_document-guide.md
  - 05_agent_08_02_configuration-llm-rag.md
  - 05_agent_08_03_configuration-tools-memory.md
  - 05_agent_08_04_configuration-mcp-approval-obs.md
source:
  - 05_agent_08_01_configuration-loading-agent-config-part1.md
---

# エージェント設定

- 運用 → [05_agent_10_01_operations-and-observability-startup-and-health.md](05_agent_10_01_operations-and-observability-startup-and-health.md)

## 目的

`AgentConfig`の完全な構造、全7つのサブ設定とそのフィールド、
設定ファイルのレイアウト、検証ルール、`/reload`の対象範囲、フィールド間の制約を文書化する。

---

## 設定の読み込み

`build_agent_config()` (`agent/config_builders.py`) は`ConfigLoader.load_all()`
(`shared/config_loader.py`) を呼び出し、これがすべての設定ファイルをdictにマージした後、
`AgentConfig`データクラスを構築する。

**`load_all()`が読み込むファイル:**

| File | Sub-config |
|---|---|
| `config/agent.toml` | すべてのサブ設定 (LLMConfig, RAGConfig, DbConfig, ToolConfig, MemoryConfig, ObservabilityConfig, ApprovalConfig, MCPConfig) |

過去の経緯: 以前のバージョンでは12個の個別ファイル (`common.toml`, `llm.toml`, `http.toml`, `context.toml`, `rag.toml`, `tools.toml`, `memory.toml`, `otel.toml`, `security.toml`, `system_prompts.toml`, `tools_definitions.toml`、加えてサーバーごとの`*_mcp_server.toml`) を読み込んでいた。これらは`agent.toml`に統合され、分割されたファイルはもはや存在しない。

正準の設定所有関係表 (ファイルごとの所有レイヤー) については、
[90_shared_03 §2a Config Ownership](90_shared_03_01_runtime_and_execution-config-and-logging.md#2a-config-ownership)を参照。

`ctx.cfg`が設定を保持する。`/reload`は`ConfigLoader().load_all()`を呼び出して
すべてのベース設定ファイルを再読み込みし、マージされたdictを
`ConfigReloadService.apply_config_dict(new_cfg)`に渡す。これが`ctx.cfg`の
フィールドを更新し、実行中のサービスインスタンスに同期する。

呼び出しチェーンは以下の通り:
1. `ConfigLoader().load_all()` — `config/`からすべてのファイルを再読み込み
2. `ConfigReloadService.apply_config_dict(new_cfg)` — `ctx.cfg`の
   フィールドを更新し、変更をサービスに伝播
3. `ConfigReloadOutcome` — `applied`,
   `needs_restart`, `skipped`, `source_files`フィールドと共に呼び出し元に返される

### 設定ファイルの所有関係とホットリロード可否

`/reload`はすべてのベース設定ファイルを読み込む — 起動時に読み込まれるものと同一の集合。
`ConfigReloadService`は変更されたキーごとに4つのカテゴリのいずれかに分類する。

すべての設定キーは`config/agent.toml`で定義されている。デフォルト値を提供する個別の`common.toml`や他の分割ファイルは存在しない。

| File | Purpose | Classification |
|---|---|---|
| `config/agent.toml` | すべてのサブ設定 | ホットリロード可能 (ほとんど); `use_memory_layer`, `plugin_strict`は起動時のみ |
| `config/*_mcp_server.toml` | MCPサーバーのトランスポート/URL設定 (`[mcp_servers.<key>]`経由) | 再起動必須: 全フィールド (`transport`, `url`, `startup_mode`, `healthcheck_mode`, `call_timeout_sec`, `startup_timeout_sec`, `tool_names`, `auth_token`, `role`, `cmd`, `env`)、およびサーバーの追加/削除/リネーム |

**分類の定義:**

- **ホットリロード可能** — 実行中のエージェントに即座に適用される; 再起動不要。
- **再起動必須** — 変更を適用するにはサブシステムの再起動が必要。
  `/reload`の出力はこれらを`[RESTART]`として表示する。
- **起動時のみ** — エージェント起動時に一度だけ読み込まれる; `/reload`では一切変更されない。
  `/reload`はフィールドの値が実行中の設定と異なる場合のみ`[STARTUP-ONLY]`を出力する。

**再起動必須の設定** (`ConfigReloadOutcome`内の`needs_restart`):
- `McpServerConfig`のフィールド変更、新規サーバー、削除されたサーバー、
  リネーム (旧サーバーの削除+新規追加) はすべて該当する。例:
  `mcp_servers/<server>.url`, `mcp_servers/<server>.auth_token`, `mcp_servers/<server>.startup_mode`,
  `mcp_servers/<server>.cmd`, `mcp_servers/<server>.env`。

**起動時のみの設定** (`apply_config_dict()`では変更されない):
- `use_memory_layer` — 起動時にメモリサブシステムを有効/無効にする
- `plugin_strict` — 起動時にプラグインのインポートエラーでfail-fastを有効にする
- `routing_drift_strict` — 起動時に config/registry のルーティングドリフトをfatal扱いにする
  (`ToolConfig.routing_drift_strict`; `ConfigReloadService._detect_startup_only()`が
  `use_memory_layer`, `plugin_strict`と共に3フィールドを比較する。根拠: Explicit in code —
  `agent/services/config_reload.py::_detect_startup_only()`)

**削除されたキー** (設定読み込み時に拒否される、`ConfigLoadError`; 2026-07-09検証済み — 
`build_agent_config()`の`_FORBIDDEN_KEYS`参照): `workflow_mode`, `workflow_require_approval`,
`use_tool_summarize`, `tool_summarize_threshold`。これらはもはや一切有効な設定キーではない —
単にホットリロードできない起動時のみの設定というわけではない。

さらに、`github_server_url`キーも単独のチェックで拒否される
(`_FORBIDDEN_KEYS`とは別の`if "github_server_url" in cfg:`分岐、
`agent/config_builders.py`)。エラーメッセージは`[mcp_servers.github].url`を使うよう案内する
(根拠: Explicit in code)。

すべての設定キーは`config/agent.toml`で定義されている。デフォルト値を提供する個別の`common.toml`や他の分割ファイルは存在しない。

### リロード実行パイプライン

`ConfigReloadService` (`agent/services/config_reload.py`) はリロードされた
設定を実行中のサービスインスタンスに適用する:

| Service | Method called | Config fields propagated |
|---|---|---|
| `LLMClient` | `.apply_config()` | temperature, max_tokens, max_retries, retry_base_delay, SSEパラメータ |
| `HistoryManager` | `.apply_config()` | context_char_limit, context_compress_turns, context_token_limit, tokenize_url |
| `ToolExecutor` | `.apply_config()` | tool_cache_ttl |
| システムプロンプト | 直接書き込み | system_prompt_tool → `ctx.conv.system_prompt_content` |

**`ConfigReloadOutcome`のフィールド:**

| Field | Type | Description |
|---|---|---|
| `applied` | `list[str]` | 実行時に適用された変更 (ホットリロード済み) |
| `needs_restart` | `list[str]` | エージェントの完全な再起動が必要な変更 |
| `skipped` | `list[str]` | 意図的に無視された変更、MCPサーバー定義ではない — `needs_restart`参照 |
| `source_files` | `list[str]` | リロードされた設定ファイル |
| `startup_only` | `list[str]` | 実行中の設定と異なる起動時のみのフィールド |

フィールド単位の完全なマッピングについては`agent/services/config_reload.py`を参照。

---

## Related Documents

- `05_agent_00_document-guide.md`
- `05_agent_08_02_configuration-llm-rag.md`
- `05_agent_08_03_configuration-tools-memory.md`
- `05_agent_08_04_configuration-mcp-approval-obs.md`
- `05_agent_08_01_configuration-loading-agent-config-part2.md`

## Keywords

configuration loading
config file ownership
hot-reload eligibility
reload execution pipeline
AgentConfig structure
