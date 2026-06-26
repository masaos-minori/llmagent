## Goal

Clarify the diagnostics model for HTTP RAG `remote_empty` results so a successful empty remote response is not confused with fallback behavior — specifically, avoid using `fallback_reason` for success-empty cases.

## Scope

**In-Scope**:
- Decide whether `remote_empty` is represented as success with a non-fallback reason field or a separate explicit status/kind
- Avoid using `fallback_reason` for success-empty cases
- Update `/rag search --debug` output to show success-empty clearly
- Update docs to state that `remote_empty` does not run in-process fallback

**Out-of-Scope**:
- Changing HTTP fallback policy itself
- Changing remote API response format unless required

## Assumptions

1. `SearchDiagnostics.http_result_kind` already has an `EMPTY` kind — confirmed by models_result.py:24
2. `StageResult.fallback_reason` is typed as `str | None` and used for both fallback and non-fallback cases
3. Changing `StageResult` may be too invasive — need to evaluate impact

## Implementation

### Target file: scripts/rag/pipeline.py

**Procedure**: Remove fallback_reason for success-empty case.

**Method**: Modify pipeline.py to set fallback_reason=None instead of "http_remote_empty" for success-empty cases.

**Details**:
1. In pipeline.py:436-442, when `result == ""` (empty string from remote), set `fallback_reason = None` instead of `"http_remote_empty"`
2. The `_http_result_kind = "remote_empty"` field already tracks this distinction

### Target file: scripts/agent/commands/output_port.py

**Procedure**: Update debug output for success-empty.

**Method**: Modify debug output formatting in output_port.py.

**Details**:
1. Add explicit display of `http_result_kind` in `/rag search --debug` output
2. Show `result_source=remote` with `http_result_kind=empty` clearly as a success case

### Target file: docs/03_rag_03_query_pipeline.md

**Procedure**: Update documentation for remote_empty behavior.

**Method**: Clarify in documentation that `remote_empty` is a success case, not a fallback.

**Details**:
1. Clarify that `remote_empty` (HTTP 200 with no context) is a success case, not a fallback
2. State explicitly that `remote_empty` does not trigger in-process fallback

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| pipeline.py | Verify fallback_reason is None for success-empty | Review conditional logic | No fallback_reason set when result == "" and status is success |
| StageResult consumers | Verify no consumer relies on fallback_reason for success cases | Check all code reading fallback_reason from StageResult | Zero consumers relying on success-case fallback_reason |
| /rag search --debug | Verify debug output clearly distinguishes success-empty | Review debug output formatting | Success-empty shown with http_result_kind=empty, not as fallback |

## Risks

- **Risk**: Removing fallback_reason for success-empty may break consumers that check for this value | **Likelihood**: Low (only 2 references found in pipeline.py) | **Mitigation**: Verify all consumers before making the change; add a separate `success_reason` field if needed instead of removing fallback_reason | False
- **Risk**: Changing StageResult semantics may require updates across multiple files | **Likelihood**: Low-Medium | **Mitigation**: Audit all StageResult creation sites; only change where fallback_reason is set for success cases | False
