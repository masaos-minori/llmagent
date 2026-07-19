# Implementation procedure: `tests/test_mcp_tool_discovery.py` (schema validation test matrix)

Source plan: `plans/20260717-131019_plan.md` ("Add MCP tool schema versioning and validation tests"),
Implementation step 4.

**Relationship to existing docs with a similar filename**: `implementations/20260717-203931_test_mcp_tool_discovery.py.md`
and `implementations/20260717-224812_test_mcp_tool_discovery.py.md` both target
`tests/agent/services/test_mcp_tool_discovery.py` (a **nested** path) and cover
`McpToolDiscoveryService.discover_all()`'s own unit behavior (mocked HTTP fetch, schema
validation/normalization, duplicate-name/drift detection, unified severity) for requirements 03/09.
**Flagged explicitly as a real path/scope mismatch, not a silent skip**: this plan's own Assumption 2
states — confirmed via direct `ls`/`find` — that `tests/agent/services/` does not exist as a directory in
this repo, and the real, flat-layout convention is `tests/test_mcp_tool_discovery.py` (no subdirectory).
Additionally, this plan's Assumption 4 requires a **per-server test matrix against each server's actual
`TOOL_LIST`/real FastAPI app** (not only the mocked-`httpx` discovery-service unit tests those two prior
docs specify) — a genuinely different, additive test surface. This doc's test cases are new; they do not
duplicate the mocked `discover_all()` unit tests in the two prior docs (which remain valid for whenever
`McpToolDiscoveryService` itself is implemented, at the path corrected by this doc).

## Goal

Create `tests/test_mcp_tool_discovery.py` (flat path — confirmed the real convention, not
`tests/agent/services/test_mcp_tool_discovery.py`) with a parametrized test matrix that runs against each
of the 9 in-scope MCP servers' **real, importable FastAPI app** and **real `TOOL_LIST`**, asserting: (1)
`/v1/tools` response includes `schema_version`, (2) every tool has non-empty `name` and `description`, (3)
`inputSchema` is an object/dict, (4) optional fields `status`/`is_write`/`requires_serial`/`resource_scope`
are correctly typed when present, and (5) any failure names both the offending `server_key` and tool
`name` in its assertion message. Also includes a synthetic-fixture test confirming a response lacking
`schema_version` is still accepted (migration tolerance).

## Scope

**In scope**
- New file `tests/test_mcp_tool_discovery.py`.
- Per-server test matrix using real `app_module` imports (mirrors `tests/test_mcp_server_base.py`'s
  `TestAppModuleImportability` pattern, confirmed at lines 323-343 of that file) plus FastAPI's
  `TestClient` to call each server's real `/v1/tools` route and assert on the actual JSON response.
- A synthetic (non-HTTP, dict-literal) fixture test for the missing-`schema_version` tolerance case,
  since this exercises `McpToolDiscoveryService`'s parsing tolerance (per
  `implementations/20260718-084109_mcp_tool_discovery.py.md`) rather than the servers' own response shape
  (which, once step 2's rollout lands, will always include `schema_version` — the tolerance path is only
  reachable via a hand-built fixture simulating an older/non-migrated server).

**Out of scope (tracked separately / already covered)**
- Mocked-HTTP unit tests of `McpToolDiscoveryService.discover_all()` itself (fetch loop, dedup, drift,
  unified severity) — tracked by `implementations/20260717-203931_test_mcp_tool_discovery.py.md` and
  `implementations/20260717-224812_test_mcp_tool_discovery.py.md`. Those docs' nested target path
  (`tests/agent/services/test_mcp_tool_discovery.py`) should be corrected to the flat path
  (`tests/test_mcp_tool_discovery.py`) at implementation time, and their test classes merged into the same
  physical file this doc creates — flagged here so the two implementation efforts land in the same file,
  not two files with the same basename in different directories.
- Full validation sequence — tracked separately in
  `implementations/20260718-084253_full_validation_pass_mcp_schema_version.md` (this plan's own scoped
  validation doc, per the batch-wide convention that the generic `full_validation_pass` slug is not
  interchangeable across plans).

## Assumptions

1. **Per-server real-app testing mirrors `tests/test_mcp_server_base.py:323-343`'s existing
   `TestAppModuleImportability` pattern** (confirmed by direct read): that test globs
   `scripts/mcp_servers/**/*server.py`, regex-extracts each `app_module` string, and confirms
   `importlib.util.find_spec()` succeeds. This doc's matrix goes one step further — actually importing
   each of the 9 in-scope app modules and using `fastapi.testclient.TestClient(app).get("/v1/tools")` to
   fetch the real response, rather than only checking importability.
