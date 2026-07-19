# Implementation: tests/test_mcp_tools_validation.py — enabled/disabled_reason coverage

Source plan: `plans/20260717-174024_plan.md` ("Add runtime availability metadata
(enabled / disabled_reason) to /v1/tools")

Note: an existing doc `implementations/20260718-090139_test_mcp_tools_validation.py.md`
matches this filename, but its Goal is "Add a new... pytest test... that asserts... no
tool dict contains the key `requires_config`... every tool dict contains
`config_dependent`" — this is for the sibling plan `plans/20260717-173602_plan.md`
(`requires_config` -> `config_dependent` rename), a different field entirely. Also two
`implementations/done/` docs (`20260709-160926_tests_test_mcp_tools_validation.md`,
`20260710-120509_tests_test_mcp_tools_validation.md`) match by filename but are about
subprocess/`os.killpg` teardown fixture fixes — unrelated. None cover `enabled`/
`disabled_reason`. Not previously implemented for this feature.

## Goal

Add new, fast (non-integration, no subprocess) pytest tests to
`tests/test_mcp_tools_validation.py` that exercise the file-server and git-server
`/v1/tools` handlers directly via `fastapi.testclient.TestClient`, with `_cfg`
monkeypatched, asserting the `enabled`/`disabled_reason` behavior specified in the plan
across every state combination.

## Scope

**In scope**: new test functions in `tests/test_mcp_tools_validation.py` covering:
- file server(s), `allowed_dirs=[]` → all tools `enabled=False`,
  `disabled_reason="allowed_dirs is empty"`.
- file server(s), `allowed_dirs=["/tmp"]` → all tools `enabled=True`,
  `disabled_reason=""`.
- git server, `allowed_repo_paths=[]` → all tools disabled with
  `"allowed_repo_paths is empty"`, regardless of `read_only` (both `True` and `False`
  sub-cases, to pin the precedence-order regression called out in the plan's Risks table).
- git server, `allowed_repo_paths=["/tmp"], read_only=True` → only the 5
  `GIT_WRITE_TOOLS` tools disabled with `"read_only=true"`; all other tools enabled with
  `""`.
- git server, `allowed_repo_paths=["/tmp"], read_only=False` → all tools enabled with
  `""`.
- schema-shape assertion: every tool in every `/v1/tools` response has a `bool` `enabled`
  key and a `str` `disabled_reason` key.

**Out of scope**: the existing `@pytest.mark.integration` subprocess-based tests
(`test_v1_tools_returns_expected_tools`, `test_v1_tools_each_has_name_and_description`) and
`test_read_tools_schema_matches_hand_written` — unaffected, left as-is. Shell/cicd servers
are out of scope per the plan's Scope section (feature not implemented there).

## Assumptions

- `tests/conftest.py` inserts `scripts/` onto `sys.path` (confirmed pattern used
  elsewhere in this file, e.g. `from mcp_servers.file.read_tools import TOOL_LIST` at
  line 148), so `from mcp_servers.file.read_server import app as read_app` (etc.) works
  directly.
- Pattern to follow: `tests/test_mdq_error_taxonomy.py` (`TestClient(app)` +
  `unittest.mock.patch`) and `tests/test_eventbus_ack_endpoint.py`
  (`monkeypatch.setattr(module, "load_config", lambda: cfg)` then `TestClient(app)`).
  For this feature: `monkeypatch.setattr(<server_module>, "_cfg", <Config instance>)`
  before constructing `TestClient(<server_module>.app)`, since each server module holds
  `_cfg` as a plain module-level global re-read on every request (confirmed: `_cfg` is
  referenced directly inside each `list_tools()`, not captured in a closure at import
  time, so monkeypatching the module attribute takes effect for requests made after the
  patch).
- Config classes construct directly without touching disk: `FileReadConfig(allowed_dirs=[])`,
  `FileWriteConfig(allowed_dirs=["/tmp"])`, `FileDeleteConfig(allowed_dirs=[])`,
  `GitConfig(allowed_repo_paths=["/tmp"], read_only=True)`, etc. — all plain
  `@dataclasses.dataclass` with defaulted fields (per the plan's Unknowns table,
  already verified).
- New tests must NOT be marked `@pytest.mark.integration` — they start no subprocess, only
  use in-process `TestClient`, so they belong in the fast/default test tier.
- Import module paths: `mcp_servers.file.read_server`, `mcp_servers.file.write_server`,
  `mcp_servers.file.delete_server`, `mcp_servers.git.server` (each module's `app` is the
  FastAPI instance and `_cfg` is the module-level config global to monkeypatch).

## Implementation

### Target file

`/home/sugimoto/llmagent/tests/test_mcp_tools_validation.py` (204 lines currently)

### Procedure

1. Add imports needed for the new tests near the top (after existing `import httpx` /
   `import pytest` at lines 22-23): `from fastapi.testclient import TestClient`. Import
   the four server modules and their Config dataclasses lazily inside each test function
   (matching the existing lazy-import style already used in
   `test_read_tools_schema_matches_hand_written`, which does
   `from mcp_servers.file.read_tools import TOOL_LIST` inside the test body, not at
   module level) — this avoids import-time side effects for servers not under test in a
   given run.
2. Insert new test functions after `test_read_tools_schema_matches_hand_written` (ends at
   line 165) and before the `@pytest.mark.integration` block starting at line 174 —
   same insertion point used by the sibling `config_dependent` test doc, so both new test
   additions land adjacent without conflicting insertion points (apply both plans as
   separate sequential commits per this plan's "SHARED WITH" note; re-diff before each
   commit).
3. Write one parametrized (or several discrete) test function(s) per state combination
   listed in Scope above, each: monkeypatch `_cfg` on the target server module, build a
   `TestClient(app)`, call `client.get("/v1/tools")`, assert `response.status_code == 200`,
   then assert per-tool `enabled`/`disabled_reason` values against the expected outcome.
4. Add one schema-shape test that runs against all 4 servers (file read/write/delete +
   git) with a "happy path" `_cfg` (non-empty `allowed_dirs`/`allowed_repo_paths`,
   `read_only=False`) asserting every tool dict has `isinstance(tool["enabled"], bool)`
   and `isinstance(tool["disabled_reason"], str)`.

### Method

Pseudocode (no production code blocks per design-doc convention):

```
def test_file_read_tools_disabled_when_allowed_dirs_empty(monkeypatch) -> None:
    from mcp_servers.file.read_models import FileReadConfig
    from mcp_servers.file import read_server
    monkeypatch.setattr(read_server, "_cfg", FileReadConfig(allowed_dirs=[]))
    client = TestClient(read_server.app)
    data = client.get("/v1/tools").json()
    for tool in data["tools"]:
        assert tool["enabled"] is False
        assert tool["disabled_reason"] == "allowed_dirs is empty"

def test_file_read_tools_enabled_when_allowed_dirs_set(monkeypatch) -> None:
    # allowed_dirs=["/tmp"] -> enabled=True, disabled_reason=""
    ...

# repeat shape for write_server / delete_server (parametrize over the 3 modules +
# their Config classes + server_key literal to avoid 3x copy-paste, OR write 3 separate
# small functions matching existing file style -- either is acceptable; prefer
# parametrize via pytest.mark.parametrize("module_path,config_cls", [...]) to keep the
# file from growing 3x as long)

def test_git_tools_disabled_when_allowed_repo_paths_empty_even_if_read_only_false(monkeypatch) -> None:
    from mcp_servers.git.git_models import GitConfig
    from mcp_servers.git import server as git_server
    monkeypatch.setattr(git_server, "_cfg", GitConfig(allowed_repo_paths=[], read_only=False))
    client = TestClient(git_server.app)
    data = client.get("/v1/tools").json()
    for tool in data["tools"]:
        assert tool["enabled"] is False
        assert tool["disabled_reason"] == "allowed_repo_paths is empty"
    # this pins the precedence order: allowed_repo_paths empty wins even though
    # read_only=False would otherwise enable everything

def test_git_write_tools_disabled_when_read_only_and_repo_paths_set(monkeypatch) -> None:
    from mcp_servers.git.git_models import GitConfig
    from mcp_servers.git import server as git_server
    from shared.tool_constants import GIT_WRITE_TOOLS
    monkeypatch.setattr(git_server, "_cfg", GitConfig(allowed_repo_paths=["/tmp"], read_only=True))
    client = TestClient(git_server.app)
    data = client.get("/v1/tools").json()
    for tool in data["tools"]:
        if tool["name"] in GIT_WRITE_TOOLS:
            assert tool["enabled"] is False
            assert tool["disabled_reason"] == "read_only=true"
        else:
            assert tool["enabled"] is True
            assert tool["disabled_reason"] == ""

def test_git_tools_all_enabled_when_repo_paths_set_and_not_read_only(monkeypatch) -> None:
    ...

def test_v1_tools_enabled_and_disabled_reason_have_correct_types(monkeypatch) -> None:
    # happy-path _cfg on all 4 servers; assert bool/str types on every tool dict
    ...
```

### Details

- Use `monkeypatch` fixture (function-scoped, auto-reverts) rather than manual
  save/restore of `_cfg` — matches the existing repo pattern in
  `tests/test_eventbus_ack_endpoint.py`.
- `TestClient(app)` does NOT start a subprocess or bind a real port — it is an in-process
  ASGI test client, so these tests run in the default (non-integration) tier and add
  negligible runtime.
- Precedence-order test (`allowed_repo_paths=[], read_only=False`) is the single most
  important new test — it directly pins the regression the plan's Risks table flags
  ("Precedence rule... implemented backwards, silently disabling read tools too... /
  enabling read tools when it shouldn't"). Do not skip this case even if parametrizing
  the rest.
- Exact string equality (not substring/regex) for `disabled_reason` values, per the
  plan's Risks table concern about literal-string drift.
- If parametrizing the 3 file servers, a compact table works well:
  `[(read_server, FileReadConfig, "file_read"), (write_server, FileWriteConfig,
  "file_write"), (delete_server, FileDeleteConfig, "file_delete")]`.

## Validation plan

| Check | Command | Target |
|---|---|---|
| New tests run and pass | `uv run pytest tests/test_mcp_tools_validation.py -k "enabled or disabled_reason" -v` | all pass |
| Existing tests unaffected | `uv run pytest tests/test_mcp_tools_validation.py -m "not integration" -v` | all pass |
| Format | `uv run ruff format tests/test_mcp_tools_validation.py` | clean |
| Lint | `uv run ruff check tests/test_mcp_tools_validation.py` | 0 errors |
| Type check | `uv run mypy tests/test_mcp_tools_validation.py` | no new errors |
| Coverage | `diff-cover` on changed lines in the 4 `server.py` files | >= 90%, all branches (both `if`/`elif`/`else` in git's precedence check) hit |

Full cross-file validation (mypy repo-wide, lint-imports, bandit, full pytest,
pre-commit, repo-wide grep for stray `"enabled"`/`disabled_reason` usages) is covered by
the cross-cutting doc `full_validation_pass_tools_enabled_disabled_reason.md`.
