# Issue: Missing Documentation for RAG Search Stages Fusion Quality Trade-off Warning

## Summary
`docs/03_rag_03_04_query_pipeline-search-stages.md` warns that `use_rrf=False` degrades quality but doesn't quantify the degradation or provide guidance on acceptable thresholds.

## Evidence
- File: `docs/03_rag_03_04_query_pipeline-search-stages.md`, section 5.3
- Text: "> **Warning:** `use_rrf=False` is NOT a harmless fallback; it represents a **significant degradation in quality**."
- The warning is qualitative but lacks quantitative data on how much quality degrades
- No guidance on when it's acceptable to disable RRF

## Impact
- Operators making performance trade-offs lack data to justify disabling RRF
- Debugging degraded results may not reveal RRF as the cause
- Performance tuning efforts may waste time optimizing RRF-disabled pipelines

## Recommended Action
Add quantitative analysis to the warning:
1. Benchmark data showing quality difference between RRF-enabled and disabled modes
2. Specific metrics (e.g., recall@k, precision@k) comparing both modes
3. Thresholds for when RRF can be safely disabled (e.g., latency-sensitive operations)
4. References to any ADRs or design reviews that established these thresholds
