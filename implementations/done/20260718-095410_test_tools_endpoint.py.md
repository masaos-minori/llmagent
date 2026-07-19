# Implementation: tests/test_tools_endpoint.py — live /v1/tools enabled/disabled_reason validation (new file)

Source plan: `plans/20260717-175630_plan.md` ("Add schema tests for MCP runtime availability
metadata", requirement 18), Implementation step 3.

Checked `implementations/` and `implementations/done/` for any filename containing
`test_tools_endpoint` — no match exists (confirmed via `grep -rln "test_tools_endpoint"
implementations/*.md`, zero results). The real file `tests/test_tools_endpoint.py` does not exist
yet either. Not previously documented as its own file.

**Important overlap flag (not a filename match, but a functional one — surfaced because the plan's
own "SHARED WITH" note in Scope explicitly calls this out)**: an existing doc,
`implementations/20260718-090741_test_mcp_tools_validation.py.md` (requirement 15's own test
addition, source plan `plans/20260717-174024_plan.md`), already documents adding near-identical
`TestClient` + `monkeypatch.setattr(<module>, "_cfg", ...)` tests asserting `enabled`/
`disabled_reason` on the same four servers' `/v1/tools` responses — including its own "schema-shape
assertion: every tool in every `/v1/tools` response has a bool `enabled` key and a str
`disabled_reason` key" (that doc's Scope, last bullet), which is functionally the same assertion
this plan's `test_tools_endpoint.py` wants to make. The two differ only in target file
(`tests/test_mcp_tools_validation.py` vs. a new `tests/test_tools_endpoint.py`) and in framing
(15's tests validate 15's own field-computation correctness; 18's tests validate the contract
shape against malformed-metadata reaching Agent-side discovery). This is exactly the
state-construction/fixture duplication risk the plan's own Scope section already names under
"SHARED WITH `plans/20260717-174024_plan.md`" and its Risks table — not silently skipped, but not
resolved by skipping this doc either, since the plan explicitly calls for a **new, separate** file
`tests/test_tools_endpoint.py` (its own Scope/Affected-areas table names it as a distinct file from
`test_mcp_tools_validation.py`). Flagging here per the task's instruction to surface — not
silently absorb — any near-duplicate coverage found. See Details for the concrete de-duplication
action to take at implementation time.

## Goal

Add a new pytest module using `fastapi.testclient.TestClient` against each of the four file/git MCP
servers' live `GET /v1/tools` handler, with `_cfg` monkeypatched to construct enabled and disabled
server states, asserting every tool in the response carries `enabled: bool` and
`disabled_reason: str`, and that the two correlate (`enabled=True` <=> `disabled_reason == ""`).
This is the request-time-computed half of requirement 18's acceptance criteria (the static half is
covered by the companion file `tests/test_tool_schema.py`).

## Scope

**In scope**: one new file, `tests/test_tools_endpoint.py`, with 5 parametrized/discrete test cases
matching the plan's Design section one-to-one:
1. File servers (read/write/delete), `allowed_dirs=[]` -> all tools `enabled=False`.
2. File servers, `allowed_dirs=["/tmp"]` -> all tools `enabled=True`.
3. Git server, `allowed_repo_paths=[]` -> all tools disabled (empty-allowlist reason).
4. Git server, `allowed_repo_paths=["/tmp"], read_only=True` -> only the 5 `GIT_WRITE_TOOLS` disabled.
5. Git server, `allowed_repo_paths=["/tmp"], read_only=False` -> all tools enabled.

**Out of scope**:
- `/v1/call_tool` disabled-tool rejection (requirement 16's own test file,
  `tests/test_call_tool_validation.py`, already documented at
  `implementations/20260718-091834_test_call_tool_validation.py.md`) — this file covers only the
  *listing* path.
- Agent-side `RuntimeToolRegistry` consumption of these fields (requirement 17) — out of scope
  entirely per the plan.
- `shell`, `cicd`, `github`, `rag_pipeline`, `mdq`, `web_search` servers.
- Any change to `scripts/mcp_servers/**` — read-only reference only.

## Assumptions

