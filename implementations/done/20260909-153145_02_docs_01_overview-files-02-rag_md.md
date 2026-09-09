## Goal

Remove ASCII directory trees and per-file descriptions from `docs/01_overview-files-02-rag.md`; replace with design-intent prose covering component responsibility, owned state, allowed dependency direction, reason for process separation, reason for per-process config separation, and design boundaries needing joint review. [REQ-001, REQ-003]

## Scope

- Remove the ASCII tree block (lines 26-34): `/opt/llm/rag-src/` tree
- Replace with prose describing the RAG pipeline's data flow: crawled text ingestion, chunking, registration, and vector DB indexing
- Preserve existing "Related Documents" and "Keywords" sections unchanged
- Note: the file also contains a retention-period uncertainty comment about `registered/` files — this should be addressed as an Unknown item rather than silently resolved

## Assumptions

- The RAG pipeline follows a staged data flow: crawl → chunk → register → index
- The `sqlite-vec/vec0.so` extension is a runtime dependency of the RAG pipeline, not a configuration artifact
- The six-file split remains unchanged (File Split Rule's 400-line threshold)
- The retention period for `registered/` files is genuinely unknown and needs resolution

## Design decisions

- Keep the thematic grouping as prose structure (e.g., "RAG Pipeline Stages" as a section heading) but replace file-by-file listing with component responsibility descriptions
- Replace bare file enumeration with a single pointer sentence ("see `rag-src/` for the current file layout") per `skills/DESIGN.md` Avoid implementation-reference duplication
- Flag the retention-period uncertainty as an actionable Unknown item rather than silently resolving it

## Alternatives considered

- Merging this file with `01_overview-files-01-build.md` (rejected: different domains — RAG pipeline vs. build/deployment)
- Converting remaining prose to table format (rejected: prose better conveys causal relationships between pipeline stages)

## Implementation

### Target file

`docs/01_overview-files-02-rag.md`

### Procedure

1. Identify and remove the ASCII tree block (the `/opt/llm/rag-src/` tree at lines 26-34)
2. Write prose replacing the tree: describe the four RAG pipeline stages (crawled text, chunked files, registered files, sqlite-vec extension) as responsible entities with their owned state and dependency direction
3. Create a new "Unknowns" subsection noting the unresolved retention period question for `registered/` files
4. Verify Related Documents and Keywords sections are preserved unchanged

### Method

Read the current file to identify the exact tree block boundary. Write replacement prose that covers: what each stage does (responsibility), what it owns (state), which direction its dependencies flow (allowed dependency direction), why each stage runs separately (reason for process separation), and which boundaries require joint review (design boundaries).

### Details

**Section 1 — RAG Pipeline Stages:**

- Crawled text (`rag-src/`): collects raw crawled content as `{yyyymmddhhmmss}-{slug}.json`; owned by crawler process; feeds into chunking stage
- Chunked files (`rag-src/chunk/`): produced by chunk_splitter process from crawled text; `{stem}-{idx:04d}.json` naming convention; feeds into ingester stage
- Registered files (`rag-src/registered/`): moved here by ingester after successful DB insertion; retention period and cleanup policy currently unconfirmed — needs resolution
- sqlite-vec extension (`sqlite-vec/vec0.so`): loadable SQLite extension module providing vector search capability; runtime dependency of RAG pipeline's vector store layer

**Section 2 — Data Flow Dependencies:**
- Crawler → chunk_splitter: crawled text is consumed by chunk splitter
- chunk_splitter → ingester: chunks are consumed by ingester for DB insertion
- ingester → registered/: post-insertion staging area (retention TBD)
- sqlite-vec: used by RAG pipeline's vector store for embedding similarity queries

**Section 3 — Unknowns:**
- Retention period for files under `registered/` is not confirmed within this document (needs verification against ingester implementation)

## Compatibility considerations

- Cross-references in other `docs/*.md` files must be updated if section headings change
- The "see `rag-src/` for the current file layout" pointer replaces the old inline file references; consumers should verify no stale cross-references remain
- No port number handling needed for this file (no literal port numbers present)

## Security considerations

No security impact — this is a documentation-only change. The removed ASCII tree contained no secrets or credentials.

## Rollback considerations

To rollback: restore the original file from git history (`git checkout HEAD -- docs/01_overview-files-02-rag.md`). The ASCII tree can be recovered from any prior commit before this change.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `docs/01_overview-files-02-rag.md` | Manual review + checker | `uv run python tools/check_docs_content_policy.py` && `uv run python tools/check_docs_structure.py docs/01_overview-files-02-rag.md` | Zero findings; structure check passes |

## Completion criteria

- `uv run python tools/check_docs_content_policy.py` reports zero findings for `docs/01_overview-files-02-rag.md`
- All ASCII tree-drawing characters (`├─`, `│`, `└─`) removed from the file
- Design-intent prose covers: component responsibility, owned state, allowed dependency direction, reason for process separation, reason for per-process config separation, and design boundaries
- The retention-period uncertainty for `registered/` files is documented as an actionable Unknown
- Related Documents and Keywords sections preserved without loss
- No cross-references broken in other `docs/*.md` files

## Out of scope

- Modifying `rules/env.md` (explicitly out-of-scope per Plan)
- Changing GV-021's report-only status
- Merging or deleting this file outright (File Split Rule's 400-line threshold)
- Deciding the auto-generated port-reference-table exemption (tracked in dcp001)
- Implementing the actual code changes to RAG pipeline components
- Resolving the retention-period unknown (deferred to separate investigation)

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove ASCII tree and per-file descriptions | Completed | 2026-09-09 | 2026-09-09 | Removed ASCII tree block (lines 26-34) |
| 2 | Add design-intent prose for RAG pipeline stages | Completed | 2026-09-09 | 2026-09-09 | Added prose for RAG Pipeline Stages, Data Flow Dependencies sections |
| 3 | Document retention-period unknown | Completed | 2026-09-09 | 2026-09-09 | Added Unknowns subsection noting retention period uncertainty |
| 4 | Run validation checkers | Completed | 2026-09-09 | 2026-09-09 | Zero findings; structure check passes |
| 5 | Update documentation per `docs/00_index.md` task-scope mapping | Completed | 2026-09-09 | 2026-09-09 | N/A: no docs/00_index.md task-scope mapping for docs/01_overview-files-02-rag.md |
| 6 | Validate documentation updates | Completed | 2026-09-09 | 2026-09-09 | N/A: no documentation changes to validate |
| 7 | Move the implementation procedure file to `implementations/done/` | Completed | 2026-09-09 | 2026-09-09 | Moved via git mv |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-001, REQ-003
- **Source issue**: issues/20260905-153715_dcp002_overview_file_structure_docs_redesign.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260908-210427_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260909-153145
- **Related target files**: docs/01_overview-files-02-rag.md
