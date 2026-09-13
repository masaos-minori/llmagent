# Issue: Two Different Diagnostic Fields With Similar Names But Different Vocabularies

## Summary
`SearchDiagnostics.http_result_kind` (enum) and `get_diagnostics()["http_result_kind"]` (string literals) have similar names but different vocabularies and granularities — they cannot be directly derived from each other.

## Evidence
- File: `docs/03_rag_03_03_query_pipeline-context-and-diagnostics.md`, section 4.2
- Text: "Note that the name `http_result_kind` is used in two different value systems; do not confuse them"
- `SearchDiagnostics.http_result_kind`: enum values `SUCCESS` / `EMPTY` / `ERROR` / `NOT_USED`
- `get_diagnostics()["http_result_kind"]`: string literals `"remote_nonempty"` / `"remote_empty"` / `"in_process_fallback"`
- Both represent the same HTTP call results but use different vocabularies and granularities

## Impact
- Developers may mistakenly assume these fields are interchangeable or derivable from each other
- Debugging becomes harder when the wrong field is consulted
- Monitoring/alerting logic built on one field won't work correctly if applied to the other

## Recommended Action
Investigate whether these two fields can be unified into a single canonical representation. If both must coexist, add clear documentation explaining their relationship and when to use each. Consider renaming one field to avoid confusion (e.g., prefix with `search_` or `pipeline_`).
