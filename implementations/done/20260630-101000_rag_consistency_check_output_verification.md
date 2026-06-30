## Goal
- Confirm RAG consistency check output already includes chunk_id/URL-level repair targets, enabling operators to determine specific repair actions from `/db consistency` output.

## Scope
- **In-Scope**:
  - Verify `maintenance.py` `RagConsistencyReport` has `affected_chunk_ids`, `affected_doc_ids`, `affected_orphan_chunk_ids`, `affected_orphan_urls`
  - Verify `/db consistency` command displays these details
  - Verify docs repair guidance table is complete
- **Out-of-Scope**:
  - Auto-repair implementation
  - Consistency check as background job
  - `check_rag_consistency()` read-only change

## Findings

### 1. RagConsistencyReport fields — Already present
`maintenance.py:91`:
```python
issues: tuple[str, ...] = ()  # human-readable consistency issues
```
And the report has:
- `affected_chunk_ids` (L505-L508)
- `affected_doc_ids` (L501-L504)
- `affected_orphan_chunk_ids` (L515-L518)
- `affected_orphan_urls` (L519-L522, L532-L535)

### 2. `/db consistency` output — Already displays details
`cmd_db.py:L363-L364`:
```python
for issue in result.issues:
    self._out.write_error(f"Consistency issue: {issue}")
```
The `result.issues` comes from `summarize_issues()` which includes affected identifiers.

### 3. `summarize_issues()` — Already includes affected chunk_ids/URLs
- L499-L512: FTS gap with `affected_doc_ids` or `affected_chunk_ids`
- L513-L529: FTS orphan with `affected_orphan_chunk_ids` or `affected_orphan_urls`
- L530-L542: Orphan vec rows with `affected_orphan_urls` or `affected_orphan_chunk_ids`
- L543+: vec != chunks with `affected_orphan_urls` or `affected_orphan_chunk_ids`

### 4. Docs repair guidance — Already complete
- L346-L347: Mentions affected chunk_id/URL identifiers in output
- L351-L356: Repair decision tree with all four issue types
- L332-L336: Example output showing `Affected doc_ids: [1, 2, 3]`

## Conclusion
No changes needed. The RAG consistency check already includes chunk_id/URL-level repair targets in `/db consistency` output via `summarize_issues()`, and the docs repair guidance table is complete.
