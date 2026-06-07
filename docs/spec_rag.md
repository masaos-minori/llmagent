# RAG パイプライン仕様

## 1. 目的

Web クロール・チャンク分割・埋め込み生成・SQLite 格納の 4 段階からなるインジェストパイプライン、および MQE・ベクター/FTS 検索・RRF・リランク・増補の 5 段階からなるクエリパイプラインを提供し、エージェントの応答精度を高めるためのドキュメントコンテキストを供給する。

---

## 2. スコープ

- **インジェスト:** `rag/ingestion/web_crawler.py`、`rag/ingestion/chunk_splitter.py`、`rag/ingestion/rag_ingester.py`
- **クエリ:** `rag/pipeline.py`、`rag/repository.py`、`rag/llm.py`
- **ユーティリティ:** `rag/utils.py`
- **MCP ラッパー:** `mcp/rag_pipeline/server.py`（ポート 8010）
- **対象外:** MDQ（Markdown 専用インデックス）、エージェント REPL

---

## 3. 背景

インジェストパイプラインは管理者が `scripts/agent.py --ingest` コマンドまたはエージェントの `/ingest` コマンドで実行する。クエリパイプラインはエージェントが各ターンで自動的に呼び出す。すべての索引は SQLite + sqlite-vec（ベクター拡張）に格納される。

---

## 4. 前提条件

1. 埋め込みサーバーがポート 8003 で起動済みであること（multilingual-E5-small 384 次元）。
2. SQLite + sqlite-vec 拡張（`/opt/llm/sqlite-vec/vec0.so`）がロード可能であること。
3. `config/rag_pipeline.toml` が設定済みであること。
4. インジェスト対象の URL または Markdown ファイルが指定されていること。

---

## 5. 制約

| 制約 | 内容 |
|---|---|
| 言語検出 | 日本語・英語のみ対応。100 文字未満のページは言語不明として除外 |
| チャンクサイズ | `min_chunk=40`〜`max_chunk=500` 文字 |
| チャンク重複 | `chunk_overlap=50` 文字のスライディングウィンドウ |
| 埋め込み次元 | 384 次元（float32 little-endian BLOB、1536 バイト） |
| クロール制限 | 最大 500 ページ、同一オリジン、深さ 6 |
| クロール遅延 | 1.5 秒/リクエスト |
| FTS5 日本語 | Sudachi（SplitMode.C）による正規化テキスト（`normalized_content`）を使用 |
| レプリカ構成 | 単一ノード（SQLite）のみ対応 |

---

## 6. 機能要件

### 6.1 インジェストパイプライン

1. **クロール（`WebCrawler`）:** BFS で URL を辿り、テキストを JSON 形式で `rag-src/` に保存
2. **チャンク分割（`ChunkSplitter`）:** 言語別・形式別に文章境界でチャンク分割し `rag-src/chunk/` に保存
3. **埋め込み生成・格納（`RagIngester`）:** 埋め込みベクターを生成し SQLite に upsert

### 6.2 クエリパイプライン

1. **MQE（Multi-Query Expansion）:** クエリを複数のバリエーションに展開（`use_mqe=true` 時）
2. **ベクター/FTS 検索:** KNN（sqlite-vec）+ BM25（FTS5）の並列検索
3. **RRF マージ:** 複数クエリ結果を `Σ 1/(60+rank)` でマージ
4. **クロスエンコーダー再ランク:** LLM によるスコアリングとフィルタリング（`use_rerank=true` 時）
5. **増補（Augment）:** 選択チャンクを `[Source: {title} | {url}]\n{content}` 形式でメッセージに付加

### 6.3 セマンティックキャッシュ（`use_semantic_cache=true` 時）
- クエリ埋め込みの類似度 ≥ `semantic_cache_threshold`（デフォルト 0.92）なら前回結果を再利用
- LRU キャッシュ（最大 `semantic_cache_max_size = 100` エントリ）

---

## 7. 入出力

### 7.1 インジェスト入力・出力

**Stage 1 入力:** URL またはローカルパス  
**Stage 1 出力:** `rag-src/yyyymmddhhmmss-{slug}.txt`（JSON）

```json
{
  "url": "https://...",
  "title": "タイトル",
  "lang": "ja",
  "fetched_at": "2026-06-06T00:00:00Z",
  "content": "本文...",
  "code_blocks": ["コードブロック1", ...],
  "etag": "...",
  "last_modified": "..."
}
```

**Stage 2 出力:** `rag-src/chunk/{stem}-{idx:04d}.txt`（JSON）

