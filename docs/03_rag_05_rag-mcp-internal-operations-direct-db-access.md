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

# RAG MCP Internal Operations (Direct DB Access)

## RAG MCP Internal Operations (Direct DB Access)

The following operations are internal to the RAG MCP service and directly access `rag.sqlite`
through `SQLiteHelper("rag")`. These are **not** Agent-layer direct DB access — they are
part of the RAG MCP service's responsibility boundary.

### `list_documents()`

Returns a list of documents with chunk counts, used by `/db rag urls` (via `rag_list_documents`
MCP tool).

```python
def list_documents(lang: str | None = None, limit: int = 20) -> list[DocumentItem]
```

**Access pattern:** Read-only query against `documents` and `chunks` tables.

### `delete_document()`

Deletes a document and its associated chunks/embeddings, used by `/db rag clean` (via
`rag_delete_document` MCP tool).

```python
def delete_document(url: str) -> bool
```

**Deletion order (critical):** The method enforces a strict deletion order to prevent orphan
records:

1. Delete `chunks_vec` rows first (embedding vectors for this document's chunks)
2. Delete `chunks` rows (triggers auto-sync `chunks_fts`)
3. Delete `documents` row (parent document)

This order is necessary because `chunks_vec` has no foreign key constraint pointing to
`chunks`. Deleting `chunks` first would leave orphaned vector records.

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

Other derived records (e.g., `chunks` table rows) rely on cascade deletes or triggers
where applicable.

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