2. **The 9-server list is explicit, not glob-discovered** — deliberately mirroring
   `implementations/20260718-084035_mcp_server_schema_version_rollout.md`'s Scope table (`mdq`, `cicd`,
   `github`, `git`, `web_search`, `shell`, `file_read`→`file/read_server.py`, `file_write`→
   `file/write_server.py`, `file_delete`→`file/delete_server.py`). A blind
   `scripts_dir.glob("mcp_servers/**/*server.py")` (as `TestAppModuleImportability` uses) would also match
   `scripts/mcp_servers/rag_pipeline/server.py` and `scripts/mcp_servers/server.py` itself (the base
   class, no `TOOL_LIST`/app) — both would spuriously fail a `schema_version`-presence assertion since
   `rag_pipeline` is explicitly out of scope for this plan (see the rollout doc's Out-of-scope). Using an
   explicit, hardcoded list of `(module_path, app_attr, server_key)` tuples for the 9 in-scope servers
   avoids this false failure.
3. **`TestClient` usage mirrors `tests/test_mcp_server_base.py:95-104`'s `_make_test_app()` helper**
   (confirmed by direct read) — `TestClient(app, raise_server_exceptions=True)`. Each of the 9 real `app`
   objects can be imported directly (e.g. `from mcp_servers.mdq.mdq_server import app as mdq_app`) and wrapped
   the same way; no server process/uvicorn needs to actually run for these tests (FastAPI's `TestClient`
   calls the ASGI app in-process).
4. **`status`/`is_write`/`requires_serial` values observed in real `TOOL_LIST`s today** (confirmed via
   grep): `status` is present as a string (`"production"`) on every tool across all sampled servers;
   `is_write`/`requires_serial` are present as booleans on a subset of `mdq`'s tools
   (`mdq/tools.py:106-107,124-125`) and absent elsewhere; `resource_scope` is not present in any
   `TOOL_LIST` today (confirmed zero matches under `scripts/mcp_servers/*/tools.py`) — the test for this
   field must therefore validate "type-checked only if present" without requiring any current server to
   actually populate it (a type-check test using a synthetic fixture is the only way to exercise the
   `resource_scope`-present branch until some server adds it).
5. Once `implementations/20260718-084109_mcp_tool_discovery.py.md`'s addition and the base/extension docs
   (203830, 224511) land, `McpToolDiscoveryService` will exist and can be tested for the
   missing-`schema_version` tolerance case directly (per that doc's target). Until that service exists,
   this test can still be written against a hand-built dict fixture representing "what a non-migrated
   server's `/v1/tools` response would look like" and fed through whichever validation function
   `McpToolDiscoveryService` exposes (per the base doc's `_validate_and_normalize_entry`) — implement in
   the same PR/commit as the service itself so the import target is valid.

## Implementation

### Target file

`tests/test_mcp_tool_discovery.py` (new file, flat path under `tests/`).

### Procedure

1. Module docstring: state scope — real-app schema validation matrix for all 9 in-scope MCP servers'
   `/v1/tools` endpoints, plus a migration-tolerance test for the discovery service's `schema_version`
   handling.
2. Define a module-level constant listing the 9 in-scope servers as
   `(import_path: str, app_attr: str, server_key: str)` tuples, e.g.:
   ```
   _IN_SCOPE_SERVERS = [
       ("mcp_servers.mdq.server", "app", "mdq"),
       ("mcp_servers.cicd.server", "app", "cicd"),
       ("mcp_servers.github.server", "app", "github"),
       ("mcp_servers.git.server", "app", "git"),
       ("mcp_servers.web_search.server", "app", "web_search"),
       ("mcp_servers.shell.server", "app", "shell"),
       ("mcp_servers.file.read_server", "app", "file_read"),
       ("mcp_servers.file.write_server", "app", "file_write"),
       ("mcp_servers.file.delete_server", "app", "file_delete"),
   ]
   ```
   (Confirm each module's actual FastAPI app attribute name is `app` at implementation time — all 9
   files were confirmed to define `app = FastAPI(...)` at module scope during investigation.)
3. Test class `TestToolsEndpointSchemaVersion` — one `@pytest.mark.parametrize` test over
   `_IN_SCOPE_SERVERS`: `importlib.import_module(import_path)`, get the `app` attribute,
   `TestClient(app).get("/v1/tools")`, assert `response.status_code == 200` and
   `"schema_version" in response.json()` and `response.json()["schema_version"]` is a non-empty string —
   failure message includes the `server_key` under test.
4. Test class `TestToolsEndpointToolShape` — same parametrization; for each tool dict in
   `response.json()["tools"]`: assert `tool["name"]` is a non-empty `str`; assert `tool["description"]` is
   a non-empty `str`; assert `isinstance(tool["inputSchema"], dict)`; if `"status"` present, assert
   `isinstance(tool["status"], str)`; if `"is_write"` present, assert `isinstance(tool["is_write"], bool)`;
   if `"requires_serial"` present, assert `isinstance(tool["requires_serial"], bool)`; if
   `"resource_scope"` present, assert `isinstance(tool["resource_scope"], str)`. Every assertion message
   includes `f"[{server_key}] tool {tool.get('name')!r}: ..."` (mirrors `repl_health.py`'s existing
   `f"[{server_key}] tool {t!r}..."` message-format convention, confirmed established in requirement 09's
   investigation).
5. Test function `test_resource_scope_type_checked_when_present_synthetic` — since no real `TOOL_LIST`
   currently populates `resource_scope` (Assumption 4), construct a synthetic tool-entry dict with a
   `resource_scope` field of the wrong type (e.g. an int) and assert the shared validation helper (whatever
   `McpToolDiscoveryService._validate_and_normalize_entry`-equivalent function is exposed — resolve exact
   import at implementation time per Assumption 5) flags it, and a second synthetic entry with a correctly
   typed `str` value passes.
6. Test function `test_missing_schema_version_tolerated` — synthetic fixture: a dict shaped like
   `{"tools": [...]}` with **no** `schema_version` key, fed through the discovery service's per-server
   parse step; assert no error/warning/`StartupCheckOutcome` is produced solely due to the missing key
   (per `implementations/20260718-084109_mcp_tool_discovery.py.md`).

### Method

Real `TestClient` calls against real, importable `app` objects for the schema/shape matrix (classes 1-2) —
no mocking needed since these are pure in-process ASGI calls with no external I/O. Plain synthetic
dict fixtures (no HTTP) for the two service-level tolerance/type-check tests (5-6), following whatever
mocking convention `tests/test_repl_health.py`/the base discovery-service test doc establishes for
`McpToolDiscoveryService`-level tests (see `implementations/20260717-203931_test_mcp_tool_discovery.py.md`'s
Assumption 1 for the established `AsyncMock`/`MagicMock` pattern, if the validation helper under test is
async).

### Details

Pseudocode only (no production code):

```
_IN_SCOPE_SERVERS = [
    ("mcp_servers.mdq.server", "app", "mdq"),
    # ... 8 more, per Procedure step 2 ...
]


class TestToolsEndpointSchemaVersion:
    @pytest.mark.parametrize("import_path, app_attr, server_key", _IN_SCOPE_SERVERS)
    def test_schema_version_present(self, import_path: str, app_attr: str, server_key: str) -> None: ...
        # module = importlib.import_module(import_path)
        # client = TestClient(getattr(module, app_attr), raise_server_exceptions=True)
        # body = client.get("/v1/tools").json()
        # assert "schema_version" in body, f"[{server_key}] missing schema_version"
        # assert isinstance(body["schema_version"], str) and body["schema_version"]


class TestToolsEndpointToolShape:
    @pytest.mark.parametrize("import_path, app_attr, server_key", _IN_SCOPE_SERVERS)
    def test_every_tool_matches_schema(self, import_path: str, app_attr: str, server_key: str) -> None: ...
        # for tool in body["tools"]:
        #     assert tool.get("name"), f"[{server_key}] tool {tool!r}: missing/empty name"
        #     assert tool.get("description"), f"[{server_key}] tool {tool.get('name')!r}: missing description"
        #     assert isinstance(tool.get("inputSchema"), dict), f"[{server_key}] tool {tool.get('name')!r}: inputSchema not object"
        #     # optional-field type checks, only if present, per Procedure step 4


def test_resource_scope_type_checked_when_present_synthetic() -> None: ...


def test_missing_schema_version_tolerated() -> None: ...
```

## Validation plan

| Check | Command | Target |
|---|---|---|
| Format/lint | `uv run ruff format tests/test_mcp_tool_discovery.py && uv run ruff check tests/test_mcp_tool_discovery.py` | 0 errors |
| Type check | `uv run mypy tests/test_mcp_tool_discovery.py` | 0 errors |
| Schema validation matrix | `uv run pytest tests/test_mcp_tool_discovery.py -v` | all 9 servers pass schema_version-presence and tool-shape checks; synthetic tests pass |
| Failure identification spot check | manually break one server's `TOOL_LIST` (e.g. empty `name`) locally and re-run | assertion message names the exact `server_key` and tool |
| No regression | `uv run pytest tests/test_mcp_server_base.py -v` | unaffected — this is a new file, no shared fixtures modified |
| Full suite | `uv run pytest -v` | no new failures |
| Diff coverage | `uv run coverage run -m pytest tests/ && uv run coverage xml && uv run diff-cover coverage.xml --compare-branch=main --fail-under=90` | meets project threshold on this new file's lines |
