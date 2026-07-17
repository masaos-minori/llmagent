---
title: "Agent Configuration - LLMConfig and RAGConfig"
category: agent
tags:
  - agent
  - configuration
  - llmconfig
  - ragconfig
related:
  - 05_agent_00_document-guide.md
  - 05_agent_08_01_configuration-loading-agent-config-part1.md
  - 05_agent_08_03_configuration-tools-memory.md
  - 05_agent_08_04_configuration-mcp-approval-obs.md
source:
  - 05_agent_08_01_configuration-loading-agent-config-part1.md
---

# エージェント設定

- 運用 → [05_agent_10_01_operations-and-observability-startup-and-health.md](05_agent_10_01_operations-and-observability-startup-and-health.md)

## LLMConfig (`cfg.llm.*`)

Source: `config/agent.toml`

| Field | Default | Description |
|---|---|---|
| `llm_url` | `""` | LLMエンドポイントURL |
| `http_timeout` | `30.0` | HTTPタイムアウト (秒) |
| `llm_max_retries` | `3` | HTTP 429/503/接続エラーのリトライ上限 |
| `llm_retry_base_delay` | `1.0` | 指数バックオフの基準値 (秒) |
| `llm_temperature` | `0.2` | 生成温度 (0.0-2.0) |
| `llm_max_tokens` | `1024` | 最大生成トークン数 |
| `title_llm_temperature` | `0.1` | セッションタイトル生成の温度 |
| `title_llm_max_tokens` | `20` | セッションタイトルの最大トークン数 |
| `sse_heartbeat_timeout` | `30.0` | SSEアイドルタイムアウト (0 = 無効) |
| `sse_malformed_retry` | `2` | 不正なSSEフレームの許容回数 |
| `sse_reconnect_max` | `1` | リトライ可能なエラー発生時の最大SSE再接続回数 |
| `llm_stream_retry_on_heartbeat_timeout` | `True` | HEARTBEAT_TIMEOUT発生時に再接続 |
| `llm_stream_retry_on_malformed_chunk` | `False` | MALFORMED_SSE_FRAME発生時に再接続 |
| `tokenize_url` | `""` | llamacppの`/tokenize` URL; `""` = chars//4フォールバック |
| `context_token_limit` | `0` | トークンベースの圧縮閾値 (0 = 無効) |
| `context_char_limit` | `8000` | 文字数ベースの圧縮閾値 |
| `context_compress_turns` | `4` | 1サイクルで圧縮する最も古いNターンペア |
| `history_protect_turns` | `2` | 圧縮から保護される直近のNターンペア |
| `budget_warn_ratio` | `0.8` | 履歴がこの上限に対する割合に達した場合に警告 |

**バリデーションルール** (`agent/services/config_validators.py`):

| 関数 | 条件 |
|---|---|
| `validate_llm_context_char_limit()` | `context_char_limit >= 0` |
| `validate_llm_budget_warn_ratio()` | `0.0 < budget_warn_ratio <= 1.0` |
| `validate_llm_max_retries()` | `llm_max_retries >= 0` |
| `validate_llm_retry_base_delay()` | `llm_retry_base_delay > 0` |
| `validate_llm_temperature()` | `0.0 <= llm_temperature <= 2.0` |
| `validate_llm_max_tokens()` | `llm_max_tokens >= 1` |
| `validate_llm_sse_heartbeat_timeout()` | `sse_heartbeat_timeout >= 0` |
| `validate_llm_sse_malformed_retry()` | `sse_malformed_retry >= 0` |
| `validate_llm_sse_reconnect_max()` | `sse_reconnect_max >= 0` |

---

## RAGConfig (`cfg.rag.*`)

Source: `config/agent.toml`

| Field | Default | Description |
|---|---|---|
| `top_k_search` | `20` | ベクトル/FTS検索結果数 |
| `top_k_rerank` | `15` | クロスエンコーダの候補数 |
| `max_chunks_per_doc` | `2` | 結果内の文書ごとの最大チャンク数 |
| `embed_url` | `""` | 埋め込みAPIエンドポイント |
| `use_semantic_cache` | `False` | RAG結果に対するセマンティックキャッシュを有効化 |
| `semantic_cache_threshold` | `0.92` | キャッシュヒットのコサイン類似度閾値 |
| `semantic_cache_max_size` | `100` | 最大キャッシュエントリ数 (FIFO退避; 最も古いものから削除) |
| `use_refiner` | `False` | リランキング後にLLMでチャンクを圧縮 |
| `refiner_max_tokens` | `512` | Refiner LLMの最大トークン数 |
| `refiner_timeout` | `30.0` | Refiner LLMのタイムアウト (秒) |
| `refiner_max_chars_per_chunk` | `300` | Refinerに渡すチャンクごとの最大文字数 |
| `rrf_k` | `60` | RAGパイプラインのRRF (Reciprocal Rank Fusion) 融合定数 |

**バリデーションルール** (`agent/services/config_validators.py`):

| 関数 | 条件 |
|---|---|
| `validate_rag_top_k_search()` | `top_k_search >= 1` |
| `validate_rag_top_k_rerank()` | `top_k_rerank >= 1` |
| `validate_rag_max_chunks_per_doc()` | `max_chunks_per_doc >= 1` |
| `validate_rag_refiner_max_tokens()` | `refiner_max_tokens >= 1` |
| `validate_rag_refiner_timeout()` | `refiner_timeout > 0` |
| `validate_rag_refiner_max_chars_per_chunk()` | `refiner_max_chars_per_chunk >= 1` |

**注記(2026-07-17):** `web_search_max_results`（`agent.toml`, `RAGConfig`）は削除された。`RAGConfig.web_search_max_results`はどのコードパスからも読み取られておらず、web検索の結果件数上限は`config/web_search_mcp_server.toml`の`default_max_results`/`max_results_limit`（`WebSearchConfig`、`search_web` MCPサーバー側で実際に enforced）が唯一の実効設定である。
| `validate_rag_rrf_k()` | `rrf_k >= 1` |

> **矛盾の記録:** 旧版では`top_k_search`のデフォルトを`10`、`embed_url`のデフォルトを
> `http://127.0.0.1:8003/embedding`としていたが、`agent/config_dataclasses.py::RAGConfig`の
> 現在の実装ではそれぞれ`20`と`""` (空文字) である。`embed_url`が空の場合、
> `use_semantic_cache=True`や`memory.memory_embed_enabled=True`との組み合わせは
> `AgentConfig`のフィールド間検証で`ValueError`となる (Part 2参照)。
> 根拠: Explicit in code。

---

## Related Documents

- `05_agent_00_document-guide.md`
- `05_agent_08_01_configuration-loading-agent-config-part1.md`
- `05_agent_08_03_configuration-tools-memory.md`
- `05_agent_08_04_configuration-mcp-approval-obs.md`

## Keywords

LLMConfig
RAGConfig
