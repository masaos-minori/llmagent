
title: "Agent Configuration - Loading and AgentConfig Structure (Part 1)"
category: agent
tags:
  - agent
  - configuration
  - config-loading
related:
  - 05_agent_00_document-guide.md
source:
  - 05_agent_08_01_configuration-loading-agent-config.md


# エージェント設定

- 運用 → [05_agent_10_01_operations-and-observability-startup-and-health.md](05_agent_10_01_operations-and-observability-startup-and-health.md)

## Purpose

`AgentConfig`の構造、設定ファイルの所有関係、ホットリロードの分類について文書化する。

## Design Intent

### 設定の読み込み

`build_agent_config()`は`ConfigLoader.load_all()`を呼び出し、これがすべての設定ファイルをdictにマージした後、`AgentConfig`データクラスを構築する。

**正典の設定ファイル:** `config/agent.toml`（LLM/RAG/DB/ツール/メモリ/観測/承認/MCPライフサイクル/診断）

### 設定ファイルの所有関係

| ファイル | 責務 | ホットリロード |
|---|---|---|
| `config/agent.toml` | エージェントプロセス設定 | ほとんど可能; `use_memory_layer`/`memory_embed_enabled`は起動時のみ; `diagnostics.*`は`/reload`未対応 |
| `config/*_mcp_server.toml` | MCPサーバー固有設定 | 再起動必須（追加/削除/リネーム時） |

### 再起動が必要な設定

- MCPサーバーのURL、認証トークン、起動モード、コマンド、環境変数の変更
- `use_memory_layer` — メモリサブシステムの有効/無効（起動時のみ）
- `memory_embed_enabled` — 埋め込み生成・KNN検索の有効/無効（起動時のみ）
- `routing_drift_strict` — ルーティングドリフトのfatal扱い（起動時のみ）

### ホットリロード可能な範囲

- LLMClient: temperature, max_tokens, max_retries, retry_base_delay, SSEパラメータ
- HistoryManager: context_char_limit, context_compress_turns, context_token_limit, tokenize_url
- ToolExecutor: tool_cache_ttl
- システムプロンプト: system_prompt_tool → `ctx.conv.system_prompt_content`

### 変更時の運用影響

`ConfigReloadOutcome`の出力で以下のカテゴリを確認:
- `[APPLIED]` — ホットリロード適用済み
- `[RESTART]` — サブシステム再起動が必要
- `[STARTUP-ONLY]` — `/reload`では変更できないフィールド

### セキュリティに関わる設定

- MCPサーバーのauth_token変更は再起動必須
- allowlist/denylistの変更は再起動必須

## Responsibility Boundary

- **設定ファイル**: `config/agent.toml`が正典
- **フィールド単位のマッピング**: `agent/services/config_reload.py`を参照

## Key Constraints

- 不明

## Operational Notes

- 不明

## Known Limitations

- 不明

## Related Docs

- `05_agent_00_document-guide.md`
- `05_agent_08_02_configuration-llm-rag.md`
- `05_agent_08_03_configuration-tools-memory.md`
- `05_agent_08_04_configuration-mcp-approval-obs.md`
- `05_agent_08_01_configuration-loading-agent-config.md`

## Keywords

configuration loading
config file ownership
hot-reload eligibility

# エージェント設定

- 運用 → [05_agent_10_01_operations-and-observability-startup-and-health.md](05_agent_10_01_operations-and-observability-startup-and-health.md)

## Purpose

`AgentConfig`の構造、設定ファイルの所有関係、ホットリロードの分類について文書化する。

## Design Intent

### 設定の読み込み

`build_agent_config()`は`ConfigLoader.load_all()`を呼び出し、これがすべての設定ファイルをdictにマージした後、`AgentConfig`データクラスを構築する。

**正典の設定ファイル:** `config/agent.toml`（LLM/RAG/DB/ツール/メモリ/観測/承認/MCPライフサイクル/診断）

### 設定ファイルの所有関係

| ファイル | 責務 | ホットリロード |
|---|---|---|
| `config/agent.toml` | エージェントプロセス設定 | ほとんど可能; `use_memory_layer`/`memory_embed_enabled`は起動時のみ; `diagnostics.*`は`/reload`未対応 |
| `config/*_mcp_server.toml` | MCPサーバー固有設定 | 再起動必須（追加/削除/リネーム時） |

### 再起動が必要な設定

- MCPサーバーのURL、認証トークン、起動モード、コマンド、環境変数の変更
- `use_memory_layer` — メモリサブシステムの有効/無効（起動時のみ）
- `memory_embed_enabled` — 埋め込み生成・KNN検索の有効/無効（起動時のみ）
- `routing_drift_strict` — ルーティングドリフトのfatal扱い（起動時のみ）

### ホットリロード可能な範囲

- LLMClient: temperature, max_tokens, max_retries, retry_base_delay, SSEパラメータ
- HistoryManager: context_char_limit, context_compress_turns, context_token_limit, tokenize_url
- ToolExecutor: tool_cache_ttl
- システムプロンプト: system_prompt_tool → `ctx.conv.system_prompt_content`

### 変更時の運用影響

