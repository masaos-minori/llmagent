---
title: "Agent Configuration - ToolConfig and MemoryConfig"
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

ツール設定とメモリ設定の構造と制約について文書化する。

## Design Intent

### ツール設定

#### 安全性

- `tool_definitions_strict`: スキーマ不一致 → 起動時にRuntimeError（production推奨）
- `routing_drift_strict`: ルーティングドリフトを検出 → RuntimeError（起動中止）（production推奨）
- `plan_blocked_tools`: プランモードで自動ブロックされるツール
- `masked_fields`: コンソール表示でマスクする引数キー

#### 実行制御

- `serial_tool_calls`: ツール実行の逐次化
- `max_tool_turns`: メッセージごとの最大ツール呼び出しターン数
- `tool_cycle_detect_window`: 循環検出ウィンドウ（ラウンド数）
- `tool_error_max_consecutive`: 連続全エラーラウンド数（ループ終了条件）
- `tool_error_retry_max`: エラーとなった(name,args)のリトライ上限

#### コンテキスト肥大防止

- `tool_result_max_llm_chars`: LLMコンテキストに追加されるツール実行結果の最大文字数
- `tool_results_turn_max_chars`: 1ターン中にLLMコンテキストへ追加されるツール実行結果の累積最大文字数

#### キャッシュ

- `tool_cache_ttl`: ツール実行結果キャッシュのTTL（秒）
- `tool_cache_max_size`: LRUキャッシュサイズ

#### 並列実行

- `tool_concurrency_limits`: サーバーキー → 最大並行呼び出し数

#### resource_scope 規約（DAGモード、`serial_tool_calls=False`のとき常時有効）

| Tool type | `resource_scope` default | `requires_serial` default | Scheduling bucket |
|---|---|---|---|
| WRITE_TOOLS / DELETE_TOOLS | `{tool_name}` | `False` | `resource_groups[tool_name]` → concurrent batch |
| `shell_run` (SHELL_TOOLS) | `""` | `True` | serial_barrier |
| Read / その他 | `""` | `False` | `parallel` → concurrent batch |

#### その他のフィールド

- `tool_definitions`: `[[tool_definitions]]`由来のLLM向けツールスキーマ一覧
- `system_prompts`: システムプロンプトプリセットのdict
- `allowed_tools`: セッションのツールホワイトリスト（空 = すべて許可）

### メモリ設定

#### 有効化モード

`use_memory_layer`, `memory_embed_enabled`, 埋め込みサーキットの状態の組み合わせにより決定される:

| `use_memory_layer` | `memory_embed_enabled` | Circuit | Mode |
|---|---|---|---|
| `false` | any | any | `disabled` |
| `true` | `false` | any | `fts-only` |
| `true` | `true` | open | `degraded` |
| `true` | `true` | closed | `hybrid` |

#### 注入パラメータ

- `memory_max_inject_semantic`: セッション開始時に注入されるセマンティックエントリ数
- `memory_max_inject_episodic`: ユーザープロンプトごとに注入されるエピソードエントリ数
- `memory_min_importance`: 注入に必要な最小重要度スコア

#### 埋め込み関連

- `memory_embed_enabled`: メモリ検索のための埋め込み+KNNを有効化
- `memory_embed_dim`: 埋め込み次元数（vec0スキーマと一致する必要がある）
- `memory_embed_timeout_sec`: 埋め込みHTTP呼び出しのタイムアウト
- `memory_local_only`: 起動時にloopback以外の`embed_url`を拒否

#### 検索・フィルタリング

- `memory_fts_limit`: 再スコアリング前のFTS5候補数上限
- `memory_rrf_k`: RRF融合定数
- `memory_recency_days`: 直近性ブーストのウィンドウ（日数）
- `memory_retention_days`: 保持期間（日数）

#### 重複排除

- `memory_dedup_threshold`: 重複排除リンク検出のL2距離

#### コンテンツ制限

- `memory_max_content_chars`: メモリエントリごとに保存する最大コンテンツ文字数

## Responsibility Boundary

- **正典**: `config/agent.toml`のTool/Memoryセクション
- **バリデーション**: `agent/services/config_validators.py`
- **データクラス**: `agent/config_dataclasses.py`の`ToolConfig` / `MemoryConfig`

## Key Constraints

- `tool_definitions_strict=True`の場合、到達可能なサーバーでのスキーマ不一致は起動中止
- `routing_drift_strict=True`の場合、ルーティングドリフトは起動中止
- `allowed_tools=[]`（空）は「すべて許可」を意味する — 意図しない動作を防ぐため明示的に確認が必要
- `memory_embed_enabled=True` → `rag.embed_url`は非空である必要がある（Part 2参照）

## Operational Notes

- 不明

## Known Limitations

- 不明

## Related Docs

- `05_agent_00_document-guide.md`
- `05_agent_08_01_configuration-loading-agent-config-part1.md`
- `05_agent_08_02_configuration-llm-rag.md`
- `05_agent_08_04_configuration-mcp-approval-obs.md`

## Keywords

ToolConfig
MemoryConfig
