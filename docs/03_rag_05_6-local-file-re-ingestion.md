---
title: "6. Local file re-ingestion"
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

# 6. ローカルファイルの再取り込み

## 初回取り込み

`config/crawler.toml`の`target_urls`に、スキーム`file://`でファイルパスを追加する
(`--targets-file`で別ファイルを指定する場合も同じ`target_urls = [[url, lang], ...]`形式)。

```toml
[[target_urls]]
url = "file:///path/to/file.py"
lang = "en"
```

その後、以下を実行する。

``` python
uv run python scripts/rag/ingestion/crawler.py --targets-file /path/to/targets.toml
```

クローラーは`crawl()`内で`url.startswith("file://")`を判定して`crawl_file()`を呼び出し、
JSONを`rag-src/`に書き込む (`scripts/rag/ingestion/crawler.py:crawl_file()`)。
その後`chunk_splitter.py`がチャンク分割を行い、`ingester.py`がSQLiteベクトルストアに埋め込む
(`crawler.py`自体はチャンク分割・埋め込みを行わない。3スクリプトは個別に実行する別プロセスである)。

**実装上の補足 (Strongly implied by code):**
- `.py`拡張子のファイルは`content`ではなく`code_blocks`に格納され、コード用チャンカー
  (`chunk_english.py`側のコードパス) が適用される。
- `crawl_file()`が`documents.etag`に書き込む値は、HTTPのETagではなくファイル内容の
  SHA-256ハッシュそのものである。`last_modified`にはファイルの`mtime` (ISO8601) を格納する。
  Web URLの場合と同じカラムを再利用しているため、カラム名から実体が本物のHTTP ETagだと
  誤解しないよう注意する。

## ファイル変更後の再取り込み

ingesterは、現在のファイル内容のSHA-256ハッシュを`documents`に保存されている
`etag`と比較する。

- **変更なし** (ハッシュが一致): 自動的にスキップされ、再取り込みは行われない。
- **変更あり** (ハッシュが異なる): 自動的に再取り込みされる — 旧ドキュメントとチャンクを削除し、再チャンク分割、再埋め込みを行う。
- **`--force`**: ハッシュに関わらず削除して再取り込みする。

取り込み中のログメッセージ:

- `"file:// unchanged (sha256 match): file:///path/to/file"` — スキップされた
- `"file:// changed — auto re-ingesting: file:///path/to/file"` — 再取り込みされた

## 多数のローカルファイルの一括再取り込み

複数のファイルが変更された場合は、`--targets-file`を指定してクローラーを実行し、
リストされた`file://` URLをすべて再クロールする。
クローラーは`--force`をサポートしない。未変更のファイルはSHA-256ハッシュ比較により自動的にスキップされる。
すでに取り込み済みのURLの埋め込みを強制的に再実行するには、クロール後に`ingester.py --force`を実行する。

``` python
uv run python scripts/rag/ingestion/crawler.py --targets-file /path/to/targets.toml
uv run python scripts/rag/ingestion/ingester.py --force
```

## 比較: ローカルファイル vs. Web URL

| Aspect | Web URL | ローカルファイル (file://) |
|---|---|---|
| 未変更時のスキップ | あり (ETag/304) | あり (SHA-256ハッシュ) |
| 強制再インデックス | `--force` | `--force` |

---


## Related Documents

- [03_rag_05_1-configuration-reference.md](03_rag_05_1-configuration-reference.md)
- [03_rag_05_8-rag-mcp-internal-operations-direct-db-access.md](03_rag_05_8-rag-mcp-internal-operations-direct-db-access.md)

## Keywords

configuration
file-ingestion
crawler
etag
sha256