`ConfigReloadOutcome`の出力で以下のカテゴリを確認:
- `[APPLIED]` — ホットリロード適用済み
- `[RESTART]` — サブシステム再起動が必要
- `[STARTUP-ONLY]` — `/reload`では変更できないフィールド

### セキュリティに関わる設定

- MCPサーバーのauth_token変更は再起動必須
- allowlist/denylistの変更は再起動必須

## Responsibility Boundary

- **設定ファイル**: `config/agent.toml`が正典
- **フィールド単位のマッピング**: `agent/services/config_reload.py`を参照

## Key Constraints

- 不明

## Operational Notes

- 不明

## Known Limitations

- 不明

## Related Docs

- `05_agent_00_document-guide.md`
- `05_agent_08_02_configuration-llm-rag.md`
- `05_agent_08_03_configuration-tools-memory.md`
- `05_agent_08_04_configuration-mcp-approval-obs.md`
- `05_agent_08_01_configuration-loading-agent-config.md`

## Keywords

configuration loading
config file ownership
hot-reload eligibility



# エージェント設定

- 運用 → [05_agent_10_01_operations-and-observability-startup-and-health.md](05_agent_10_01_operations-and-observability-startup-and-health.md)

## Purpose

`AgentConfig`の構造とフィールド間制約について文書化する。

## Design Intent

### 構造の概要

`AgentConfig`は7つのドメインサブ設定とスカラーフィールドで構成される:
- `llm`, `rag`, `tool`, `memory`, `mcp`, `approval`, `obs`
- `security_lockdown_enabled`: DENY-ALL承認警告の抑制

### 無効なキー

`workflow_mode`と`workflow_require_approval`は有効なキーではない。
`build_agent_config()`はこれらのキーを消費せず、エラー・警告なしで無視される。

### ワークフロー必須の設計判断

エージェントは無条件に有効なワークフロー定義を要求する。
`StartupOrchestrator`の初期化処理は`Orchestrator.__init__()`の前に
2つのプレフライトチェックを呼び出す:
1. ワークフロー定義の存在チェック
2. ワークフロースキーマ検証

いずれのチェックも`StartupOrchestrator.run()`によって捕捉されない;
失敗はREPLに伝播し、起動を中止させる。

### フィールド間検証

- `rag.use_semantic_cache=True` → `rag.embed_url`は非空である必要がある
- `memory.use_memory_layer=True` → `memory.memory_jsonl_dir`は非空である必要がある
- `memory.memory_embed_enabled=True` → `rag.embed_url`は非空である必要がある

## Responsibility Boundary

- **正典**: `agent/config_builders.py`の`AgentConfig`データクラス

## Key Constraints

- ワークフロー定義は必須（スキップ不可）
- 無効なキーは静かに無視される

## Operational Notes

- 不明

## Known Limitations

- 不明

## Related Docs

- `05_agent_00_document-guide.md`
- `05_agent_08_02_configuration-llm-rag.md`
- `05_agent_08_03_configuration-tools-memory.md`
- `05_agent_08_04_configuration-mcp-approval-obs.md`
- `05_agent_08_01_configuration-loading-agent-config.md`

## Keywords

configuration loading
hot-reload eligibility
AgentConfig structure

# エージェント設定

- 運用 → [05_agent_10_01_operations-and-observability-startup-and-health.md](05_agent_10_01_operations-and-observability-startup-and-health.md)

## Purpose

`AgentConfig`の構造とフィールド間制約について文書化する。

## Design Intent

### 構造の概要

`AgentConfig`は7つのドメインサブ設定とスカラーフィールドで構成される:
- `llm`, `rag`, `tool`, `memory`, `mcp`, `approval`, `obs`
- `security_lockdown_enabled`: DENY-ALL承認警告の抑制

### 無効なキー

`workflow_mode`と`workflow_require_approval`は有効なキーではない。
`build_agent_config()`はこれらのキーを消費せず、エラー・警告なしで無視される。

### ワークフロー必須の設計判断

エージェントは無条件に有効なワークフロー定義を要求する。
`StartupOrchestrator`の初期化処理は`Orchestrator.__init__()`の前に
2つのプレフライトチェックを呼び出す:
1. ワークフロー定義の存在チェック
2. ワークフロースキーマ検証

いずれのチェックも`StartupOrchestrator.run()`によって捕捉されない;
失敗はREPLに伝播し、起動を中止させる。

### フィールド間検証

- `rag.use_semantic_cache=True` → `rag.embed_url`は非空である必要がある
- `memory.use_memory_layer=True` → `memory.memory_jsonl_dir`は非空である必要がある
- `memory.memory_embed_enabled=True` → `rag.embed_url`は非空である必要がある

## Responsibility Boundary

- **正典**: `agent/config_builders.py`の`AgentConfig`データクラス

## Key Constraints

- ワークフロー定義は必須（スキップ不可）
- 無効なキーは静かに無視される

## Operational Notes

- 不明

## Known Limitations

- 不明

## Related Docs

- `05_agent_00_document-guide.md`
- `05_agent_08_02_configuration-llm-rag.md`
- `05_agent_08_03_configuration-tools-memory.md`
- `05_agent_08_04_configuration-mcp-approval-obs.md`
- `05_agent_08_01_configuration-loading-agent-config.md`

## Keywords

configuration loading
hot-reload eligibility
AgentConfig structure

