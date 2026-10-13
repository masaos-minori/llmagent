## Goal
- Add the new real-application tests for the GitHub server: 401 without a token and with a wrong token on a tool route and on `/health`, success with the correct token, the fail-closed startup refusal, and the model and TOML loading checks (REQ-006; REQ-003; REQ-001, REQ-002).

## Scope
- In: one new test module; each test runs the real application in a separate interpreter, because the application reads its token at import time.
- Out: edits to existing tests (rows 16-28) and production code.

## Assumptions
- The server rows are applied in the same Plan step: rows 3, 4, and 12.
- `tests/conftest.py` keeps its `"test-token"` defaults; the tests below pass their own token (`unit-test-token`) to the subprocess and pin only the variable under test.
- With `GITHUB_TOKEN` unset the application still imports (the log line "GITHUB_TOKEN is not set" is informational) and `/health` answers 503 for readiness; the tests therefore never assert 200 on `/health`.

## Design decisions
- Follow `TestRealAppSharedToken` in `tests/mcp_servers/web_search/test_web_search_health.py`: a script string run with `sys.executable -c`, its JSON result asserted.
- Use an unknown tool name for the call route: with a valid token it must reach the handler (any status except 401), without a token it must be 401; no external call is made.
- Assert `!= 401` (not `== 200`) for `/health` and the call route with the correct token: readiness depends on the environment (for example the github server reports 503 when `GITHUB_TOKEN` is unset, which is not an authentication failure). `/v1/tools` is asserted to be exactly 200.

## Alternatives considered
- In-process `TestClient` tests: rejected — the token is captured at import time, so a different token per test needs a fresh interpreter; the process boundary also exercises the real import-time refusal.

## Implementation
### Target file
`tests/mcp_servers/github/test_github_server_auth.py` (new)

### Procedure
1. Create the module with the structure in Details.
2. Run it against the server rows of Plan Step 4.
3. Confirm the tests fail before the server change and pass after it.

### Method
- Pattern source: `tests/mcp_servers/web_search/test_web_search_health.py` (the `TestRealAppSharedToken` class); inbound-auth tests: `tests/mcp_servers/rag_pipeline/test_rag_pipeline_server_endpoints.py` (`TestInboundAuth`).
- Repository root from the test file: `Path(__file__).resolve().parents[3]` (the file sits three directories below it); the subprocess runs with `cwd` and `PYTHONPATH` set to the `scripts/` directory.
- Substitutions: module `mcp_servers.github.github_server`, variable `MCP_GITHUB_AUTH_TOKEN`, model `GitHubConfig` from `mcp_servers.github.github_models_config`, TOML `github_mcp_server.toml`, message `github-mcp: auth_token is empty`.

### Details
Module structure (a complete skeleton; adjust names only through `ruff format`):

```python
"""tests/mcp_servers/github/test_github_server_auth.py

Bearer authentication and fail-closed startup of github-mcp (REQ-003, REQ-004, REQ-006).
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest
from mcp_servers.github.github_models_config import GitHubConfig

_REPO = Path(__file__).resolve().parents[3]
_SCRIPTS = _REPO / "scripts"
_MODULE = "mcp_servers.github.github_server"
_ENV_VAR = "MCP_GITHUB_AUTH_TOKEN"
_TOKEN = "unit-test-token"

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


def _run(args: list[str], token: str | None) -> subprocess.CompletedProcess[str]:
    """Run python in a separate interpreter with the server variable set, empty, or unset."""
    env = {**os.environ, "PYTHONPATH": str(_SCRIPTS)}
    if token is None:
        env.pop(_ENV_VAR, None)
    else:
        env[_ENV_VAR] = token
    return subprocess.run(
        [sys.executable, *args],
        env=env, cwd=str(_SCRIPTS), capture_output=True, text=True, timeout=60, check=False,
    )


class TestRealAppAuthentication:
    def test_requests_require_the_token(self) -> None:
        proc = _run(["-c", _APP_SCRIPT, _MODULE, _TOKEN], token=_TOKEN)
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


class TestFailClosedStartup:
    def test_empty_token_refuses_to_start(self) -> None:
        proc = _run(["-c", f"import {_MODULE}"], token="")
        assert proc.returncode != 0
        assert "RuntimeError" in proc.stderr
        assert "github-mcp: auth_token is empty" in proc.stderr

    def test_unset_variable_fails_fast(self) -> None:
        proc = _run(["-c", f"import {_MODULE}"], token=None)
        assert proc.returncode != 0
        assert "ValueError" in proc.stderr
        assert _ENV_VAR in proc.stderr

    def test_non_empty_token_imports(self) -> None:
        assert _run(["-c", f"import {_MODULE}"], token=_TOKEN).returncode == 0


class TestGitHubConfigAuthToken:
    def test_default_is_empty(self) -> None:
        assert GitHubConfig.from_dict({}).auth_token == ""

    def test_env_reference_is_resolved(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(_ENV_VAR, "abc")
        cfg = GitHubConfig.from_dict({"auth_token": "${ENV:" + _ENV_VAR + "}"})
        assert cfg.auth_token == "abc"

    def test_unset_reference_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv(_ENV_VAR, raising=False)
        with pytest.raises(ValueError):
            GitHubConfig.from_dict({"auth_token": "${ENV:" + _ENV_VAR + "}"})

    def test_shipped_toml_uses_the_agent_variable(self) -> None:
        text = (_REPO / "config" / "github_mcp_server.toml").read_text(encoding="utf-8")
        assert tomllib.loads(text)["auth_token"] == "${ENV:" + _ENV_VAR + "}"
        agent = (_REPO / "config" / "agent.toml").read_text(encoding="utf-8")
        assert "${ENV:" + _ENV_VAR + "}" in agent
```

## Compatibility considerations
- Test-only. The tests run in subprocesses (about a second each); they do not bind a network port.

## Security considerations
- Only dummy tokens appear; the unset and empty cases assert the refusal, which is the security property.

## Rollback considerations
- Delete the file (the server rows can stay, but then lose their tests).

## Validation plan
- `uv run ruff format tests/mcp_servers/github/test_github_server_auth.py` and `uv run ruff check tests/mcp_servers/github/test_github_server_auth.py --fix`; `uv run mypy --no-namespace-packages scripts/` is unaffected.
- `uv run pytest tests/mcp_servers/github/test_github_server_auth.py -q` and `uv run pytest tests/mcp_servers -q -rs`.
- Negative check: temporarily reverting a server edit makes the corresponding test fail (do this locally; do not commit it).

## Completion criteria
- All tests in the module pass with the server rows applied, and the 401, fail-closed, and loading cases each fail when the matching server edit is absent.

## Out of scope
- Changing existing tests, the helper module, or production code.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Create the test module | Completed | — | — | Plan Step 4 |
| 2 | Run it against the server rows and check the negative case locally | Completed | — | — |  |
| 3 | Run `tests/mcp_servers` and the validation sequence (`rules/toolchain.md`) | Completed | — | — |  |

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
- **Related target files**: tests/mcp_servers/github/test_github_server_auth.py