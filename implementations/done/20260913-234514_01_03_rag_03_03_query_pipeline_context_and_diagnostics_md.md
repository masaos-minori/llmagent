## Goal

Correct the Boundary Conditions note in `docs/03_rag_03_03_query_pipeline-context-and-diagnostics.md` section 4.2 — both `SearchDiagnostics.http_result_kind` and `get_diagnostics()["http_result_kind"]` share the same `HttpResultKind` enum vocabulary; the three string literals exist only as an internal implementation detail inside `HttpAugment`, never exposed via `get_diagnostics()`'s output (REQ-001).

## Scope

- Rewrite the Boundary Conditions note (lines 54-59) in `docs/03_rag_03_03_query_pipeline-context-and-diagnostics.md` section 4.2 to describe the actual, current relationship between `SearchDiagnostics.http_result_kind` and `get_diagnostics()["http_result_kind"]` — both are `HttpResultKind` enum values; the three string literals exist only as an internal implementation detail inside `HttpAugment`, never exposed via `get_diagnostics()`

## Assumptions

- No other documentation file repeats the same disconfirmed claim about `RagPipeline._run_http_augment()`/`RagPipeline._http_result_kind` (only this one note was found citing them)
- `_map_http_result_kind()`'s mapping (`http_augment.py:18-22`) is exhaustive over every value `HttpAugment._http_result_kind` can take, confirmed by direct reading of both the mapping dict and the `Literal` type it's derived from

## Design decisions

1. Correct the note rather than leave it as a resolved, no-action issue — an inaccurate warning actively misleads future readers into over-engineering defensive handling for a non-existent vocabulary mismatch, so correcting it is the right-sized action
2. Explicitly attribute the string-literal representation to `HttpAugment` (not `RagPipeline`) in the corrected text — this cycle found the documentation's method/attribute citations were not just imprecise but referred to a different class entirely, so the correction should be specific about ownership to prevent the same confusion recurring

## Alternatives considered

1. Renaming either field — rejected because the Issue's Recommended Action offers this as an option; not needed once the fields are confirmed to already share one vocabulary at the public-API boundary
2. Unifying `SearchDiagnostics.http_result_kind` and `get_diagnostics()["http_result_kind"]` into a single field — rejected because they are already the same enum value at two different points in the data flow (no further unification is needed)

## Implementation

### Target file

`docs/03_rag_03_03_query_pipeline-context-and-diagnostics.md`

### Procedure

1. Confirm the conversion mapping and non-existent citations
2. Rewrite the Boundary Conditions note

### Method

Phase 1: Preparation — confirm evidence line numbers
- Re-confirm `_map_http_result_kind()`'s mapping (`http_augment.py:18-32`) and `get_diagnostics()`'s normalization (`pipeline.py:342-366`) are still current before writing the corrected note (REQ-001; `docs/03_rag_03_03_query_pipeline-context-and-diagnostics.md`)

Phase 2: Core Logic — correct documentation claims
- Replace the note at lines 54-59 with corrected text describing the shared `HttpResultKind` vocabulary and the internal-only string-literal representation in `HttpAugment` (REQ-001; `docs/03_rag_03_03_query_pipeline-context-and-diagnostics.md`)

### Details

**Phase 1:** Verify via read/grep that:
- `get_diagnostics()` at `pipeline.py:342-366` normalizes `http_result_kind_raw` via `_map_http_result_kind()` before returning — always returns `HttpResultKind` enum, never raw string literal
- `_map_http_result_kind()` at `http_augment.py:18-32` maps:
  - `"remote_nonempty" → HttpResultKind.SUCCESS`
  - `"remote_empty" → HttpResultKind.EMPTY`
  - `"in_process_fallback" → HttpResultKind.ERROR`
  - `None → HttpResultKind.NOT_USED`
- `HttpResultKind` at `models_result.py:29-35` is a StrEnum with values: `SUCCESS`, `EMPTY`, `ERROR`, `NOT_USED`
- `SearchDiagnostics.http_result_kind` at `models_result.py:109` is typed `HttpResultKind = HttpResultKind.NOT_USED`
- `PipelineDiagnostics.http_result_kind` at `diagnostics.py:68` is typed `HttpResultKind | None`
- `RagPipeline._run_http_augment()` and `RagPipeline._http_result_kind` do NOT exist anywhere in `pipeline.py` — confirmed via grep

**Phase 2:** Replace lines 54-59 with the following corrected text:

```markdown
Both `SearchDiagnostics.http_result_kind` and `get_diagnostics()["http_result_kind"]` carry the same `HttpResultKind` enum value by the time either is read from `get_diagnostics()` or `last_search_diagnostics`. The three string literals (`"remote_nonempty"` / `"remote_empty"` / `"in_process_fallback"`) exist only as an internal implementation detail inside `HttpAugment` (`http_augment.py`): `HttpAugment._http_result_kind` stores these literals, but `_map_http_result_kind()` converts them to the `HttpResultKind` enum before either public field is set — the string literals never reach a caller reading either field.
```

Also update the table row at line 75:
- Change `http_result_kind` type from `str \| None` to `HttpResultKind`
- Update description to reflect the enum vocabulary

## Compatibility considerations

This is a documentation-only correction. No backward compatibility concerns.

## Security considerations

No security impact — documentation correction only. However, accurate documentation of a security-relevant function's behavior is important for readers who may rely on it to understand the pipeline's defense posture.

## Rollback considerations

Simple revert: restore the original Boundary Conditions note and table row. The underlying code remains unchanged.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| docs/03_rag_03_03_query_pipeline-context-and-diagnostics.md | Manual — verify corrected note's claims against cited code | Manual inspection of `pipeline.py:342-366`, `http_augment.py:18-32` | Note accurately describes current behavior |

## Completion criteria

- [ ] The note no longer claims `get_diagnostics()["http_result_kind"]` returns the three string literals (`"remote_nonempty"` etc.) (REQ-001)
- [ ] The note states both `SearchDiagnostics.http_result_kind` and `get_diagnostics()["http_result_kind"]` carry `HttpResultKind` enum values (REQ-001)
- [ ] The note correctly attributes the string-literal representation to `HttpAugment` (not `RagPipeline`) and cites `_map_http_result_kind()` as the conversion mechanism (REQ-001)

## Out of scope

- Renaming either field (the Issue's Recommended Action offers this as an option; not needed once the fields are confirmed to already share one vocabulary at the public-API boundary)
- Changing `HttpAugment._http_result_kind`'s internal string-literal representation or the `_map_http_result_kind()` conversion function itself
- Unifying `SearchDiagnostics.http_result_kind` and `get_diagnostics()["http_result_kind"]` into a single field (they are already the same enum value at two different points in the data flow)

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: Confirm conversion mapping and non-existent citations | Completed | — | — | |
| 2 | Phase 2: Rewrite Boundary Conditions note | Completed | — | — | |
| 3 | Verification: manual review | Completed | — | — | |

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
- **Source issue**: issues/20260913-183010_two_http_result_kind_fields_confusion.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260913-204849_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260913-234514
- **Related target files**: docs/03_rag_03_03_query_pipeline-context-and-diagnostics.md
