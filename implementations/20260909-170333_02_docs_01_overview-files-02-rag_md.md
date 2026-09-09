## Goal

Rewrite `docs/01_overview-files-02-rag.md` to comply with `skills/DESIGN.md` Docs content policy — remove/retain — by removing ASCII directory trees and per-file descriptions, replacing them with design-intent prose covering component responsibility, owned state, allowed dependency direction, reason for process separation, and design boundaries. [REQ-001, REQ-003]

## Scope

**In scope**: Remove the ASCII directory tree (lines 26-34) and its inline per-file descriptions; replace with design-intent prose preserving existing design-intent subsections without loss of content.

**Out of scope**: Merging or deleting this file outright (File Split Rule's 400-line threshold); modifying any other file outside this one.

## Assumptions

- The RAG pipeline components map to distinct lifecycle phases (crawl → chunk → ingest) that should remain separate sections.
- The retention/cleanup note about `registered/` is operational detail worth preserving.
- Cross-references in other `docs/*.md` files will be updated separately if section headings change.

## Design decisions

- Keep the three-stage RAG pipeline structure (crawler, chunk-splitter, ingester) as prose section headers rather than a single flat list.
- Replace file enumeration with component-level descriptions of what each stage does, owns, and depends on.
- Preserve the retention/cleanup note since it describes an operational constraint, not file layout.

## Alternatives considered

- Consolidating all three stages into a single prose narrative: rejected because each stage has distinct ownership, failure modes, and restart semantics.
- Removing the entire `## 3. File Structure` section: rejected because the section title itself is misleading — the content is about RAG pipeline topology, not file listing.

## Implementation

### Target file

`docs/01_overview-files-02-rag.md`

### Procedure

1. Remove the ASCII directory tree block (lines 26-34) including the ```` text` fence markers.
2. Replace the removed content with prose describing the three thematic groups:
   a. Crawler output directory (`/opt/llm/rag-src/`) — describe what this component is responsible for, what state it owns, and which direction dependencies run.
   b. Chunk directory (`/opt/llm/rag-src/chunk/`) — describe what this component is responsible for, what state it owns, and which direction dependencies run.
   c. Registered directory (`/opt/llm/rag-src/registered/`) — describe what this component is responsible for, what state it owns, and which direction dependencies run.
3. Preserve the retention/cleanup note about `registered/` as-is since it describes an operational constraint.
4. Ensure Front Matter (title, area, tags, related, etc.) remains intact.

### Method

Apply `skills/python-design/SKILL.md` narrow usage: draw only the few relevant bullets from its broader 12-section template for the Design-decisions-family fields. For each thematic group, write a short paragraph covering:
- Component responsibility: what the group of components is responsible for
- State owned: what data or runtime state belongs to this group
- Allowed dependency direction: which direction dependencies run (reference `rules/env.md` Architecture's layer diagram, do not restate it)
- Reason for process separation: why this concern runs as its own process rather than in-process

### Details

Replace the current structure:

```
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
```

With prose such as:

```markdown
### Crawler Output

The `/opt/llm/rag-src/` directory holds raw crawled text files in timestamped JSON format. This component is responsible for capturing external content before any processing occurs. It owns transient crawl artifacts and is read-only during normal operation. Dependencies flow outward from this directory toward the chunk-splitter and ingester processes.

### Chunk Directory

The `/opt/llm/rag-src/chunk/` directory stores chunked text files indexed by stem and sequence number. This component is responsible for breaking down crawled documents into retrievable units. It owns chunk metadata and is read-write during the chunking phase but becomes read-only after ingestion begins. Dependencies flow inward from the chunk-splitter toward this directory.

### Registered Directory

The `/opt/llm/rag-src/registered/` directory contains files that have been moved by the ingester after successful database insertion. This component serves as a staging area confirming ingestion completion. It owns post-ingestion file state and is write-only during the ingestion phase. Dependencies flow inward from the ingester toward this directory.

### Vector Search Extension

The `/opt/llm/sqlite-vec/` directory holds the `vec0.so` loadable extension module for SQLite vector search. This component is responsible for enabling similarity search within SQLite tables. It owns a shared library binary and is read-only during normal operation. Dependencies flow from the RAG store implementations toward this extension.
```

Reference the current file layout with a single sentence: "see `scripts/rag/` for the current file layout."

## Compatibility considerations

Section heading changes may break cross-references in other `docs/*.md` files. If the rewritten section heading differs from `## 3. File Structure`, update links in:
- `01_overview-files-01-build.md`
- `01_overview-files-04-shared.md`
- `01_overview-files-05-config.md`
- `01_overview-files-06-misc.md`
- `01_overview-arch-01-process.md`

## Security considerations

No security impact. The change removes implementation-detail content (file paths, naming conventions) that could leak internal data flow details.

## Rollback considerations

Rolling back means restoring the ASCII tree blocks. Since no source code or production configuration is modified, rollback is straightforward: revert the file to its pre-modification state via git checkout.

## Validation plan

| Target | Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `docs/01_overview-files-02-rag.md` | Manual review + checker | `uv run python tools/check_docs_content_policy.py` && `uv run python tools/check_docs_structure.py docs/01_overview-files-02-rag.md` | Zero findings; structure check passes |

## Completion criteria

- No ASCII tree-drawing blocks (`├─`/`│`/`└─`) remain in the file
- No per-entry descriptions attached to tree entries remain
- Prose covers component responsibility, owned state, and allowed dependency direction for each thematic group
- Existing design-intent notes are preserved without loss of content
- `uv run python tools/check_docs_content_policy.py` reports zero findings for this file
- `uv run python tools/check_docs_structure.py docs/01_overview-files-02-rag.md` passes

## Out of scope

- Modifying any other file under `docs/`
- Deciding whether to merge this file with others (deferred until after rewrite)
- Updating cross-references in other `docs/*.md` files unless section headings change

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove ASCII tree and per-file descriptions | Pending | — | — | |
| 2 | Write design-intent prose for each thematic group | Pending | — | — | |
| 3 | Preserve existing design-intent subsections | Pending | — | — | |
| 4 | Validate with checkers | Pending | — | — | |

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
- **Generated at**: 20260909-170333
- **Related target files**: docs/01_overview-files-02-rag.md
