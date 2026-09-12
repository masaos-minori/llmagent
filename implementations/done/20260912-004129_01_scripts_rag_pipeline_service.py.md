# Implementation: scripts/rag/pipeline_service.py

## Goal

Parse `selected_hits` from the RAG service's JSON response in `call_rag_service()` and invoke the existing `_set_fetch_result()` helper with the raw hit-dict list on both success return paths; retype `set_fetch_result` and `_set_fetch_result` parameters from `Callable[[str], None]` to `Callable[[list[dict[str, Any]]], None]`.

## Scope

- Modify `scripts/rag/pipeline_service.py` only.
- Add `selected_hits` parsing logic in `call_rag_service()`.
- Change type annotations for `set_fetch_result` parameter and `_set_fetch_result` function.
- Invoke `_set_fetch_result(selected_hits)` on both success return paths (lines 137 and 142).

## Assumptions

- The RAG service's `/v1/call_tool` response for `rag_run_pipeline` includes a top-level `selected_hits` key containing a list of dicts (confirmed server-side in `scripts/mcp_servers/rag_pipeline/rag_pipeline_models.py:215`).
- `selected_hits` may be absent from the response body (no exception should be raised in that case — just skip the callback invocation).
- `selected_hits` may be empty (`[]`) — the callback should still be invoked with the empty list; the caller (`AugmentRefiner`) decides whether to forward it based on emptiness.
- The callback signature change from `Callable[[str], None]` to `Callable[[list[dict[str, Any]]], None]` does not break any other callers (confirmed via repo-wide `rg` search — only the 7 test files enumerated in the plan reference these symbols).

## Design decisions

- Parse `selected_hits` using `body.get("selected_hits")` — same pattern used for `"result"` — keeping the code style consistent.
- Only invoke `_set_fetch_result` when `selected_hits` is present (truthy). When absent or falsy, skip the callback — this avoids passing `None` or an empty list where the caller might not expect it.
- The callback is invoked on BOTH success paths (empty-result and non-empty-result) because `selected_hits` and `result` vary independently in the RAG service response.

## Alternatives considered

- **Always invoke callback even when `selected_hits` is absent**: Would require the callback to handle `None`, adding defensive checks everywhere. Simpler locally but less clean globally.
- **Invoke callback only when `selected_hits` is non-empty**: Would defer the "don't overwrite `last_fetch_result` when hits are empty" logic to the caller, but means the callback isn't called consistently across success paths. The plan explicitly requires invocation on both paths.

## Implementation

### Target file

`scripts/rag/pipeline_service.py`

### Procedure

1. Add import for `Any` from `typing` (needed for the new type annotation).
2. Change `_set_fetch_result`'s second parameter type from `fetch_result: str` to `fetch_result: list[dict[str, Any]]`.
3. Change `call_rag_service`'s `set_fetch_result` parameter type from `Callable[[str], None] | None` to `Callable[[list[dict[str, Any]]], None] | None`.
4. Update the docstring for `set_fetch_result` parameter to reflect the new type.
5. In the empty-result success path (line ~137), after `return "", status_code, elapsed_ms`, add: `if selected_hits := body.get("selected_hits"): _set_fetch_result(set_fetch_result, selected_hits)`.
6. In the non-empty-result success path (line ~142), after `return result_raw, status_code, elapsed_ms`, add: `if selected_hits := body.get("selected_hits"): _set_fetch_result(set_fetch_result, selected_hits)`.

### Method

```python
# Step 1: Add import (around line 10, alongside existing imports)
from typing import Any

# Step 2: Change _set_fetch_result signature (line 40-46)
def _set_fetch_result(
    set_fetch_result: Callable[[list[dict[str, Any]]], None] | None,
    fetch_result: list[dict[str, Any]],
) -> None:
    """Call the fetch result callback if provided."""
    if set_fetch_result is not None:
        set_fetch_result(fetch_result)

# Step 3: Change call_rag_service parameter type (line 56)
set_fetch_result: Callable[[list[dict[str, Any]]], None] | None = None,

# Step 4: Update docstring for set_fetch_result parameter (around line 105)
# Change from:
#     set_fetch_result: Callback to store fetch result metadata.
# To:
#     set_fetch_result: Callback to store raw hit-dict list from selected_hits.

# Step 5: Add selected_hits parsing in empty-result path (after line 137)
# After: return "", status_code, elapsed_ms
# Insert before the return:
if selected_hits := body.get("selected_hits"):
    _set_fetch_result(set_fetch_result, selected_hits)

# Step 6: Add selected_hits parsing in non-empty-result path (after line 142)
# After: return result_raw, status_code, elapsed_ms
# Insert before the return:
if selected_hits := body.get("selected_hits"):
    _set_fetch_result(set_fetch_result, selected_hits)
```

