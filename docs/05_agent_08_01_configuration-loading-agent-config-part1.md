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

過去の経緯: 以前のバージョンでは複数の個別ファイル (`common.toml`, `llm.toml`, `http.toml`, `context.toml`, `rag.toml`, `tools.toml`, `memory.toml`, `otel.toml`, `security.toml`, `system_prompts.toml`, `tools_definitions.toml`、加えてサーバーごとの`*_mcp_server.toml`) を読み込んでいた。これらは`agent.toml`に統合され、分割されたファイルはもはや存在しない。

正準の設定所有関係表 (ファイルごとの所有レイヤー) については、
[90_shared_03 §2a Config Ownership](90_shared_03_01_runtime_and_execution-config-and-logging.md#config-ownership)を参照。

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

### 設定の責務境界

#### 設定ファイルの所有関係

| ファイル | 責務 | ホットリロード |
|---|---|---|
| `config/agent.toml` | エージェントプロセス設定（LLM/RAG/DB/ツール/メモリ/観測/承認/MCPライフサイクル） | ほとんど可能; `use_memory_layer`/`memory_embed_enabled`は起動時のみ |
| `config/*_mcp_server.toml` | MCPサーバー固有設定（allowlist/denylist/リソース制限/監査パス等） | 再起動必須（追加/削除/リネーム時） |

#### 再起動が必要な設定

- MCPサーバーのURL、認証トークン、起動モード、コマンド、環境変数の変更
- `use_memory_layer` — メモリサブシステムの有効/無効（起動時のみ）
- `memory_embed_enabled` — 埋め込み生成・KNN検索の有効/無効（起動時のみ）
- `memory_jsonl_dir` — メモリエントリのJSONLバックアップ先ディレクトリ（起動時のみ）
- `routing_drift_strict` — ルーティングドリフトのfatal扱い（起動時のみ）

#### ホットリロード可能な範囲

- LLMClient: temperature, max_tokens, max_retries, retry_base_delay, SSEパラメータ
- HistoryManager: context_char_limit, context_compress_turns, context_token_limit, tokenize_url
- ToolExecutor: tool_cache_ttl
- システムプロンプト: system_prompt_tool → `ctx.conv.system_prompt_content`

#### 変更時の運用影響

`ConfigReloadOutcome`の出力で以下のカテゴリを確認:
- `[APPLIED]` — ホットリロード適用済み
- `[RESTART]` — サブシステム再起動が必要
- `[STARTUP-ONLY]` — `/reload`では変更できないフィールド

#### セキュリティに関わる設定

- MCPサーバーのauth_token変更は再起動必須
- allowlist/denylistの変更は再起動必須

### 実装詳細の参照先

フィールド単位の完全なマッピングについては `agent/services/config_reload.py` を参照。

---

## Workflow Definition Schema

ワークフロー定義は `config/workflows/<name>.json` に配置される。ファイル名がワークフロー名になる。

### スキーマ

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `name` | string | Yes | — | ワークフローの名前（ファイル名と一致） |
| `version` | string | Yes | — | ワークフローのバージョン（文字列） |
| `stages` | array[Stage] | Yes | — | ステージ定義の配列。必須ステージ: `plan`, `execute`, `verify` |
| `retry_policy` | RetryPolicy | Yes | — | リトライポリシー |
| `require_approval` | boolean | No | `false` | execute→verify間に人間承認ゲートを有効化 |

### Stage

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `id` | string | Yes | — | ステージID（一意） |
| `timeout_sec` | integer | Yes | — | タイムアウト秒数 |
| `retryable` | boolean | Yes | — | リトライ可能かどうか。`WorkflowEngine._run_stage_with_retry()`がこのフラグを見て、ステージごとにリトライループを適用するか単発実行にするかを決定する（enforced; 単なる宣言値ではない） |

**注記(2026-07-17):** `description`フィールドは削除された。`StageDefinition.description`はどのコードパスからも読み取られておらず、`config/workflows/default.json`のインラインコメントとしての役割しか持たなかった。ステージの説明は本ドキュメントおよびソースコードのコメントを参照すること。

### RetryPolicy

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `max_attempts` | integer | Yes | — | 最大試行回数（>= 1） |
| `backoff_sec` | integer | Yes | — | バックオフ秒数（>= 0） |

**注記(2026-07-17):** `backoff`フィールドは削除された。バックオフ戦略は"fixed"（`backoff_sec`秒の固定遅延）のみが実装されており、他の戦略を選択する余地がなかったため、この文字列フィールドは実質的に定数だった。将来、`"fixed"`以外のバックオフ戦略を実装する際に再度検討する。

### 検証ルール

- 必須キー（`name`, `version`, `stages`, `retry_policy`）のいずれかが欠如するとエラー
- `stages` は空でないリストである必要があり、重複したステージIDは許されない
- 必須ステージ（`plan`, `execute`, `verify`）のすべてが含まれている必要がある
- 各ステージは `id`, `timeout_sec`, `retryable` のすべてのキーを持つ必要がある
- `retry_policy` は `max_attempts`, `backoff_sec` のすべてのキーを持つ必要がある
- `max_attempts` は 1 以上、`backoff_sec` は 0 以上である必要がある

### 承認ゲートについて

`require_approval=true` を設定すると、ワークフローエンジンは execute ステージ完了後、verify ステージの前に承認ゲートを挿入する。この状態は `workflow.sqlite` の `approvals` テーブルに永続化され、エージェント再起動後も復元される。承認は `/approve <approval_id>` または `/reject <approval_id>` コマンドで解決する。

標準デプロイでは、`config/workflows/default.json` に `require_approval` フィールドが含まれていないため、デフォルトで承認ゲートは発火しない。

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
