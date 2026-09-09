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

### Component Responsibilities

**Crawled content** — Raw crawled data collected by the crawler process. Owned by the crawler; feeds into the chunking stage. Dependency direction flows from crawler into this component.

**Chunked content** — Produced by the chunk_splitter process from crawled content. Feeds into the ingester stage. Dependency direction flows from chunk_splitter into this staging area.

**Post-ingestion staging** — Files moved here by the ingester after successful database insertion. Retention period and cleanup policy are unresolved — requires verification against ingester implementation.

**Vector search extension** — SQLite extension module providing vector search capability. Runtime dependency of the RAG pipeline's vector store layer.

### Data Flow Dependencies

Crawler produces crawled content consumed by chunk_splitter; chunk_splitter produces chunks consumed by ingester for database insertion; ingester moves processed files to post-ingestion staging; vector search extension supports embedding similarity queries across all stages.

### Unknowns

Retention period for post-ingestion staging files is not confirmed within this document (requires verification against ingester implementation).

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
