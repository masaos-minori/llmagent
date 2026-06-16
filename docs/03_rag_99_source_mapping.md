# RAG Documentation Source Mapping

Audit table: maps content from the 7 original source files to the 8 restructured output files.

Status values:
- **Preserved** — content moved in full to new location
- **Summarized+Link** — brief summary kept; full content in canonical location
- **Merged** — combined with content from other sources
- **Flag(90)** — flagged as inconsistency/bug; canonical record is in `03_rag_90`

---

## 1. `docs/03_spec_rag.md`

| Source Section | New File | New Section | Status |
|---|---|---|---|
| §1 Purpose | `03_rag_01` | §Purpose | Preserved |
| §2 Scope | `03_rag_01` | §Scope | Preserved |
| §3 Background | `03_rag_01` | §System Architecture | Merged |
| §4 Prerequisites | `03_rag_05` | §5 Constraints Reference | Preserved |
| §5 Constraints | `03_rag_01` | §Constraints; `03_rag_05` §5 | Merged |
| §6.1 Ingestion pipeline | `03_rag_01` | §Ingestion Pipeline | Summarized+Link |
| §6.2 Query pipeline | `03_rag_01` | §Query Pipeline | Summarized+Link |
| §6.3 Semantic cache | `03_rag_03` | §6 SemanticCache | Preserved |
| §7.1 Ingestion I/O | `03_rag_04` | §1 File Format Specifications | Preserved |
| §7.2 Query I/O | `03_rag_03` | §1 Pipeline Overview | Merged |
| §8.1 Ingestion flow | `03_rag_02` | §1 Execution Guide (dataflow) | Preserved |
| §8.2 Query flow | `03_rag_03` | §1 Pipeline Overview | Preserved |
| §9.1 DB schema | `03_rag_04` | §2 SQLite Schema | Preserved |
| §9.2 RagHit types | `03_rag_04` | §3 Hit Type Hierarchy | Preserved |
| §9.3 Config params | `03_rag_05` | §1.3 | Summarized+Link |
| §10.1 RagPipeline API | `03_rag_03` | §2 | Preserved |
| §10.2 WebCrawler API | `03_rag_02` | §2 | Preserved |
| §10.3 ChunkSplitter API | `03_rag_02` | §3 | Preserved |
| §10.4 RagIngester API | `03_rag_02` | §4 | Preserved |
| §10.5 PipelineStage | `03_rag_03` | §3 | Preserved |
| §11 Error handling | `03_rag_05` | §4 Error Handling Reference | Preserved |
| §12 Validation plan | — | (internal; not republished) | — |
| §13 Known issues | `03_rag_90` | All BUG/SPEC/OQ entries | Preserved |

---

## 2. `docs/03_rag-ref-crawler.md`

| Source Section | New File | New Section | Status |
|---|---|---|---|
| §2.1 Class overview | `03_rag_02` | §2.1 | Preserved |
| §2.2 Feature summary | `03_rag_02` | §2.2 Behavior details | Merged |
| §2.3 Implementation | `03_rag_02` | §2.2 Behavior details | Merged |
| §2.4 CLI args + output format | `03_rag_02` | §2.3 + §2.4 | Preserved |
| §2.5 Error handling | `03_rag_02` | §2.5 | Preserved |
| §2.6 Logging | `03_rag_02` | §2.6 | Preserved |
| §2.7 Config items | `03_rag_05` | §1.1 | Preserved |
| Title `web_crawler.py` | `03_rag_90` | DOC-1 | Flag(90) |

---

## 3. `docs/03_rag-ref-splitter.md`

| Source Section | New File | New Section | Status |
|---|---|---|---|
| §3.1 Class overview | `03_rag_02` | §3.1 | Preserved |
| §3.2 Feature summary | `03_rag_02` | §3.2 Splitting strategies | Merged |
| §3.3 Implementation | `03_rag_02` | §3.2 | Merged |
| §3.4 CLI args + output format | `03_rag_02` | §3.3 + §3.4 | Preserved |
| §3.5 Error handling | `03_rag_02` | §3.5 | Preserved |
| §3.6 Logging | `03_rag_02` | §3.6 | Preserved |
| §3.7 Config items | `03_rag_05` | §1.1 | Preserved |

