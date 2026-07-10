---
title: "3. Logging"
category: rag
tags:
  - rag
  - configuration
related:
  - 03_rag_00_document-guide.md
  - 03_rag_05_configuration_and_operations.md
source:
  - 03_rag_05_configuration_and_operations.md
---

# 3. Logging

## 3. Logging

| Script | Log file | Log levels |
|---|---|---|
| `crawler.py` | `/opt/llm/logs/crawl.log` + stderr | INFO: start/save/skip; WARNING: HTTP error/retry |
| `chunk_splitter.py` | `/opt/llm/logs/chunk.log` + stderr | INFO: file/chunk counts; WARNING: Sudachi error; ERROR: file failure (traceback) |
| `ingester.py` | `/opt/llm/logs/ingest.log` + stderr | INFO: chunk/insert/move counts; WARNING: embed error/retry/skip; ERROR: read/move/group failure (traceback) |

**Common format:** `%(asctime)s %(levelname)s [%(funcName)s] %(message)s`

---


## Related Documents

- [03_rag_05_configuration_and_operations.md](03_rag_05_1-configuration-reference.md)

## Keywords

configuration
