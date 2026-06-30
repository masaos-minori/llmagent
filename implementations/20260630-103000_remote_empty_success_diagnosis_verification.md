## Goal
- Confirm HTTP RAG `remote_empty` (HTTP 200 but empty response) is correctly diagnosed as success rather than fallback, with no semantic confusion in `fallback_reason`.

## Scope
- **In-Scope**:
  - Verify `pipeline.py` `_http_result_kind = "remote_empty"` has `StageResult.fallback_reason = None`
  - Verify `SearchDiagnostics.http_result_kind = HttpResultKind.EMPTY`, `result_source = ResultSource.REMOTE` consistency
  - Verify `docs/03_rag_03_query_pipeline.md:L139` `remote_empty` definition is accurate
  - Verify `HttpResultKind` enum has `SUCCESS`, `EMPTY`, `ERROR`, `NOT_USED`
- **Out-of-Scope**:
  - HTTP fallback policy changes
  - Remote API response format changes

## Findings

### 1. `StageResult.fallback_reason` for `remote_empty` — Correctly `None`
`pipeline.py:L489`:
```python
fallback_reason=(http_fallback_reason if result is None else None),
```
When `result == ""` (not None), `fallback_reason = None` ✓

### 2. `SearchDiagnostics` for `remote_empty` — Correctly set
`pipeline.py:L500-L508`:
```python
if result is not None:  # True when result == ""
    self.last_search_diagnostics = dataclasses.replace(
        self.last_search_diagnostics,
        result_source=ResultSource.REMOTE,
        http_result_kind=HttpResultKind.EMPTY if result == "" else HttpResultKind.SUCCESS,
        remote_status_code=remote_status_code,
        remote_latency_ms=remote_latency_ms,
    )
```
- `result_source = REMOTE` ✓ (not FALLBACK)
- `http_result_kind = EMPTY` ✓

### 3. `_http_result_kind` string vs enum — Different concepts, no conflict
- `_http_result_kind` (string): raw HTTP response body state (`"remote_nonempty"`, `"remote_empty"`, `"in_process_fallback"`)
- `SearchDiagnostics.http_result_kind` (enum): semantic diagnostic meaning (`HttpResultKind.SUCCESS`, `EMPTY`, `ERROR`)
- `get_diagnostics()["http_result_kind"]` returns the string at L595

### 4. Debug output for `remote_empty` — Correctly labeled as success
`cmd_rag_export.py:L112-L120`:
```python
if debug and diag.result_source.value == "remote":
    kind = diag.http_result_kind.value
    kind_label = (
        "success (empty response — no in-process fallback)"
        if kind == "empty"
        else kind
    )
    print(f"[debug] http mode: result_source=remote http_result_kind={kind_label}")
```
When `HttpResultKind.EMPTY`: shows `http_result_kind=success (empty response — no in-process fallback)` ✓

### 5. Docs `remote_empty` definition — Accurate
`03_rag_03_query_pipeline.md:L139-L146`:
- `"remote_empty"` → status `"success"`, `fallback_reason = None` ✓
- "HTTP 200 but context field is `""` — valid empty result, not a fallback" ✓
- "`fallback_reason` is `None` for both `remote_nonempty` and `remote_empty` to prevent confusion with actual fallback events" ✓

### 6. `HttpResultKind` enum — Complete
All four values defined: `SUCCESS`, `EMPTY`, `ERROR`, `NOT_USED` ✓

## Conclusion
No changes needed. `remote_empty` is correctly diagnosed as success with `fallback_reason=None`, `result_source=REMOTE`, and `http_result_kind=EMPTY`. All observability channels (diagnostics, debug output, docs) accurately reflect this semantics.
