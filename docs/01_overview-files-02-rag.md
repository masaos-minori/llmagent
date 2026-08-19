---
title: "RAG Files File Structure"
category: overview
tags:
  - rag
  - rag-src
  - crawler
  - chunk-splitter
  - ingester
  - embedding
  - file-structure
related:
  - 01_overview-files-01-build.md
  - 01_overview-files-05-config.md
  - 01_overview-files-06-misc.md
---

# File Structure

Architecture Overview → [`01_overview-arch-01-process.md`](01_overview-arch-01-process.md), [`01_overview-arch-02-pipelines.md`](01_overview-arch-02-pipelines.md), [`01_overview-arch-03-features.md`](01_overview-arch-03-features.md)

## 3. File Structure

Directory structure at deployment target:

``` text
/opt/llm/
├─ rag-src/                           # Crawled text (yyyymmddhhmmss-{slug}.json)
│   ├─ chunk/                         # Chunked files ({stem}-{idx:04d}.json)
│   └─ registered/                    # Files ingested into DB (moved by ingester.py)
│       * Retention period and cleanup policy for files under `registered/` is not confirmed within this document (needs verification).
├─ sqlite-vec/
│   └─ vec0.so                        # SQLite vector search extension (loadable extension module)
```

## Related Documents

- `01_overview-files-01-build.md`
- `01_overview-files-03-scripts.md`
- `01_overview-files-04-shared.md`
- `01_overview-files-05-config.md`
- `01_overview-files-06-misc.md`
- [01_overview.md](01_overview.md)

## Keywords

rag
rag-src
crawler
chunk-splitter
ingester
embedding
file-structure
