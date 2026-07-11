---
title: "RAG System Overview"
category: rag
tags:
  - rag
  - system
  - overview
  - architecture
  - pipeline
related:
  - 03_rag_00_document-guide.md
  - 03_rag_02_01_ingestion_pipeline-overview.md
  - 03_rag_03_01_query_pipeline-overview.md
---

# RAG システム概要

- ドキュメントガイド → [03_rag_00_document-guide.md](03_rag_00_document-guide.md)

## 目的

Webページとローカルファイルをクロールし、SQLiteにインデックスを構築し、各LLMターンに
関連するコンテキストブロックを注入することで、LLMエージェントに文書検索拡張を提供する。

---

## 対象範囲

**対象に含まれるもの:**
- インジェクションパイプライン: `scripts/rag/ingestion/crawler.py`, `scripts/rag/ingestion/chunk_splitter.py`, `scripts/rag/ingestion/ingester.py`
- クエリパイプライン: `scripts/rag/pipeline.py`, `scripts/rag/repository.py`, `scripts/rag/llm_client.py`, `scripts/rag/stages/`
- ユーティリティ: `scripts/rag/utils.py`
- MCPラッパー: `scripts/mcp_servers/rag_pipeline/server.py`（ポート8010）

**対象に含まれないもの:**
- MDQ（Markdown専用インデックス）— 別サービス。境界の定義は [04_mcp_05 §MDQ vs RAG Boundary](04_mcp_05_security_and_safety_model.md#mdq-vs-rag-boundary) を参照
- エージェントREPL — MCPを介してパイプラインを呼び出すのみで、RAGロジックは持たない
- LLMおよび埋め込みサーバー — ポート8001および8003で動作する外部サービス

---

## システムアーキテクチャ

```
[Admin / Operator]
      |
      | crawler.py CLI
      v
+------------------+     rag-src/*.json     +-------------------+     rag-src/chunk/*.json
|  crawler.py      | -------------------->  | chunk_splitter.py | -------------------->
|  (WebCrawler)    |                         | (ChunkSplitter)   |
+------------------+                         +-------------------+
                                                                         |
                                                                         v
                                                               +------------------+
                                                               |  ingester.py     |
                                                               |  (RagIngester)   |
                                                               +------------------+
                                                                        |
                                                                        | embed (port 8003)
                                                                        | INSERT SQLite
                                                                        v
                                                              rag-src/registered/

[Agent turn]
      |
      | augment(query)
      v
+----------------------+    MCP :8010    +-------------------+
| scripts/mcp_servers/rag_pipeline/ | <-------------> | RagPipeline       |
| service.py           |                 | (6 logical stages)|
+----------------------+                 +-------------------+
                                                   |
                                          +--------+--------+
                                          | KNN + BM25      |
                                          | SQLite (rag.db) |
                                          +-----------------+
```

---

## インジェクションパイプライン

**3つのスクリプト / 4つの処理フェーズ**

| スクリプト | フェーズ | 入力 | 出力 |
|---|---|---|---|
| `crawler.py` | クロール | URLまたはローカルパス | `rag-src/yyyymmddhhmmss-{slug}.json`（JSON） |
| `chunk_splitter.py` | チャンク化 | `rag-src/*.json` | `rag-src/chunk/{stem}-{idx:04d}.json`（JSON） |
| `ingester.py` | 埋め込み | `rag-src/chunk/*.json` | 埋め込みAPI呼び出し（ポート8003） |
| `ingester.py` | 格納 | 埋め込みベクトル | SQLiteテーブル + `rag-src/registered/` |

> **用語について:** 「3つのスクリプト」とは、3つの実行ファイル（`crawler.py`、`chunk_splitter.py`、`ingester.py`）を指す。
> 「4つの処理フェーズ」とは、4つの論理的なステップ（クロール、チャンク化、埋め込み、格納）を指し、そのうち2つは `ingester.py` の内部で実行される。
> 「ステージ（Stage）」という語はクエリパイプラインのステージ（MQE、Search、Fusion、Rerank、PluginHooks、Augment）専用であり、インジェクションでは使用しない。

### インジェクションのデータフロー（概要）

```
config/rag_pipeline.toml [target_urls]
  → crawler.py: BFS crawl (same-origin) → rag-src/
  → chunk_splitter.py: language-aware splitting (JA: Sudachi / EN: sentence / code: blank-line)
                       → rag-src/chunk/
  → ingester.py: "passage: {text}" embed → struct.pack float32 BLOB → SQLite INSERT
                → rag-src/registered/
```

---

## クエリパイプライン

**エージェントの1ターンごとに実行される6つの論理ステージ**（固定5つ + PluginHooksは任意）

| ステージ | クラス | 機能 |
|---|---|---|
| 1. MQE | `MqeStage` | 再現率向上のためクエリをN個のバリアントに展開する |
| 2. Search | `SearchStage` | 各クエリバリアントに対しKNN（sqlite-vec）+ BM25（FTS5）を実行する |
| 3. Fusion | `FusionStage` | RRF（Σ 1/(rrf_k+rank)）を用いて複数クエリの結果を統合する。`rrf_k` は設定で変更可能（デフォルト: 60） |
| 4. Rerank | `RerankStage` | クロスエンコーダLLMによるスコアリング。`rag_min_score` でフィルタし、リランク後にURL単位で重複排除する |
| 5. PluginHooks | 登録済みフック | リランク後のプラグインステージ。RerankStageの後、AugmentStageの前に実行される。エラーは分離される（失敗はログに記録されスキップされる）。`run()` の `hook_strict` で挙動を設定可能 |
| 6. Augment | `AugmentStage` | チャンクを `[RAG_CONTEXT_START]...[RAG_CONTEXT_END]` 形式に整形する |

**エントリポイント:** `RagPipeline.augment(query) -> str`
**呼び出し元:** `scripts/mcp_servers/rag_pipeline/service.py`（MCP HTTP、ポート8010経由）

### セマンティックキャッシュ

`use_semantic_cache=True` の場合、クエリ埋め込みのコサイン類似度が `semantic_cache_threshold`
（デフォルト0.92）以上であれば、パイプラインをスキップしてキャッシュ済みのコンテキストブロックを返す。`threading.RLock` によりスレッドセーフである。FIFOキャッシュ（最古のエントリから削除）で、最大サイズは `semantic_cache_max_size`（デフォルト100件）。

---

## 前提条件

| 要件 | 確認コマンド |
|---|---|
| ポート8003で埋め込みサーバーが稼働していること | `curl -s http://127.0.0.1:8003/health` |
| `sqlite-vec` 拡張がロード可能であること | `/opt/llm/sqlite-vec/vec0.so` が存在すること |
| 設定ファイルが存在すること | `config/rag_pipeline.toml` |
| インジェクション対象のURLまたはファイルが指定されていること | CLIの `--url`、または設定内の `target_urls` |

---

## 制約

| 制約 | 値 | ソース |
|---|---|---|
| 言語判定 | CJK比率 ≥ 0.10 → `ja`; それ以外は `en`; 100文字未満はヒントへのフォールバック | `crawler.py` |
| チャンクサイズ | 最小40文字、最大500文字 | `rag_pipeline.toml` |
| チャンクの重複 | 50文字のスライディングウィンドウ | `rag_pipeline.toml` |
| 埋め込み次元 | 384（本番環境、`config/agent.toml:43`）。dataclassのデフォルト値はなく、設定ファイルでのみ定義される。float32リトルエンディアンBLOB | `config/agent.toml` — `03_rag_90` DOC-03を参照 |
| クロール深度 | 開始URLから最大6ホップ | `rag_pipeline.toml` |
| クロールページ数上限 | サイトあたり最大500ページ | `rag_pipeline.toml` |
| DB | SQLiteシングルノードのみ | アーキテクチャ |

---

## MCPサーバーの責務分担

| ファイル | 責務 |
|---|---|
| `scripts/mcp_servers/rag_pipeline/server.py` | HTTPエントリポイント + ルート定義 |
| `scripts/mcp_servers/rag_pipeline/service.py` | パイプラインアダプタ（ライフサイクル + レスポンス整形） |
| `scripts/rag/pipeline.py` | RAGのコアロジック |

## Related Chapters

| トピック | ファイル |
|---|---|
| インジェクションスクリプト（API、CLI、設定） | [03_rag_02_01_ingestion_pipeline-overview.md](03_rag_02_01_ingestion_pipeline-overview.md) |
| クエリパイプライン（API、ステージ詳細） | [03_rag_03_01_query_pipeline-overview.md](03_rag_03_01_query_pipeline-overview.md) |
| DBスキーマ、型定義 | [03_rag_04_05_dto-types.md](03_rag_04_01_dto-models_data.md) |
| 設定、実行コマンド、ログ | [03_rag_05_1-configuration-reference.md](03_rag_05_1-configuration-reference.md) |
| 既知のバグと不整合 | [03_rag_90_inconsistencies_and_known_issues.md](03_rag_90_inconsistencies_and_known_issues.md) |

## Related Documents

- `03_rag_00_document-guide.md`
- `03_rag_02_01_ingestion_pipeline-overview.md`
- `03_rag_03_01_query_pipeline-overview.md`

## Keywords

rag
system
overview
architecture
pipeline
