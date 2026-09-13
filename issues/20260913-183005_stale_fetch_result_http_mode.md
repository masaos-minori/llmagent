# Issue: Stale fetch_result in HTTP Mode Diagnostics

## Summary
In HTTP mode, `get_diagnostics()["fetch_result"]` may contain stale values from the previous in-process execution rather than the current call's result.

## Evidence
- File: `docs/03_rag_03_03_query_pipeline-context-and-diagnostics.md`, section 4.3
- Text: "In HTTP mode, `fetch_result` might contain stale values from the previous in-process execution rather than the current call's result. This is because `RagPipeline._run_http_augment()` does not call `self.run()` upon an HTTP success"
- The note explains that `self.last_fetch_result` updates occur in multiple places but are not synchronized when HTTP mode succeeds

## Impact
- Operators relying on `fetch_result` diagnostics during HTTP mode queries will see outdated information
- This can lead to incorrect conclusions about search performance and hit counts
- The stale data may mask real issues with the current query's execution

## Recommended Action
Investigate whether `fetch_result` should be updated before returning from `_run_http_augment()` when HTTP mode succeeds, or document this limitation clearly in the diagnostics API contract. Consider adding a separate diagnostic field for HTTP-mode-specific fetch results.
