# Implementation: tests/test_call_tool_validation.py (new file) — /v1/call_tool disabled-tool gate + validate_args coverage

Source plan: `plans/20260717-174848_plan.md` ("Reject disabled tools before dispatch in
/v1/call_tool and clarify validation policy")

Checked `implementations/` and `implementations/done/` for filename matches against
`call_tool_validation` / `test_call_tool`: no hits (only unrelated
`20260610-142752_audit_validators_models_py.md`, about audit-log validator field names,
no relation to `/v1/call_tool`). Also checked `20260718-090741_test_mcp_tools_validation.py.md`
— its Goal is new tests for `GET /v1/tools`'s `enabled`/`disabled_reason` fields
(requirement 15), a different endpoint and a different test file
(`tests/test_mcp_tools_validation.py`, not `tests/test_call_tool_validation.py`). Not
previously implemented/documented for this feature.

## Goal

Add a new test file `tests/test_call_tool_validation.py` with `TestClient`-based tests
exercising `POST /v1/call_tool` on the file-read, file-write, file-delete, and git
servers, covering: disabled-tool rejection (per server's config), the
`validate_args()` call path (both success and `ValueError` cases), and proof that a
disabled tool's handler/dispatch table is never reached.

## Scope

**In scope**: new file `tests/test_call_tool_validation.py` with test functions covering:
- File servers (read/write/delete), `allowed_dirs=[]` → `POST /v1/call_tool` returns
  `is_error=True`, `result="Tool disabled: allowed_dirs is empty"`, for any tool name.
- File servers, `allowed_dirs=["/tmp"]` (or a `tmp_path`) → a valid call proceeds to
  dispatch (not rejected as disabled).
- Git server, `allowed_repo_paths=[]` → any git tool (read or write) call returns
  `is_error=True`, `result="Tool disabled: allowed_repo_paths is empty"`, regardless of
  `read_only` (both `True`/`False` sub-cases — pins the precedence-order regression).
- Git server, `allowed_repo_paths=["/tmp"], read_only=True` → a write tool (e.g.
  `git_commit`) call returns `is_error=True`,
  `result="Tool disabled: read_only=true"`; a read tool (e.g. `git_status`) call is NOT
  rejected as disabled (proceeds past the gate).
- `validate_args()` invoked case: a tool with a registered validator (e.g. `git_commit`
  with a blank/missing `message` arg, on an otherwise-enabled git server) returns
  `is_error=True`, `result` starting with `"Validation error: "`.
- A tool with no registered validator still dispatches successfully after the change
  (validate_args() no-op path does not block it).
- Disabled-tool handler-never-invoked proof: monkeypatch the server's dispatch table (or
  `_dispatch_<x>_tool` function) with a spy/sentinel that raises `AssertionError` if
  called; assert it is never called when the tool is disabled, and IS called when
  enabled.

**Out of scope**: shell/cicd/github/rag_pipeline/mdq/web_search servers (not in this
plan's Target files; identical gap confirmed via grep but explicitly deferred as a
follow-up candidate per the plan's Unknowns table). `tests/test_mcp_tools_validation.py`
(unaffected — that file covers `GET /v1/tools`, a different endpoint, for the sibling
requirement 15). `tests/test_mcp_tool_validators.py` (unaffected — unit tests for
`validate_tool_args()`/`register_validator()` themselves, not the HTTP endpoint).

## Assumptions

- `tests/conftest.py` puts `scripts/` on `sys.path`, so
  `from mcp_servers.file.read_server import app as read_app` (and write/delete/git
  equivalents) works directly, matching the existing pattern in
  `tests/test_mcp_tools_validation.py`.
- Pattern to follow (confirmed by reading `tests/test_eventbus_ack_endpoint.py` and
  `tests/test_mcp_tool_validators.py`): `monkeypatch.setattr(<server_module>, "_cfg",
  <ConfigInstance>)` then `TestClient(<server_module>.app)`; each server module's `_cfg`
  is a plain module-level global read fresh inside each handler (not captured in a
  closure at import time), so monkeypatching the module attribute takes effect for
  requests made after the patch — same assumption already used and verified true by the
  sibling requirement-15 test doc.
- Config classes construct directly without touching disk (confirmed via
  `read_models.py`/`write_models.py`/`delete_models.py`/`git/models.py`): e.g.
  `FileReadConfig(allowed_dirs=[])`, `GitConfig(allowed_repo_paths=["/tmp"],
  read_only=True)`.
- `req.validate_args()` and `CallToolRequest`/`CallToolResponse` are unchanged by this
  plan (only the four servers' `call_tool()` handlers change) — tests import
  `CallToolRequest`/`CallToolResponse`'s effect only indirectly, via HTTP JSON
  request/response through `TestClient`, not by constructing the Pydantic models
  directly.
- `git_commit`'s registered validator (in `tool_validators.py`, exercised by
  `tests/test_mcp_tool_validators.py`) raises `ValueError` for a blank/missing
  `message` argument — used as the concrete validate_args-triggering case.
- New tests must NOT be marked `@pytest.mark.integration` — `TestClient` is in-process,
  no subprocess.

## Implementation

### Target file

`/home/sugimoto/llmagent/tests/test_call_tool_validation.py` (new file)

### Procedure

1. Create the new file with a module docstring identifying its purpose (disabled-tool
   gate + validate_args coverage for `/v1/call_tool` on file-read/write/delete and git
   servers), `from __future__ import annotations`, and imports: `pytest`,
   `fastapi.testclient.TestClient`. Import server modules and Config dataclasses lazily
   inside each test function (matches the lazy-import style already used in
   `tests/test_mcp_tools_validation.py`), to avoid import-time side effects for servers
   not under test in a given run.
2. Write a parametrized or discrete set of test functions for the file servers (read/
   write/delete) covering the disabled (`allowed_dirs=[]`) and enabled
   (`allowed_dirs=["/tmp"]` or `tmp_path`) cases from Scope, using a representative tool
   name per server (e.g. `list_directory` for read, `write_file` for write,
   `delete_file` for delete) via `client.post("/v1/call_tool", json={"name": ...,
   "args": {...}})`.
3. Write test functions for the git server covering: `allowed_repo_paths=[]` with both
   `read_only=True` and `read_only=False` (both must reject with
   `"allowed_repo_paths is empty"`); `allowed_repo_paths=["/tmp"], read_only=True` with a
   write tool (rejected, `"read_only=true"`) and a read tool (not rejected as disabled).
4. Write the validate_args-triggering test: enabled git server, `git_commit` call with a
   blank/missing `message` arg → `is_error=True`,
   `result.startswith("Validation error: ")`.
5. Write the handler-never-invoked test: monkeypatch the target server's
   `_dispatch_<x>_tool` function (or its underlying service dispatch table) with a
   spy that raises `AssertionError("dispatch must not be called for a disabled tool")` if
   invoked; call a disabled tool via `/v1/call_tool`; assert the response is the
   disabled-tool response and the spy was never called. Repeat (or parametrize) for an
   enabled call to confirm the spy path IS reachable in that case (positive control).
6. Ensure every response assertion checks both `is_error` and the exact `result` string
   (not substring, except the `"Validation error: "` prefix case which by nature includes
   a dynamic exception message suffix) — exact-string matching per the plan's Risks table
   concern about literal-string drift.

### Method

Pseudocode (no production code blocks per design-doc convention):

```
def test_file_read_call_tool_disabled_when_allowed_dirs_empty(monkeypatch) -> None:
    from mcp_servers.file.read_models import FileReadConfig
    from mcp_servers.file import read_server
    monkeypatch.setattr(read_server, "_cfg", FileReadConfig(allowed_dirs=[]))
    client = TestClient(read_server.app)
    resp = client.post("/v1/call_tool", json={"name": "list_directory", "args": {"path": "/tmp"}})
    data = resp.json()
    assert data["is_error"] is True
    assert data["result"] == "Tool disabled: allowed_dirs is empty"

def test_file_read_call_tool_dispatch_not_reached_when_disabled(monkeypatch) -> None:
    from mcp_servers.file.read_models import FileReadConfig
    from mcp_servers.file import read_server
    def _spy(name, args):
        raise AssertionError("dispatch must not be called for a disabled tool")
    monkeypatch.setattr(read_server, "_cfg", FileReadConfig(allowed_dirs=[]))
    monkeypatch.setattr(read_server, "_dispatch_read_tool", _spy)
    client = TestClient(read_server.app)
    resp = client.post("/v1/call_tool", json={"name": "list_directory", "args": {"path": "/tmp"}})
    assert resp.json()["is_error"] is True  # spy never raised -> handler returned early

def test_git_call_tool_disabled_when_repo_paths_empty_even_if_read_only_false(monkeypatch) -> None:
    from mcp_servers.git.git_models import GitConfig
    from mcp_servers.git import server as git_server
    monkeypatch.setattr(git_server, "_cfg", GitConfig(allowed_repo_paths=[], read_only=False))
    client = TestClient(git_server.app)
    resp = client.post("/v1/call_tool", json={"name": "git_status", "args": {"repo": "/tmp"}})
    data = resp.json()
    assert data["is_error"] is True
    assert data["result"] == "Tool disabled: allowed_repo_paths is empty"

def test_git_call_tool_write_tool_disabled_when_read_only(monkeypatch) -> None:
    from mcp_servers.git.git_models import GitConfig
    from mcp_servers.git import server as git_server
    monkeypatch.setattr(git_server, "_cfg", GitConfig(allowed_repo_paths=["/tmp"], read_only=True))
    client = TestClient(git_server.app)
    resp = client.post("/v1/call_tool", json={"name": "git_commit", "args": {"repo": "/tmp", "message": "x"}})
    data = resp.json()
    assert data["is_error"] is True
    assert data["result"] == "Tool disabled: read_only=true"

def test_git_call_tool_validate_args_rejects_blank_commit_message(monkeypatch) -> None:
    from mcp_servers.git.git_models import GitConfig
    from mcp_servers.git import server as git_server
    monkeypatch.setattr(git_server, "_cfg", GitConfig(allowed_repo_paths=["/tmp"], read_only=False))
    client = TestClient(git_server.app)
    resp = client.post("/v1/call_tool", json={"name": "git_commit", "args": {"repo": "/tmp", "message": ""}})
    data = resp.json()
    assert data["is_error"] is True
    assert data["result"].startswith("Validation error: ")

# repeat file-server disabled/enabled/spy shape for write_server / delete_server
# (parametrize over module + Config class + representative tool name to avoid 3x
# copy-paste, matching the sibling test doc's stated preference)
```

### Details

- Use the `monkeypatch` fixture (function-scoped, auto-reverts) for both `_cfg` and any
  dispatch-function spy — consistent with repo convention.
- `TestClient(app)` is in-process ASGI, no subprocess — tests belong in the default
  (non-integration) tier.
- The handler-never-invoked test is the single most important new test for this plan: it
  directly proves the requirement's core guarantee ("Do not call the service dispatch
  table for disabled tools"), not just that the response text looks right.
- Exact string equality for `disabled_reason`/`result`, per the plan's Risks table
  concern about literal-string drift and the plan's Assumption that a future
  `RuntimeToolRegistry` client may parse this string.
- If parametrizing the 3 file servers, a compact table works well:
  `[(read_server, FileReadConfig, "list_directory", {"path": "/tmp"}),
  (write_server, FileWriteConfig, "write_file", {...}), (delete_server,
  FileDeleteConfig, "delete_file", {...})]`.

## Validation plan

| Check | Command | Target |
|---|---|---|
| New tests run and pass | `uv run pytest tests/test_call_tool_validation.py -v` | all pass |
| Existing validator tests unaffected | `uv run pytest tests/test_mcp_tool_validators.py -v` | all pass |
| Format | `uv run ruff format tests/test_call_tool_validation.py` | clean |
| Lint | `uv run ruff check tests/test_call_tool_validation.py` | 0 errors |
| Type check | `uv run mypy tests/test_call_tool_validation.py` | no new errors |
| Coverage | `diff-cover` on changed lines in the 4 server files | >= 90%, all new branches (disabled/validate_args/dispatch) hit |

Full cross-file validation is covered by the cross-cutting doc
`full_validation_pass_call_tool_disabled_gate.md`.
