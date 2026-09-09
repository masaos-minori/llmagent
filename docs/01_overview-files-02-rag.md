---
title: "RAG Files File Structure"
area: overview
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

See `rag-src/` for the current file layout.

### RAG Pipeline Stages

**Crawled text (`rag-src/`)** — Collects raw crawled content as `{yyyymmddhhmmss}-{slug}.json`. Owned by the crawler process. Feeds into the chunking stage. Direction of dependency flows from crawler into this component.

**Chunked files (`rag-src/chunk/`)** — Produced by the chunk_splitter process from crawled text. Uses `{stem}-{idx:04d}.json` naming convention. Feeds into the ingester stage. Dependency direction flows from chunk_splitter into this staging area.

**Registered files (`rag-src/registered/`)** — Moved here by the ingester after successful database insertion. Retention period and cleanup policy currently unconfirmed — needs resolution against ingester implementation.

**sqlite-vec extension (`sqlite-vec/vec0.so`)** — Loadable SQLite extension module providing vector search capability. Runtime dependency of the RAG pipeline's vector store layer.

### Data Flow Dependencies

- Crawler → chunk_splitter: crawled text is consumed by chunk splitter
- chunk_splitter → ingester: chunks are consumed by ingester for database insertion
- ingester → registered/: post-insertion staging area (retention TBD)
- sqlite-vec: used by RAG pipeline's vector store for embedding similarity queries

### Unknowns

- Retention period for files under `registered/` is not confirmed within this document (needs verification against ingester implementation)

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
