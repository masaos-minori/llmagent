## Goal
Remove `/rag_invalidate_cache` endpoint tests from
`tests/mcp_servers/rag_pipeline/test_rag_pipeline_server_endpoints.py`, since the route
they exercise is removed by procedure document `07` (`REQ-003`, `REQ-006`).

## Scope
- **In-Scope**: remove the `- POST /rag_invalidate_cache (success and failure)` line
  from the module docstring's endpoint-coverage list (line 9); remove
  `class TestRagInvalidateCacheEndpoint:` in its entirety (lines 145-163: both
  `test_success_returns_ok` and `test_failure_returns_500`); remove
  `_FakeService.__init__`'s `self.invalidate_cache = MagicMock()  # sync method:
  called without await in server.py` assignment (lines 47-49) — an adversarial-
  verification finding not named in the Plan's `Repository Evidence` for this row, but
  confirmed by this document's own inspection to be a `_FakeService` attribute that
  exists solely to back the removed endpoint's tests (see Details).
- **Out-of-Scope**: every other `_FakeService` attribute (`start`, `stop`,
  `run_pipeline`, `run_debug_pipeline`, `_dispatch_table`) and every other test class in
  this file — confirmed unrelated to cache invalidation by reading the full file's
  class list (lifespan, `RagPipelineServiceError` handler, `/rag_run_pipeline`,
  `/rag_debug_pipeline`, `/v1/tools`, `/v1/call_tool`, `dispatch()`).

## Assumptions
- The `/rag_invalidate_cache` route itself (procedure document `07`) is removed in the
  same implementation pass — otherwise this test suite would silently stop covering a
  still-live route.

## Design decisions
(per `skills/python-design/SKILL.md` Final Output §7, narrow bullet only)
- Remove `_FakeService.invalidate_cache`'s attribute assignment in the same document as
  the test class it backs — per Step 3a Adversarial Verification, a fixture attribute
  that exists solely for a removed test class is itself part of "every test... made
  obsolete" (`REQ-006`), not a separate target file (it is the same file, same row);
  this is recorded here rather than silently left as a `MagicMock()` no test asserts
  against.

## Alternatives considered
- Leaving `_FakeService.invalidate_cache` in place as an inert `MagicMock()` attribute
  — rejected: once no test references it, it is dead fixture code inconsistent with
  `REQ-006`'s intent to remove obsolete test infrastructure, not only obsolete test
  functions.

## Implementation
### Target file
`tests/mcp_servers/rag_pipeline/test_rag_pipeline_server_endpoints.py`

### Procedure
1. Remove the `- POST /rag_invalidate_cache (success and failure)` line from the
   module docstring's endpoint list (line 9).
2. Remove `_FakeService.__init__`'s `self.invalidate_cache = (\n    MagicMock()\n)  #
   sync method: called without await in server.py` assignment (lines 47-49).
3. Remove `class TestRagInvalidateCacheEndpoint:` in its entirety (lines 145-163:
   docstring-free class containing `test_success_returns_ok` and
   `test_failure_returns_500`).
4. Confirm blank-line spacing between the preceding class (`... == {"config": "check
   failed"}`, ending at line 142) and the following `class TestToolsListEndpoint:`
   (line 165) is left at the file's existing single-blank-line convention.

### Method
Direct removal via `Edit`, applied as three separate edits within the same file
(docstring line, fixture attribute, test class).

### Details
- `_FakeService.invalidate_cache`'s removal (step 2) is scoped strictly to that one
  attribute assignment — do not touch `start`/`stop`/`run_pipeline`/
  `run_debug_pipeline`/`_dispatch_table` in the same `__init__`, confirmed unrelated by
  reading the full method.
- Confirm after editing: `rg -n "invalidate_cache|rag_invalidate_cache"
  tests/mcp_servers/rag_pipeline/test_rag_pipeline_server_endpoints.py` returns zero
  matches.

## Compatibility considerations
N/A: test-only file; no production caller depends on it.

## Security considerations
N/A: no security-sensitive code path is touched.

## Rollback considerations
- Revert via `git checkout` on this single file; functionally coupled to procedure
  document `07` (reverting only this test file while `07` remains applied would leave
  tests exercising a route that no longer exists, causing 404s instead of the asserted
  200/500).

## Validation plan
- `uv run pytest tests/mcp_servers/rag_pipeline/test_rag_pipeline_server_endpoints.py -v`
  — all remaining tests pass.
- `rg -n "invalidate_cache|rag_invalidate_cache"
  tests/mcp_servers/rag_pipeline/test_rag_pipeline_server_endpoints.py` — zero matches.

## Completion criteria
- `TestRagInvalidateCacheEndpoint` and `_FakeService.invalidate_cache` no longer exist
  in this file (Plan `AC-5`, `AC-9`).
- `uv run pytest tests/mcp_servers/rag_pipeline/test_rag_pipeline_server_endpoints.py -v`
  passes in full.

## Out of scope
- The `/rag_invalidate_cache` route itself (procedure document `07`).
- `_FakeService`'s other attributes and every other test class in this file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 2026-09-06 | 2026-09-06 | All rag_invalidate_cache references removed; rg returns zero matches |
| 2 | Add or update tests per Validation plan | Completed | 2026-09-06 | 2026-09-06 | N/A: this document itself is a test-removal change |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-09-06 | 2026-09-06 | pytest passes with zero regressions |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 2026-09-06 | 2026-09-06 | N/A |

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
- **Requirement ID**: `REQ-003` (endpoint removed); `REQ-006` (remove tests referencing the removed API)
- **Source issue**: issues/20260902-150339_semcacherm_remove_semanticcache_implementation_and_invalidation_paths.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260904-140151_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260905-165123
- **Related target files**: tests/mcp_servers/rag_pipeline/test_rag_pipeline_server_endpoints.py
