## Goal

Add a subsection to `docs/03_rag_05_4-error-handling-reference.md` documenting
`ChunkFormatError`'s place in the exception hierarchy, when it should be raised versus
its sibling exceptions, that callers should catch it specifically (not a base class), and
the one already-known hierarchy deviation — all grounded in `scripts/rag/exceptions.py`'s
actual class definitions/docstrings and the existing catch-site pattern. Per REQ-001.

## Scope

- Insert exactly one new subsection into `docs/03_rag_05_4-error-handling-reference.md`
  after line 55 (end of "Pipeline Utils — Artifact Validation") and before line 57
  ("## RagIngester")
- Cover four items requested in the Issue's Recommended Action:
  (1) ChunkFormatError's position in the hierarchy; (2) when to raise vs siblings;
  (3) that callers catch it specifically; (4) the one known hierarchy deviation
- Each item backed by `scripts/rag/exceptions.py`'s class definitions/docstrings or
  a cited catch-site location — no invented guidance beyond what the existing code
  pattern supports

## Assumptions

- Each sibling exception class's docstring in `scripts/rag/exceptions.py` (lines 15-36)
  is the authoritative statement of when that class should be raised — this Plan
  restates those docstrings rather than inferring additional distinguishing rules
- The repository-wide catch-site search performed for this Plan is exhaustive as of
  this Plan's writing — no caller catches `RagLayerError` or `ValueError` directly
  for `ChunkFormatError` handling
- The Plan's frozen `Implementation Target Files` section accurately reflects scope

## Design decisions

- Insert the new subsection immediately after "Pipeline Utils — Artifact Validation"
  (line 55) and before "## RagIngester" (line 57)
- Quote or closely paraphrase each sibling class's docstring rather than summarizing
  loosely, minimizing near-term drift risk if `scripts/rag/exceptions.py` is edited later
- Cite the specific catch-site file:line locations in Reference Files above
- Do NOT invent additional hierarchy deviations beyond the one documented at Implementation Notes line 79

## Alternatives considered

- Placing the subsection elsewhere in the document: rejected — inserting after
  "Pipeline Utils — Artifact Validation" keeps it as a natural continuation of the
  ChunkFormatError discussion rather than a disconnected addition
- Deriving new distinguishing rules for exception selection instead of citing docstrings:
  rejected — the Issue's Recommended Action asks for connecting existing accepted evidence,
  not inventing new claims

## Implementation

### Target file

`docs/03_rag_05_4-error-handling-reference.md`

### Procedure

1. **Locate the insertion point** — between line 55 (end of "Pipeline Utils — Artifact Validation")
   and line 57 ("## RagIngester")

2. **Insert the new subsection** covering all four acceptance criteria with explicit citations

### Method

1. Read `docs/03_rag_05_4-error-handling-reference.md` around lines 55-57
2. Read `scripts/rag/exceptions.py` around lines 11-36 (class hierarchy and docstrings)
3. Insert the new subsection after line 55
4. Verify all four acceptance criteria are met

### Details

**Step 1 — Locate the insertion point:**

Current content around lines 55-57:
```
For the full per-field Required/Nullable/Conditional classification referenced above,
see the canonical table in
[03_rag_02_03_ingestion_pipeline-chunksplitter.md](03_rag_02_03_ingestion_pipeline-chunksplitter.md).

## RagIngester
```

**Step 2 — Insert the new subsection:**

