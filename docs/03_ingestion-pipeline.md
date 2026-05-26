# 取込パイプライン

## 1. ドキュメント収集・投入

取込は `web_crawler.py` → `chunk_splitter.py` → `rag_ingester.py` の 3 ステップで実行する。
事前に `deploy/deploy.sh` でスクリプトが配置済みであること。

### 1.1 前提条件

- `deploy/deploy.sh` が実行済み (スクリプト・設定ファイルが `/opt/llm/scripts/` に配置済み)
- `embed-llm` サービスが起動済み (`curl -s http://127.0.0.1:8003/health` で確認)

### 1.2 実行手順

```bash
source /opt/llm/venv/bin/activate

# ── ステップ 1: クロール ──────────────────────────────────────────────────────
# 全 TARGET_URLS のクロール (N100 では長時間: nohup 推奨)
nohup python /opt/llm/scripts/web_crawler.py > /opt/llm/logs/crawl.log 2>&1 &

tail -f /opt/llm/logs/crawl.log

# 単一 URL のクロール
python /opt/llm/scripts/web_crawler.py --url "https://ziglang.org/documentation/master/" --lang en

# 複数 URL のクロール (同一 --lang が全 URL に適用される)
python /opt/llm/scripts/web_crawler.py \
    --url "https://ziglang.org/documentation/master/" \
          "https://zig.guide/" \
    --lang en

# ── ステップ 2: チャンク分割 ─────────────────────────────────────────────────
python /opt/llm/scripts/chunk_splitter.py

# 特定ファイルのみ処理
python /opt/llm/scripts/chunk_splitter.py --file /opt/llm/rag-src/20240101120000-ziglang.txt

# 既存チャンクを再生成する場合 (--force)
python /opt/llm/scripts/chunk_splitter.py --force

# ── ステップ 3: 埋込生成・DB 投入 ────────────────────────────────────────────
# embed-llm が起動していることを確認
curl -s http://127.0.0.1:8003/health

python /opt/llm/scripts/rag_ingester.py

# 強制再登録 (既登録 URL を最新コンテンツで上書き)
python /opt/llm/scripts/rag_ingester.py --force
```

### 1.3 ファイルライフサイクル

| パス | 生成元 | フォーマット |
|---|---|---|
| `rag-src/yyyymmddhhmmss-{slug}.txt` | `web_crawler.py` | JSON: `{url, title, lang, fetched_at, content, code_blocks: [...]}` |
| `rag-src/chunk/{stem}-{idx:04d}.txt` | `chunk_splitter.py` | JSON: `{url, title, lang, source_file, chunk_index, chunk_type, content, normalized_content}` |
| `rag-src/registered/{stem}-{idx:04d}.txt` | `rag_ingester.py` が移動 | 上記と同一 (処理済みを示す) |

拡張子は `.txt` でも中身は JSON。

---

## 2. web_crawler.py

### 2.1 クラス概要

`WebCrawler` クラス。指定 URL を起点に同一オリジン内を BFS (幅優先探索: Breadth-First Search) でクロールし、各ページのテキストとコードブロックを JSON 形式で `/opt/llm/rag-src/` に保存する。ファイル名は `yyyymmddhhmmss-{slug}.txt` (slug は URL パスを英数字ハイフンに変換したもの)。`--url` 未指定の場合は `config/rag_pipeline.json` の `target_urls` を使用する。

**公開メソッド**

| メソッド | シグネチャ | 説明 |
|---|---|---|
| `__init__` | `(config: dict \| None = None)` | `rag_pipeline.json` を読み込みインスタンスを初期化する。`config` を渡すとファイル読み込みをスキップする (テスト用) |
| `crawl` | `async (targets: list[tuple[str, str]] \| None = None) -> None` | 全ターゲットをクロールする。`targets` が `None` の場合は設定ファイルの `target_urls` を使用する |
| `crawl_site` | `async (start_url: str, hint_lang: str) -> None` | 単一の起点 URL から非同期 BFS クロールを実行する |
| `crawl_file` | `(path: Path, lang: str) -> int` | ローカルファイルをクロール結果 JSON として `rag-src/` に保存する。`.py` はコードブロックとして格納する。成功時 1、失敗時 0 を返す |

**モジュールレベルユーティリティ関数** (純粋関数、他モジュールから import 可)

