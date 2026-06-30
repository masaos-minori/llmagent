## Goal
- Confirm refiner fallback (`refiner_returned_empty`, `refiner_exception`) visibility across diagnostics, logs, and debug commands — no additional counters or diagnostic items needed.

## Scope
- **In-Scope**:
  - Verify `pipeline.py` `get_diagnostics()` returns `refiner_fallback_count`, `refiner_returned_empty`, `refiner_exception_count`
  - Verify `/rag search --debug` displays refiner fallback info
  - Verify `docs/03_rag_03_query_pipeline.md` documents refiner fallback visibility
  - Verify retry policy is documented (refiner exceptions are not retried)
- **Out-of-Scope**:
  - Refiner model changes
  - Augment stage redesign
  - Auto-retry implementation

## Findings

### 1. `get_diagnostics()` counters — Already present
`pipeline.py:L572-L603`:
```python
refiner_fallback_count = len(refiner_fallbacks)
refiner_returned_empty = sum(1 for r in refiner_fallbacks if str(r.get("fallback_reason", "")) == "refiner_returned_empty")
refiner_exception_count = sum(1 for r in refiner_fallbacks if str(r.get("fallback_reason", "")).startswith("refiner_exception:"))
...
"refiner_fallback_count": refiner_fallback_count,
"refiner_returned_empty": refiner_returned_empty,
"refiner_exception_count": refiner_exception_count,
"refiner_exception": refiner_exception_count > 0,
```

### 2. `/rag search --debug` output — Already displays refiner fallback
`cmd_rag_export.py:L148`: `[warn] refiner fallback: {reason}`
`cmd_rag_export.py:L166-L178`: Summary line `[refiner] fallback: N time(s)` with exception note

### 3. Docs refiner fallback visibility — Already documented
`03_rag_03_query_pipeline.md:L312-L321`:
- L312: `refiner_returned_empty` definition and common causes ✓
- L313: `refiner_exception: {e}` definition, "Not retried" note ✓
- L318: INFO level log `augment: refiner fallback (reason=...)` ✓
- L319: `/rag search` output `[warn] refiner fallback: <reason>` ✓
- L320: `/rag search --debug` stage results and summary line ✓
- L321: `get_diagnostics()` diagnostic keys ✓

### 4. Retry policy — Already documented as "Not retried"
`03_rag_03_query_pipeline.md:L313`: "Not retried." ✓
No `refiner_retry` config exists — refiner exceptions are intentionally not retried.

## Conclusion
No changes needed. Refiner fallback is fully visible across all channels (diagnostics, logs, debug output) with accurate reason classification and documented retry policy.
