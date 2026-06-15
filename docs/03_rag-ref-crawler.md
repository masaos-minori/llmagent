# 取込パイプライン — web_crawler.py API リファレンス

実行ガイド → [`03_rag-ingestion-run.md`](03_rag-ingestion-run.md)  
共通実装注意事項 → [`03_rag-ref-ingestion.md`](03_rag-ref-ingestion.md)

## 2. web_crawler.py

### 2.1 クラス概要

`WebCrawler` クラス。指定 URL を起点に同一オリジン内を BFS (幅優先探索: Breadth-First Search) でクロールし、各ページのテキストとコードブロックを JSON 形式で `rag-src/` に保存する。ファイル名は `yyyymmddhhmmss-{slug}.txt` (slug は URL パスを英数字ハイフンに変換したもの)。`--url` 未指定の場合は `config/rag_pipeline.toml` の `target_urls` を使用する。

**公開メソッド**

| メソッド | シグネチャ | 説明 |
|---|---|---|
| `__init__` | `(config: dict \| None = None)` | `rag_pipeline.toml` を読み込みインスタンスを初期化する。`config` を渡すとファイル読み込みをスキップする (テスト用) |
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

- テキスト抽出: `crawler_utils.extract_text()` で本文テキストを、`BeautifulSoup4` で `<pre>` コードブロックを別途抽出
- 言語検出: CJK 文字比率 (ひらがな + カタカナ + CJK統合漢字 が 10% 以上なら `ja`) でページ言語を自動判定。100 文字未満のページはヒント言語 (`--lang`) を使用。`--lang auto` またはヒント言語 `"auto"` を指定した場合は常に自動判定し、判定不能時は `en` にフォールバック
- 冪等性: クロール済み URL を `visited` セットで管理し、同一 URL を 2 回以上取得しない
- 出力: `rag-src/yyyymmddhhmmss-{slug}.txt` (JSON 形式; `url`, `title`, `lang`, `fetched_at`, `content`, `code_blocks` フィールド)

### 2.3 実装方式

| 機能 | 実装 |
|---|---|
| HTTP クライアント | `httpx.AsyncClient` (非同期) + 指数バックオフリトライ (`asyncio.sleep`) |
| HTML 解析 | `BeautifulSoup4` (lxml) でタイトル・`<pre>` コードブロック抽出、`crawler_utils.extract_text()` で本文テキスト抽出 |
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
| `--url URL [URL ...]` | クロール対象 URL (省略時は `config/rag_pipeline.toml` の `target_urls`) | なし |
| `--lang {en,ja,auto}` | ヒント言語 (既定: `en`)。`auto` を指定するとページ本文の CJK 文字比率で言語を自動判定する | `en` |

**出力 JSON フォーマット** (`rag-src/yyyymmddhhmmss-{slug}.txt`)

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

すべて `config/rag_pipeline.toml` に記載。

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
