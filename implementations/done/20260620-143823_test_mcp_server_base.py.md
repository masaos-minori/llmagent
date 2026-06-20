# Implementation: tests/test_mcp_server_base.py (update — app_module regression test)

## Goal

Add a regression test to `tests/test_mcp_server_base.py` that discovers all production
MCP server files, extracts their `app_module` attribute values, and verifies each module
is importable. This prevents a recurrence of the `GithubMCPServer` path mismatch fixed
in commit `85dcf25`.

## Scope

**In:**
- Add one new test class `TestAppModuleImportability` with one test function
  `test_all_server_app_modules_are_importable` to `tests/test_mcp_server_base.py`
- Discovery: glob `scripts/mcp/**/server.py` + `scripts/mcp/**/delete_server.py` +
  `scripts/mcp/**/write_server.py` + `scripts/mcp/**/read_server.py`
  (i.e., all files matching `scripts/mcp/**/*server.py`)
- Extraction: regex `app_module\s*=\s*"([^"]+)"` per file; skip stub values used in tests
- Validation: `importlib.util.find_spec(module_path)` must return non-None for each

**Out:**
- Instantiating any `MCPServer` subclass (import only, no object creation)
- Triggering FastAPI app startup
- Modifying production code

## Assumptions

- The `scripts/` directory is on `sys.path` during `pytest` (confirmed by existing test imports)
- Each production `*server.py` file contains at most one `app_module = "mcp.*.server:app"` assignment
- Test-fixture stub values (`"test:app"`, `"empty:app"`) in `test_mcp_server_base.py` itself
  are not in production server files and can be excluded by scoping the glob to `scripts/mcp/`
- `importlib.util.find_spec()` is sufficient; it does not execute module code
- 11 production server files exist:
  `cicd/server.py`, `git/server.py`, `sqlite/server.py`, `web_search/server.py`,
  `file/delete_server.py`, `file/write_server.py`, `file/read_server.py`,
  `mdq/server.py`, `rag_pipeline/server.py`, `github/server.py`, `shell/server.py`

## Implementation

### Target file

`tests/test_mcp_server_base.py`

### Procedure

1. Add `import importlib.util`, `import re`, `from pathlib import Path` at the top of the
   file (after the existing imports — `re` and `Path` may already be imported; check first)
2. Append a new test class after `TestAuditLog`:

```
class TestAppModuleImportability:
    def test_all_server_app_modules_are_importable(self) -> None:
        ...
```

### Method

```python
class TestAppModuleImportability:
    def test_all_server_app_modules_are_importable(self) -> None:
        scripts_dir = Path(__file__).parent.parent / "scripts"
        server_files = list(scripts_dir.glob("mcp/**/*server.py"))
        assert server_files, "No server.py files found under scripts/mcp/"

        pattern = re.compile(r'app_module\s*=\s*"([^"]+)"')
        missing: list[str] = []

        for path in server_files:
            for match in pattern.finditer(path.read_text()):
                app_module_value = match.group(1)
                module_path = app_module_value.split(":")[0]
                spec = importlib.util.find_spec(module_path)
                if spec is None:
                    missing.append(f"{path.relative_to(scripts_dir)}: {module_path!r}")

        assert not missing, (
            "The following app_module paths are not importable:\n"
            + "\n".join(f"  {m}" for m in missing)
        )
```

### Details

- `Path(__file__).parent.parent / "scripts"` resolves to `scripts/` relative to `tests/`
- `scripts_dir.glob("mcp/**/*server.py")` matches all `*server.py` files recursively under
  `scripts/mcp/` — covers both `server.py` and `delete_server.py`, `write_server.py`, etc.
- `app_module_value.split(":")[0]` strips the `:app` suffix to get the importable module path
- `importlib.util.find_spec()` checks importability without executing the module
- The `missing` list accumulates all failures before asserting, so the error message shows
  all broken paths at once (not just the first)
- `re` is already imported in the file (line 9) — do not add a duplicate import
- `importlib.util` requires a new import; `Path` is not currently imported — both must be added
- No `pytest.mark` decorator needed; this is a fast test (11 `find_spec` calls)

## Validation plan

| Check | Command | Expected |
|---|---|---|
| New test present | `grep -n "TestAppModuleImportability" tests/test_mcp_server_base.py` | 1 match |
| All 11 server files discovered | Add `print(len(server_files))` temporarily or check test output | 11 files |
| Lint | `uv run ruff check tests/test_mcp_server_base.py` | 0 errors |
| Type check | `uv run mypy tests/test_mcp_server_base.py` | 0 errors |
| New test passes | `uv run pytest tests/test_mcp_server_base.py::TestAppModuleImportability -v` | 1 passed |
| Full test file passes | `uv run pytest tests/test_mcp_server_base.py -v` | all pass |