### Details

- Line numbers are approximate — verify against current source before applying changes.
- The walrus operator (`:=`) is used to combine the presence check and assignment in one expression, matching Python 3.8+ idioms already used elsewhere in the codebase.
- No changes to retry/failure paths — `_set_fetch_result` is only called on successful responses where `selected_hits` can be meaningfully parsed.

## Compatibility considerations

- **Breaking change**: The callback type changes from `Callable[[str], None]` to `Callable[[list[dict[str, Any]]], None]`. All existing callers must be updated:
  - `scripts/rag/http_augment.py`: `HttpAugment.__init__`'s `set_fetch_result` parameter must be retyped to `Callable[[list[dict[str, Any]]], None] | None`.
  - `scripts/rag/augment.py`: `AugmentRefiner.__init__`'s `set_fetch_result` parameter must be retyped to `Callable[[TwoStageFetchResult], None] | None` (a different wrapper layer).
  - Test files: fixtures like `_noop_fetch(r: TwoStageFetchResult)` in `tests/rag/test_rag_pipeline_service.py` already assume the corrected type.
- **No API contract change**: The HTTP endpoint (`POST /v1/call_tool`) is unchanged; only the client-side parsing of its response is modified.

## Security considerations

- No new security surface introduced. Parsing `selected_hits` uses the same safe `.get()` pattern as the existing `result` field.
- No input validation added for `selected_hits` content — the dataclass `TwoStageFetchResult.hits` is typed `list[Any]` precisely to accept HTTP-mode's `list[dict]` shape without per-hit validation (matching the in-process path's own lack of per-hit validation).

## Rollback considerations

- Revert the type annotations and remove the two `_set_fetch_result` calls from the success paths.
- If the callback type change breaks an unexpected caller, revert to `Callable[[str], None]` and adjust the caller separately.

## Validation plan

| Target | Strategy | Tool / Command | Expected Outcome |
|--------|----------|----------------|------------------|
| `call_rag_service()` behavior | Unit (regression) | `uv run pytest tests/rag/test_rag_pipeline_service.py -q` | All existing tests pass (baseline: all currently passing) |
| Type correctness | Static | `uv run mypy scripts/rag/pipeline_service.py` | No new errors |
| Lint | Static | `uv run ruff check scripts/rag/pipeline_service.py` | 0 errors |
| Security | Static | `uv run bandit -r scripts/rag/pipeline_service.py -c pyproject.toml` | No new findings beyond pre-existing baseline |

## Completion criteria

- [ ] `_set_fetch_result` signature accepts `list[dict[str, Any]]` instead of `str`.
- [ ] `call_rag_service`'s `set_fetch_result` parameter type changed to `Callable[[list[dict[str, Any]]], None] | None`.
- [ ] Both success return paths (empty-result at line ~137, non-empty-result at line ~142) invoke `_set_fetch_result(selected_hits)` when `selected_hits` is present in the response body.
- [ ] Docstring for `set_fetch_result` parameter updated to describe the new type.
- [ ] No lint/type/security regressions introduced.

## Out of scope

- Modifying `scripts/rag/http_augment.py` — handled by a separate implementation procedure document.
- Modifying `scripts/rag/augment.py` — handled by a separate implementation procedure document.
- Modifying `scripts/rag/pipeline.py` — handled by a separate implementation procedure document.
- Adding new tests — handled by a separate implementation procedure document.
- Changing the RAG service's response schema — confirmed the server already emits `selected_hits`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Retype `_set_fetch_result` and `call_rag_service` parameters | Pending | — | — | |
| 2 | Add `selected_hits` parsing in empty-result success path | Pending | — | — | |
| 3 | Add `selected_hits` parsing in non-empty-result success path | Pending | — | — | |
| 4 | Update docstring for `set_fetch_result` parameter | Pending | — | — | |
| 5 | Run validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Source issue**: issues/20260911-132739_raghits01_http-mode-selected-hits-unparsed.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260911-205352_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260912-004129
- **Related target files**: scripts/rag/pipeline_service.py