| 関数 | 説明 |
|---|---|
| `url_to_slug(url)` | URL をファイルシステム安全な ASCII スラッグに変換する (最大 80 文字) |
| `normalize_url(url)` | フラグメント除去・末尾スラッシュ除去で URL を正規化する |
| `same_origin(url, base)` | scheme + hostname が一致するか判定する |

### 2.2 機能概要

指定 URL を起点に同一オリジン内を BFS で巡回し、各ページのテキストとコードブロックを JSON ファイルとして `rag-src/` に保存。

- テキスト抽出: `trafilatura` で本文テキストを、`BeautifulSoup4` で `<pre>` コードブロックを別途抽出
- 言語検出: CJK 文字比率 (ひらがな + カタカナ + CJK統合漢字 が 10% 以上なら `ja`) でページ言語を自動判定。100 文字未満のページはヒント言語 (`--lang`) を使用。`--lang auto` またはヒント言語 `"auto"` を指定した場合は常に自動判定し、判定不能時は `en` にフォールバック
- 冪等性: クロール済み URL を `visited` セットで管理し、同一 URL を 2 回以上取得しない
- 出力: `rag-src/yyyymmddhhmmss-{slug}.txt` (JSON 形式; `url`, `title`, `lang`, `fetched_at`, `content`, `code_blocks` フィールド)

### 2.3 実装方式

| 機能 | 実装 |
|---|---|
| HTTP クライアント | `httpx.AsyncClient` (非同期) + 指数バックオフリトライ (`asyncio.sleep`) |
| HTML 解析 | `BeautifulSoup4` (lxml) でタイトル・`<pre>` コードブロック抽出、`trafilatura` で本文テキスト抽出 |
| 並列 BFS クロール | `asyncio.Queue` + `asyncio.Semaphore(crawl_concurrency)` で同時リクエスト数を制御。`asyncio.wait(FIRST_COMPLETED)` でタスク完了駆動 |
| URL 正規化 | `normalize_url()` でフラグメント除去・トレイリングスラッシュ除去して重複チェック |
| 言語検出 | CJK 文字比率で自動判定 (`_detect_lang`)。ヒント言語が `"auto"` のとき `_resolve_lang` は常に自動判定し、短文や判定不能は `en` にフォールバック。`skip_nofollow` / `skip_external` で BFS リンク追加時のフィルタを設定可能 |
| クロール間隔 | `crawl_delay` をセマフォ取得後の `asyncio.sleep()` に適用してサーバ負荷を制御する |
| 条件付き GET | `_get_conditional_headers()` が SQLite の `documents` テーブルから ETag / Last-Modified を取得し `If-None-Match` / `If-Modified-Since` ヘッダを付与する。サーバが 304 を返した場合はファイル保存をスキップする |
| ローカルファイル | `crawl_file()` が `file://{path}` URL で JSON を生成し `rag-src/` に保存する。BFS クロールは行わない |

### 2.4 入出力インタフェース

**CLI 引数**

| 引数 | 説明 | デフォルト |
|---|---|---|
| `--url URL [URL ...]` | クロール対象 URL (省略時は `config/rag_pipeline.json` の `target_urls`) | なし |
| `--lang {en,ja,auto}` | ヒント言語 (既定: `en`)。`auto` を指定するとページ本文の CJK 文字比率で言語を自動判定する | `en` |

**出力 JSON フォーマット** (`/opt/llm/rag-src/yyyymmddhhmmss-{slug}.txt`)

```json
{
  "url": "https://example.com/page",
  "title": "ページタイトル",
  "lang": "ja",
  "fetched_at": "2024-01-01T12:00:00",
  "content": "本文テキスト",
  "code_blocks": ["コードブロック1", "コードブロック2"]
}
```

### 2.5 エラーハンドリング

| ケース | 対処 |
|---|---|
| HTTP リクエスト失敗 | `fetch_retry` 回まで指数バックオフ (`min(2 ** i, 10)` 秒、最終試行後はスリープなし) でリトライ |
| URL 単位の例外 | `WARNING` ログを出力して次 URL に継続 (1 URL の失敗でクロール全体は止まらない) |
| テキスト 100 文字未満 | ヒント言語が `"auto"` の場合は `en` にフォールバック。それ以外は `--lang` 引数のヒント言語を使用する |
| 言語検出結果が `ja`/`en` 以外 | 対応外言語としてその URL をスキップし次 URL に継続する |

### 2.6 ログ出力

