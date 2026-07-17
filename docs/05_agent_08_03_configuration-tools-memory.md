---
title: "Agent Configuration - ToolConfig and MemoryConfig"
category: agent
tags:
  - agent
  - configuration
  - toolconfig
  - memoryconfig
related:
  - 05_agent_00_document-guide.md
  - 05_agent_08_01_configuration-loading-agent-config-part1.md
  - 05_agent_08_02_configuration-llm-rag.md
  - 05_agent_08_04_configuration-mcp-approval-obs.md
source:
  - 05_agent_08_01_configuration-loading-agent-config-part1.md
---

# エージェント設定

- 運用 → [05_agent_10_01_operations-and-observability-startup-and-health.md](05_agent_10_01_operations-and-observability-startup-and-health.md)

## ToolConfig (`cfg.tool.*`)

Source: `config/agent.toml`

| Field | Default | Production Recommended | Description |
|---|---|---|---|
| `tool_cache_ttl` | `300.0` | `300.0` | ツール実行結果キャッシュのTTL (秒) |
| `tool_cache_max_size` | `200` | `200` | LRUキャッシュサイズ (0 = 無制限) |
| `serial_tool_calls` | `False` | `False` | ツール実行を強制的に逐次化 |
| `tool_definitions_strict` | `False` | `True` | `true`: 到達可能なサーバーでのスキーマ不一致 → 起動時に`RuntimeError`。`false`: 不一致 → WARNINGのみ。すべてのサーバーが到達不可の場合、strictモードでも検証をスキップする (中止しない)。全体の挙動表は[04_mcp_06 §Startup Validation Behavior](04_mcp_06_02_configuration-file-inventory.md)を参照。 |
| `routing_drift_strict` | `False` | `True` | `true`: 起動時にconfig/レジストリのルーティングドリフトを検出 → `RuntimeError` (起動中止)。`false`: ドリフト → `[non-fatal]` WARNINGのみ。起動時のみのフィールド; 反映には再起動が必要。 |
| `tool_dedup_max_repeats` | `3` | `3` | 同一(name,args)の繰り返し上限 |
| `tool_cycle_detect_window` | `2` | `2` | 循環検出ウィンドウ (ラウンド数; 0=無効) |
| `tool_error_max_consecutive` | `3` | `3` | ループを終了させる連続全エラーラウンド数 |
| `tool_error_retry_max` | `1` | `1` | エラーとなった(name,args)のリトライ上限 |
| `tool_concurrency_limits` | `{}` | `{}` | サーバーキー → 最大並行呼び出し数 |
| `masked_fields` | `["file_content"]` | `["file_content"]` | コンソール表示でマスクする引数キー |
| `plan_blocked_tools` | `[write_file, create_directory, ...]` | `[write_file, create_directory, ...]` | プランモードで自動ブロックされる |
| `max_tool_turns` | `5` | `5` | メッセージごとの最大ツール呼び出しターン数 |
| `tool_result_max_llm_chars` | `8000` | `8000` | LLMコンテキストに追加されるツール実行結果の最大文字数 |
| `tool_results_turn_max_chars` | `50000` | `50000` | 1ターン中にLLMコンテキストへ追加されるツール実行結果の累積最大文字数。複数のツール出力によるターンあたりの過剰なコンテキスト増大を防ぐ。超過した場合、省略された結果はTURN_LIMIT_HINTに置き換えられる。 |

