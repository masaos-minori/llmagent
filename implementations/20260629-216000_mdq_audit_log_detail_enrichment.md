## 1. Goal
- Improve accuracy of audit log detail fields in `scripts/mcp/mdq/server.py` `call_tool` endpoint: add precise result counts, elapsed time, truncated flag, and index operation details for each MDQ tool.

## 2. Scope
- **In-Scope**:
  - Improve `_audit_target()` per-tool target string accuracy
  - Add `result_count`, `elapsed_ms`, `truncated` flags to `call_tool` endpoint log detail
  - Implement per-tool detail generation logic for: search_docs, get_chunk, grep_docs, index_paths, refresh_index
- **Out-of-Scope**:
  - Audit log format change (`_audit_log` signature unchanged)
  - `X-Session-Id` / `X-Request-Id` correlation processing (keep as-is)
  - DB schema or config file changes

## 3. Requirements
### Functional
- `search_docs`: `result_count` approximated from `---` delimiter count in result text
- `get_chunk`: `truncated` flag = `"[Truncated" in r.output`
- `grep_docs`: `match_count` = `"---"` occurrence count (already implemented but needs accuracy verification)
- `index_paths`: `indexed_count` parsed from result text
- `refresh_index`: `indexed_count`, `skipped_count`, `deleted_count` parsed from result text
- All success responses include `duration_ms` (currently only some do)
- Error `error_kind` changed from `"dispatch_error"` to `"tool_error"` for spec alignment

### Non-functional
- No audit log format change — backward compatible
- Text parsing is approximate; future migration to structured responses will improve accuracy

## 4. Architecture
### Component Boundaries
```
scripts/mcp/mdq/server.py (call_tool endpoint)
  ├── _audit_target() → improved per-tool target strings
  ├── call_tool() → detail generation per tool type:
  │     ├── search_docs: result_count = "---" delimiter count
  │     ├── get_chunk: truncated = "[Truncated" in output
  │     ├── grep_docs: match_count = "---" occurrence count
  │     ├── index_paths: indexed_count parsed from "Indexed:" text
  │     └── refresh_index: indexed_count, skipped_count, deleted_count parsed
  └── _audit_log() → unchanged signature; detail field enriched
```

## 5. Module Design
No changes to dependency direction. All changes within `server.py` — no new module imports needed.

## 6. Interface Design
### Modified Methods

```python
# server.py
def call_tool(self, name: str, arguments: dict) -> tuple[dict[str, object], int]:
    # MODIFIED: per-tool detail generation in success path
    if isinstance(r, MCPResponse):
        result_count = None
        truncated = False
        indexed_count = None
        skipped_count = None
        deleted_count = None

        if name == "search_docs":
            # Approximate count from "---" delimiter count
            if hasattr(r.output, "__iter__") and not isinstance(r.output, str):
                result_count = len(r.output)
            elif isinstance(r.output, str):
                result_count = r.output.count("---")

        elif name == "get_chunk":
            # Truncated flag from output text
            if isinstance(r.output, str) and "[Truncated" in r.output:
                truncated = True

        elif name == "grep_docs":
            # Match count from "---" delimiter count
            if isinstance(r.output, str):
                result_count = r.output.count("---")

        elif name == "index_paths":
            # Parse "Indexed: N" from result text
            if isinstance(r.output, str):
                import re
                m = re.search(r"Indexed:\s*(\d+)", r.output)
                indexed_count = int(m.group(1)) if m else None

        elif name == "refresh_index":
            # Parse "Indexed: N", "Skipped (unchanged): N", "Deleted from index: N"
            if isinstance(r.output, str):
                import re
                m_idx = re.search(r"Indexed:\s*(\d+)", r.output)
                m_skip = re.search(r"Skipped.*?:\s*(\d+)", r.output)
                m_del = re.search(r"Deleted from index:\s*(\d+)", r.output)
                indexed_count = int(m_idx.group(1)) if m_idx else None
                skipped_count = int(m_skip.group(1)) if m_skip else None
                deleted_count = int(m_del.group(1)) if m_del else None

        # Build detail_parts with duration_ms for ALL success responses
        duration_ms = int((time.monotonic() - req_start) * 1000)
        detail_parts = [f"duration_ms={duration_ms}"]
        if result_count is not None:
            detail_parts.append(f"result_count={result_count}")
        if truncated:
            detail_parts.append("truncated=true")
        if indexed_count is not None:
            detail_parts.append(f"indexed_count={indexed_count}")
        if skipped_count is not None:
            detail_parts.append(f"skipped_count={skipped_count}")
        if deleted_count is not None:
            detail_parts.append(f"deleted_count={deleted_count}")

        self._audit_log(req_id, name, "success", detail_parts)
```

### Error Path Change

```python
# server.py — error path
# MODIFIED: change error_kind from "dispatch_error" to "tool_error"
error_kind = "tool_error"  # was "dispatch_error"
detail_parts = [f"duration_ms={duration_ms}", f"error_kind={error_kind}"]
self._audit_log(req_id, name, "error", detail_parts)
```

## 7. Data Model & Serialization
No changes to data models. Audit log fields are added to existing log detail string — no schema migration needed.

## 8. Error Handling & Resource Lifecycle
### Failure Modes
- Text parsing by `---` delimiter count for `search_docs` is approximate → **Mitigation**: Acceptable as approximation; "0 miscount" is better than nothing. Future structured response migration will improve accuracy.
- `refresh_index` result format change breaks regex → **Mitigation**: Lock result format in tests to prevent regression.

### Resource Lifecycle
- No connection pooling changes; each operation opens and closes its own connection (unchanged)
- Time measurement uses `time.monotonic()` — no resource lifecycle impact

## 9. Configuration
No config changes needed. Audit log format unchanged — backward compatible.

## 10. Test Strategy
### Unit Tests
- Verify `---` delimiter count matches expected result count for `search_docs` with known input
- Verify truncated flag detection for `get_chunk` with known truncated output
- Verify regex parsing of "Indexed:", "Skipped (unchanged):", "Deleted from index:" for `refresh_index`

### Regression Tests
- Full mdq regression: `uv run pytest tests/ -x -q -k mdq`

## 11. Implementation Plan
### Phase 1: Detail Generation Logic
- Organize `detail_parts` generation in `call_tool` per tool type
- Implement per-tool detail parsing as shown above
- Add `duration_ms` to ALL success responses (currently only some do)

### Phase 2: error_kind Unification
- Change `error_kind` from `"dispatch_error"` to `"tool_error"` in error path

### Phase 3: Verification
- Run `uv run pytest tests/ -x -q -k mdq` to confirm existing tests pass
- Run lint/type check: `uv run ruff check scripts/mcp/mdq/server.py && uv run mypy scripts/mcp/mdq/server.py`

## 12. Risks / Open Questions
- **UNK-01**: `search_docs` result count from text parsing is imprecise (uses `---` delimiter count) → **Resolution**: Acceptable as approximation; better than "0 miscount". Future structured response migration will improve accuracy.
- **UNK-02**: `get_chunk` truncated flag detection via `"[Truncated" in r.output` — may be unreliable if text formatting changes → **Resolution**: Acceptable for current state; future structured response migration will provide precise flag.
- **Risk**: Text parsing by `---` delimiter count is approximate → **Mitigation**: Document as approximation; future structured response migration will improve accuracy.
- **Risk**: `refresh_index` result format change breaks regex → **Mitigation**: Lock result format in tests to prevent regression.