- **ファイル:** `/opt/llm/logs/crawl.log` + 標準エラー出力
- **フォーマット:** `%(asctime)s %(levelname)s [%(funcName)s] %(message)s`

| レベル | タイミング |
|---|---|
| `INFO` | クロール開始、URL 保存完了 (件数)、スキップ URL |
| `WARNING` | HTTP エラー、リトライ発生 |

### 2.7 設定項目

すべて `config/rag_pipeline.json` に記載。

| パラメータ | デフォルト | 説明 |
|---|---|---|
| `rag_src_dir` | `/opt/llm/rag-src` | クロール済みファイルの出力ディレクトリ |
| `crawl_delay` | `1.5` | リクエスト間の待機時間 (秒)。最低 1.0 秒以上を推奨 |
| `max_depth` | `6` | BFS クロールの最大深度 (起点 URL からのホップ数上限) |
| `fetch_retry` | `3` | HTTP フェッチ失敗時の指数バックオフリトライ上限回数 |
| `fetch_timeout` | `15` | 1 リクエストあたりの HTTP タイムアウト秒数。`Crawler._fetch_timeout` に設定される |
| `crawl_concurrency` | `3` | 並列 BFS クロールの同時リクエスト数上限。`asyncio.Semaphore` の許可数として使用する |
| `max_pages` | `500` | 1 サイトあたりのクロール最大ページ数上限。`visited` セットがこの値に達したとき BFS を中断する |
| `skip_nofollow` | `false` | `true` のとき `rel="nofollow"` 属性付きリンクを BFS キューに追加しない |
| `skip_external` | `true` | `true` のとき同一オリジン外リンクを BFS キューに追加しない (デフォルトは既存動作と同じ) |
| `target_urls` | — | クロール対象の URL と言語のペアリスト `[[url, lang], ...]`。lang は `"ja"` / `"en"` / `"auto"`。`--url` 未指定時に使用する |

---

## 3. chunk_splitter.py

### 3.1 クラス概要

`ChunkSplitter` クラス。`/opt/llm/rag-src/*.txt` のクロール済みファイルを読み込み、言語とコンテンツ種別 (テキスト / コード) に応じてチャンクに分割する。チャンクは `/opt/llm/rag-src/chunk/{stem}-{idx:04d}.txt` に JSON 形式で保存する。冪等性を持ち、`{stem}-0000.txt` が既存の場合はスキップする (`--force` で上書き)。`md_index_enable=true` のとき、URL が `.md`/`.markdown`/`.mdx` で終わるか本文に Markdown 見出しが 2 行以上存在する場合は見出し境界でスニペット分割を行う。エージェントの `/ingest --snippets-only` は `md_index_enable` を一時的に `true` にオーバーライドして強制適用する。

**公開メソッド**

| メソッド | シグネチャ | 説明 |
|---|---|---|
| `__init__` | `(config: dict \| None = None)` | `rag_pipeline.json` を読み込みインスタンスを初期化する。Sudachi 辞書 (`core`) と `SplitMode.C` トークナイザも起動時に初期化する |
| `process_all` | `(target: Path \| None = None, force: bool = False) -> int` | `rag-src/*.txt` をすべて処理する。`target` を指定すると単一ファイルのみ処理する。戻り値は書き込んだ総チャンク数 |
| `process_file` | `(src_path: Path, force: bool = False) -> int` | 単一 JSON ファイルを読み込んでチャンク分割し書き出す。戻り値は書き込んだチャンク数 |

### 3.2 機能概要

`rag-src/*.txt` (web_crawler.py の出力) を読み込み、言語とコンテンツ種別に応じた戦略でチャンクに分割して `rag-src/chunk/` に保存。

- 日本語テキスト: Sudachi SplitMode.C で形態素解析し、各文について `(原文, normalized_form() スペース結合)` のペアを生成。`content` に原文、`normalized_content` に正規化形を格納し、FTS5 は正規化形でインデックスしつつ LLM には原文を提供
- 英語テキスト: 正規表現 (`(?<=[.!?])\s+`) でセンテンス分割
- Markdown テキスト: `md_index_enable=true` かつ URL が `.md`/`.markdown`/`.mdx` で終わるか見出し行 2 行以上存在する場合、`#`/`##`/`###` 境界でスニペット分割 (`chunk_type="text"`)。セクションが `md_snippet_max_chars` を超える場合は英語チャンク分割にフォールバック
- コードブロック: 空行区切りでチャンク化 (言語非依存)
- 冪等性: `{stem}-0000.txt` が既存の場合はスキップ (`--force` で上書き)
- 出力: `rag-src/chunk/{stem}-{idx:04d}.txt` (JSON 形式; `chunk_type`: `"text"` / `"code"`)