```json
{
  "url": "https://...",
  "chunk_index": 0,
  "content": "チャンク本文...",
  "normalized_content": "正規化済みテキスト（JA のみ）",
  "lang": "ja"
}
```

**Stage 3:** SQLite `documents` + `chunks` + `chunks_fts` + `chunks_vec` にアップサート

### 7.2 クエリ入出力

**入力:**
```python
RagPipeline.augment(
    query: str,
    history_context: str = "",
) -> str
```

**出力:** コンテキストブロック文字列（空文字列 = 結果なし）
```
[RAG_CONTEXT_START]
[Source: タイトル | https://...]
チャンク本文...

---

[Source: タイトル2 | https://...]
チャンク本文2...
[RAG_CONTEXT_END]
```

---

## 8. 処理フロー

### 8.1 インジェスト処理フロー

```
WebCrawler.crawl(target_urls)
  → BFS クロール（同一オリジン、max_pages=500, max_depth=6）
  → Conditional GET（ETag/Last-Modified → 304 スキップ）
  → trafilatura でメインテキスト抽出
  → BeautifulSoup でコードブロック抽出
  → langdetect で言語判定（ja/en 以外は除外）
  → rag-src/*.txt に保存

ChunkSplitter.split(source_files)
  → 日本語: NFKC + Sudachi SplitMode.C + stopword 除去 + 40-500 文字境界
  → 英語: 文境界分割 + 40-500 文字
  → Markdown: heading 境界（md_index_enable=true 時）
  → chunk_overlap=50 文字のオーバーラップ
  → rag-src/chunk/*.txt に保存

RagIngester.ingest(chunk_files)
  → "passage: {content}" を埋め込みサーバー（:8003）に送信
  → ThreadPoolExecutor(embed_workers=4) で並列埋め込み生成
  → struct.pack("<384f", ...) で BLOB 変換
  → documents + chunks + chunks_fts + chunks_vec にアップサート（ETag 同一は SKIP）
```

### 8.2 クエリ処理フロー

```
RagPipeline.augment(query)
  → use_search=false の場合は "" を返す
  → rag_service_url 設定時は外部 RAG サービスに委譲
  → run(query, db, history_context)
      [1] MQE: RagLLM.expand_queries(query, context)
          → use_mqe=false: [query] のみ
      [2] 検索: search_queries(queries, db)
          → 各クエリで並列: get_embedding(:8003) + KNN + FTS
          → all_results: list[list[RagHit]]
      [3] RRF マージ: RagScorer.rrf_merge(all_results)
          → use_rrf=false: _dedup_hits() で単純重複除去
      [4] リランク: rerank_candidates(query, merged)
          → use_rerank=false: merged をそのまま使用
          → rag_min_score でフィルタリング
      [5] dedup: deduplicate_chunks(reranked, max_chunks_per_doc=2)
  → use_refiner=true の場合: _augment_refiner(reranked, query) でチャンク圧縮
  → _format_chunks(reranked): [RAG_CONTEXT_START]...[RAG_CONTEXT_END] フォーマット
```

---

## 9. データ仕様

### 9.1 RAG DB スキーマ（rag.sqlite）

**documents テーブル:**

| カラム | 型 | 説明 |
|---|---|---|
| `doc_id` | INTEGER PK | 自動採番 |
| `url` | TEXT UNIQUE | ドキュメント URL |
| `title` | TEXT | ページタイトル |
| `lang` | TEXT | 言語コード（`ja`/`en`） |
| `fetched_at` | TEXT | 取得日時（ISO-8601） |
| `etag` | TEXT | HTTP ETag |
| `last_modified` | TEXT | HTTP Last-Modified |

**chunks テーブル:**

| カラム | 型 | 説明 |
|---|---|---|
| `chunk_id` | INTEGER PK | 自動採番 |
| `doc_id` | INTEGER FK | documents 参照 |
| `chunk_index` | INTEGER | ドキュメント内インデックス |
| `content` | TEXT | 原文（LLM コンテキスト注入用） |
| `normalized_content` | TEXT | Sudachi 正規化テキスト（JA FTS 用） |

**chunks_fts（FTS5 バーチャルテーブル）:**
- `COALESCE(normalized_content, content)` を全文検索対象

**chunks_vec（sqlite-vec バーチャルテーブル）:**
- `embedding float[384]` — KNN 検索対象

### 9.2 RagHit TypedDict フィールド

| フィールド | 型 | 付与ステージ |
|---|---|---|
| `chunk_id` | int | 検索 |
| `content` | str | 検索 |
| `url` | str | 検索 |
| `title` | str | 検索 |
| `distance` | float | KNN 検索時のみ |
| `bm25_score` | float | FTS 検索時のみ |
| `rrf_score` | float | RRF マージ後 |
| `rerank_score` | float | リランク後 |