- Per `implementations/20260718-095246_requirements_14_15_landing_check_for_availability_metadata_schema_tests.md`,
  requirement 15 (`enabled`/`disabled_reason` computation) has **not** landed in real
  `scripts/mcp_servers/**/server.py` source as of this writing (confirmed via direct read below).
  Every assertion in this file that depends on `enabled`/`disabled_reason` actually being present in
  the JSON response must therefore be wrapped in `pytest.mark.xfail(reason="depends on requirement
  15 landing", strict=True)` at the parametrize-case level, per that gate doc's Procedure.
- Current real `/v1/tools` handler shape (confirmed by direct read):
  - `scripts/mcp_servers/file/read_server.py` (handler near end of file, `@app.get("/v1/tools")` ->
    `return {"tools": [{**t, "server_key": "file_read"} for t in TOOL_LIST]}`) — no `enabled`/
    `disabled_reason` merge.
  - `scripts/mcp_servers/file/write_server.py:144-148` — identical shape, `server_key: "file_write"`.
  - `scripts/mcp_servers/file/delete_server.py:106-110` — identical shape, `server_key: "file_delete"`.
  - `scripts/mcp_servers/git/server.py:72-76` — identical shape, `server_key: "git"`, return type
    annotated `dict[str, list[dict[str, object]]]`.
  - None of the four handlers today read `_cfg` inside `list_tools()` at all — the monkeypatch
    fixture this file needs will have no observable effect on the response until requirement 15
    lands (the handler doesn't consult `_cfg` yet). This is expected and is exactly why every
    assertion depending on the merged field must be `xfail`-gated, not just the field-presence check.
- `_cfg` module-level globals confirmed by direct grep: `scripts/mcp_servers/git/server.py:41`
  (`_cfg = GitConfig.load()`), `scripts/mcp_servers/file/read_server.py:66`
  (`_cfg = FileReadConfig.load()`), `scripts/mcp_servers/file/delete_server.py:47`
  (`_cfg = FileDeleteConfig.load()`), `scripts/mcp_servers/file/write_server.py:53`
  (`_cfg = FileWriteConfig.load()`).
- Config dataclass fields confirmed by direct read: `FileReadConfig.allowed_dirs: list[str]`
  (`scripts/mcp_servers/file/read_models.py:28`), `FileWriteConfig.allowed_dirs: list[str]`
  (`scripts/mcp_servers/file/write_models.py:28`), `FileDeleteConfig.allowed_dirs: list[str]`
  (`scripts/mcp_servers/file/delete_models.py:28`), `GitConfig.allowed_repo_paths: list[str]` /
  `read_only: bool = True` (`scripts/mcp_servers/git/models.py:27-28`). All are plain
  `@dataclasses.dataclass` with `default_factory`/literal defaults, constructible directly in tests
  without touching disk (e.g. `FileReadConfig(allowed_dirs=[])`).
- `GIT_WRITE_TOOLS: frozenset[str]` exists at `scripts/shared/tool_constants.py:98`, already used by
  requirement 15's own test doc for the same 5-write-tool partitioning — reuse this constant rather
  than hardcoding the 5 tool names, to avoid drift if the constant's membership changes.
- **De-duplication action (resolving the overlap flagged above)**: since requirement 15's own doc
  (`implementations/20260718-090741_test_mcp_tools_validation.py.md`) already plans equivalent
  `_cfg`-monkeypatch + `TestClient` state-construction logic in `tests/test_mcp_tools_validation.py`,
  whichever of {this plan (18), plan `20260717-174024_plan.md` (15)} is actually implemented in real
  code first should factor the `monkeypatch.setattr(<module>, "_cfg", <Config instance>)` +
  `TestClient(<module>.app)` construction into a small shared pytest fixture (e.g. in
  `tests/conftest.py` or a new `tests/mcp_server_fixtures.py` helper), and the second-landing plan's
  test file should import and reuse it rather than re-deriving the same four `(module, ConfigClass,
  server_key)` tuples independently. This plan's own test file's assertions (enabled/disabled_reason
  *shape and correlation*, contract-level) and requirement 15's (exact `disabled_reason` string
  values, computation-level) remain distinct and both worth keeping — only the state-construction
  scaffolding should be shared, per the plan's own Risks table mitigation.