### 3.3 実装方式

| 種別 | 実装 |
|---|---|
| 日本語テキスト | Sudachi (`SplitMode.C`) で形態素解析し `(原文文, normalized_form スペース結合)` ペアを生成。`content` = 原文, `normalized_content` = 正規化形 |
| 英語テキスト | 正規表現 (`(?<=[.!?])\s+`) でセンテンス分割 |
| Markdown テキスト | `_is_markdown_source()` で判定 (.md 拡張子 or 見出し 2 行以上)。`_chunk_markdown_by_heading()` で見出し境界分割し、超過分は `_chunk_english()` にフォールバック |
| コードブロック | 空行区切りでチャンク化 |

チャンク種別は `chunk_type` フィールド (`"text"` / `"code"`) で区別する。

### 3.4 入出力インタフェース

**CLI 引数**

| 引数 | 説明 | デフォルト |
|---|---|---|
| `--file PATH` | 特定ファイルのみ処理 (省略時はすべての未処理 `.txt` ファイル) | 全ファイル |
| `--force` | 既存チャンクを削除して再生成 | false |

**入力:** `/opt/llm/rag-src/*.txt` (web_crawler.py の出力 JSON)

**出力 JSON フォーマット** (`/opt/llm/rag-src/chunk/{stem}-{idx:04d}.txt`)

```json
{
  "url": "https://example.com/page",
  "title": "ページタイトル",
  "lang": "ja",
  "source_file": "20240101120000-example.txt",
  "chunk_index": 0,
  "chunk_type": "text",
  "content": "チャンクテキスト (原文)",
  "normalized_content": "正規化 形 (日本語のみ; 英語・コードは null)"
}
```

### 3.5 エラーハンドリング

| ケース | 対処 |
|---|---|
| Sudachi トークナイズエラー | 例外キャッチして空文字列 `""` を返す (そのチャンクはスキップ) |
| ファイル単位の処理失敗 | `ERROR` ログ (スタックトレースあり) を出力して次ファイルに継続 |
| 既存チャンク (`{stem}-0000.txt` 存在) | `--force` 未指定の場合はスキップ (再実行安全) |

### 3.6 ログ出力

- **ファイル:** `/opt/llm/logs/chunk.log` + 標準エラー出力
- **フォーマット:** `%(asctime)s %(levelname)s [%(funcName)s] %(message)s`

| レベル | タイミング |
|---|---|
| `INFO` | 処理ファイル数、生成チャンク数、スキップ件数 |
| `WARNING` | Sudachi エラー |
| `ERROR` | ファイル読み込みエラー、ファイル単位の処理失敗 (スタックトレースあり) |

### 3.7 設定項目

すべて `config/rag_pipeline.json` に記載。

| パラメータ | デフォルト | 説明 |
|---|---|---|
| `rag_src_dir` | `/opt/llm/rag-src` | 入力ファイルのディレクトリ (`{rag_src_dir}/*.txt`) およびチャンク出力先 (`{rag_src_dir}/chunk/`) |
| `min_chunk` | `40` | チャンクの最小文字数。これ未満のチャンクはノイズとして破棄する |
| `max_chunk` | `500` | チャンクの最大文字数。コンテキスト長を圧迫しないよう分割する |
| `en_stopwords` | (リスト) | 英語ストップワードリスト。チャンク分割後のトークンから除外する機能語 |
| `ja_stop_pos` | `["助詞","助動詞",...]` | 日本語ストップワード対象の大品詞区分。Sudachi の品詞タグで判定する |
| `chunk_overlap` | `50` | 前チャンク末尾の文字列を次チャンク先頭に付加するオーバーラップ文字数。検索境界をまたいだコンテキストの喪失を緩和する。0 を指定すると無効 |
| `md_index_enable` | `false` | `true` のとき、Markdown 見出し境界でスニペット分割を有効化する。エージェントの `/ingest --snippets-only` はランタイムで一時的に `true` に上書きする |
| `md_snippet_max_chars` | `600` | Markdown 見出し単位スニペットの最大文字数。超過した場合は `_chunk_english()` でさらに分割する |

