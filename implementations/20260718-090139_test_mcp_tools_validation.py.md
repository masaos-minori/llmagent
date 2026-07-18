# Implementation: tests/test_mcp_tools_validation.py — add config_dependent schema-validation test

Source plan: `plans/20260717-173602_plan.md` ("Replace requires_config with config_dependent in MCP tool definitions")

Note: two docs in `implementations/done/` match this filename
(`20260709-160926_tests_test_mcp_tools_validation.md`,
`20260710-120509_tests_test_mcp_tools_validation.md`), but both are about
subprocess/`os.killpg` teardown fixes in the `mcp_server` fixture — unrelated
to schema validation of the `config_dependent`/`requires_config` field.
Stale filename matches; treated as not-already-implemented.

## Goal

Add a new, fast (non-integration, no subprocess) pytest test to
`tests/test_mcp_tools_validation.py` that asserts, across every MCP server's
`TOOL_LIST`: (a) no tool dict contains the key `"requires_config"`, and (b)
every tool dict contains `"config_dependent"` with a `bool` value. This is
the permanent regression guard called for by the plan's Design section and
directly satisfies the requirement's acceptance criteria.

## Scope

**In scope**: one new test function in this file, importing `TOOL_LIST` from
all 13 MCP server tool modules (10 renamed + 3 already-compliant-by-having-
no-such-field: `rag_pipeline`, `web_search`, `mdq`).

**Out of scope**: modifying the existing `test_read_tools_schema_matches_hand_written`
test or the `@pytest.mark.integration` HTTP tests (`test_v1_tools_returns_expected_tools`,
`test_v1_tools_each_has_name_and_description`) — those are unaffected by this
plan and remain as-is.

## Assumptions

- `tests/conftest.py` inserts `scripts/` onto `sys.path` (line 11:
  `sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))`), so
  `from mcp_servers.<pkg>.<mod> import TOOL_LIST` works directly, matching
  the existing pattern at line 148
  (`from mcp_servers.file.read_tools import TOOL_LIST`).
- All 13 modules export a top-level `TOOL_LIST` of type `list[dict[str, Any]]`
  (or `list[dict]`) — confirmed via grep: `read_tools.py:48`,
  `write_tools.py`, `delete_tools.py`, `git/tools.py:15`,
  `shell/tools.py:11`, `cicd/tools.py:11`, `github/tools_file.py:9`,
  `github/tools_issues.py:9`, `github/tools_pull_requests.py:9`,
  `github/tools_repository.py:9`, `web_search/tools.py:11`,
  `rag_pipeline/tools.py:11`, `mdq/tools.py:21`. No import errors expected
  since these modules have no side-effecting top-level code beyond building
  the list.
- This new test must run WITHOUT starting any server subprocess — it only
  imports Python modules and inspects the `TOOL_LIST` data, so it should NOT
  be marked `@pytest.mark.integration` (keeps it in the fast/unit-test tier
  per the plan's Design section: "fails fast, no server process needed").

## Implementation

### Target file

`/home/sugimoto/llmagent/tests/test_mcp_tools_validation.py`

### Procedure

1. Add a new module-level list (or reuse an inline list in the test body) of
   the 13 `(module_path)` strings to import `TOOL_LIST` from, e.g.:
   - `mcp_servers.file.read_tools`
   - `mcp_servers.file.write_tools`
   - `mcp_servers.file.delete_tools`
   - `mcp_servers.git.tools`
   - `mcp_servers.shell.tools`
   - `mcp_servers.cicd.tools`
   - `mcp_servers.github.tools_file`
   - `mcp_servers.github.tools_issues`
   - `mcp_servers.github.tools_pull_requests`
   - `mcp_servers.github.tools_repository`
   - `mcp_servers.web_search.tools`
   - `mcp_servers.rag_pipeline.tools`
   - `mcp_servers.mdq.tools`
2. Insert a new test function directly after
   `test_read_tools_schema_matches_hand_written` (which ends at line 165,
   before the blank lines preceding the `@pytest.mark.integration` block at
   line 174), e.g. `test_all_tool_lists_use_config_dependent_not_requires_config`.
3. In the test body, use `importlib.import_module(module_path)` (add
   `import importlib` to the existing import block near line 15-24) to load
   each module, read its `TOOL_LIST` attribute, and iterate every tool dict
   asserting:
   - `"requires_config" not in tool` (with an assertion message including
     the module path and tool name for easy debugging on failure).
   - `"config_dependent" in tool`.
   - `isinstance(tool["config_dependent"], bool)`.
4. Do not add `@pytest.mark.integration` — this test needs no subprocess/
   network and should run in the default fast suite.

### Method

Pseudocode (no production code blocks per design-doc convention):

```
_ALL_TOOL_MODULES = [
    "mcp_servers.file.read_tools",
    "mcp_servers.file.write_tools",
    "mcp_servers.file.delete_tools",
    "mcp_servers.git.tools",
    "mcp_servers.shell.tools",
    "mcp_servers.cicd.tools",
    "mcp_servers.github.tools_file",
    "mcp_servers.github.tools_issues",
    "mcp_servers.github.tools_pull_requests",
    "mcp_servers.github.tools_repository",
    "mcp_servers.web_search.tools",
    "mcp_servers.rag_pipeline.tools",
    "mcp_servers.mdq.tools",
]

def test_all_tool_lists_use_config_dependent_not_requires_config() -> None:
    for module_path in _ALL_TOOL_MODULES:
        module = importlib.import_module(module_path)
        tool_list = module.TOOL_LIST
        for tool in tool_list:
            assert "requires_config" not in tool, f"{module_path}:{tool.get('name')} still has requires_config"
            assert "config_dependent" in tool, f"{module_path}:{tool.get('name')} missing config_dependent"
            assert isinstance(tool["config_dependent"], bool), f"{module_path}:{tool.get('name')} config_dependent not bool"
```

### Details

- Placement: after line 165 (end of `test_read_tools_schema_matches_hand_written`),
  before line 167's blank-line gap leading into the `@pytest.mark.integration`
  section starting at line 174.
- New import needed: `import importlib` added to the existing stdlib import
  block (lines 15-19: `os`, `socket`, `subprocess`, `sys`, `time`) — insert
  alphabetically.
- This test is independent of Implementation step order — it can be added
  before or after the 10 Python file renames land, but will only pass once
  ALL 10 files' renames are complete (since it checks all 13 modules
  including the 3 already-compliant ones). Run it last, after all 10 rename
  docs are applied.
- Run in isolation by name to confirm it actually executes (per the plan's
  Risks table): `uv run pytest
  tests/test_mcp_tools_validation.py::test_all_tool_lists_use_config_dependent_not_requires_config -v`

## Validation plan

| Check | Command | Target |
|---|---|---|
| New test runs and passes | `uv run pytest tests/test_mcp_tools_validation.py::test_all_tool_lists_use_config_dependent_not_requires_config -v` | 1 passed, not skipped/xfailed |
| Existing tests unaffected | `uv run pytest tests/test_mcp_tools_validation.py -m "not integration" -v` | all pass |
| Format | `uv run ruff format tests/test_mcp_tools_validation.py` | clean |
| Lint | `uv run ruff check tests/test_mcp_tools_validation.py` | 0 errors |
| Type check | `uv run mypy tests/test_mcp_tools_validation.py` | no new errors |

Full cross-file validation (mypy repo-wide, lint-imports, bandit, full
pytest, diff-cover, pre-commit, repo-wide residual grep) is covered by the
cross-cutting doc `full_validation_pass_config_dependent_rename.md`.
