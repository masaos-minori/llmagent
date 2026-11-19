## Goal

State in the error-handling reference that a size-rule discard is not an error and how it is reported (REQ-005, AC-004).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The discard is reported as a per-file WARNING (zero chunks) or INFO (kept + discarded) by `scripts/rag/ingestion/chunk_splitter.py` `process_file`, not as an ERROR.
- A non-blocking caveat: the structured discard fields are attached via `extra=`; the current `_JsonFormatter` does not serialize arbitrary extra fields to the JSON line, so they are observable on the record and message text, consistent with existing structured fields.

## Design decisions
- Add a row to the `ChunkSplitter` error table in `docs/21_rag/rag_05_04-error-handling-reference.md` distinguishing a size-rule discard from an error.

## Alternatives considered
- N/A: single, well-scoped documentation addition.

## Implementation
### Target file
`docs/21_rag/rag_05_04-error-handling-reference.md`

### Procedure
Add a row to the `## ChunkSplitter` table (after the existing rows):

| Size-rule discard (content below `min_chunk`) | Not an error; WARNING (zero chunks) or INFO (kept + discarded) per-file discard summary with `discard_reason="below_min_chunk"`; continue |

Add a short note under the table pointing to `rag_05_03-logging.md` for the record shape and clarifying that a discard is an observability event, not a failure, and does not abort the file.

### Details
- Do not alter the existing error rows; only add the discard row and note.
- Keep the wording consistent with the logging reference's trigger/level description.

## Compatibility considerations
- N/A: documentation-only; no code, schema, or behavior impact.

## Security considerations
- N/A.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- Structure/quality: `uv run python tools/check_docs_quality.py`.
- Structure/reachability: `uv run python tools/check_docs_structure.py docs/21_rag/rag_05_04-error-handling-reference.md`.
- Content policy: `uv run python tools/check_docs_content_policy.py`.
- Japanese check: `uv run python tools/check_docs_japanese.py` (must report none).
- Domain consistency: `uv run python tools/check_docs_consistency.py --domain rag`.

## Completion criteria
The error-handling reference states that a size-rule discard is not an error and names how it is reported; all documented RAG-domain checks pass.

## Out of Scope
- Logging reference (`rag_05_03-logging.md`); covered in its own procedure.
- Code and test changes.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | State that a size-rule discard is not an error and how it is reported | Completed | 20261119-175837 | 20261119-175837 | Add ChunkSplitter table row + note |
| 2 | Update documentation (RAG-domain checks) | Completed | 20261119-175837 | 20261119-175837 | check_docs_quality/structure/content_policy/japanese/consistency |

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
- **Requirement ID**: REQ-005 (state in the error-handling reference that a discard is not an error)
- **Source issue**: issues/20261119-112016_ragcrv004_silent-chunk-discard-logging.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261119-164553_ragcrv004_silent-chunk-discard-logging.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261119-170454
- **Related target files**: `docs/21_rag/rag_05_04-error-handling-reference.md`