---

## 4. rag_ingester.py

### 4.1 クラス概要

`RagIngester` クラス。`/opt/llm/rag-src/chunk/*.txt` のチャンクファイルを読み込み、`embed-llm` サービス (multilingual-E5-small, ポート 8003) で埋込ベクトルを生成して SQLite の 4 テーブル (`documents` / `chunks` / `chunks_vec` / `chunks_fts`) に登録する。処理済みチャンクファイルは `/opt/llm/rag-src/registered/` に移動する。

**公開メソッド**

| メソッド | シグネチャ | 説明 |
|---|---|---|
| `__init__` | `(config: dict \| None = None)` | `common.json` と `rag_pipeline.json` をマージして読み込みインスタンスを初期化する。`requests.Session` も生成する |
| `ingest_all` | `(force: bool = False) -> None` | `chunk_dir` の全チャンクファイルを URL 単位でグループ化して投入する |
| `ingest_url_group` | `(db: SQLiteHelper, url: str, chunk_files: list[Path], force: bool) -> None` | 1 URL 分のチャンクファイル群を SQLite に投入し、処理後ファイルを `registered/` に移動する |

### 4.2 機能概要

`rag-src/chunk/*.txt` のチャンクファイルを URL 単位でグループ化し、`embed-llm` API でベクトルを生成して SQLite の 4 テーブルに登録。登録済みファイルは `rag-src/registered/` に移動。

- E5 プレフィックス: 埋込 API リクエスト時に `passage: {text}` を付与 (クエリ時の `query: ` と区別)
- ベクトル格納: `struct.pack("<{N}f", ...)` で little-endian float32 BLOB に変換して `chunks_vec` に INSERT
- upsert: `--force` 指定時は `chunks_vec` → `chunks` → `documents` の順に削除してから再登録
- 冪等性: `--force` 未指定の場合、`documents.url` が既登録の URL はスキップ
- ETag/Last-Modified 更新: `--force` 未指定でスキップした場合でも、チャンクファイルから読み取った `etag` / `last_modified` を `documents` テーブルに UPDATE し、次回 Crawler の条件付き GET で使用可能
- ローカルファイル対応: `file://` スキームの URL をチャンクグループとして受け付け

### 4.3 実装方式

| 機能 | 実装 |
|---|---|
| 埋込 API 呼び出し | `requests.Session()` で `POST http://127.0.0.1:8003/embedding` を呼び出す |
| E5 モデルプレフィックス | 取込時は `passage: {text}` を付与 (クエリ時は `query: {text}`) |
| ベクトル格納 | `struct.pack(f"<{N}f", *values)` でリトルエンディアン float32 BLOB に変換 (sqlite-vec の `MATCH` 演算子要件) |
| 埋込並列化 | `_ingest_chunk_files()` が `ThreadPoolExecutor(embed_workers)` でチャンクを並列投入する。ドキュメントレコードを `db.commit()` してから並列開始し、各スレッドは独立した `SQLiteHelper().open()` を使用する |
| WAL モード | `PRAGMA journal_mode=WAL` を設定し並行読み書きを安全に処理 |
| upsert | `--force` 指定時は `chunks_vec` → `chunks` → `documents` の順に削除してから再登録 |
| ETag/Last-Modified 保存 | チャンクファイルの `etag` / `last_modified` フィールドを `documents` テーブルに保存する。スキップ時も UPDATE して最新値を維持する |

### 4.4 入出力インタフェース

**CLI 引数**

| 引数 | 説明 | デフォルト |
|---|---|---|
| `--force` | 既登録 URL のレコードを削除して最新コンテンツで再登録 | false |

**埋込 API**

```
POST http://127.0.0.1:8003/embedding
リクエスト : {"content": "passage: {テキスト}"}
レスポンス : {"embedding": [float, ...]}  # 384 次元 (llama.cpp レガシーエンドポイント)
```

**DB 更新テーブル**

| テーブル | 操作 |
|---|---|
| `documents` | `SELECT` で既登録を確認 → `force=False` のときスキップ、`force=True` のとき削除して `INSERT` |
| `chunks` | `doc_id` FK (ON DELETE CASCADE) → `INSERT` でチャンクを登録 |
| `chunks_vec` | `chunk_id` PK → `INSERT` でベクトル BLOB を登録 |
| `chunks_fts` | `chunks_ai` トリガが `COALESCE(normalized_content, content)` を自動 INSERT。日本語は正規化形、英語・コードは原文でインデックス |

