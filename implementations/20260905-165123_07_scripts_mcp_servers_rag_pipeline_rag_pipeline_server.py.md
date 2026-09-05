## Goal
Remove the `/rag_invalidate_cache` HTTP endpoint and its handler from
`scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py` (`REQ-003`).

## Scope
- **In-Scope**: remove the `@app.post("/rag_invalidate_cache")` route decorator and its
  `async def rag_invalidate_cache() -> JSONResponse:` handler function in its entirety
  (lines 162-174: docstring, `try`/`except` block, both success and error
  `JSONResponse` returns, and the `# noqa: BLE001` suppression comment attached to the
  `except Exception as e:` clause).
- **Out-of-Scope**: the `/health` endpoint immediately preceding it, and the "MCP
  standard endpoints" section immediately following — confirmed unrelated by reading
  the surrounding context; `_service.invalidate_cache()` itself (removed by procedure
  document `06`, this file's route is its sole HTTP caller).

## Assumptions
- `scripts/rag/ingestion/cache_invalidation.py`'s `CacheInvalidator` (procedure document
  `04`) is the only other client that POSTs to this route (confirmed by the Plan's own
  evidence: "`CacheInvalidator` is a confirmed active caller of that endpoint"); no
  external/production HTTP client outside this repository's own code is assumed to call
  this route (Constraint: this is a local MCP server endpoint, not a public API).

## Design decisions
(per `skills/python-design/SKILL.md` Final Output §6, narrow bullet only)
- Remove the entire route in one document, rather than disabling it (e.g. returning
  404 unconditionally) — per the Plan's Design section, "the endpoint is the direct
  exposure" of a capability (`RagPipelineMCPService.invalidate_cache()`, procedure `06`)
  that no longer exists once this Plan lands; a disabled-but-present route would be
  dead code with no caller expecting a stub response.

## Alternatives considered
- Returning `410 Gone` from the route instead of deleting it, to give any stray caller
  a clear signal — rejected: no external caller is known or expected once
  `CacheInvalidator` (procedure `04`) is also removed in the same Plan; the originating
  issue's scope is explicit deletion, not deprecation-in-place, and FastAPI already
  returns 404 for an undefined route without any extra code.

## Implementation
### Target file
`scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py`

### Procedure
1. Remove the `@app.post("/rag_invalidate_cache")` decorator and the
   `async def rag_invalidate_cache() -> JSONResponse:` function body beneath it (lines
   162-174), including its docstring, the `try`/`except Exception as e:  # noqa: BLE001 — ...`
   block, and both `JSONResponse` return statements (success and error).
2. Confirm the blank-line spacing between the preceding `/health` endpoint and the
   following "MCP standard endpoints" section-comment block is left clean (no double
   blank line or orphaned separator).

### Method
Direct removal via `Edit` — FastAPI requires no further registration cleanup; removing
the decorated function itself deregisters the route.

### Details
- The `# noqa: BLE001` suppression comment is removed along with the handler it
  annotates — no separate action is needed against
  `tools/check_suppression_justification.py`'s allowlist, since the line itself is
  deleted, not merely its suppression comment.
- Confirm after editing: `rg -n "rag_invalidate_cache" scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py`
  returns zero matches.

## Compatibility considerations
- This is a local FastAPI route on the `rag-pipeline-mcp` server process — removing it
  is a breaking change only for a caller that still POSTs to `/rag_invalidate_cache`;
  this Plan's evidence confirms the only such caller (`CacheInvalidator`, procedure
  document `04`) is removed in the same Plan.
- No `docs/*.md` file documenting this endpoint's port/route is updated by this
  document — that is `semcachedocs`'s scope (Plan Documentation Impact).

## Security considerations
N/A: no security-sensitive code path is touched — this removes an unauthenticated
internal endpoint entirely rather than altering its access control.

## Rollback considerations
- Revert via `git checkout` on this single file; no data migration or external state is
  affected. Should be reverted together with procedure document `06`
  (`RagPipelineMCPService.invalidate_cache()`) — reverting this file alone while `06`
  remains applied would restore a route calling a method that no longer exists.

## Validation plan
- `rg -n "rag_invalidate_cache" scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py`
  — zero matches.
- `uv run pytest tests/mcp_servers/rag_pipeline/test_rag_pipeline_server_endpoints.py -v`
  (updated by procedure document `15`) — passes; asserts the route no longer exists
  (404/route-not-found).

## Completion criteria
- The `/rag_invalidate_cache` route and its handler no longer exist in this file (Plan
  `AC-5`).
- `tests/mcp_servers/rag_pipeline/test_rag_pipeline_server_endpoints.py` passes.

## Out of scope
- `RagPipelineMCPService.invalidate_cache()` (procedure document `06`).
- `CacheInvalidator`, the endpoint's other confirmed caller (procedure document `04`).
- The `/health` endpoint or any other route in this file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | Covered by procedure document `15` |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: documentation deferred to `semcachedocs` |

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
- **Requirement ID**: `REQ-003` (remove the `/rag_invalidate_cache` endpoint and its handler)
- **Source issue**: issues/20260902-150339_semcacherm_remove_semanticcache_implementation_and_invalidation_paths.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260904-140151_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260905-165123
- **Related target files**: scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py