### 9.3 主要設定パラメータ

| パラメータ | デフォルト | 説明 |
|---|---|---|
| `top_k_search` | 20 | ベクター/FTS 検索結果数 |
| `top_k_rerank` | 15 | リランク候補数 |
| `rag_top_k` | 5 | 最終 LLM コンテキスト注入数 |
| `max_chunks_per_doc` | 2 | ドキュメントあたりの上限チャンク数 |
| `rag_min_score` | 0.0 | リランクスコアフィルター |
| `use_mqe` | True | MQE 有効フラグ |
| `use_rrf` | True | RRF マージ有効フラグ |
| `use_rerank` | True | クロスエンコーダーリランク有効フラグ |
| `embed_url` | `http://127.0.0.1:8003/embedding` | 埋め込みサーバー URL |
| `embed_workers` | 4 | 並列埋め込み生成スレッド数 |

---

## 10. 公開インターフェース仕様

### 10.1 RagPipeline（rag/pipeline.py）

```python
class RagPipeline:
    async def run(
        query: str,
        db: SQLiteHelper,
        history_context: str = "",
    ) -> tuple[list[str], list[list[RagHit]], list[RagHit], list[RagHit]]
    # 戻り値: (queries, all_results, merged, reranked)

    async def augment(
        query: str,
        debug_fn=None,
        history_context: str = "",
    ) -> str
    # 戻り値: コンテキストブロック（空文字列 = 検索無効または結果なし）
```

### 10.2 WebCrawler（rag/ingestion/crawler.py）

```python
class WebCrawler:
    async def crawl(targets: list[tuple[str, str]] | None = None) -> None
    # targets: [(url_or_path, hint_lang), ...] — None の場合は config から読み込み
    async def crawl_site(start_url: str, hint_lang: str) -> None
    def crawl_file(path: Path, lang: str) -> int
    # 戻り値: 取り込んだページ数（crawl_file）
```

### 10.3 ChunkSplitter（rag/ingestion/chunk_splitter.py）

```python
class ChunkSplitter:
    def process_all(target: Path | None = None, force: bool = False) -> int
    # 戻り値: 生成されたチャンク数
    def process_file(src_path: Path, force: bool = False) -> int
```

### 10.4 RagIngester（rag/ingestion/ingester.py）

```python
class RagIngester:
    def ingest_all(force: bool = False) -> None
    def ingest_url_group(url_group: str, force: bool = False) -> None
```

### 10.5 PipelineStage（rag/stage.py）

```python
class PipelineStage(Protocol):
    async def run(ctx: PipelineContext) -> PipelineContext
# 実装クラス: SearchStage, MqeStage, FusionStage, RerankStage, AugmentStage（rag/stages/）
```

---

## 11. エラーハンドリング

| エラー種別 | 対応 |
|---|---|
| 埋め込みサーバー接続エラー | `embed_retry` 回（デフォルト 3）リトライ後に例外を送出 |
| DB オープンエラー | `logger.warning()` を出力して `augment()` が `""` を返す |
| クロール HTTP エラー | ページをスキップして次の URL に進む |
| 言語判定エラー | `langdetect` 例外時はページをスキップ |
| セマンティックキャッシュ | `use_semantic_cache=false` の場合は常にキャッシュバイパス |

---

## 12. 検証計画

| 検証項目 | ツール | 合格基準 |
|---|---|---|
| ユニットテスト | `uv run pytest tests/test_rag_pipeline.py tests/test_rag_utils.py` | 全パス |
| 型チェック | `uv run mypy scripts/rag/` | 新規エラーなし |
| セキュリティ | `uv run bandit -r scripts/rag/` | HIGH 未対応なし |
| 統合テスト | `/ingest <url>` → `/rag search <q>` | ヒット返却を確認 |
| FTS 日本語 | 正規化クエリで日本語チャンクがヒット | ヒット確認 |

---

## 13. 未解決事項・既知問題

| 項目 | 詳細 |
|---|---|
| Prompt Injection 防御 | RAG ドキュメントのサニタイゼーションおよび `[RAG_CONTEXT_START/END]` 境界マーカーが未実装 (`implementations/20260606-195251_rag_sanitize.md` 参照) |
| 外部 RAG サービス | `rag_service_url` 設定時の外部委譲は実装済みだが、認証・エラー処理の仕様が未定義 |
| MDQ との分離 | Markdown 専用インデックス（`mdq-mcp`）との責務分担が `04_mcp-mdq.md` に記載されているが、移行基準が未定義 |
