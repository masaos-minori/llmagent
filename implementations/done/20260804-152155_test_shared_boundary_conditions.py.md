# Implementation Procedure: Rewrite `test_different_subsections_in_load_all_merged` to call the real `ConfigLoader.load_all()`

## Goal

Rewrite `tests/shared/test_shared_boundary_conditions.py::TestDictMergeConflictResolution::test_different_subsections_in_load_all_merged` so it exercises the real `ConfigLoader.load_all()` merge path (via the established `monkeypatch.setattr("shared.config_loader._BASE_CONFIG_FILES", ...)` pattern) instead of asserting against a hand-rolled copy of `load_all()`'s one-level-deep dict-merge loop.

## Scope

**In scope:**
- `tests/shared/test_shared_boundary_conditions.py`, method `test_different_subsections_in_load_all_merged` (lines 37-62): add `monkeypatch: pytest.MonkeyPatch` parameter; replace the two `loader.load(...)` calls and the manual merge loop with `monkeypatch.setattr(...)` + `loader.load_all()`; update assertions to read from the real result.

**Out of scope:**
- `scripts/shared/config_loader.py` — reference only, no production code change.
- `tests/shared/test_config_loader.py` — already fixed by a sibling plan/procedure; not touched here.
- `test_same_subsection_later_file_wins`, `test_deep_nested_same_subsection_replaced` (same file) — test `load()`'s flat shallow-merge behavior, unaffected.
- `test_parent_dict_merge_one_level_deep` (same file, lines 91-116) — has the identical hand-rolled-merge anti-pattern but is out of scope per the source plan; tracked separately in `issues/20260804-140019_risks.md`.

## Assumptions

- The target test method is unchanged at lines 37-62 (verified by direct read during this document's preparation).
- The `monkeypatch.setattr("shared.config_loader._BASE_CONFIG_FILES", (...))` pattern used by `test_nested_dict_merge` in `tests/shared/test_config_loader.py` (lines 58-74) is valid and applicable unchanged to this test.
- The `from typing import Any` import (line 12 of the target file) must be kept — `Any` is still used elsewhere in the file (`test_parent_dict_merge_one_level_deep` and `TestKnownToolsNoneFallback`), outside the method being rewritten.

## Design decisions

- Reuse the exact monkeypatch pattern already proven in production test code (`test_nested_dict_merge`) rather than inventing a new fixture or helper — keeps the two tests structurally consistent and minimizes review surface.
- Keep the existing docstring ("Different subsections under the same parent are merged by `load_all()`.") unchanged — it becomes accurate once the test calls the real method, so no wording change is needed.
- Assert directly on `result["mcp_servers"]` (or `.get("mcp_servers", {})`) from `load_all()`'s return value; do not reintroduce any local merge/copy logic.

## Alternatives considered

- **Leave the hand-rolled merge as-is**: rejected — this is exactly the flaw the source plan targets; a regression in `load_all()`'s merge loop would not be caught.
- **Extract a shared monkeypatch fixture for both this test and `test_nested_dict_merge`**: rejected as out of scope — the source plan explicitly limits changes to this one method; introducing a shared fixture would touch `test_config_loader.py`, which is out of scope here.

## Implementation

### Target file
`tests/shared/test_shared_boundary_conditions.py`

### Procedure
1. Add `monkeypatch: pytest.MonkeyPatch` as a parameter to `test_different_subsections_in_load_all_merged` (currently only takes `tmp_path: Path`).
2. Keep the two `tmp_path.write_text(...)` calls for `extra_mcp.toml` / `extra_mcp2.toml` unchanged (lines 39-44).
3. After writing the fixture files and before instantiating `ConfigLoader`, insert:
   ```python
   monkeypatch.setattr(
       "shared.config_loader._BASE_CONFIG_FILES",
       ("extra_mcp.toml", "extra_mcp2.toml"),
   )
   ```
4. Replace the two `loader.load("extra_mcp.toml")` / `loader.load("extra_mcp2.toml")` calls and the manual merge loop (current lines 46-60) with:
   ```python
   loader = ConfigLoader(config_dir=tmp_path)
   result = loader.load_all()
   ```
5. Replace the final two assertions to read `result` instead of the hand-rolled `merged` dict:
   ```python
   assert "server_a" in result.get("mcp_servers", {})
   assert "server_b" in result.get("mcp_servers", {})
   ```
6. Remove the misleading inline comments ("load_all merges dict-valued keys one level deep" / "We need to manually combine since load_all only loads `_BASE_CONFIG_FILES`") since the real `load_all()` call replaces the need for them.
7. Do not touch the `from typing import Any` import or any other test method in the class/file.

### Method
Direct in-place edit of the single method body; no new fixtures, no changes to imports, no changes to other test classes/methods.

### Details
- Reference (`scripts/shared/config_loader.py`, `load_all()`, lines 68-94): reads `_BASE_CONFIG_FILES` module-level tuple directly inside its loop (`for name in _BASE_CONFIG_FILES:`), and merges dict-valued keys one level deep (`if isinstance(val, dict) and isinstance(merged.get(key), dict): merged[key] = {**merged[key], **val}`) — this is the exact behavior the hand-rolled loop in the test was duplicating.
- Reference pattern (`tests/shared/test_config_loader.py::TestMergeOrder::test_nested_dict_merge`, lines 58-74): identical `monkeypatch.setattr("shared.config_loader._BASE_CONFIG_FILES", (...))` + `ConfigLoader(config_dir=tmp_path).load_all()` technique already in production use — confirms the monkeypatch redirects `load_all()`'s file list correctly for arbitrary TOML filenames written under `tmp_path`.

## Compatibility considerations

- Test-only change; no production code, no public API, no config schema affected.
- No other test or module references `test_different_subsections_in_load_all_merged` by name (confirmed via `rg` in the source plan) — safe to rewrite the method body without breaking other tests.

## Security considerations

N/A — test-only change, no handling of secrets, credentials, or external input.

## Rollback considerations

- Single self-contained method-body edit in one file; revert via `git checkout -- tests/shared/test_shared_boundary_conditions.py` or a follow-up commit reverting the diff.
- No migration, no data, no deployment artifact involved.

## Validation plan

| Target | Command | Expected outcome |
|---|---|---|
| Rewritten test + siblings in same class | `PYTHONPATH=scripts pytest tests/shared/test_shared_boundary_conditions.py::TestDictMergeConflictResolution -v` | All 5 tests in the class pass |
| Regression guard for sibling pattern | `PYTHONPATH=scripts pytest tests/shared/test_config_loader.py -v` | All tests pass, `test_nested_dict_merge` unaffected |
| Lint | `uv run ruff check tests/shared/test_shared_boundary_conditions.py` | 0 errors (no unused-import/unused-variable regression) |
| Type check | `uv run mypy tests/shared/test_shared_boundary_conditions.py` | No new errors |
| Full suite | `uv run pytest` | All pass, no regressions |
| Pre-commit | `uv run pre-commit run --all-files` | Pass |

## Out of scope

- `scripts/shared/config_loader.py` production code.
- `tests/shared/test_config_loader.py`.
- `test_same_subsection_later_file_wins`, `test_deep_nested_same_subsection_replaced`, `test_parent_dict_merge_one_level_deep` in the same file.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260804-135935_plan.md
- Source implementation procedure: N/A
- Generated at: 20260804-152155
- Related target files: tests/shared/test_shared_boundary_conditions.py
