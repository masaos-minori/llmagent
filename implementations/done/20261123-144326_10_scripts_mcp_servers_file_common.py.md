## Goal
Merge the dedup store metrics block into the shared `_health()` helper used by the three file servers (REQ-004, the health payload reports dedup store metrics and capacity status).
## Scope
**Release unit**: health exposure
- One change confined to the shared `_health()` helper in `scripts/mcp_servers/file/common.py`, covering the three file servers.
## Assumptions
- `dedup_health_details()` (new) is added by the row-09 sibling document in `scripts/mcp_servers/health_response.py`; it reads the dispatcher's `_dedup_store` / `_dedup_config` module globals and returns `{}` — never an exception — when the store is absent or the read fails (REQ-002 degradation path, the default in existing tests).
- `scripts/mcp_servers/file/read_server.py`, `write_server.py`, `delete_server.py` call `_health()` unchanged; none of them is edited here.
## Design decisions
- The change stays inside `_health()` so the three servers inherit it through the shared helper; `make_health_response()`'s signature, the payload keys, and the `security=posture` argument stay unchanged.
## Alternatives considered
- N/A: the Plan fixes the wiring point at the shared helper; no alternative for a confined one-key merge.
## Implementation
### Target file
`scripts/mcp_servers/file/common.py`
### Procedure
- Extend the existing `from mcp_servers.health_response import make_health_response` (line 31) to also import `dedup_health_details` (new).
- In `_health()` (line 229-241): the current call passes an inline empty dict (`make_health_response(deps, {}, security=posture)`); build a local `details: dict[str, object] = {}` instead, add `details.update(dedup_health_details())` after `deps = _build_health_deps(allowed_dirs)`, and pass `details` in place of the inline `{}`.
- Update the docstring sentence that states `details` stays empty to name the single new `"dedup"` key and its absence without a store.
### Method
- Additive merge of the single new `details` key `"dedup"`, present only when the server's dedup store is open; posture handling (`_build_health_deps`, the optional `posture` argument) is untouched.
### Details
- The block carries the REQ-004 metrics fields: per-status counts, growth, WAL size, lock wait, lease health, and threshold status.
### Companion test files
- `tests/mcp_servers/file/test_file_health_posture.py`
  - Procedure: keep the exact-equality `assert body["details"] == {}` in `test_posture_data_is_not_folded_into_details` (line 149) as the no-store case, and add a store-configured assertion that `body["details"]` then contains a `"dedup"` block whose fields match the REQ-004 metrics fields, following the file's existing `_health()`-call fixture pattern.
  - Validation: `uv run pytest tests/mcp_servers/file/test_file_health_posture.py`
## Compatibility considerations
- `tests/mcp_servers/file/test_file_health_posture.py` pins the current `details` shape by exact equality (`body["details"] == {}`); it stays passing with no store configured and is extended for the configured case.
## Security considerations
- The block exposes counts and paths only, never row payloads or results.
## Rollback considerations
- N/A: revert the commit.
## Validation plan
- `uv run pytest tests/mcp_servers/file/test_file_health_posture.py`: pass with and without a configured dedup store.
- `uv run python tools/run_validation_gates.py` for the diff: pass.
## Completion criteria
- All three file servers' `/health` publish the `"dedup"` block when the dedup store is open, and their `details` is unchanged otherwise; `BASE_KEYS` is unchanged.
## Out of Scope
- The three file server wrapper files, `make_health_response()` itself (row 09), and the metrics module internals (rows 05-06).
## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the `_health()` change per Procedure/Method/Details | Completed | 20261123-223506 | 20261123-223506 | Changed: scripts/mcp_servers/file/common.py (the health_response import also imports dedup_health_details, _health() builds a local details dict and merges the block instead of passing an inline empty dict, and the docstring sentence that said details stays empty now names the single dedup key and its absence without a store). _build_health_deps and the optional posture argument untouched, so the three file servers inherit the change. |
| 2 | Extend the companion test's `details` expectation | Completed | 20261123-223506 | 20261123-223506 | Extended tests/mcp_servers/file/test_file_health_posture.py with a DEDUP_FIELDS constant. The exact-equality assertion is kept as the no-store case, and that test now states the precondition by patching the dispatch store and config globals to None because the session's autouse bootstrap fixture configures a store from the isolated config copy. A store-configured test asserts details carries only the dedup key, its fields match the REQ-004 set, and no posture field appears in it. Run: 8 passed. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261123-230806 | 20261123-230806 | This member Step 3e: ruff format and check pass, run_validation_gates.py fast mode all applicable gates Pass, lint-imports 6 contracts kept, mypy clean across scripts/, bandit clean on this file. Validation-plan run of the nine health test files: 248 passed, 1 skipped (the mdq skip is the pre-existing git-fame skip). Full suite runs once at end of the release unit. End-of-unit run for the health-exposure unit: full suite with coverage 13660 passed 4 skipped, diff-scoped coverage 94 percent against the 90 gate, all gates pass. Deviation: the run was executed once for the whole diff. |

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
- **Requirement ID**: `REQ-004` (the health payload reports dedup store metrics and capacity status)
- **Source issue**: issues/20261120-115844_mcpdl005_retention-capacity-monitoring.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261123-120131_mcpdl005_retention-capacity-monitoring.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261123-144326
- **Related target files**: `scripts/mcp_servers/file/common.py`, `tests/mcp_servers/file/test_file_health_posture.py`