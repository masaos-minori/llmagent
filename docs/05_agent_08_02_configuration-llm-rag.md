---
title: "Agent Configuration - LLMConfig and RAGConfig"
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

LLM設定とRAG設定の構造と制約について文書化する。

## Design Intent

### LLM設定

#### 生成パラメータ

- `temperature`: 生成温度（0.0-2.0）
- `max_tokens`: 最大生成トークン数
- セッションタイトル用: `title_llm_temperature` (0.1), `title_llm_max_tokens` (20)

#### HTTP/接続

- `llm_url`: LLMエンドポイントURL
- `http_timeout`: HTTPタイムアウト（秒）
- `llm_max_retries`: HTTP 429/503/接続エラーのリトライ上限
- `llm_retry_base_delay`: 指数バックオフの基準値（秒）

#### SSEストリーミング

- `sse_heartbeat_timeout`: SSEアイドルタイムアウト（0 = 無効）
- `sse_malformed_retry`: 不正なSSEフレームの許容回数
- `sse_reconnect_max`: リトライ可能なエラー発生時の最大SSE再接続回数
- `llm_stream_retry_on_heartbeat_timeout`: HEARTBEAT_TIMEOUT発生時に再接続
- `llm_stream_retry_on_malformed_chunk`: MALFORMED_SSE_FRAME発生時に再接続

#### トークンカウント

- `tokenize_url`: llamacppの/tokenize URL; "" = chars//4フォールバック

#### 履歴圧縮

- `context_token_limit`: トークンベースの圧縮閾値（0 = 無効）
- `context_char_limit`: 文字数ベースの圧縮閾値
- `context_compress_turns`: 1サイクルで圧縮する最も古いNターンペア
- `history_protect_turns`: 圧縮から保護される直近のNターンペア

#### バジェット警告

- `budget_warn_ratio`: 履歴がこの上限に対する割合に達した場合に警告

### RAG設定

#### 検索パラメータ

- `top_k_search`: ベクトル/FTS検索結果数
- `top_k_rerank`: クロスエンコーダの候補数
- `max_chunks_per_doc`: 結果内の文書ごとの最大チャンク数
- `rrf_k`: RAGパイプラインのRRF（Reciprocal Rank Fusion）融合定数

#### セマンティックキャッシュ

- `use_semantic_cache`: セマンティックキャッシュの有効化
- `semantic_cache_threshold`: キャッシュヒットのコサイン類似度閾値
- `semantic_cache_max_size`: 最大キャッシュエントリ数（FIFO退避）

#### Refiner

- `use_refiner`: リランキング後にLLMでチャンクを圧縮
- `refiner_max_tokens`: Refiner LLMの最大トークン数
- `refiner_timeout`: Refiner LLMのタイムアウト（秒）
- `refiner_max_chars_per_chunk`: Refinerに渡すチャンクごとの最大文字数

## Responsibility Boundary

- **正典**: `config/agent.toml`のLLM/RAGセクション
- **バリデーション**: `agent/services/config_validators.py`
- **データクラス**: `agent/config_dataclasses.py`の`LLMConfig` / `RAGConfig`

## Key Constraints

- `rag.use_semantic_cache=True` → `rag.embed_url`は非空である必要がある（Part 2参照）
- `memory.memory_embed_enabled=True` → `rag.embed_url`は非空である必要がある（Part 2参照）

## Operational Notes

- 不明

## Known Limitations

- 不明

## Related Docs

- `05_agent_00_document-guide.md`
- `05_agent_08_01_configuration-loading-agent-config-part1.md`
- `05_agent_08_03_configuration-tools-memory.md`
- `05_agent_08_04_configuration-mcp-approval-obs.md`

## Keywords

LLMConfig
RAGConfig