---

## 4. `docs/03_rag-ref-ingester.md`

| Source Section | New File | New Section | Status |
|---|---|---|---|
| §4.1 Class overview | `03_rag_02` | §4.1 | Preserved |
| §4.2 Feature summary | `03_rag_02` | §4.2 Behavior details | Merged |
| §4.3 Implementation | `03_rag_02` | §4.2 | Merged |
| §4.4 CLI args + embed API | `03_rag_02` | §4.3 + §4.4 | Preserved |
| §4.5 Error handling | `03_rag_02` | §4.6 | Preserved |
| §4.6 Logging | `03_rag_02` | §4.7 | Preserved |
| §4.7 Config items | `03_rag_05` | §1.1 + §1.2 | Preserved |
| Title `rag_ingester.py` | `03_rag_90` | DOC-2 | Flag(90) |
| BUG-1/2/3 (root cause) | `03_rag_90` | BUG-1/2/3 | Preserved |

---

## 5. `docs/03_rag-ingestion-pipeline.md`

| Source Section | New File | New Section | Status |
|---|---|---|---|
| Index table (links to ref-*) | `03_rag_00` | §5 File Index | Summarized+Link |
| `rag/utils.py` API | `03_rag_02` | §5 Shared Utilities | Preserved |
| Dataflow diagram | `03_rag_02` | §1 Execution Guide | Preserved |
| FTS5 Sudachi filter note | `03_rag_02` | §6 FTS5 Notes | Preserved |
| FTS5/LLM content separation | `03_rag_02` | §6 FTS5 Notes | Preserved |

---

## 6. `docs/03_rag-ingestion-run.md`

| Source Section | New File | New Section | Status |
|---|---|---|---|
| §1.1 Prerequisites | `03_rag_05` | §2.1 | Preserved |
| §1.2 Execution commands | `03_rag_05` | §2.2–2.4 | Preserved |
| §1.3 File lifecycle table | `03_rag_04` | §1; `03_rag_02` §1 | Preserved |
| Stage count "3 steps" | `03_rag_90` | SPEC-2 | Flag(90) |

---

## 7. `docs/05_ref-rag.md`

| Source Section | New File | New Section | Status |
|---|---|---|---|
| Module overview table | `03_rag_03` | §1 Pipeline Overview | Preserved |
| §1.1 Feature + stage table | `03_rag_03` | §1 + §5 | Preserved |
| §1.2 RagPipeline API | `03_rag_03` | §2 | Preserved |
| §1.2 PipelineStage Protocol | `03_rag_03` | §3 | Preserved |
| §1.2 PipelineContext | `03_rag_03` | §4 | Preserved |
| §1.2 Stage constructors | `03_rag_03` | §5 | Preserved |
| §1.2 SemanticCache | `03_rag_03` | §6 | Preserved |
| §1.2 RagRepository/Scorer/LLM | `03_rag_03` | §7 | Preserved |
| §1.3 Exported types (RawHit etc.) | `03_rag_04` | §3 | Preserved |
| §1.3 LLMMessage | `03_rag_04` | §5.2 | Preserved |
| §1.3 PipelineStageResult | `03_rag_04` | §5.3 | Preserved |
| §1.4 Config items | `03_rag_05` | §1.3 | Preserved |
| §1.5 Callers | `03_rag_03` | §1 Pipeline Overview | Preserved |
| `use_rrf` implementation note | `03_rag_90` | SPEC-1 | Flag(90) |

---

## Coverage Summary

| Source file | Sections | Mapped | Unmapped |
|---|---|---|---|
| `03_spec_rag.md` | 23 | 22 | §12 (validation; internal only) |
| `03_rag-ref-crawler.md` | 7 | 7 | — |
| `03_rag-ref-splitter.md` | 7 | 7 | — |
| `03_rag-ref-ingester.md` | 7 | 7 | — |
| `03_rag-ingestion-pipeline.md` | 5 | 5 | — |
| `03_rag-ingestion-run.md` | 3 | 3 | — |
| `05_ref-rag.md` | 14 | 14 | — |

All significant content from the 7 source files has been mapped to one or more new files.
No source information has been silently dropped.