### 4.5 エラーハンドリング

| ケース | 対処 |
|---|---|
| 埋込 API 失敗 | `embed_retry` 回まで指数バックオフでリトライ |
| チャンク単位の埋込失敗 (リトライ全失敗) | `WARNING` ログを出力してそのチャンクをスキップし次チャンクに継続 |
| `chunks_vec` 削除順序 | `chunks_vec` → `chunks` → `documents` の順で削除 (`chunks_vec` は sqlite-vec 仮想テーブルのため外部キー制約なし、先行削除しないと孤立レコードが残る) |
| `lang` 不正値 (`ja`/`en` 以外) | `_get_or_create_document` が `ValueError` を送出し、該当 URL グループをスキップする (`ERROR` ログ; スタックトレースあり) |

### 4.6 ログ出力

- **ファイル:** `/opt/llm/logs/ingest.log` + 標準エラー出力
- **フォーマット:** `%(asctime)s %(levelname)s [%(funcName)s] %(message)s`

| レベル | タイミング |
|---|---|
| `INFO` | 処理チャンク数、DB 登録件数、ファイル移動完了 |
| `WARNING` | 埋込 API エラー、リトライ発生、埋込スキップ |
| `ERROR` | チャンクファイル読み込みエラー、ファイル移動エラー、URL グループ処理失敗 (スタックトレースあり) |

### 4.7 設定項目

`config/common.json` と `config/rag_pipeline.json` を参照する。

| パラメータ | 設定ファイル | デフォルト | 説明 |
|---|---|---|---|
| `embed_url` | `config/common.json` | `http://127.0.0.1:8003/embedding` | 埋込 API のエンドポイント (llama.cpp レガシー形式) |
| `db_path` | `config/common.json` | `/opt/llm/db/rag.sqlite` | SQLite データベースのパス |
| `sqlite_vec_so` | `config/common.json` | `/opt/llm/sqlite-vec/vec0.so` | sqlite-vec 拡張 (.so) のパス |
| `rag_src_dir` | `config/rag_pipeline.json` | `/opt/llm/rag-src` | チャンクファイル入力ディレクトリ (`{rag_src_dir}/chunk/*.txt`) および登録済みファイル移動先 (`{rag_src_dir}/registered/`) |
| `embed_retry` | `config/rag_pipeline.json` | `3` | 埋込 API 失敗時の指数バックオフリトライ上限回数 |
| `embed_workers` | `config/rag_pipeline.json` | `4` | 埋込並列実行数。`ThreadPoolExecutor(embed_workers)` でチャンクを並列投入する |

---

## 5. 実装注意事項

取込パイプライン全体にわたる実装上の注意点をまとめる。

### 5.1 パイプラインデータフロー

```
config/rag_pipeline.json の target_urls
  → web_crawler.py:    BFS クロール (同一オリジン) → rag-src/yyyymmddhhmmss-{slug}.txt
  → chunk_splitter.py: チャンク分割
                       JA: Sudachi / EN: sentence split / code: 空行区切り
                       → rag-src/chunk/{stem}-{idx:04d}.txt
  → rag_ingester.py:   embed (passage: prefix) → SQLite INSERT → rag-src/registered/
```

### 5.2 FTS5 クエリ Sudachi フィルタ

`agent_rag._build_fts_query()` は日本語クエリを `_build_fts_tokens_ja()` で処理し、名詞・動詞・形容詞の `normalized_form()` のみを FTS5 トークンとして使用する。`chunks_fts` は `normalized_content` (正規化形スペース結合) でインデックスされているため、クエリも同じ正規化形で照合する必要がある。Sudachi は `_get_sudachi_tokenizer()` で遅延初期化 (import 時の副作用ゼロ)。英語クエリは regex トークン化のまま。

### 5.3 FTS5 / LLM コンテンツ分離

日本語チャンクは `chunks.content` に原文、`chunks.normalized_content` に Sudachi normalized_form スペース結合形を格納する。FTS5 の `chunks_ai` / `chunks_au` / `chunks_ad` トリガが `COALESCE(normalized_content, content)` を `chunks_fts` に書き込む。LLM には `chunks.content` (原文) が渡り、BM25 検索は `normalized_content` でマッチする。英語・コードは `normalized_content = NULL` のため FTS5 は `content` をそのまま使用する。
