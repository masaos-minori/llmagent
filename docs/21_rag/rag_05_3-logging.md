---
title: "3. Logging"
area: rag
tags:
  - rag
  - configuration
related:
  - rag_00_document-guide.md
  - rag_05_1-configuration-reference.md
source:
  - rag_05_1-configuration-reference.md
---


# 3. Logging

| Script | Log file | Log levels |
|---|---|---|
| `crawler.py` | `/opt/llm/logs/crawl.log` + stderr | INFO: Start/Save/Skip; WARNING: HTTP Error/Retry |
| `chunk_splitter.py` | `/opt/llm/logs/chunk.log` + stderr | INFO: File Count/Chunk Count; WARNING: Sudachi Error; ERROR: File Failure (with traceback) |
| `ingester.py` | `/opt/llm/logs/ingest.log` + stderr | INFO: Chunk Count/Insert Count/Move Count; WARNING: Embedding Error/Retry/Skip; ERROR: Read/Move/Grouping Failure (with traceback) |

**Common Format:** `%(asctime)s %(levelname)s [%(funcName)s] %(message)s`

If the log file cannot be opened (`OSError`), these scripts intentionally continue
running with stderr-only output rather than failing — this fallback is a deliberate
availability choice, not a silent failure mode.

## Implementation Notes

JSON-lines output is available (`structured_log=True`) but unused by these 3 scripts;
whether this is a deliberate scope decision or unfinished work is tracked as
`docs/governance_03_issue-and-uncertainty-management.md` NC-039.

---


## Related Documents

- [rag_05_1-configuration-reference.md](rag_05_1-configuration-reference.md)

## Keywords

configuration