## Implementation

### Target file

`/home/sugimoto/llmagent/tests/test_tools_endpoint.py` (new file, does not exist yet)

### Procedure

1. Create the new file with a module docstring noting the overlap/fixture-sharing note above and a
   pointer to `tests/test_mcp_tools_validation.py` for the sibling requirement-15 tests.
2. Import `fastapi.testclient.TestClient` at module level (no server-process side effects — matches
   the existing repo pattern in `tests/test_mcp_tools_validation.py`'s planned addition). Import the
   four server modules and Config dataclasses lazily inside each test function, matching that same
   doc's established lazy-import convention.
3. Define a parametrization table for the three file servers:
   `[("mcp_servers.file.read_server", "FileReadConfig", "mcp_servers.file.read_models"),
   ("mcp_servers.file.write_server", "FileWriteConfig", "mcp_servers.file.write_models"),
   ("mcp_servers.file.delete_server", "FileDeleteConfig", "mcp_servers.file.delete_models")]`.
4. Write test case 1 (`allowed_dirs=[]` -> all disabled) and test case 2 (`allowed_dirs=["/tmp"]` ->
   all enabled), each parametrized over the three file-server tuples: monkeypatch `_cfg`, build
   `TestClient(app)`, `GET /v1/tools`, assert every tool's `enabled` is `bool` and matches the
   expected state, and `disabled_reason` is `str` and empty iff `enabled` is `True`. Wrap the
   `enabled`/`disabled_reason` presence-and-correlation assertions in
   `xfail(strict=True)` per the current landing-check gate.
5. Write test cases 3-5 for the git server (empty allowlist; read-only with non-empty allowlist;
   fully enabled), using `GIT_WRITE_TOOLS` from `shared.tool_constants` to partition expected-disabled
   tools in case 4. Same `xfail` wrapping.
6. Add one final cross-cutting test asserting the type-correctness (`isinstance(..., bool)` /
   `isinstance(..., str)`) of `enabled`/`disabled_reason` across all four servers' "fully enabled"
   state in one pass, matching the plan's Design section's final bullet on uniform correlation
   assertion. Also `xfail`-wrapped for now.

### Method

Pseudocode (no production code blocks per design-doc convention):

```
_FILE_SERVERS = [
    ("mcp_servers.file.read_server", "FileReadConfig", "mcp_servers.file.read_models"),
    ("mcp_servers.file.write_server", "FileWriteConfig", "mcp_servers.file.write_models"),
    ("mcp_servers.file.delete_server", "FileDeleteConfig", "mcp_servers.file.delete_models"),
]

@pytest.mark.xfail(reason="depends on requirement 15 landing in scripts/mcp_servers/", strict=True)
@pytest.mark.parametrize("server_mod_path,cfg_cls_name,cfg_mod_path", _FILE_SERVERS)
def test_file_server_tools_disabled_when_allowed_dirs_empty(server_mod_path, cfg_cls_name, cfg_mod_path, monkeypatch) -> None:
    server_mod = importlib.import_module(server_mod_path)
    cfg_mod = importlib.import_module(cfg_mod_path)
    cfg_cls = getattr(cfg_mod, cfg_cls_name)
    monkeypatch.setattr(server_mod, "_cfg", cfg_cls(allowed_dirs=[]))
    client = TestClient(server_mod.app)
    data = client.get("/v1/tools").json()
    for tool in data["tools"]:
        assert tool["enabled"] is False
        assert isinstance(tool["disabled_reason"], str) and tool["disabled_reason"] != ""

# ... test_file_server_tools_enabled_when_allowed_dirs_set (mirror, allowed_dirs=["/tmp"], enabled=True, reason=="")

@pytest.mark.xfail(reason="depends on requirement 15 landing in scripts/mcp_servers/", strict=True)
def test_git_tools_all_disabled_when_allowed_repo_paths_empty(monkeypatch) -> None:
    from mcp_servers.git.git_models import GitConfig
    from mcp_servers.git import server as git_server
    monkeypatch.setattr(git_server, "_cfg", GitConfig(allowed_repo_paths=[], read_only=True))
    client = TestClient(git_server.app)
    data = client.get("/v1/tools").json()
    for tool in data["tools"]:
        assert tool["enabled"] is False

@pytest.mark.xfail(reason="depends on requirement 15 landing in scripts/mcp_servers/", strict=True)
def test_git_write_tools_disabled_when_read_only(monkeypatch) -> None:
    from mcp_servers.git.git_models import GitConfig
    from mcp_servers.git import server as git_server
    from shared.tool_constants import GIT_WRITE_TOOLS
    monkeypatch.setattr(git_server, "_cfg", GitConfig(allowed_repo_paths=["/tmp"], read_only=True))
    client = TestClient(git_server.app)
    data = client.get("/v1/tools").json()
    for tool in data["tools"]:
        expect_disabled = tool["name"] in GIT_WRITE_TOOLS
        assert tool["enabled"] is (not expect_disabled)
        assert (tool["disabled_reason"] != "") is expect_disabled

# ... test_git_tools_all_enabled_when_repo_paths_set_and_not_read_only (mirror, all enabled)

@pytest.mark.xfail(reason="depends on requirement 15 landing in scripts/mcp_servers/", strict=True)
def test_enabled_and_disabled_reason_types_across_all_servers(monkeypatch) -> None:
    # happy-path _cfg on all 4 servers; assert bool/str types on every tool dict
    ...
```

### Details

- Use the `monkeypatch` fixture (function-scoped, auto-reverts), not manual save/restore — matches
  the established repo pattern already used by requirement 15's own test doc.
- `TestClient(app)` is in-process ASGI, no subprocess — these tests belong in the default
  (non-`integration`) tier.
- Exact `disabled_reason` string values (`"allowed_dirs is empty"`, `"allowed_repo_paths is empty"`,
  `"read_only=true"`) are requirement 15's own literal contract, documented in
  `implementations/20260718-090741_test_mcp_tools_validation.py.md`. This file's assertions
  deliberately check *type and non-emptiness* of `disabled_reason` rather than the exact string,
  per the plan's own Design note ("asserts on the response contract, not... implementation detail")
  — this keeps `test_tools_endpoint.py` stable even if requirement 15 later tweaks its exact wording,
  while requirement 15's own test file remains the authority for the exact string values.
- Once the fixture-sharing de-duplication action (see Assumptions) is carried out at actual
  implementation time, this file's per-test `monkeypatch.setattr` + `TestClient` construction lines
  should be replaced with a call to the shared fixture — flagged here so the implementer does not
  independently re-derive it a third time.

## Validation plan

| Check | Command | Target |
|---|---|---|
| Format | `uv run ruff format tests/test_tools_endpoint.py` | clean |
| Lint | `uv run ruff check tests/test_tools_endpoint.py` | 0 errors |
| Type check | `uv run mypy tests/test_tools_endpoint.py` | no new errors |
| Architecture | `PYTHONPATH=scripts uv run lint-imports` | 0 violations |
| Security | `uv run bandit -r tests/test_tools_endpoint.py` | no new HIGH findings |
| Tests (today) | `uv run pytest tests/test_tools_endpoint.py -v` | all 6 cases report `xfail` (not `XPASS`), given requirement 15 has not landed |
| Tests (post-requirement-15) | same command, re-run after requirement 15 lands | each case flips to `XPASS(strict)` failure until its marker is removed, then passes cleanly |
| Residual xfail | `grep -n "xfail" tests/test_tools_endpoint.py` | 0 matches once requirement 15 has landed and markers are removed |
| Fixture de-duplication check | `grep -rn "monkeypatch.setattr.*_cfg" tests/` | shows a shared helper/fixture, not three independently-written near-duplicates (this file + `test_mcp_tools_validation.py` + `test_call_tool_validation.py`) |

Full cross-file validation (mypy repo-wide, lint-imports, bandit, full pytest, pre-commit) is
covered by the cross-cutting doc
`implementations/{sibling-timestamp}_full_validation_pass_availability_metadata_schema_tests.md`
(this batch's companion doc for requirement 18).
