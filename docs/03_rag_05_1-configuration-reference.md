---
title: "1. Configuration Reference"
category: rag
tags:
  - rag
  - configuration
related:
  - 03_rag_00_document-guide.md
  - 03_rag_05_1-configuration-reference.md
source:
  - 03_rag_05_1-configuration-reference.md
---

# 1. 設定リファレンス

crawler / chunk_splitter / ingester / rag-pipeline-mcpはそれぞれ独立したプロセスであり、各自の設定ファイルのみを読み込む。共有の設定ファイルは存在しない。DBパスや外部サービスのURLを複数プロセスで必要とする場合、各設定ファイルにそれぞれ個別に指定する必要がある。

→ プロセス分離ポリシーの詳細: [90_shared_03 §2a](90_shared_03_01_runtime_and_execution-config-and-logging.md#2a-process-separation-policy-config-isolation-policy)

## 1.1 `config/crawler.toml`

使用元: `crawler.py` のみ

| Parameter | Default | Description |
|---|---|---|
| `rag_src_dir` | `/opt/llm/rag-src` | クローラーの出力先ディレクトリ: `{rag_src_dir}/*.json` |
| `rag_db_path` | `/opt/llm/db/rag.sqlite` | SQLiteデータベースのパス (ETag/Last-Modifiedの参照用) |
| `sqlite_timeout` | `30` | SQLite接続タイムアウト (秒) |
| `sqlite_busy_timeout_ms` | `30000` | SQLite busyタイムアウト (ミリ秒) |
| `crawl_delay` | `1.5` | クロールリクエスト間の待機秒数 (最小1.0推奨) |
| `max_depth` | `3` | 開始URLからのBFS最大ホップ深度 |
| `fetch_retry` | `3` | HTTPリクエストの再試行上限 (指数バックオフ: `min(2**i, 10)` 秒) |
| `fetch_timeout` | `15` | リクエストごとのHTTPタイムアウト (秒) |
| `crawl_concurrency` | `3` | 並列BFSリクエスト用の`asyncio.Semaphore`上限 |
| `max_pages` | `200` | サイトごとの最大ページ数 (`visited`がこの値に達するとBFSを停止) |
| `skip_nofollow` | `true` | trueの場合、`rel="nofollow"`リンクをBFSキューからスキップ |
| `skip_external` | `true` | trueの場合、クロスオリジンリンクをBFSキューからスキップ |
| `target_urls` | — | `[[url, lang], ...]`形式のペアのリスト。`--url`未指定時に使用 |
| `min_chunk` | `40` | 最小チャンクサイズ (文字数)。これより小さいチャンクはノイズとして破棄 |

## 1.2 `config/chunk_splitter.toml`

使用元: `chunk_splitter.py` のみ

| Parameter | Default | Description |
|---|---|---|
| `rag_src_dir` | `/opt/llm/rag-src` | チャンク入出力のベースディレクトリ |
| `min_chunk` | `40` | 最小チャンクサイズ (文字数)。これより小さいチャンクはノイズとして破棄 |
| `max_chunk` | `500` | 最大チャンクサイズ (文字数) |
| `chunk_overlap` | `50` | 前のチャンクから次のチャンクの先頭に付加する重複文字数 (0=無効) |
| `md_index_enable` | `false` | 見出し行が2行以上ある非`.md`コンテンツについて、Markdown見出し境界での分割を有効化。`.md`/`.markdown`/`.mdx`のURLは常に見出し分割を使用する |
| `md_snippet_max_chars` | `600` | Markdown見出しセクションごとの最大文字数。超えた場合はテキスト分割にフォールバック |
| `en_stopwords` | (設定を参照) | FTS5インデックスとチャンキングから除外する英語のストップワード |
| `ja_stop_pos` | `["助詞", "助動詞", "補助記号", "空白", "感動詞", "接続詞"]` (助詞、助動詞、補助記号、空白、感動詞、接続詞) | 日本語FTS5インデックスでストップワードとして扱われるSudachi品詞カテゴリ |

## 1.3 `config/ingester.toml`

使用元: `ingester.py` のみ

| Parameter | Default | Description |
|---|---|---|
| `rag_src_dir` | `/opt/llm/rag-src` | チャンク入力ディレクトリ: `{rag_src_dir}/chunk/*.json` |
| `rag_db_path` | `/opt/llm/db/rag.sqlite` | SQLiteデータベースのパス |
| `sqlite_vec_so` | `/opt/llm/sqlite-vec/vec0.so` | sqlite-vec拡張の共有ライブラリパス |
| `sqlite_timeout` | `30` | SQLite接続タイムアウト (秒) |
| `sqlite_busy_timeout_ms` | `30000` | SQLite busyタイムアウト (ミリ秒) |
| `embed_url` | `http://127.0.0.1:8081/embedding` | 埋め込みAPIのエンドポイント |
| `embedding_dims` | `384` | float32埋め込みベクトルの次元数 (モデルと一致必須: all-MiniLM-L6-v2 = 384) |
| `embed_retry` | `3` | 埋め込みAPIの再試行上限 (指数バックオフ) |
| `embed_workers` | `4` | 並列埋め込み用の`ThreadPoolExecutor`スレッド数 |

**注記（2026-07-13）:** `strict_artifact_validation` は設定として未参照(`RagIngester.__init__`が読まない、artifact検証関数の呼び出し側も`strict`未指定)であることを確認し、`config/ingester.toml`から削除した。実際にはartifact検証関数のPythonデフォルトにより、必須フィールド欠落チャンクの拒否は常時有効。

## 1.4 `config/rag_pipeline_mcp_server.toml`

使用元: `rag-pipeline-mcp` のみ (rag-pipeline MCPサーバープロセス)。`mcp_servers/rag_pipeline/models.py` の `RagPipelineConfig.from_dict()` が読み込む。`agent.toml`は使用しない (冒頭コメントに明記)。

**注記（2026-07-13）:** `host`/`port` は `RagPipelineConfig` に一切読み込まれず未参照だったため設定ファイルから削除した。実際の値はハードコード: `http_host="127.0.0.1"`（`MCPServer` 基底クラス）、`http_port=8010`（`server.py`）。`http_timeout` は `service.py` で `120.0` としてハードコードされているが、これはMCPサーバー自体のHTTPクライアントタイムアウトであり、外部RAGサービスへのフォールバック呼び出しには別のタイムアウト（10秒）が使用される。

| Parameter | Default | Description |
|---|---|---|
| `rag_db_path` | `/opt/llm/db/rag.sqlite` | SQLiteデータベースのパス |
| `sqlite_vec_so` | `/opt/llm/sqlite-vec/vec0.so` | sqlite-vec拡張の共有ライブラリパス |
| `sqlite_timeout` | `30` | SQLite接続タイムアウト (秒) |
| `sqlite_busy_timeout_ms` | `30000` | SQLite busyタイムアウト (ミリ秒) |
| `llm_url` | `http://127.0.0.1:8080/v1/chat/completions` | MQEおよびリランク用のLLMエンドポイント |
| `embed_url` | `http://127.0.0.1:8081/embedding` | 埋め込みAPIのエンドポイント |
| `use_mqe` | `true` | クエリ展開を有効化 |
| `use_rrf` | `true` | RRFマージを有効化 |
| `rrf_k` | `60` | RRF平滑化定数 (文献推奨値60) |
| `use_rerank` | `true` | クロスエンコーダーによるリランクを有効化 |
| `use_refiner` | `false` | LLMによるチャンク圧縮を有効化 |
| `top_k_search` | `5` (コードデフォルト。運用設定ファイルでは`20`) | クエリごとのKNN/FTSヒット数 |
| `top_k_rerank` | `10` (コードデフォルト。運用設定ファイルでは`15`) | クロスエンコーダーの候補数 |
| `rag_top_k` | `5` | LLMに返す最終的なチャンク数 |
| `rag_min_score` | `0.0` (コードデフォルト。運用設定ファイルでは`2.0`) | クロスエンコーダーのスコア下限 |
| `max_chunks_per_doc` | `3` | ドキュメントごとのチャンク数上限 |
| `use_semantic_cache` | `false` | SemanticCacheの使用可否 |
| `semantic_cache_max_size` | `128` (コードデフォルト。運用設定ファイルでは`100`) | SemanticCacheの容量 |
| `semantic_cache_threshold` | `0.92` | キャッシュヒット判定用のコサイン類似度閾値 |
| `refiner_max_tokens` | `512` | Refiner LLMの最大トークン数 |
| `refiner_max_chars_per_chunk` | `800` (`models.py` デフォルト値) | Refinerでのチャンクごとの最大文字数 |
| `refiner_timeout` | `30.0`(運用設定ファイル値) | Refiner LLMのタイムアウト (秒) |
| `mqe_n_queries` | `3` | MQEで生成するクエリバリエーションの数 |
| `mqe_prompt_template` | (組み込み) | MQEプロンプトテンプレート。プレースホルダー: `{n_queries}`、`{query}` |
| `rerank_prompt_template` | (組み込み) | クロスエンコーダー用プロンプトテンプレート。プレースホルダー: `{query}`、`{items_text}` |

**注記（2026-07-13）:** 外部RAGサービスへのフォールバック呼び出し（`call_rag_service()`）では、各試行ごとに `timeout=10.0` がハードコードされている（`pipeline_service.py:121`）。この値は設定ファイルや `RagPipelineConfig` から読み込まれておらず、変更するにはソースコードの修正が必要。

## 実装上の補足 (Current behavior)

- `top_k_search`・`top_k_rerank`・`rag_min_score`・`semantic_cache_max_size`は、`RagPipelineConfig`(`mcp_servers/rag_pipeline/models.py`)のコード上のデフォルト値と、実運用の`config/rag_pipeline_mcp_server.toml`に書かれている値が異なる。tomlに値がある限りコードデフォルトは使われないため実害はないが、tomlを削除・簡略化する場合はこの差に注意する必�がある。(Explicit in code)
- `rag_pipeline_mcp_server.toml`は`agent.toml`とは完全に独立しており、両ファイルで`use_mqe`等の同名キーが別々の値を持ちうる。ファイル冒頭コメントに「`agent_rag`・`rag_llm`・`sqlite_helper`のモジュールレベルキャッシュを上書きし、RAGパイプラインをメインエージェントプロセスから独立実行させるため」と明記されている。(Explicit in code)

## 1.5 `config/agent.toml`

使用元: エージェントプロセスのみ。`ConfigLoader().load_all()`から読み込まれ、`AgentConfig`を構築する。

**RagConfigプロトコルのフィールド** (`AgentConfig`経由で注入):

| Field | Description |
|---|---|
| `use_search` | RAG全体のオン/オフ切り替え |
| `use_mqe` | クエリ展開を有効化 |
| `use_rrf` | RRFマージを有効化 (`True`、デフォルト) してランク重み付き融合を行うか、重複排除のみ (`False`) にするか。**品質上のトレードオフ:** `False`にするとランクスコアリングが無効化され、すべてのヒットの`rrf_score`が`0.0`になる。MQEによる追加のランキング効果も得られなくなる。オーバーヘッドを最小化したい場合を除き`True`を維持することを推奨。`False`に設定するとパイプライン起動時に`WARNING rag config warning: use_rrf=false degrades retrieval quality`が出力される。 |
| `use_rerank` | クロスエンコーダーによるリランクを有効化 |
| `use_refiner` | LLMによるチャンク圧縮を有効化 |
| `top_k_search` | クエリごとのKNN/FTSヒット数 |
| `top_k_rerank` | クロスエンコーダーの候補数 |
| `rag_top_k` | LLMに返す最終的なチャンク数 |
| `rag_min_score` | クロスエンコーダーのスコア下限 |
| `max_chunks_per_doc` | ドキュメントごとのチャンク数上限 |
| `rag_service_url` | 外部RAGサービスのURL (空=インプロセス) |
| `semantic_cache_max_size` | SemanticCacheの容量 (0=即時全破棄/事実上無効、負値はバリデーションエラー) |
| `semantic_cache_threshold` | キャッシュヒット判定用のコサイン類似度閾値 |
| `refiner_max_tokens` | Refiner LLMの最大トークン数 |
| `refiner_max_chars_per_chunk` | Refinerでのチャンクごとの最大文字数 |
| `refiner_timeout` | Refiner LLMのタイムアウト (秒) |

---


## Related Documents

- [03_rag_05_1-configuration-reference.md](03_rag_05_1-configuration-reference.md)

## Keywords

configuration
