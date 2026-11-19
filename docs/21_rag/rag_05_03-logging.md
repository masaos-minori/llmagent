---
title: "Logging"
area: rag
tags:
  - rag
  - configuration
related:
  - rag_00_document-guide.md
  - rag_05_01-configuration-reference.md
---


# Logging

| Script | Log file | Log levels |
|---|---|---|
| `crawler.py` | crawl log file (configured via logging setup) + stderr | INFO: Start/Save/Skip; WARNING: HTTP Error/Retry |
| `chunk_splitter.py` | chunk log file (configured via logging setup) + stderr | INFO: File Count/Chunk Count, Size-rule Discard Summary; ERROR: File Failure including Sudachi tokenization errors (with traceback) |
| `ingester.py` | ingest log file (configured via logging setup) + stderr | INFO: Chunk Count/Insert Count/Move Count; WARNING: Embedding Error/Retry/Skip; ERROR: Read/Move/Grouping Failure (with traceback) |

**Common Format:** `%(asctime)s %(levelname)s [%(funcName)s] %(message)s`

If the log file cannot be opened (`OSError`), these scripts intentionally continue
running with stderr-only output rather than failing — this fallback is a deliberate
availability choice, not a silent failure mode.

## Implementation Notes

JSON-lines output (`structured_log=True`) is enabled on `crawler.py`, `chunk_splitter.py`, and `ingester.py`, so the context fields (`turn_id`, `session_id`, `rag_query_id`, `workflow_id`, `task_id`) are included in their log output. `chunk.log` and `ingest.log` are also written by helper modules that use text format (`chunk_japanese.py`; `chunk_grouping.py`, `document_manager.py`, `etag_manager.py`, `transaction_commit.py`, `embedding.py`, `file_routing.py`), so those two files contain a mix of text-format and JSON-lines entries — an accepted, owner-confirmed property, not a defect. `crawl.log` is written only by `crawler.py` and is JSON-lines only.

### Discard Summary

When a source file has one or more items dropped by the size rule (content shorter
than `min_chunk`), `chunk_splitter.py` emits one additional record per file, additive
to the normal `INFO` chunk-count line. This makes silent size-rule discards
observable without treating them as failures.

- **Trigger:** once per source file, only when at least one item was discarded by the
  `below_min_chunk` size rule.
- **Level:** `WARNING` when the source yields zero chunks, `INFO` when it yields
  chunks but also discards some.
- **Fields:** `url`, `source_type="file"`, `stage_name="chunk"`,
  `discard_reason="below_min_chunk"`, plus `discarded_count` and `discarded_chars`.
  The message carries the count and combined character length only; it never
  contains document content.
- **Serialization caveat:** the structured fields are attached to the `LogRecord`
  via `extra=`. The shared formatter serializes only its known keys to the JSON
  line, so these fields are observable on the record and message text but are not
  yet written to the JSON line — the same limitation applies to every existing
  structured field such as `url`.

## Keywords

- configuration