**実装上の補足(`use_tool_dag`は存在しない):** `use_tool_dag`という設定フィールドはコードベース全体(`agent/config_dataclasses.py`含む)のどこにも存在しない(Explicit in code — grep調査で確認)。DAGスケジューリング(下記resource_scope規約)は`serial_tool_calls=False`(デフォルト)の場合に常時有効であり、「レガシー動作」へ切り替える設定フラグは実装上存在しない。`serial_tool_calls=True`の場合は[05_agent_06_01](05_agent_06_01_tool-execution-and-approval-execution.md#並列実行と逐次実行)記載の`_execute_standard()`(副作用のあるツールが1つでもあれば逐次、なければ並列)が使われる。詳細: [05_agent_06_01 §並列実行と逐次実行](05_agent_06_01_tool-execution-and-approval-execution.md#並列実行と逐次実行)。

**resource_scope 規約(DAGモード、`serial_tool_calls=False`のとき常時有効):**

ツールごとに `ToolSpec` を構築する際に以下のデフォルト値を適用する。

| Tool type | `resource_scope` default | `requires_serial` default | Scheduling bucket |
|---|---|---|---|
| WRITE_TOOLS / DELETE_TOOLS (config に `resource_scope` なし) | `{tool_name}` | `False` | `resource_groups[tool_name]` → concurrent batch |
| `shell_run` (SHELL_TOOLS) | `""` | `True` | serial_barrier (1呼び出しずつ) |
| Read / その他 | `""` | `False` | `parallel` → concurrent batch |

`config/agent.toml`(`[[tool_definitions]]`)に `resource_scope` または `requires_serial` を明示した場合はそれが優先される。同一 `resource_scope` を持つ write ツールの複数呼び出しは同一グループ内で `asyncio.gather` により並行実行される。

以下も`ToolConfig`のフィールドである(Source: `config/agent.toml`):

| Field | Default | Description |
|---|---|---|
| `tool_definitions` | `[]` | `[[tool_definitions]]`由来のLLM向けツールスキーマ一覧 |
| `system_prompts` | `{}` | システムプロンプトプリセットのdict |
| `allowed_tools` | `[]` | セッションのツールホワイトリスト (空 = すべて許可) |

---

## MemoryConfig (`cfg.memory.*`)

Source: `config/agent.toml`

| Field | Default | Description |
|---|---|---|
| `use_memory_layer` | `False` | 永続的なセマンティックメモリを有効化 |
| `memory_jsonl_dir` | `"/opt/llm/memory"` | JSONLソースディレクトリ (正式なキー; `memory_jsonl_path`ではない) |
| `memory_max_inject_semantic` | `5` | セッション開始時に注入されるセマンティックエントリ数 |
| `memory_max_inject_episodic` | `3` | ユーザープロンプトごとに注入されるエピソードエントリ数 |
| `memory_min_importance` | `0.3` | 注入に必要な最小重要度スコア |
| `memory_embed_enabled` | `False` | メモリ検索のための埋め込み+KNNを有効化 |
| `memory_embed_dim` | `384` | 埋め込み次元数 (vec0スキーマと一致する必要がある) |
| `memory_dedup_threshold` | `0.3` | 重複排除リンク検出のL2距離 |
| `memory_max_content_chars` | `500` | メモリエントリごとに保存する最大コンテンツ文字数 |
| `memory_embed_timeout_sec` | `5.0` | 埋め込みHTTP呼び出しのタイムアウト |
| `memory_retention_days` | `90` | 保持期間 (日数) |
| `memory_local_only` | `False` | 起動時にloopback以外の`embed_url`を拒否 |
| `memory_fts_limit` | `50` | 再スコアリング前のFTS5候補数上限 |
| `memory_rrf_k` | `60` | RRF融合定数 |
| `memory_recency_days` | `7.0` | 直近性ブーストのウィンドウ (日数) |

**有効化モード**: `use_memory_layer`, `memory_embed_enabled`, 埋め込みサーキットの状態の組み合わせにより決定される:

| `use_memory_layer` | `memory_embed_enabled` | Circuit | Mode |
|---|---|---|---|
| `false` | any | any | `disabled` |
| `true` | `false` | any | `fts-only` |
| `true` | `true` | open | `degraded` |
| `true` | `true` | closed | `hybrid` |

---

## Related Documents

- `05_agent_00_document-guide.md`
- `05_agent_08_01_configuration-loading-agent-config-part1.md`
- `05_agent_08_02_configuration-llm-rag.md`
- `05_agent_08_04_configuration-mcp-approval-obs.md`

## Keywords

ToolConfig
MemoryConfig
