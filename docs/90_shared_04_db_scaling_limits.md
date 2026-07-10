---
title: "DB Architecture - Scaling Limits and Migration Signals"
category: shared
tags:
  - db
  - architecture
  - scaling
  - limit
  - migration
  - corpus size
  - write concurrency
  - fts5 latency
  - vector search
  - hybrid store
related:
  - 90_shared_00_document-guide.md
  - 90_shared_01_overview.md
  - 90_shared_04_db_overview_and_config.md
  - 90_shared_04_db_rag_schema.md
  - 90_shared_04_session_workflow_schemas.md
  - 90_shared_04_db_operational.md
source:
  - 90_shared_04_db_overview_and_config.md
---

# DB Architecture - Scaling Limits and Migration Signals

- Overview → [90_shared_01_overview.md](90_shared_01_overview.md)
- DB API → [90_shared_05_db_module_boundaries_and_sqlitehelper.md](90_shared_05_db_module_boundaries_and_sqlitehelper.md)

---

## 11. Scaling Limits and Migration Signals

The current RAG architecture uses single-node SQLite. This is appropriate for
team-scale deployments with moderate corpus sizes and infrequent concurrent writes.
The following signals indicate when re-evaluation may be warranted.

### Corpus size

- **`chunks` table > ~500K rows:** KNN scan time in `chunks_vec` grows linearly with corpus
  size; start monitoring `/rag search` latency at this scale.
  *(Needs confirmation: actual threshold depends on hardware and embedding dimensions.)*
- **DB file size > ~10 GB:** VACUUM time, backup duration, and WAL checkpoint latency all
  increase; `/db vacuum` may take minutes instead of seconds.
  *(Needs confirmation.)*

### Write concurrency

- Multiple simultaneous `RagIngester` processes writing to the same `rag.sqlite` serialize
  at the WAL layer. If ingestion throughput becomes a bottleneck, SQLite write serialization
  may be limiting.
- **Signal:** WAL file grows faster than checkpoint reduces it. Monitor with `/db health`.

### FTS5 search latency

- **Signal:** `/rag search` consistently takes > 500 ms. FTS5 BM25 scales with document
  count; very large corpora may see degraded search speed.
  *(Needs confirmation.)*

### Operational complexity signals

- Backup and point-in-time recovery become complex as file size grows
- Multiple environments sharing the same DB file is not supported (SQLite is single-file)
- `/db consistency` issues become harder to repair at scale

### Migration signal checklist

When two or more of the following apply, consider an architecture review:

- [ ] KNN search latency > 1 s at p95
- [ ] DB file size > 20 GB
- [ ] WAL checkpoint consistently takes > 30 s
- [ ] Ingest queue depth consistently > 10 K unprocessed chunk files
- [ ] Multiple teams or processes need simultaneous write access

Use `/db health` and `/db consistency` to monitor these signals in normal operations.

### What to evaluate when limits approach

- **Vector search:** Dedicated vector databases (approximate nearest neighbor, distributed
  index) outperform `sqlite-vec` at > 1 M vectors
- **Full-text search:** Inverted-index search services handle large corpora with lower latency
- **Hybrid stores:** Relational DB + vector extension (e.g. `pgvector`-compatible) preserves
  SQL semantics while scaling write concurrency

> **Note:** All numeric thresholds above are planning estimates, not benchmarked guarantees.
> Actual limits depend on hardware, embedding dimensions, query patterns, and corpus
> characteristics. Validate with your specific deployment before treating any threshold as firm.

---

## Related Documents

- [90_shared_00_document-guide.md](90_shared_00_document-guide.md)
- [90_shared_01_overview.md](90_shared_01_overview.md)
- [90_shared_04_db_overview_and_config.md](90_shared_04_db_overview_and_config.md)
- [90_shared_04_db_rag_schema.md](90_shared_04_db_rag_schema.md)
- [90_shared_04_session_workflow_schemas.md](90_shared_04_session_workflow_schemas.md)
- [90_shared_04_db_operational.md](90_shared_04_db_operational.md)
- [90_shared_05_db_module_boundaries_and_sqlitehelper.md](90_shared_05_db_module_boundaries_and_sqlitehelper.md)

## Keywords

scaling
limit
migration
corpus size
write concurrency
fts5 latency
vector search
hybrid store
