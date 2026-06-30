## Goal
- Confirm `use_rrf=False` retrieval quality degradation is already observable via diagnostic output, logs, and config docs — operators can detect dedup-only mode without additional changes.

## Scope
- **In-Scope**:
  - Verify `pipeline.py` outputs WARNING when `use_rrf=False`
  - Verify `get_diagnostics()["fusion_mode"]` returns `"dedup_only"` for `use_rrf=False`
  - Verify `/rag search --debug` shows `use_rrf=False` indicator
  - Verify docs `03_rag_03_query_pipeline.md` and `03_rag_05_configuration_and_operations.md` are complete
- **Out-of-Scope**:
  - Removal of `use_rrf=False`
  - RRF scoring formula changes

## Findings

### 1. Startup WARNING — Already present
`pipeline.py:L147-L150`:
```python
if not self._cfg.use_rrf:
    logger.warning(
        "use_rrf=False: RRF fusion disabled — retrieval quality degraded; "
        "use only for diagnostics or single-query testing"
    )
```

### 2. Config validator WARNING — Already present
`config_validator.py:L33-L36`:
```python
if not rag.get("use_rrf", True):
    warnings.append(
        "use_rrf=false degrades retrieval quality; use only for diagnostics"
    )
```
Logged at `pipeline.py:L134` as `rag config warning: {warning}`.

### 3. `get_diagnostics()["fusion_mode"]` — Already returns `"dedup_only"`
`pipeline.py:L565`:
```python
fusion_mode = "rrf" if self._cfg.use_rrf else "dedup_only"
```
Included in diagnostics at L594.

### 4. `/rag search --debug` output — Already shows `use_rrf=False` indicator
`cmd_rag_export.py:L89-L104`: passes `rrf_config={"use_rrf": ..., "rrf_k": ...}` to debug_fn
`output_port.py:L76-L81`: formats as `[debug] fusion: use_rrf=False (rank signal disabled)`

### 5. FusionStage log — Already present
`fusion.py:L19-L23`:
```python
logger.info(
    "FusionStage: dedup-only mode (use_rrf=False)"
    " — rank signal disabled, MQE provides no ranking benefit"
)
```

### 6. Docs completeness — Already complete
`03_rag_03_query_pipeline.md:L276-L280`: All four observability items documented:
- `/rag search --debug` shows `[debug] fusion: use_rrf=False (rank signal disabled)` ✓
- `get_diagnostics()["fusion_mode"]` returns `"rrf"` or `"dedup_only"` ✓
- Log: `INFO FusionStage: dedup-only mode (use_rrf=False) — rank signal disabled, MQE provides no ranking benefit` ✓
- Startup: `WARNING rag config warning: use_rrf=false degrades retrieval quality; use only for diagnostics` ✓

### 7. Quality tradeoff section — Already complete
`03_rag_03_query_pipeline.md:L255-L274`: Detailed quality impact explanation with table comparing `use_rrf=True` vs `use_rrf=False`.

## Conclusion
No changes needed. All four observability channels (startup WARNING, config validator WARNING, debug output, FusionStage log) already indicate `use_rrf=False` degradation, and the docs are complete.
