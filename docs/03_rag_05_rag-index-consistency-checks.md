---
title: "RAG index consistency checks"
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

# RAG index consistency checks

## RAG index consistency checks

The RAG index requires three tables to remain synchronized:
- `chunks` — canonical chunk records
- `chunks_fts` — FTS5 full-text index (populated by SQLite triggers)
- `chunks_vec` — vector embedding index

### Startup warning

On every agent startup, the RAG consistency check runs `check_rag_consistency()` (3 COUNT queries,
read-only, fast). If any inconsistency is detected, a warning is emitted to the console:

```
[RAG] Consistency issue: fts_gap=3 (3 chunks missing from FTS index)
```

No warning is shown on a healthy index (only `logger.info("RAG consistency: OK")` is written).

### `/db rag rebuild-fts` command

The `/db rag rebuild-fts` command rebuilds `chunks_fts` from the canonical `chunks` table.

**Rebuild rule:** The rebuild indexes `COALESCE(normalized_content, content)`, identical to the FTS5 trigger (`chunks_ai`).

- Japanese chunks: when `normalized_content` is present (Sudachi-normalized), it is indexed
- English/code chunks: `normalized_content` is NULL → FTS5 falls back to `content` directly
- `chunks_fts` must not be manually edited — it is a derived index maintained by triggers or rebuild operations

**When to use:**
- `fts_gap > 0` (missing FTS entries) detected by `/db consistency`
- `fts_orphan_count > 0` (extra FTS entries, data loss risk)
- After large-scale ingestion to verify FTS index integrity

**Repair decision tree:**

| Issue | Fix |
|---|---|
| `fts_gap > 0` | Run `/db rag rebuild-fts` — FTS entries are missing; rebuild from `chunks` |
| `fts_orphan_count > 0` | Run `/db rag rebuild-fts` — FTS has extra entries (data loss risk; urgent) |

### `/db consistency` command

The `/db consistency` command shows numeric counts followed by an OK or error summary:

```
  chunks: 1042  fts: 1042  vec: 1042  fts_gap: 0  orphan_vec: 0  fts_orphan: 0
RAG consistency: OK (chunks/FTS/vec in sync)
```

On inconsistency:

```
  chunks: 1042  fts: 1039  vec: 1042  fts_gap: 3  orphan_vec: 0  fts_orphan: 0
RAG consistency: FAIL
Consistency issue: [WARNING] FTS gap detected (chunks=1042, fts=1039, gap=3). Affected doc_ids: [1, 2, 3]. Run '/db rag rebuild-fts' to repair.
```

### Threshold policy

The check uses a **strict-zero** threshold: any non-zero `fts_gap`, `fts_orphan_count`,
or `orphan_vec_count` is reported as inconsistent. Configurable thresholds (e.g. allowing
`fts_gap <= 5`) are not implemented. **Needs confirmation** if partial-OK policy is required.

### Fixing inconsistencies

Use `/db consistency` to detect issues. The report includes affected `chunk_id`/URL
identifiers (up to 10 each) so operators can act without manual DB investigation.

**Repair decision tree:**

| Issue | Fix |
|---|---|
| `fts_gap > 0` | Run `/db rag rebuild-fts` — FTS entries are missing; rebuild from `chunks` |
| `fts_orphan_count > 0` | Run `/db rag rebuild-fts` — FTS has extra entries (data loss risk; urgent) |
| `orphan_vec_count > 0` | Run `ingester.py --force` for affected URLs — `chunks_vec` rows without `chunks` counterparts |
| `vec != chunks` | Run `ingester.py --force` for the affected URL — embedding step likely failed |

Run `/db rag rebuild-fts` to resynchronize `chunks_fts` from the `chunks` table.


<!-- AUTO-GENERATED: gen_rag_reference.py config -->
| Key | Default | Description |
|---|---|---|
| `rag_src_dir` | `/opt/llm/rag-src` | — |
| `crawl_delay` | `1.5` | — |
| `max_depth` | `6` | — |
| `min_chunk` | `40` | — |
| `max_chunk` | `500` | — |
| `embed_retry` | `3` | — |
| `embed_workers` | `4` | — |
| `fetch_retry` | `3` | — |
| `fetch_timeout` | `15` | — |
| `crawl_concurrency` | `3` | — |
| `max_pages` | `500` | — |
| `chunk_overlap` | `50` | — |
| `md_index_enable` | `False` | — |
| `md_snippet_max_chars` | `600` | — |
| `skip_nofollow` | `False` | — |
| `skip_external` | `True` | — |
| `target_urls` | `[['https://ziglang.org/documentation/master/', 'en'], ['https://zig.guide/', 'en'], ['https://www.ruby-lang.org/en/documentation/quickstart/', 'en'], ['https://www.ruby-lang.org/ja/documentation/quickstart/', 'ja'], ['https://docs.ruby-lang.org/en/3.4/doc/', 'en'], ['https://docs.ruby-lang.org/ja/3.4/doc/', 'ja'], ['https://www.gnu.org/software/emacs/manual/html_node/elisp/', 'en']]` | — |
| `en_stopwords` | `['a', 'an', 'the', 'and', 'or', 'but', 'if', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'shall', 'can', 'this', 'that', 'these', 'those', 'it', 'its', 'i', 'you', 'he', 'she', 'we', 'they', 'them', 'their', 'our', 'your', 'my', 'his', 'her', 'not', 'no', 'nor', 'so', 'yet', 'both', 'either', 'each', 'other', 'such', 'into', 'through', 'about', 'than', 'then', 'when', 'where', 'who', 'which', 'what', 'how', 'all', 'any', 'more', 'most', 'also', 'up', 'out', 'as', 'just', 'over', 'after', 'before', 'while', 'since', 'because', 'although', 'however', 'therefore', 'thus', 'hence', 'whether', 'once', 'only', 'even', 'still', 'now', 'here', 'there', 'very', 'too', 'much', 'many', 'some', 'few', 'must', 'let', 'get', 'got', 'make', 'made', 'use', 'used', 'using', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten', 'new', 'old', 'first', 'last', 'long', 'great', 'little', 'own', 'right', 'big', 'high', 'small', 'large', 'next', 'early', 'young', 'important', 'public', 'private', 'real', 'best', 'free', 'same', 'different']` | — |
| `ja_stop_pos` | `['particle', 'auxiliary verb', 'supplementary symbol', 'blank', 'interjection', 'conjunction']` | — |

---


## Related Documents

- [03_rag_05_configuration_and_operations.md](03_rag_05_1-configuration-reference.md)

## Keywords

configuration
