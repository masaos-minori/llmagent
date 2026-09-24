# Implementation Procedure: Add Deletion Column to File Lifecycle Table in Ingestion Pipeline Overview

## Goal

Add a Deletion column to the File Lifecycle table in `docs/03_rag_02_01_ingestion_pipeline-overview.md`, per REQ-002.

## Scope

- Modify `docs/03_rag_02_01_ingestion_pipeline-overview.md`
- Add a Deletion column to the existing File Lifecycle table
- Document the retention/deletion policy for `rag-src/registered/` files

## Assumptions

- The File Lifecycle table exists at lines 71-76 with "Path", "Created By", and "Content" columns
- The retention policy is: files are retained indefinitely for audit/debug purposes (per design rationale in the plan)
- The cleanup mechanism is out of scope for this phase (requires separate design decision)

## Design decisions

- Add a third column "Deletion" alongside "Created By" and "Content"
- For `rag-src/registered/` files, document: "Indefinite (audit trail); configurable retention planned"
- Keep the existing columns unchanged
- Use Japanese headers consistent with the document style

## Alternatives considered

- **Replace the entire table**: Would be disruptive and unnecessary. Adding a column preserves existing content.
- **Create a separate table**: Would fragment the lifecycle documentation. A single table provides better discoverability.

## Implementation

### Target file

`docs/03_rag_02_01_ingestion_pipeline-overview.md`

### Procedure

1. Read the current File Lifecycle table at lines 71-76
2. Add a Deletion column to the header row
3. Add deletion information to each row

### Method

**Step 1: Locate the File Lifecycle table**

Current content at lines 69-76:
```markdown
### File Lifecycle

| Path | Created By | Content |
|---|---|---|
| `{rag_src_dir}/{timestamp}-{slug}.json` | crawler.py | URL, Title, Language, Content, Code Blocks |
| `{rag_src_dir}/chunks/{timestamp}-{slug}-[0-N].json` | chunk_splitter.py | Chunk text, metadata |
```

**Step 2: Replace with updated table**

Replace the above block with:
```markdown
### File Lifecycle

| Path | Created By | Content | Deletion |
|---|---|---|---|
| `{rag_src_dir}/{timestamp}-{slug}.json` | crawler.py | URL, Title, Language, Content, Code Blocks | Operator intervention or periodic task (design pending) |
| `{rag_src_dir}/chunks/{timestamp}-{slug}-[0-N].json` | chunk_splitter.py | Chunk text, metadata | Deleted by RagIngester after successful registration |
| `rag-src/registered/{timestamp}-{slug}-[0-N].json` | file_routing.py (shutil.move) | Processed chunk data | Indefinite (audit trail); configurable retention planned |
```

### Details

- **REQ-002**: The File Lifecycle table must include deletion information
- **AC-002**: The File Lifecycle table includes deletion information

## Compatibility considerations

- The update adds a column to an existing Markdown table — does not modify existing content
- Uses mixed English/Japanese consistent with the existing document style
- The new row for `rag-src/registered/` extends the table rather than replacing existing rows

## Security considerations

- No security impact — this is a documentation update only

## Rollback considerations

- To revert, restore the original File Lifecycle table from git history

## Validation plan

| Target | Testing Strategy | Tool / Command | Expected Outcome |
|--------|-----------------|----------------|-----------------|
| Ingestion pipeline overview doc | Manual: File Lifecycle table review | Read File Lifecycle section | Table has Deletion column with policy details |

## Completion criteria

- [ ] `docs/03_rag_02_01_ingestion_pipeline-overview.md` contains a Deletion column in the File Lifecycle table
- [ ] All three rows have deletion information populated
- [ ] Existing columns (Path, Created By, Content) remain unchanged

## Out of scope

- Implementing a cron infrastructure for automated cleanup
- Changes to the FileRouter's routing logic
- Changes to the ingestion pipeline's core functionality
- Changes to the FTS indexing process
- Changes to the chunk storage format

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: REQ-002
- **Source issue**: issues/20260924-054355_rag006_missing-operational-guidance-rag-src-registered-file-lifecycle.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260924-080000_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260924-121326
- **Related target files**: docs/03_rag_02_01_ingestion_pipeline-overview.md
