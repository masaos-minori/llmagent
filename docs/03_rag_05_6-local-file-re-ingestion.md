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

## 6. ローカルファイルの再取り込み

### 初回取り込み

`config/rag_pipeline.toml`の`target_urls`に、スキーム`file://`でファイルパスを追加する。

```toml
[[target_urls]]
url = "file:///path/to/file.py"
lang = "en"
```

その後、以下を実行する。

```
uv run python scripts/rag/ingestion/crawler.py --targets-file /path/to/targets.toml
```

クローラーは`crawl_file()`を呼び出し、JSONを`rag-src/`に書き込み、チャンク分割を行い、
SQLiteベクトルストアに埋め込む。

### ファイル変更後の再取り込み

ingesterは、現在のファイル内容のSHA-256ハッシュを`documents`に保存されている
`etag`と比較する。

- **変更なし** (ハッシュが一致): 自動的にスキップされ、再取り込みは行われない。
- **変更あり** (ハッシュが異なる): 自動的に再取り込みされる — 旧ドキュメントとチャンクを削除し、再チャンク分割、再埋め込みを行う。
- **`--force`**: ハッシュに関わらず削除して再取り込みする。

取り込み中のログメッセージ:

- `"file:// unchanged (sha256 match): file:///path/to/file"` — スキップされた
- `"file:// changed — auto re-ingesting: file:///path/to/file"` — 再取り込みされた

### 多数のローカルファイルの一括再取り込み

複数のファイルが変更された場合は、`--targets-file`を指定してクローラーを実行し、
リストされた`file://` URLをすべて再クロールする。
クローラーは`--force`をサポートしない。未変更のファイルはSHA-256ハッシュ比較により自動的にスキップされる。
すでに取り込み済みのURLの埋め込みを強制的に再実行するには、クロール後に`ingester.py --force`を実行する。

```
uv run python scripts/rag/ingestion/crawler.py --targets-file /path/to/targets.toml
uv run python scripts/rag/ingestion/ingester.py --force
```

### 比較: ローカルファイル vs. Web URL

| Aspect | Web URL | ローカルファイル (file://) |
|---|---|---|
| 未変更時のスキップ | あり (ETag/304) | あり (SHA-256ハッシュ) |
| 強制再インデックス | `--force` | `--force` |

---


## Related Documents

- [03_rag_05_1-configuration-reference.md](03_rag_05_1-configuration-reference.md)

## Keywords

configuration
