## Goal

Record the valid ranges, the enforced relations between the four chunk-size keys, and the `PipelineValidationError` raised on violation in the RAG configuration reference (`docs/21_rag/rag_05_01-configuration-reference.md`), so operators reading the reference see how the keys constrain one another.

## Scope
**Release unit**: N/A: not part of a release unit (documentation change validates alone).

## Assumptions
- The relations documented here must match exactly what `ChunkSplitter.__init__` enforces (row 01) and what `config/chunk_splitter.toml` states (row 03). Keep all three in sync.
- The current key VALUES are unchanged; only prose is added to the `config/chunk_splitter.toml` section.
- The upper bound for `md_snippet_max_chars` uses `<= max_chunk` (UNK-01 default).

## Design decisions
- Extend the existing two bullet points in the `config/chunk_splitter.toml` section (lines 43–44) with a third bullet that lists each enforced relation and the error. No new section header; the relations belong inside the existing chunk-splitter entry.

## Alternatives considered
- **A dedicated "Chunk-size validation" subsection.** Rejected: the reference's convention is one bullet-list per config file; a new subsection would break that pattern and duplicate the config-file comment (row 03).
- **A table of relations.** Rejected: there are only four relations plus one conditional; a bullet list matches the surrounding prose style better than a table.

## Compatibility considerations
N/A: prose addition only; the document's structure and front matter are unchanged.

## Security considerations
N/A: documentation only.

## Rollback considerations
N/A: revert the commit.

## Validation plan

## Implementation
### Target file
`docs/21_rag/rag_05_01-configuration-reference.md`

### Procedure
Add a third bullet to the `## config/chunk_splitter.toml` section (after line 44) describing the enforced relations and the error raised on violation. Do not touch any other section.

### Method
Insert this bullet immediately after the existing `md_index_enable` bullet (line 44):

```markdown
- The four chunk-size keys are validated as a unit in `ChunkSplitter.__init__` (`scripts/rag/ingestion/chunk_splitter.py`); a violation raises `PipelineValidationError` at construction. Enforced relations: `min_chunk >= 0`; `min_chunk <= max_chunk`; `chunk_overlap >= 0` and `chunk_overlap < max_chunk`; and, when `md_index_enable` is true, `min_chunk <= md_snippet_max_chars <= max_chunk`. The values themselves remain an unvalidated heuristic (NC-034) with no measured rationale; only the relations between them are enforced.
```

### Details
- Confirm the relations match row 01 exactly (`<=` upper bound for `md_snippet_max_chars`, per UNK-01) and the wording matches the config-file comment in row 03.
- The existing bullets already note that `min_chunk` also appears in `crawler.toml` (line 37) and that `md_index_enable`/`md_snippet_max_chars` control heading splitting; this bullet adds only the constraint layer.
- After editing, run `tools/check_docs_quality.py` against the file (per the plan's Step 3 validation gate) to confirm the doc structure remains valid.

## Completion criteria
- The `config/chunk_splitter.toml` section records each enforced relation and the `PipelineValidationError` raised on violation.
- The document structure remains valid under `tools/check_docs_quality.py`.

## Out of Scope
- Documenting the relations in `config/chunk_splitter.toml` (that is row 03).
- Re-tuning the chunk-size constants (NC-034).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | add relations bullet to config/chunk_splitter.toml section |
| 2 | Add or update tests per Validation plan | Pending | — | — | docs change; no tests |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | ruff + check_docs_quality.py |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | — |

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
- **Requirement ID**: `REQ-007` — record valid ranges, relations, and the `PipelineValidationError` raised on violation in the configuration reference
- **Source issue**: `issues/20261119-112015_ragcrv003_chunk-config-validation.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261119-144007_ragcrv003_chunk-config-validation.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261119-151106
- **Related target files**: `docs/21_rag/rag_05_01-configuration-reference.md`
