---
title: "3. Logging"
area: rag
tags:
  - rag
  - configuration
related:
  - rag_00_document-guide.md
  - rag_05_01-configuration-reference.md
---


# 11. Logging

| Script | Log file | Log levels |
|---|---|---|
| `crawler.py` | crawl log file (configured via logging setup) + stderr | INFO: Start/Save/Skip; WARNING: HTTP Error/Retry |
| `chunk_splitter.py` | chunk log file (configured via logging setup) + stderr | INFO: File Count/Chunk Count; ERROR: File Failure including Sudachi tokenization errors (with traceback) |
| `ingester.py` | ingest log file (configured via logging setup) + stderr | INFO: Chunk Count/Insert Count/Move Count; WARNING: Embedding Error/Retry/Skip; ERROR: Read/Move/Grouping Failure (with traceback) |

**Common Format:** `%(asctime)s %(levelname)s [%(funcName)s] %(message)s`

If the log file cannot be opened (`OSError`), these scripts intentionally continue
running with stderr-only output rather than failing — this fallback is a deliberate
availability choice, not a silent failure mode.

## Implementation Notes

JSON-lines output (`structured_log=True`) is enabled on `crawler.py`,
`chunk_splitter.py`, and `ingester.py`, so the context fields (`turn_id`,
`session_id`, `rag_query_id`, `workflow_id`, `task_id`) are included in their
log output. `chunk.log` and
`ingest.log` are also written by other, unchanged scripts in this scope
(`chunk_japanese.py`; `chunk_grouping.py`, `document_manager.py`,
`etag_manager.py`, `transaction_commit.py`, `embedding.py`, `file_routing.py`),
so those two files now contain a mix of text-format and JSON-lines entries —
an accepted, owner-confirmed consequence, not a defect. `crawl.log` is written
only by `crawler.py` and is unaffected by this.

---


## Keywords

- configuration
