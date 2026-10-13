## Goal
- Add the new real-application tests for the file-read, file-write, and file-delete servers: 401 without a token and with a wrong token on a tool route and on `/health`, success with the correct token, the fail-closed startup refusal, and the model and TOML loading checks (REQ-006; REQ-003; REQ-001, REQ-002).

## Scope
- In: one new test module; each test runs the real application in a separate interpreter, because the application reads its token at import time.
- Out: edits to existing tests (rows 16-28) and production code.

## Assumptions
- The server rows are applied in the same Plan step: rows 5-8 and 13-14 in Steps 5 and 6, and rows 9, 10, and 15 in Step 7 (the module is created in Step 5 for the read server and extended in Steps 6 and 7).
- `tests/conftest.py` keeps its `"test-token"` defaults; the tests below pass their own token (`unit-test-token`) to the subprocess and pin only the variable under test.
- `mcp_servers/file/__init__.py` imports `delete_server`, `read_server`, and `write_server`, so importing any one of them runs all three. Consequence for the tests: an empty token for one server makes every import of the package fail, and the error message names the server whose token is empty; the tests assert that message, not which module was imported. In production each server runs as its own process, but a process also refuses to start when any of the three file tokens is empty.

## Design decisions
- Follow `TestRealAppSharedToken` in `tests/mcp_servers/web_search/test_web_search_health.py`: a script string run with `sys.executable -c`, its JSON result asserted.
- Use an unknown tool name for the call route: with a valid token it must reach the handler (any status except 401), without a token it must be 401; no external call is made.
- Assert `!= 401` (not `== 200`) for `/health` and the call route with the correct token: readiness depends on the environment (for example the github server reports 503 when `GITHUB_TOKEN` is unset, which is not an authentication failure). `/v1/tools` is asserted to be exactly 200.

## Alternatives considered
- In-process `TestClient` tests: rejected — the token is captured at import time, so a different token per test needs a fresh interpreter; the process boundary also exercises the real import-time refusal.

## Implementation
### Target file
`tests/mcp_servers/file/test_file_server_auth.py` (new)

### Procedure
1. Create the module with the structure in Details.
2. Run it against the server rows of Plan Step 5.
3. Confirm the tests fail before the server change and pass after it.

### Method
- Pattern source: `tests/mcp_servers/web_search/test_web_search_health.py` (the `TestRealAppSharedToken` class); inbound-auth tests: `tests/mcp_servers/rag_pipeline/test_rag_pipeline_server_endpoints.py` (`TestInboundAuth`).
- Repository root from the test file: `Path(__file__).resolve().parents[3]` (the file sits three directories below it); the subprocess runs with `cwd` and `PYTHONPATH` set to the `scripts/` directory.
- Parametrize over the three servers (read, write, delete): module, variable, message name, model class, TOML file. In Step 5 only the read entry passes; add the write entry in Step 6 and the delete entry in Step 7 together with their server rows (until then the corresponding cases fail, so add each entry only with its server change).
- Substitutions are listed in the server table of the skeleton.

### Details
Module structure (a complete skeleton; adjust names only through `ruff format`):

