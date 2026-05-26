# 取込パイプライン — chunk_splitter.py API リファレンス

実行ガイド → [`03_ingestion-run.md`](03_ingestion-run.md)  
共通実装注意事項 → [`03_ref-ingestion.md`](03_ref-ingestion.md)

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
