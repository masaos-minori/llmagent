# Implementation Procedure: Remove stale common.toml references from RAG ingestion pipeline documentation

## Goal

Remove outdated meta-notes about `common.toml::embedding_dims` from `docs/03_rag_02_04_ingestion_pipeline-ingester.md`, since these notes document a problem that has already been resolved.

## Scope

- **In-Scope**: Removing two meta-notes about `common.toml::embedding_dims` being outdated from `docs/03_rag_02_04_ingestion_pipeline-ingester.md` (lines 163 and 237)
- **Out-of-Scope**: Restoring `config/common.toml`, modifying source code, changing configuration values, restructuring the databases/ directory

## Assumptions

- The document's meta-notes about `common.toml::embedding_dims` being outdated are stale and should be removed
- No other process depends on these notes existing in the documentation

## Design decisions

- The two meta-notes about `common.toml::embedding_dims` being outdated are self-referential stale content — they document a problem that was already resolved when `common.toml` was deleted
- Keeping these notes misleads readers into thinking there is an unresolved issue
- The actual `embedding_dims` value is now defined in `scripts/db/store_protocols.py::get_embedding_dims()` returning 1024

## Alternatives considered

- Replace the meta-notes with updated references pointing to `scripts/db/store_protocols.py::get_embedding_dims()` instead of removing them entirely
- Keep the meta-notes as historical context for why `embedding_dims` is not configurable

## Implementation

### Target file

`docs/03_rag_02_04_ingestion_pipeline-ingester.md`

### Procedure

Remove the two meta-notes about `common.toml::embedding_dims` being outdated from lines 163 and 237.

### Method

The meta-notes are comments ABOUT references that no longer exist. Since `common.toml` was deleted during the config migration, these notes are self-referentially stale and should be removed.

### Details

1. Verify file exists and has valid content (REQ-001; docs/03_rag_02_04_ingestion_pipeline-ingester.md)
   - Confirm `docs/03_rag_02_04_ingestion_pipeline-ingester.md` exists and is readable
   - Verify `grep -rn 'common\.toml' docs/03_rag_02_04_ingestion_pipeline-ingester.md` returns matches at lines 163 and 237
2. Confirm embedding_dims source is store_protocols.py (REQ-003; docs/03_rag_02_04_ingestion_pipeline-ingester.md)
   - Read `scripts/db/store_protocols.py` to confirm `get_embedding_dims()` returns 1024
   - Confirm this is the current source of truth for embedding dimension
3. Remove stale common.toml meta-notes from the document (REQ-002; docs/03_rag_02_04_ingestion_pipeline-ingester.md)
   - Edit line 163: remove `- docstring reference to \`common.toml::embedding_dims\` is outdated (\`common.toml\` does not exist).`
   - Edit line 237: remove `- docstring reference to \`common.toml::embedding_dims\` is outdated (\`common.toml\` does not exist).`
4. Validate result with check_docs_structure.py (REQ-004; docs/03_rag_02_04_ingestion_pipeline-ingester.md)
   - Run `uv run python tools/check_docs_structure.py "docs/**/*.md"` to confirm zero errors

## Compatibility considerations

- Removing these meta-notes does not affect compatibility with existing documentation or tooling
- The file is referenced by `check_docs_structure.py` as part of the documentation inventory

## Security considerations

- No security impact — the file is documentation-only and contains no sensitive information

## Rollback considerations

- Revert the edit to restore the two meta-notes if needed

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| docs/03_rag_02_04_ingestion_pipeline-ingester.md | Structural validation | uv run python tools/check_docs_structure.py "docs/**/*.md" | Zero errors |

## Completion criteria

- `docs/03_rag_02_04_ingestion_pipeline-ingester.md` に `common.toml` のメタ注釈が残っていない (REQ-002)
- 全ての設定参照が正しいソースを指している (REQ-003)
- Zero errors from `uv run python tools/check_docs_structure.py "docs/**/*.md"` after changes (REQ-004)

## Out of scope

- Updating the file's content if it becomes outdated relative to current database state
- Adding new databases to the file
- Restructuring the databases/ directory

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | — | Remove stale common.toml meta-notes |
| 2 | Add or update tests per Validation plan | Skipped | — | — | N/A — no test changes required |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Skipped | — | — | N/A — no changes to validate |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Skipped | — | — | N/A — no documentation updates needed |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-003, REQ-004
- **Source issue**: issues/20260923-100001_p002_common_toml_outdated_reference.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260923-152820_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260923-154223
- **Related target files**: docs/03_rag_02_04_ingestion_pipeline-ingester.md
