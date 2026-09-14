## Goal

Add a catch-guidance note to `docs/03_rag_05_4-error-handling-reference.md`'s Pipeline Utils section stating that callers should catch the specific `ChunkFormatError` class, not its base `RagLayerError`, consistent with every actual catch site in the codebase.

## Scope

- **In-Scope**: Adding one short note after the existing raise-condition table (line 51) stating that all actual callers catch `ChunkFormatError` specifically, not the `RagLayerError` base class
- **Out-of-Scope**: Changing any `except` clause's actual exception type (this Plan documents the existing, consistent pattern, it does not change code); addressing the broader exception-hierarchy fragmentation (already tracked by a sibling Plan, `plans/20260913-205453_plan.md`); inventing an "edge case where the wrong exception type is used" — this cycle's search found none

## Assumptions

- The `rg` search across `scripts/rag/ingestion/` found the complete set of `ChunkFormatError` catch sites — no catch site elsewhere in the repository catches it or `RagLayerError` in a way that would contradict this Plan's claim
- The existing hierarchy-position statement (line 35) and raise-condition table (lines 42-51) remain accurate and unchanged

## Design decisions

1. State the catch guidance as an observed, confirmed practice (citing all 4 actual catch sites) rather than a prescriptive rule invented for this Plan — the codebase already demonstrates the correct pattern consistently
2. State plainly that no wrong-exception-type edge case was found, rather than omitting point 4 silently

## Alternatives considered

1. Prescribe catching `RagLayerError` instead — rejected; the codebase's own consistent practice is to catch `ChunkFormatError` specifically, and prescribing a different pattern would conflict with existing code
2. Omit the "no wrong-exception-type edge case" finding — rejected; this tells a future reader the search was performed and came back clean

## Implementation

### Target file

`docs/03_rag_05_4-error-handling-reference.md`

### Procedure

1. Read the Pipeline Utils section (lines 35-55) to confirm current content and identify insertion point
2. Re-confirm all catch sites via `rg "except.*ChunkFormatError"` across `scripts/rag/ingestion/`
3. Add the catch-guidance note after line 51 (after the raise-condition table, before the cross-reference paragraph starting at line 53)
4. Manual review: confirm each cited catch site's line number and file are accurate

### Method

Insert a new paragraph between the raise-condition table (ending at line 51) and the cross-reference paragraph (starting at line 53). The note is a single prose paragraph — no structural changes to the section.

### Details

Current content around insertion point:

```markdown
| Crawl artifact only: `content` is empty and `code_blocks` is also empty (cross-field rule) | `ChunkFormatError` |

For the full per-field Required/Nullable/Conditional classification referenced above,
see the canonical table in
[03_rag_02_03_ingestion_pipeline-chunksplitter.md](03_rag_02_03_ingestion_pipeline-chunksplitter.md).
```

Required addition (inserted after line 51, before the "For the full..." paragraph):

```markdown
**Catch guidance**: Callers should catch `ChunkFormatError` specifically, not the broader `RagLayerError` base class. This matches every actual catch site in the codebase — `chunk_grouping.py:30`, `chunk_splitter.py:197` (as part of `(FileNotFoundError, ChunkFormatError)`), `file_routing.py:52,101`, and `ingester.py:217,235,348`. No catch site was found using the wrong exception type as of this cycle's search.
```

Reference files read (must NOT be modified):
- `scripts/rag/ingestion/chunk_grouping.py:30` — confirms `except ChunkFormatError:`
- `scripts/rag/ingestion/chunk_splitter.py:197` — confirms `except (FileNotFoundError, ChunkFormatError)`
- `scripts/rag/ingestion/file_routing.py:52,101` — confirms two `except ChunkFormatError:` sites
- `scripts/rag/ingestion/ingester.py:217,235,348` — confirms three `except ChunkFormatError:` sites

## Compatibility considerations

N/A — documentation-only change affecting a single doc file. No code behavior, API contract, or runtime compatibility impact.

## Security considerations

N/A — documentation-only change.

## Rollback considerations

If the addition introduces an error, revert the inserted paragraph to restore the original text. No downstream dependencies exist on this doc file's content.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| docs/03_rag_05_4-error-handling-reference.md | Manual — verify cited catch sites against source | `rg "except.*ChunkFormatError" scripts/rag/ingestion/` | Every cited site matches the actual code |

## Completion criteria

- [ ] The note states callers should catch `ChunkFormatError` specifically, not `RagLayerError`
- [ ] The note cites the actual catch sites confirming this practice (`chunk_grouping.py:30`, `chunk_splitter.py:197`, `file_routing.py:52,101`, `ingester.py:217,235,348`)
- [ ] The existing hierarchy-position statement (line 35) and raise-condition table (lines 42-51) remain unchanged

## Out of scope

- Source code changes to modify exception handling
- Correction of any other documentation files that may also contain stale references
- Addressing the broader exception-hierarchy fragmentation (tracked separately)

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Verify current Pipeline Utils section and reconfirm catch sites | Completed | — | 20260914-120200 | Confirmed all 4 catch sites match the procedure's claims; no except RagLayerError found |
| 2 | Insert catch-guidance note after raise-condition table | Completed | — | 20260914-120200 | Added Catch guidance paragraph citing all confirmed catch sites |
| 3 | Manual review: confirm all cited catch sites match actual code | Completed | — | 20260914-120200 | All claims verified against source |

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
- **Requirement ID**: REQ-001 (catch-guidance note citing all confirmed catch sites)
- **Source issue**: issues/20260913-183031_missing_pipeline_utils_chunkformaterror_classification.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260913-213415_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260914-103348
- **Related target files**: docs/03_rag_05_4-error-handling-reference.md
