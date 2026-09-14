## Goal

Add a dedicated "Cross-Field Validation Rules" subsection to `docs/03_rag_02_03_ingestion_pipeline-chunksplitter.md` documenting the single confirmed cross-field rule (crawl artifacts' `content`/`code_blocks` relationship), its rationale (traced to `.py`-file handling in the crawler), and valid/invalid payload examples — while correcting the Issue's premise that multiple such rules exist (REQ-001).

## Scope

- Add one dedicated subsection documenting the single confirmed rule (`content` empty ⇔ `code_blocks` non-empty for crawl artifacts), its rationale, and example payloads

## Assumptions

- No other cross-field rule exists among the crawl/chunk artifact fields beyond the one confirmed this cycle — confirmed by reading both full field tables and their validators, not merely assumed from the Issue's own framing
- `CrawlPersister.save()`'s `.py`-file handling remains the only crawl-artifact producer path that legitimately produces empty `content` with non-empty `code_blocks`

## Design decisions

1. Cross-reference the existing "internal fields set vs. read" note (lines 273-277) rather than duplicate it in the new subsection — that note already answers the Issue's 2nd requested point clearly; restating it would create two sources of truth for the same fact
2. State plainly that only one cross-field rule exists, rather than write the subsection as if searching for more rules were still open — this cycle's investigation was exhaustive over both field tables, so this is a confirmed fact, not an assumption

## Alternatives considered

1. Inventing additional cross-field rules that do not exist — rejected because this cycle's investigation found exactly one such rule
2. Moving or restructuring the existing "internal fields set vs. read" note (already clearly stated at lines 273-277) — rejected because this Plan cross-references it rather than duplicating it in the new subsection
3. Correcting this file's duplicate-section numbering (`## 3a.`/`## 3b.`) — rejected because it is already addressed by a sibling Plan (`plans/20260913-202903_plan.md`, this cycle)

## Implementation

### Target file

`docs/03_rag_02_03_ingestion_pipeline-chunksplitter.md`

### Procedure

1. Re-confirm the rule and its rationale
2. Add the subsection after the crawl/chunk artifact tables

### Method

Phase 1: Preparation — re-confirm evidence line numbers
- Re-read `pipeline_utils.py:128-145` and `crawl_persister.py:69-77` to confirm the rule's enforcement and rationale are unchanged (REQ-001; `docs/03_rag_02_03_ingestion_pipeline-chunksplitter.md`)

Phase 2: Core Logic — add the subsection
- Add the "Cross-Field Validation Rules" subsection after line 299 (REQ-001; `docs/03_rag_02_03_ingestion_pipeline-chunksplitter.md`)

### Details

**Phase 1:** Verify via read/grep that:
- Section at `docs/03_rag_02_03_ingestion_pipeline-chunksplitter.md:190` states "empty string allowed only when `code_blocks` is non-empty (cross-field rule)"
- Cross-field rule's exact enforcement confirmed at `pipeline_utils.py:125-128`:
  ```python
  if not content and not code_blocks:
      raise ChunkFormatError(
          "crawl: empty 'content' requires non-empty 'code_blocks'"
      )
  ```
- Rule's rationale traced to `crawl_persister.py:69-77`:
  - Line 69: "# Python files are stored as code blocks so the code chunker applies."
  - Line 70: `is_python = path.suffix == ".py"`
  - Line 76: `"content": "" if is_python else content`
  - Line 77: `"code_blocks": [content] if is_python else []`
- Confirmed exactly one such rule exists via full reading of both field tables (lines 260-295)

**Phase 2:** Append the following subsection after line 299:

```markdown
#### Cross-Field Validation Rules

There is exactly one cross-field validation rule among the crawl/chunk artifact fields documented above. It applies only to crawl artifacts:

- **Rule**: For crawl artifacts, `content` may be an empty string only when `code_blocks` is non-empty. If both are empty, the payload is rejected with `ChunkFormatError`.
- **Rationale**: Traced to `CrawlPersister.save()`'s `.py`-file handling (`crawl_persister.py:69-77`). When processing a `.py` file, the crawler stores the source code in `code_blocks=[content]` with `content=""`, allowing the code chunker to apply. The cross-field rule permits this legitimate empty-content case while rejecting a genuinely broken/incomplete crawl result (both fields empty).
- **Chunk artifacts**: No equivalent exception — `content` is required and must be non-empty for chunk artifacts.
- **Valid example** (`.py` file): `{"content": "", "code_blocks": ["def foo(): ..."]}`
- **Invalid example**: `{"content": "", "code_blocks": []}` → rejected with `ChunkFormatError("crawl: empty 'content' requires non-empty 'code_blocks'")`
```

## Compatibility considerations

This is a documentation-only additive change. No backward compatibility concerns. However, accurately documenting the cross-field validation rule helps developers understand why certain payload combinations are accepted or rejected during ingestion.

## Security considerations

No security impact — documentation addition only. However, accurate documentation of validation rules is important for understanding how the pipeline protects against malformed or incomplete crawl results.

## Rollback considerations

Simple revert: remove the added subsection. The underlying code remains unchanged.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| docs/03_rag_02_03_ingestion_pipeline-chunksplitter.md | Manual — cross-check new subsection against `pipeline_utils.py`/`crawl_persister.py` | Manual inspection | Every claim traceable to a specific code location |

## Completion criteria

- [ ] The new subsection states crawl artifacts' `content` may be empty only when `code_blocks` is non-empty, and cites `pipeline_utils.py`'s enforcement (REQ-001)
- [ ] The subsection states the rationale: `.py` files store source in `code_blocks` with `content=""`, per `CrawlPersister.save()` (REQ-001)
- [ ] The subsection states chunk artifacts have no equivalent exception (REQ-001)
- [ ] The subsection includes one valid and one invalid example payload (REQ-001)
- [ ] The existing field tables and internal-fields note (lines 260-299) are unchanged

## Out of scope

- Inventing additional cross-field rules that do not exist (this cycle's investigation found exactly one — see Background)
- Moving or restructuring the existing "internal fields set vs. read" note (already clearly stated at lines 273-277 — this Plan cross-references it rather than duplicating it in the new subsection)
- Correcting this file's duplicate-section numbering (`## 3a.`/`## 3b.` — already addressed by a sibling Plan, `plans/20260913-202903_plan.md`, this cycle)

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: Re-confirm the rule and its rationale | Pending | — | — | |
| 2 | Phase 2: Add the subsection | Pending | — | — | |
| 3 | Verification: manual review | Pending | — | — | |

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
- **Source issue**: issues/20260913-183022_missing_pipeline_utils_cross_field_rules.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260913-211325_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260914-092713
- **Related target files**: docs/03_rag_02_03_ingestion_pipeline-chunksplitter.md
