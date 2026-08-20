---
title: "3. Logging"
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


# 3. Logging

| Script | Log file | Log levels |
|---|---|---|
| `crawler.py` | `/opt/llm/logs/crawl.log` + stderr | INFO: Start/Save/Skip; WARNING: HTTP Error/Retry |
| `chunk_splitter.py` | `/opt/llm/logs/chunk.log` + stderr | INFO: File Count/Chunk Count; WARNING: Sudachi Error; ERROR: File Failure (with traceback) |
| `ingester.py` | `/opt/llm/logs/ingest.log` + stderr | INFO: Chunk Count/Insert Count/Move Count; WARNING: Embedding Error/Retry/Skip; ERROR: Read/Move/Grouping Failure (with traceback) |

**Common Format:** `%(asctime)s %(levelname)s [%(funcName)s] %(message)s`

## Implementation Notes

- All three scripts above use the `Logger` class from `shared/logger.py` as `Logger(__name__, "<path>.log")`. The log level cannot be changed in the constructor and is always fixed to `logging.INFO` (as `setLevel(logging.INFO)` is executed during logger initialization).
  [Explicit in code]
- Output destinations include both a `FileHandler` and a `StreamHandler` to `stderr`. If opening the log file fails (`OSError`), a warning is issued to the fallback `shared.logger.fallback` logger, and execution continues using only the `stderr` handler.
  [Explicit in code]
- `propagate=False` is configured, so duplicate output to the root logger does not occur.
  [Explicit in code]
- The `Logger` can switch to JSON-lines format (`_JsonFormatter`) when `structured_log=True` is specified. However, since `crawler.py`, `chunk_splitter.py`, and `ingester.py` do not specify `structured_log`, they continue using the common text format described in this document.
  [Explicit in code]
- Context fields such as `turn_id`, `session_id`, `rag_query_id`, `workflow_id`, and `task_id` provided via `extra={...}` are not output in the text format (`_FORMAT`). These are reflected in the JSON output only when using structured logging (`structured_log=True`), because the `_FORMAT` string does not reference these fields.
  [Explicit in code]

---


## Related Documents

- [03_rag_05_1-configuration-reference.md](03_rag_05_1-configuration-reference.md)

## Keywords

configuration
