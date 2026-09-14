## Goal

Add a short note after `docs/03_rag_03_05_query_pipeline-augment-stages.md`'s `AugmentRefiner` Constructor Dependencies table, categorizing the optional parameters into two groups by consequence of omission: observational callbacks (`on_status`/`set_fetch_result`/`set_fallback_reason` — safe to omit, only lose visibility) versus functionally-required-when-used (`llm` — omitting it while `use_refiner=true` causes a runtime `ValueError`). Also clarify `search_diagnostics`'s default behavior (REQ-001).

## Scope

- Add one short categorization note after the existing Constructor Dependencies table (`docs/03_rag_03_05_query_pipeline-augment-stages.md:80-90`), distinguishing observational-callback parameters from the functionally-required `llm` parameter

## Assumptions

- Each optional parameter's use sites confirmed this cycle (single call site per callback, direct read for `llm`) are the complete set — confirmed by grepping `self._on_status`/`self._set_fetch_result`/`self._set_fallback_reason` across `augment.py`, not merely assumed

## Design decisions

1. Add a short categorization note rather than restructure the existing table — the table's per-parameter format is already correct and complete; a categorization is an orthogonal, additive grouping, not a replacement
2. Explicitly name the functional/observational distinction using the two groups' actual behavior (raises an exception vs. only loses observability), not a vaguer "important vs. less important" framing — the concrete consequence is what a developer deciding whether to wire up a dependency actually needs

## Alternatives considered

1. Restructuring the existing table to group parameters by consequence of omission — rejected because the table's per-parameter format is already correct and complete; a categorization is an orthogonal, additive grouping, not a replacement
2. Omitting `search_diagnostics`'s classification — rejected because its default (a fresh `SearchDiagnostics()`) has a distinct consequence (only affects starting values) that differs from both the observational callbacks and the `llm` parameter
3. Adding a separate diagram or flowchart — rejected because this document's existing style (tables, short prose) does not use diagrams elsewhere, and a diagram would be a larger, disproportionate addition for what the Issue's own evidence shows is a small gap (missing categorization, not a missing flow)

## Implementation

### Target file

`docs/03_rag_03_05_query_pipeline-augment-stages.md`

### Procedure

1. Re-confirm each parameter's use site
2. Add the categorization note after the Constructor Dependencies table

### Method

Phase 1: Preparation — re-confirm evidence line numbers
- Re-read `augment.py:46-67,80,110,146` to confirm each optional parameter's use site and functional/observational classification is unchanged (REQ-001; `docs/03_rag_03_05_query_pipeline-augment-stages.md`)

Phase 2: Core Logic — add the categorization note
- Add the note after the Constructor Dependencies table (line 90) (REQ-001; `docs/03_rag_03_05_query_pipeline-augment-stages.md`)

### Details

**Phase 1:** Verify via read/grep that:
- Section at `docs/03_rag_03_05_query_pipeline-augment-stages.md:80-90` contains the Constructor Dependencies table:
  - Line 84: `http` — Required
  - Line 85: `cfg` — Required
  - Line 86: `on_status` — Optional
  - Line 87: `set_fetch_result` — Optional
  - Line 88: `set_fallback_reason` — Optional
  - Line 89: `search_diagnostics` — Optional
  - Line 90: `llm` — Optional ("required when `use_refiner=true`")
- Callback use sites confirmed at `augment.py`:
  - Line 60: `self._on_status = on_status or (lambda _: None)`
  - Line 61: `self._set_fetch_result = set_fetch_result or (lambda _: None)`
  - Line 62: `self._set_fallback_reason = set_fallback_reason or (lambda _: None)`
  - Line 80: `set_fallback_reason=lambda _: self._set_fallback_reason(_)`
  - Line 110: `self._set_fetch_result(fetch_result)`
  - Line 146: `self._on_status`
- `llm` dependency confirmed functionally required at `augment.py:141` (`if self._llm is None: raise ValueError(...)`)
- `search_diagnostics` default confirmed at `augment.py:63` (`self._search_diagnostics = search_diagnostics or SearchDiagnostics()`)

**Phase 2:** Append the following note after line 90:

```markdown
Note: The optional parameters fall into two categories by consequence of omission:
- **Observational callbacks** (`on_status`, `set_fetch_result`, `set_fallback_reason`): purely informational — each forwards data to an external caller and has no effect on `AugmentRefiner`'s own HTTP-augment or refiner behavior if omitted. Leaving them as their no-op defaults means the caller loses visibility into those events but nothing else changes.
- **Functionally required** (`llm`): omitting `llm` while `run_refiner()` is invoked with `use_refiner=true` raises `ValueError` at call time; there is no silent degradation.
- **Functionally inert default** (`search_diagnostics`): its default value (a fresh `SearchDiagnostics()`) only determines the diagnostics object's starting state before the first update; omitting it has no other functional consequence.
```

## Compatibility considerations

This is a documentation-only additive change. No backward compatibility concerns. However, accurately documenting the categorization of optional parameters helps developers understand the actual consequences of wiring up or omitting each dependency, beyond what the per-parameter table cells already state individually.

## Security considerations

No security impact — documentation addition only. However, accurate documentation of dependency categorization helps developers avoid accidentally omitting the `llm` dependency when `use_refiner=true`, which would cause a runtime error.

## Rollback considerations

Simple revert: remove the added note. The underlying code remains unchanged.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| docs/03_rag_03_05_query_pipeline-augment-stages.md | Manual — cross-check categorization against `augment.py` | Manual inspection | Every claim traceable to a specific use site |

## Completion criteria

- [ ] The note states `on_status`/`set_fetch_result`/`set_fallback_reason` are purely observational and safe to omit with no functional consequence (REQ-001)
- [ ] The note states `llm` is functionally required whenever `run_refiner()` is invoked, distinguishing it from the observational callbacks (REQ-001)
- [ ] The note states `search_diagnostics`'s default only affects starting values (REQ-001)
- [ ] The existing Constructor Dependencies table and method descriptions remain unchanged

## Out of scope

- Rewriting the existing table (already accurate, per Background — this Plan adds a categorization note, not a table rewrite)
- Changing `AugmentRefiner`'s constructor signature or default-handling logic
- Restating the already-documented per-method behaviors (`run_http_augment()`, `run_refiner()` — lines 78-99, already accurate and unchanged by this Plan)

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: Re-confirm each parameter's use site | Pending | — | — | |
| 2 | Phase 2: Add the categorization note | Pending | — | — | |
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
- **Source issue**: issues/20260913-183023_missing_http_augment_constructor_deps_explanation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260913-211510_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260914-094003
- **Related target files**: docs/03_rag_03_05_query_pipeline-augment-stages.md
