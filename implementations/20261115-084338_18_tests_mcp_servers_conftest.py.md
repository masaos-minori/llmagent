## Goal

Create a route-inventory assertion reused by one test per MCP FastAPI app, asserting that no operation-specific execution POST route is registered and only `/v1/tools`, `/v1/call_tool`, `/health` (plus approved per-app diagnostics) remain. (`REQ-007`, `AC-5`)

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Each app exposes exactly the execution path `/v1/call_tool`; every other operation-specific POST route is a bypass this Plan removes.
- Non-execution GET endpoints (`/health`, `/v1/tools`) are approved on every app; any additional retained diagnostic (e.g. `read_server.py`'s `/list_allowed_directories`, pending its AC-4 decision) is app-specific and must be declared per app, not baked into the shared helper.
- The helper lives either in `tests/mcp_servers/conftest.py` (as a fixture/function alongside existing fixtures) or in a dedicated helper module such as `tests/mcp_servers/_route_inventory.py`; both are acceptable per the Plan row.

## Design decisions
- The helper takes the app and an explicit approved-non-execution set, so the app-specific diagnostic question (UNK-04) does not leak into the shared assertion.
- The core invariant asserted is structural: the only `POST` route on the app is `/v1/call_tool`. Any other registered `POST` is an operation-specific execution route and fails the test.
- Placement in `conftest.py` reuses the existing shared-fixtures file (which already imports `pytest`); a dedicated module keeps the assertion isolated. Choose one and use it consistently across all ten apps.

## Alternatives considered
- Baking a single global approved-list into the helper: rejected — per-app diagnostics differ, so the list must be passed per app.
- One bespoke assertion per app in each test file: rejected — the Plan requires a single reused helper so reintroduction fails uniformly.

## Implementation
### Target file
`tests/mcp_servers/conftest.py` (or a new `tests/mcp_servers/_route_inventory.py` helper module)

### Procedure
1. Add a helper that takes the app plus an app-declared approved-non-execution GET set (default `/health`, `/v1/tools`) and that:
   - Enumerates `app.routes`, separating `APIRoute` entries by HTTP method.
   - Asserts the set of registered `POST` paths equals `{"/v1/call_tool"}`; any other POST path is reported with the offending paths.
   - Optionally asserts every registered `GET` path is within the app-declared approved-non-execution set (union with app-specific diagnostics).
2. In each app's endpoint test module, add a small test that imports the app and calls the helper, so reintroducing a direct route fails CI via this test.
3. Do not modify the per-app test bodies beyond adding the one inventory call; the per-app test files are companions of their code rows (covered there).

### Method
- Inspect `starlette.routing.APIRoute` to enumerate paths and methods: `[r for r in app.routes if isinstance(r, APIRoute)]`.
- Confirm the helper imports cleanly and that `TestClient(app)` construction still works with the app's auth middleware attached.

### Details
- The helper must not itself import any production server module; callers pass the app fixture, keeping the helper import-light and reusable across all ten apps.
- Because `read_server.py`'s `/list_allowed_directories` disposition is an open AC-4 decision, the read app's approved-non-execution set must reflect the recorded decision before this test asserts on it.

## Compatibility considerations
N/A: adds a test helper only; no production change.

## Security considerations
Strengthens regression protection: a reintroduced direct execution route fails CI via the inventory test (`AC-5`), closing the bypass again.

## Rollback considerations
Revert the commit.

## Validation plan
- Run the new inventory test for each app; confirm all pass after route removal.
- Introduce a throwaway `@app.post("/x")` in a local copy and confirm the inventory test fails, then remove it.
- `uv run python tools/stale_detector.py` clean before hand-off.

## Completion criteria
- A shared route-inventory assertion exists and is reused by one test per MCP app.
- A reintroduced operation-specific execution POST route fails the inventory test (`AC-5`).

## Out of Scope
- Deciding the `/list_allowed_directories` disposition (AC-4, separate row).
- Modifying the per-app test bodies beyond the single inventory call (companions of code rows).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: `REQ-007` — add a route-inventory assertion reused by one test per MCP app
- **Source issue**: `issues/20261111-163724_mcproute001_remove-direct-mcp-routes.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261115-045455_mcproute001_remove-direct-mcp-routes.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261115-084338
- **Related target files**: `tests/mcp_servers/conftest.py`
