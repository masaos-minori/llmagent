---
title: "RAG MCP Internal Operations (Direct DB Access)"
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

# RAG MCP内部操作 (DB直接アクセス)

## RAG MCP内部操作 (DB直接アクセス)

以下の操作はRAG MCPサービスの内部処理であり、`SQLiteHelper("rag")`を通じて`rag.sqlite`に
直接アクセスする。これらはエージェント層によるDB直接アクセス**ではなく**、
RAG MCPサービスの責務範囲内の処理である。

### `list_documents()`

`/db rag urls`コマンド (`rag_list_documents` MCPツール経由) で使用される、チャンク数付きの
ドキュメント一覧を返す。

```python
def list_documents(lang: str | None = None, limit: int = 20) -> list[DocumentItem]
```

**アクセスパターン:** `documents`テーブルと`chunks`テーブルに対する読み取り専用クエリ。

### `delete_document()`

`/db rag clean`コマンド (`rag_delete_document` MCPツール経由) で使用される、ドキュメントと
関連するチャンク/埋め込みの削除処理。

```python
def delete_document(url: str) -> bool
```

**削除順序 (重要):** このメソッドは孤立レコードを防ぐため、厳格な削除順序を強制する。

1. まず`chunks_vec`の行を削除する (このドキュメントのチャンクに対応する埋め込みベクトル)
2. `chunks`の行を削除する (トリガーにより`chunks_fts`が自動同期される)
3. `documents`の行を削除する (親ドキュメント)

この順序が必要な理由は、`chunks_vec`が`chunks`を指す外部キー制約を持たないためである。
`chunks`を先に削除すると、孤立したベクトルレコードが残ってしまう。

```python
# Order matters — chunks_vec before chunks before documents
db.execute(
    "DELETE FROM chunks_vec"
    " WHERE chunk_id IN"
    " (SELECT chunk_id FROM chunks WHERE doc_id = ?)",
    (doc_id,),
)
db.execute("DELETE FROM chunks WHERE doc_id = ?", (doc_id,))
db.execute("DELETE FROM documents WHERE doc_id = ?", (doc_id,))
```

その他の派生レコード (例: `chunks`テーブルの行) は、該当する場合はカスケード削除または
トリガーに依存する。

---

### crawler

```
usage: crawler.py [-h] [--url URL [URL ...]] [--lang {en,ja,auto}]

BFS crawler: saves documents to rag-src/yyyymmddhhmmss-{slug}.json

options:
  -h, --help           show this help message and exit
  --url URL [URL ...]  URLs to crawl (multiple allowed; defaults to all
                       target_urls from config)
  --lang {en,ja,auto}  Hint language when --url is given (default: en). 'auto'
                       detects per-page language by CJK character ratio.
```

### chunk_splitter

```
usage: chunk_splitter.py [-h] [--file FILE] [--force]

Chunking: rag-src/*.json → rag-src/chunk/{stem}-{idx:04d}.json

options:
  -h, --help   show this help message and exit
  --file FILE  Process a single file (default: process all files in rag-
               src/*.json)
  --force      Re-process even if output chunks already exist
```

### ingester

```
usage: ingester.py [-h] [--force]

Embedding generation and DB ingestion: rag-src/chunk/*.json → SQLite → rag-
src/registered/

options:
  -h, --help  show this help message and exit
  --force     Force delete and re-ingest already registered URLs
```

<!-- END AUTO-GENERATED -->

## Related Documents

- [03_rag_05_1-configuration-reference.md](03_rag_05_1-configuration-reference.md)

## Keywords

configuration