```python
"""tests/mcp_servers/file/test_file_server_auth.py

Bearer authentication and fail-closed startup of the file-read, file-write, and
file-delete servers (REQ-003, REQ-004, REQ-006).

mcp_servers/file/__init__.py imports all three server modules, so importing any
one of them also runs the other two: an empty token for one server makes every
import fail, and the message names the server whose token is empty.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest
from mcp_servers.file.delete_models import FileDeleteConfig
from mcp_servers.file.read_models import FileReadConfig
from mcp_servers.file.write_models import FileWriteConfig

_REPO = Path(__file__).resolve().parents[3]
_SCRIPTS = _REPO / "scripts"
_TOKEN = "unit-test-token"

# (id, module, variable, server name used in the message, config class, TOML file)
_SERVERS = [
    ("read", "mcp_servers.file.read_server", "MCP_FILE_READ_AUTH_TOKEN", "file-read-mcp", FileReadConfig, "file_read_mcp_server.toml"),
    ("write", "mcp_servers.file.write_server", "MCP_FILE_WRITE_AUTH_TOKEN", "file-write-mcp", FileWriteConfig, "file_write_mcp_server.toml"),
    ("delete", "mcp_servers.file.delete_server", "MCP_FILE_DELETE_AUTH_TOKEN", "file-delete-mcp", FileDeleteConfig, "file_delete_mcp_server.toml"),
]
_IDS = [s[0] for s in _SERVERS]

_APP_SCRIPT = """
import json
import sys
from importlib import import_module

from fastapi.testclient import TestClient

mod = import_module(sys.argv[1])
client = TestClient(mod.app, client=("127.0.0.1", 50000), raise_server_exceptions=False)
good = {"Authorization": "Bearer " + sys.argv[2]}
wrong = {"Authorization": "Bearer some-other-token"}
call = {"name": "no_such_tool", "args": {}}
print(json.dumps({
    "tools_without_token": client.get("/v1/tools").status_code,
    "tools_wrong_token": client.get("/v1/tools", headers=wrong).status_code,
    "tools_good_token": client.get("/v1/tools", headers=good).status_code,
    "health_without_token": client.get("/health").status_code,
    "health_wrong_token": client.get("/health", headers=wrong).status_code,
    "health_good_token_is_401": client.get("/health", headers=good).status_code == 401,
    "call_without_token": client.post("/v1/call_tool", json=call).status_code,
    "call_good_token_is_401": client.post("/v1/call_tool", headers=good, json=call).status_code == 401,
}))
"""


def _run(args: list[str], env_var: str, token: str | None) -> subprocess.CompletedProcess[str]:
    """Run python in a separate interpreter; set, empty, or unset only the given variable."""
    env = {**os.environ, "PYTHONPATH": str(_SCRIPTS)}
    if token is None:
        env.pop(env_var, None)
    else:
        env[env_var] = token
    return subprocess.run(
        [sys.executable, *args],
        env=env, cwd=str(_SCRIPTS), capture_output=True, text=True, timeout=60, check=False,
    )


@pytest.mark.parametrize("_id, module, env_var, name, cfg_cls, toml", _SERVERS, ids=_IDS)
class TestFileServerAuth:
    def test_requests_require_the_token(self, _id, module, env_var, name, cfg_cls, toml) -> None:
        proc = _run(["-c", _APP_SCRIPT, module, _TOKEN], env_var, _TOKEN)
        assert proc.returncode == 0, proc.stderr[-500:]
        codes = json.loads(proc.stdout.strip().splitlines()[-1])
        assert codes == {
    "tools_without_token": 401,
    "tools_wrong_token": 401,
    "tools_good_token": 200,
    "health_without_token": 401,
    "health_wrong_token": 401,
    "health_good_token_is_401": False,
    "call_without_token": 401,
    "call_good_token_is_401": False,
}

    def test_empty_token_refuses_to_start(self, _id, module, env_var, name, cfg_cls, toml) -> None:
        proc = _run(["-c", f"import {module}"], env_var, "")
        assert proc.returncode != 0
        assert "RuntimeError" in proc.stderr
        assert f"{name}: auth_token is empty" in proc.stderr

    def test_unset_variable_fails_fast(self, _id, module, env_var, name, cfg_cls, toml) -> None:
        proc = _run(["-c", f"import {module}"], env_var, None)
        assert proc.returncode != 0
        assert "ValueError" in proc.stderr
        assert env_var in proc.stderr

    def test_model_loads_the_token(self, _id, module, env_var, name, cfg_cls, toml, monkeypatch: pytest.MonkeyPatch) -> None:
        assert cfg_cls.from_dict({}).auth_token == ""
        monkeypatch.setenv(env_var, "abc")
        assert cfg_cls.from_dict({"auth_token": "${ENV:" + env_var + "}"}).auth_token == "abc"
        monkeypatch.delenv(env_var, raising=False)
        with pytest.raises(ValueError):
            cfg_cls.from_dict({"auth_token": "${ENV:" + env_var + "}"})

    def test_shipped_toml_uses_the_agent_variable(self, _id, module, env_var, name, cfg_cls, toml) -> None:
        text = (_REPO / "config" / toml).read_text(encoding="utf-8")
        assert tomllib.loads(text)["auth_token"] == "${ENV:" + env_var + "}"
        agent = (_REPO / "config" / "agent.toml").read_text(encoding="utf-8")
        assert "${ENV:" + env_var + "}" in agent
```

## Compatibility considerations
- Test-only. The tests run in subprocesses (about a second each); they do not bind a network port.

## Security considerations
- Only dummy tokens appear; the unset and empty cases assert the refusal, which is the security property.

## Rollback considerations
- Delete the file (the server rows can stay, but then lose their tests).

## Validation plan
- `uv run ruff format tests/mcp_servers/file/test_file_server_auth.py` and `uv run ruff check tests/mcp_servers/file/test_file_server_auth.py --fix`; `uv run mypy --no-namespace-packages scripts/` is unaffected.
- `uv run pytest tests/mcp_servers/file/test_file_server_auth.py -q` and `uv run pytest tests/mcp_servers -q -rs`.
- Negative check: temporarily reverting a server edit makes the corresponding test fail (do this locally; do not commit it).

## Completion criteria
- All tests in the module pass with the server rows applied, and the 401, fail-closed, and loading cases each fail when the matching server edit is absent.

## Out of scope
- Changing existing tests, the helper module, or production code.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Create the test module | Pending | — | — | Plan Step 5 |
| 2 | Run it against the server rows and check the negative case locally | Pending | — | — |  |
| 3 | Run `tests/mcp_servers` and the validation sequence (`rules/toolchain.md`) | Pending | — | — |  |

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
- **Requirement ID**: `REQ-006` (new real-application tests), `REQ-003` (fail-closed startup), `REQ-001` and `REQ-002` (model and TOML loading)
- **Source issue**: issues/20261013-113008_mcp007_register-bearer-auth-in-shell-github-file-mcp-servers.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261013-120538_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261013-123717
- **Related target files**: tests/mcp_servers/file/test_file_server_auth.py
