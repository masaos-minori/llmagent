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

```bash
# target_urlsにfile://を追加して実行
uv run python scripts/rag/ingestion/crawler.py --targets-file /path/to/targets.toml
```

TOML形式:
```toml
[[target_urls]]
url = "file:///path/to/file.py"
lang = "en"
```

- クロール → チャンク分割 → 埋め込みの3ステップ（別プロセス）
- `.py`ファイル: コンテンツを `code_blocks` に格納
- `etag`: HTTP ETagではなくファイル内容のSHA-256ハッシュ
- `last_modified`: ファイルのmtime (ISO8601)

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
