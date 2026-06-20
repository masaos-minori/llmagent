# Implementation: Add "Scaling Limits and Migration Signals" section to docs/06_shared_04_db_architecture_and_schema.md

## Goal
Add a concrete, operator-facing section documenting the practical SQLite scaling limits
for the RAG architecture, the signals that indicate limits are being approached, and
a migration signal checklist.

## Scope
- File: `docs/06_shared_04_db_architecture_and_schema.md`
- Append new section: `## Scaling Limits and Migration Signals`
- No code changes

## Assumptions
- The section should be appended at the end of the document (or before a "Known Issues" section if one exists)
- All numeric thresholds are estimates, not benchmarked guarantees — marked "Needs confirmation"
- Audience: operators running the system, not necessarily storage architects
- Existing operational tooling (`/db health`, `/db consistency`, `/db checkpoint`, `/db vacuum`)
  is referenced as the primary signal mechanism

## Implementation

### Target file
`docs/06_shared_04_db_architecture_and_schema.md`

### Procedure
1. Read the end of the document to find the insertion point
2. Append the new section

### Method
Single edit — append to end of file (or before last section if appropriate).

### Details

**New section content:**

```markdown
## Scaling Limits and Migration Signals

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
```

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Section present | `grep "Scaling Limits" docs/06_shared_04_db_architecture_and_schema.md` | 1 match |
| Checklist present | `grep "Migration signal checklist" docs/06_shared_04_db_architecture_and_schema.md` | 1 match |
| Needs confirmation tagged | `grep "Needs confirmation" docs/06_shared_04_db_architecture_and_schema.md` | 3+ matches |
| Full suite | `uv run pytest -q` | no failures |
