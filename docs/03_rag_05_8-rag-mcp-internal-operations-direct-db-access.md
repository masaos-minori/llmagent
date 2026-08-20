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

The following operations are internal processes of the RAG MCP service and access `rag.sqlite` directly via `SQLiteHelper("rag")`. These are **not** direct database accesses by the agent layer, but rather processing within the responsibility scope of the RAG MCP service.

## `list_documents()`

Used by the `/db rag urls` command (via the `rag_list_documents` MCP tool) to return a list of documents with their respective chunk counts.

See `list_documents()` in `scripts/mcp_servers/rag_pipeline/document_manager.py` (or the equivalent in `scripts/rag/ingestion/document_manager.py`) for the current signature.

**Access Pattern:** Read-only queries against the `documents` and `chunks` tables.

## `delete_document()`

Used by the `/db rag clean` command (via the `rag_delete_document` MCP tool) to perform deletion of a document and its associated chunks/embeddings.

See `delete_document()` in `scripts/mcp_servers/rag_pipeline/document_manager.py` for the current signature.

**Deletion Order (Important):** This method enforces a strict deletion order to prevent orphaned records.

1. First, explicitly delete rows from `chunks_vec` (the embedding vectors corresponding to the document's chunks).
2. Delete the row from `documents` (`ON DELETE CASCADE` handles the cascading deletion of `chunks` rows, which in turn triggers synchronization of `chunks_fts`).

This order is necessary because `chunks_vec` does not have a foreign key constraint pointing to `chunks`. Explicit `DELETE` statements for the `chunks` table do not exist in the code (see `docs/03_rag_91_design_notes.md` DESIGN-3 for details).

```python
# Order matters — chunks_vec before documents (CASCADE removes chunks)
db.execute(
    "DELETE FROM chunks_vec"
    " WHERE chunk_id IN"
    " (SELECT chunk_id FROM chunks WHERE doc_id = ?)",
    (doc_id,),
)
db.execute("DELETE FROM documents WHERE doc_id = ?", (doc_id,))
```

Other derivative records (e.g., rows in the `chunks` table) depend on cascading deletes or triggers where applicable.

---


## CLI Tools
For current CLI usage, run `crawler.py --help`, `chunk_splitter.py --help`, or `ingester.py --help` in `scripts/rag/ingestion/`.

## Related Documents

- [03_rag_05_1-configuration-reference.md](03_rag_05_1-configuration-reference.md)

## Keywords

configuration
