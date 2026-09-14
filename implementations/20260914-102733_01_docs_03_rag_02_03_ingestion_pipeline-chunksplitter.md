## Goal

Correct `docs/03_rag_02_03_ingestion_pipeline-chunksplitter.md`'s Typed dict Evidence note — replace the incorrect defining file reference (`chunk_splitter.py` → `pipeline_utils.py`) and replace the blanket "not used as type annotations" claim with the accurate per-class distinction: `CrawlJsonPayload` is used as a type annotation in `crawl_persister.py`; `ChunkJsonPayload` is not, because `_build_chunk_payload()`'s return value combines `**metadata` unpacking with additional literal keys, which is incompatible with a strict `TypedDict` return annotation under current type-checker support.

## Scope

- **In-Scope**: Correcting the Evidence note in the single existing Typed dict section (lines 42-50) — fixing the defining file reference and replacing the blanket "not used" claim with the accurate per-class distinction plus the confirmed technical reason
- **Out-of-Scope**: Changing the Typed dict table rows themselves (class names and field descriptions are already correct), modifying source code, correcting the duplicate-section structure (already addressed by a sibling Plan)

## Assumptions

- The Typed dict table's field descriptions (required/optional fields) remain accurate — verified against `pipeline_utils.py:23-49`
- No other documentation file repeats the same misidentified class names (`CrawlFilePayload`/`ChunkOutputPayload`) — confirmed via repository-wide `rg` search scoped to `scripts/` in the Plan
- The Evidence note is the only part requiring correction within the Typed dict section; the table itself is already correct

## Design decisions

1. Only correct the Evidence note text — the Typed dict table rows were already fixed by a prior cycle (class names changed from `CrawlFilePayload`/`ChunkOutputPayload` to `CrawlJsonPayload`/`ChunkJsonPayload`)
2. Document the specific technical reason (`**metadata` unpacking incompatibility) rather than leaving a vague "not used" statement — this provides actionable context for future readers

## Alternatives considered

1. Enforce `TypedDict` usage in `_build_chunk_payload()` — rejected; the Plan explicitly adopts option 3 (document as interface specification with rationale)
2. Remove the TypedDict declarations entirely — rejected; they serve as interface specifications even though not used as strict return-type annotations

## Implementation

### Target file

`docs/03_rag_02_03_ingestion_pipeline-chunksplitter.md`

### Procedure

1. Read the Typed dict section (Evidence note at lines 42-50) to confirm current content
2. Edit the Evidence note to:
   a. Replace `chunk_splitter.py` with `pipeline_utils.py` as the declaring file
   b. Replace the blanket "not used as type annotations in the actual implementation within `chunk_splitter.py`" claim with the accurate per-class distinction
   c. Add the confirmed technical reason for `ChunkJsonPayload`'s non-usage

### Method

Edit the Evidence note paragraph (line 50) in-place. The correction modifies exactly one sentence within the Evidence note — no structural changes to the section.

### Details

Current Evidence note (line 50):

```
> Evidence: Explicit in code — `CrawlJsonPayload` and `ChunkJsonPayload` are declared as types in `chunk_splitter.py`, but they are not used as type annotations in the actual implementation within `chunk_splitter.py` (actual input/output is handled via `ChunkJsonRaw` from `pipeline_utils.py` or `dict[str, object]`).
```

Required corrections:

1. **Defining file**: Change `chunk_splitter.py` → `pipeline_utils.py` (appears twice in the sentence)
2. **Usage status**: Replace "they are not used as type annotations in the actual implementation within `chunk_splitter.py`" with the accurate per-class distinction
3. **Technical reason**: Add the `**metadata` unpacking incompatibility explanation for `ChunkJsonPayload`

Corrected Evidence note:

```
> Evidence: Explicit in code — `CrawlJsonPayload` and `ChunkJsonPayload` are declared as types in `pipeline_utils.py`. `CrawlJsonPayload` is used as a type annotation in `crawl_persister.py` (lines 71, 119). `ChunkJsonPayload` is not used as a type annotation anywhere — `_build_chunk_payload()` in `chunk_splitter.py` returns `dict[str, object]` (line 281) because its return value combines `**metadata` unpacking with additional literal keys, which is incompatible with a strict `TypedDict` return annotation under current type-checker support.
```

Reference files read (must NOT be modified):
- `scripts/rag/ingestion/pipeline_utils.py:23-49` — confirms TypedDict definitions
- `scripts/rag/ingestion/crawl_persister.py:71,119` — confirms `CrawlJsonPayload` usage
- `scripts/rag/ingestion/chunk_splitter.py:274-292` — confirms `**metadata` unpacking and `dict[str, object]` return type

## Compatibility considerations

N/A — documentation-only change affecting a single doc file's Evidence note. No code behavior, API contract, or runtime compatibility impact.

## Security considerations

N/A — documentation-only change.

## Rollback considerations

If the correction introduces an error, revert the single-line edit to restore the original Evidence note text. No downstream dependencies exist on this doc file's content.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| docs/03_rag_02_03_ingestion_pipeline-chunksplitter.md | Manual — cross-check corrected Evidence note against `pipeline_utils.py`/`crawl_persister.py`/`chunk_splitter.py` | Manual inspection | Every claim traceable to a specific code location |

## Completion criteria

- [ ] Evidence note cites `pipeline_utils.py` (not `chunk_splitter.py`) as the declaring file
- [ ] Evidence note states `CrawlJsonPayload` is used as a type annotation in `crawl_persister.py`
- [ ] Evidence note states `ChunkJsonPayload` is not used, citing the `**metadata`-unpacking incompatibility as the reason
- [ ] Typed dict table rows remain unchanged (class names and field descriptions already correct)

## Out of scope

- Source code changes to enforce or remove TypedDict usage
- Correction of any other documentation files that may also contain stale references
- Structural fix of the duplicate-section pattern (already tracked by a sibling Plan)

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Verify current Evidence note content and reference files | Pending | — | — | |
| 2 | Edit the Evidence note with corrected claims | Pending | — | — | |
| 3 | Manual review: confirm all claims trace to specific code locations | Pending | — | — | |

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
- **Requirement ID**: REQ-001 (correct defining file), REQ-002 (accurate per-class usage status with reason)
- **Source issue**: issues/20260913-183029_missing_chunksplitter_typedict_usage_mismatch.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260913-212731_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260914-102733
- **Related target files**: docs/03_rag_02_03_ingestion_pipeline-chunksplitter.md
