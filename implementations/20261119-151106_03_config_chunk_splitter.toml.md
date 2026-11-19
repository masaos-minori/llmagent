## Goal

Document the required relations between the four chunk-size keys in `config/chunk_splitter.toml` so operators see, next to the values, how the keys constrain one another and that the pipeline rejects violations at construction.

## Scope
**Release unit**: N/A: not part of a release unit (documentation/config change validates alone).

## Assumptions
- The current key VALUES are unchanged; only comments are added (re-tuning the constants is out of scope — NC-034).
- The relations documented here must match exactly what `ChunkSplitter.__init__` enforces (row 01). Keep the two in sync.

## Design decisions
- Add a comment block directly above the four chunk-size keys describing each enforced relation and the `PipelineValidationError` raised on violation. TOML comments are the only mechanism; no new keys are introduced.

## Alternatives considered
- **A separate keys section header.** Rejected: the keys already sit together; an inline comment block keeps the relations adjacent to the values without restructuring the file.

## Compatibility considerations
N/A: comments only; the parsed config is byte-identical in structure.

## Security considerations
N/A: documentation only.

## Rollback considerations
N/A: revert the commit.

## Validation plan

## Implementation
### Target file
`config/chunk_splitter.toml`

### Procedure
Replace the existing three-line comment above `min_chunk` (lines 5–7) with an expanded comment block that states the enforced relations and the error, then keep the four key assignments unchanged.

### Method
Set the block above `min_chunk = 40` to:

```toml
# Chunk-size group. Validated as a unit in ChunkSplitter.__init__
# (scripts/rag/ingestion/chunk_splitter.py); a violation raises
# PipelineValidationError at construction. Enforced relations:
#   - min_chunk >= 0
#   - min_chunk <= max_chunk
#   - chunk_overlap >= 0 and chunk_overlap < max_chunk
#   - when md_index_enable is true:
#       min_chunk <= md_snippet_max_chars <= max_chunk
# The values themselves remain an unvalidated heuristic (NC-034) with no
# measured rationale; only the relations between them are enforced.
min_chunk = 40
max_chunk = 500
chunk_overlap = 50

md_index_enable = false
md_snippet_max_chars = 600
```

### Details
- Confirm the relations match row 01 exactly (`<=` upper bound for `md_snippet_max_chars`, per UNK-01).
- Verify the file still parses after editing: `uv run python -c "import tomllib; tomllib.load(open('config/chunk_splitter.toml','rb'))"`.

## Completion criteria
- The four chunk-size keys are followed by a comment stating each enforced relation and the `PipelineValidationError` raised on violation.
- The config still parses and its key values are unchanged.

## Out of Scope
- Re-tuning the chunk-size constants (NC-034).
- Documenting the relations in the configuration reference (that is row 04).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | add relation comments above the four keys |
| 2 | Add or update tests per Validation plan | Pending | — | — | docs/config change; no tests |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | ruff + TOML parse check |
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
- **Requirement ID**: `REQ-006` — document the required relations between the four chunk-size keys
- **Source issue**: `issues/20261119-112015_ragcrv003_chunk-config-validation.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261119-144007_ragcrv003_chunk-config-validation.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261119-151106
- **Related target files**: `config/chunk_splitter.toml`