After edit, lines 55-80:
```
For the full per-field Required/Nullable/Conditional classification referenced above,
see the canonical table in
[03_rag_02_03_ingestion_pipeline-chunksplitter.md](03_rag_02_03_ingestion_pipeline-chunksplitter.md).

### ChunkFormatError Classification Guidance

#### Hierarchy position

`ChunkFormatError` is defined in `scripts/rag/exceptions.py` as a subclass of both
`RagLayerError` (the rag-layer base class) and `ValueError`. Its five sibling classes
under `RagLayerError` are:

| Class | Docstring-derived purpose |
|---|---|
| `EmbeddingSchemaError` | Raised when an embedding service response does not match expected schema |
| `PipelineValidationError` | Raised when a pipeline stage receives invalid configuration or input |
| `SearchQueryError` | Raised when a search query cannot be executed |
| `TokenizationError` | Raised when a tokenization step fails |
| `UnknownMetadataError` | Raised when metadata field has an unexpected value |

Each class should be raised when its docstring condition applies — e.g., use
`SearchQueryError` for an unexecutable search query, not a malformed chunk document.

#### Catch-site pattern

Every current caller in the repository catches `ChunkFormatError` specifically rather
than `RagLayerError` or `ValueError`:

- `scripts/rag/ingestion/chunk_splitter.py:197` — `except (FileNotFoundError, ChunkFormatError)`
- `scripts/rag/ingestion/file_routing.py:52,101` — `except ChunkFormatError`
- `scripts/rag/ingestion/ingester.py:217,235,348` — `except ChunkFormatError`
- `scripts/rag/ingestion/chunk_grouping.py:30` — `except ChunkFormatError`

New code should follow the same pattern: catch `ChunkFormatError` specifically, not its
base classes.

#### Known hierarchy deviation

The existing Implementation Notes (line 79) document one known edge case: `RagRerankError`
and `RagPipelineError` are defined outside `scripts/rag/exceptions.py` (in
`llm_prompts.py` and `pipeline.py` respectively), inheriting from `RuntimeError` rather
than `RagLayerError`. This fragmentation arose from three independent refactoring efforts
at different times, each introducing its own exception class without referencing the others.
No ADR or design document records a rationale for keeping them separate.

## RagIngester
```

## Compatibility considerations

- Documentation-only change: no production code affected
- Restating 6 classes' docstrings could drift from the actual docstring text if
  `scripts/rag/exceptions.py` is edited later without a corresponding doc update
  (documented as a risk in the Plan)
- If a future code change adds a catch site that catches `RagLayerError` or `ValueError`
  directly (deviating from the documented pattern), this subsection's AC-3 guidance would
  become stale (documented as a risk in the Plan)

## Security considerations

N/A: documentation update, no security-sensitive operations.

## Rollback considerations

- Revert the single insert step above to restore original document
- No data loss risk — only additive documentation change

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| docs/03_rag_05_4-error-handling-reference.md | Documentation structure/quality check | uv run python tools/check_docs_quality.py && uv run python tools/check_docs_structure.py docs/03_rag_05_4-error-handling-reference.md | No new structural/formatting findings |
| docs/03_rag_05_4-error-handling-reference.md | RAG-domain consistency check | uv run python tools/check_docs_consistency.py --domain rag | No new broken-link or drift findings |

## Completion criteria

- [ ] New subsection inserted between line 55 and line 57
- [ ] AC-1: States ChunkFormatError's position in the hierarchy (subclass of RagLayerError + ValueError, sibling to EmbeddingSchemaError/PipelineValidationError/SearchQueryError/TokenizationError/UnknownMetadataError)
- [ ] AC-2: For each of the 5 sibling classes, states the one-sentence docstring-derived distinction from ChunkFormatError
- [ ] AC-3: States that every current caller catches ChunkFormatError specifically, cites at least the 4 file paths in Reference Files above, recommends new code follow the same pattern
- [ ] AC-4: Cites the existing Implementation Notes (line 79) hierarchy deviation (RagRerankError/RagPipelineError defined outside scripts/rag/exceptions.py) as the one known edge case, without introducing any additional invented edge case
- [ ] `uv run python tools/check_docs_quality.py` reports no new findings
- [ ] `uv run python tools/check_docs_structure.py docs/03_rag_05_4-error-handling-reference.md` reports no new findings
- [ ] `uv run python tools/check_docs_consistency.py --domain rag` reports no new findings

## Out of scope

- Modifying `scripts/rag/exceptions.py` or any file that raises/catches ChunkFormatError
- Unifying the exception hierarchy (e.g. moving RagRerankError/RagPipelineError into
  scripts/rag/exceptions.py)
- Modifying any other documentation file

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: documentation validated by tooling |
| 3 | Run the validation sequence (rules/toolchain.md) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: docstring update in Phase 2 |

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
- **Requirement ID**: REQ-001
- **Source issue**: issues/20260913-183036_missing_ingestion_pipeline_chunkformaterror_classification.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260914-092842_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260914-121634
- **Related target files**: docs/03_rag_05_4-error-handling-reference.md
