## Goal

Rewrite `tests/shared/test_shared_boundary_conditions.py::TestDictMergeConflictResolution::test_parent_dict_merge_one_level_deep` so it exercises the real `ConfigLoader.load_all()` merge path (via the established `monkeypatch.setattr("shared.config_loader._BASE_CONFIG_FILES", ...)` pattern) instead of asserting against a hand-rolled copy of `load_all()`'s one-level-deep dict-merge loop.

## Scope

**In scope:**
- `tests/shared/test_shared_boundary_conditions.py`, method `test_parent_dict_merge_one_level_deep` (current lines 83-108): add `monkeypatch: pytest.MonkeyPatch` parameter; replace the two `loader.load(...)` calls and the manual merge loops with `monkeypatch.setattr(...)` + `loader.load_all()`; update assertions to read from the real result.

**Out of scope:**
- `scripts/shared/config_loader.py` — reference only, no production code change.
- `tests/shared/test_config_loader.py` — reference pattern only, not touched.
- `test_same_subsection_later_file_wins`, `test_deep_nested_same_subsection_replaced`, `test_top_level_section_values_combined` (same file) — unaffected.
- `test_different_subsections_in_load_all_merged` (same file) — already rewritten to this pattern by a prior implementation cycle (`implementations/done/20260804-152155_test_shared_boundary_conditions.py.md`); not touched here.

## Assumptions

- The target test method is unchanged at lines 83-108 (verified by direct read during this document's preparation on 2026-08-06).
- The `monkeypatch.setattr("shared.config_loader._BASE_CONFIG_FILES", (...))` + `ConfigLoader(config_dir=tmp_path).load_all()` pattern is valid and applicable unchanged, since the sibling method `test_different_subsections_in_load_all_merged` (lines 37-54, same file) already uses it successfully in production test code.

## Design decisions

- Reuse the exact monkeypatch pattern already proven in `test_different_subsections_in_load_all_merged` rather than inventing a new fixture or helper — keeps all `TestDictMergeConflictResolution` methods structurally consistent.
- Keep the existing docstring ("Parent dicts are merged one level deep in load_all.") unchanged — it becomes accurate once the test calls the real method.
- Assert directly on `result["mcp_servers"]["github"]` from `load_all()`'s return value; do not reintroduce any local merge/copy logic.

## Alternatives considered

- **Leave the hand-rolled merge as-is**: rejected — this is exactly the coverage gap the source plan targets; a regression in `load_all()`'s merge loop (`scripts/shared/config_loader.py` lines 81-94) would not be caught.
- **Extract a shared monkeypatch fixture** for all methods in the class: rejected as out of scope — the source plan limits changes to this one method.

## Implementation

### Target file
`tests/shared/test_shared_boundary_conditions.py`

### Procedure
1. Add `monkeypatch: pytest.MonkeyPatch` as a parameter to `test_parent_dict_merge_one_level_deep` (currently only takes `tmp_path: Path`).
2. Keep the two `tmp_path.write_text(...)` calls for `extra_mcp.toml` (`[mcp_servers.github]\nurl = "https://api.github.com"`) / `extra_mcp2.toml` (`[mcp_servers.github]\ntimeout = 30`) unchanged (current lines 85-90).
3. After writing the fixture files and before instantiating `ConfigLoader`, insert:
   ```python
   monkeypatch.setattr(
       "shared.config_loader._BASE_CONFIG_FILES",
       ("extra_mcp.toml", "extra_mcp2.toml"),
   )
   ```
4. Replace the two `loader.load(...)` calls and the two manual merge `for` loops (current lines 92-105: `result_a`, `result_b`, `merged` construction) with:
   ```python
   loader = ConfigLoader(config_dir=tmp_path)
   result = loader.load_all()
   ```
5. Replace the three final assertions to read `result` instead of the hand-rolled `merged` dict:
   ```python
   assert "github" in result.get("mcp_servers", {})
   assert "url" not in result["mcp_servers"]["github"]
   assert result["mcp_servers"]["github"]["timeout"] == 30
   ```
6. Remove the now-inaccurate inline comment (`# Manually merge like load_all does`, current line 92) since the real `load_all()` call replaces the need for it.
7. Do not touch the `from typing import Any` import (still used elsewhere in the file) or any other test method in the class/file.

### Method
Direct in-place edit of the single method body; no new fixtures, no import changes, no changes to other test classes/methods.

### Details
- Reference (`scripts/shared/config_loader.py::ConfigLoader.load_all()`, lines 68-94): reads `_BASE_CONFIG_FILES` module-level tuple directly inside its loop (`for name in _BASE_CONFIG_FILES:`) and merges dict-valued keys one level deep (`if isinstance(val, dict) and isinstance(merged.get(key), dict): merged[key] = {**merged[key], **val}`) — this is exactly the behavior the hand-rolled loop in the test currently duplicates.
- Reference pattern (`tests/shared/test_shared_boundary_conditions.py::test_different_subsections_in_load_all_merged`, lines 37-54, already implemented): identical `monkeypatch.setattr("shared.config_loader._BASE_CONFIG_FILES", (...))` + `ConfigLoader(config_dir=tmp_path).load_all()` technique already in production use in this same file/class — confirms the monkeypatch redirects `load_all()`'s file list correctly for arbitrary TOML filenames written under `tmp_path`.

## Compatibility considerations

- Test-only change; no production code, no public API, no config schema affected.
- No other test or module references `test_parent_dict_merge_one_level_deep` by name — safe to rewrite the method body without breaking other tests.

## Security considerations

N/A — test-only change, no handling of secrets, credentials, or external input.

## Rollback considerations

- Single self-contained method-body edit in one file; revert via `git checkout -- tests/shared/test_shared_boundary_conditions.py` or a follow-up commit reverting the diff.
- No migration, no data, no deployment artifact involved.

## Validation plan

| Target | Command | Expected outcome |
|---|---|---|
| Rewritten test + siblings in same class | `PYTHONPATH=scripts uv run pytest tests/shared/test_shared_boundary_conditions.py::TestDictMergeConflictResolution -v` | All 5 tests in the class pass |
| Lint | `uv run ruff check tests/shared/test_shared_boundary_conditions.py` | 0 errors (no unused-import/unused-variable regression) |
| Type check | `uv run mypy tests/shared/test_shared_boundary_conditions.py` | No new errors |
| Full shared test suite | `PYTHONPATH=scripts uv run pytest tests/shared/ -v` | No new failures |
| Full suite (spot check) | `uv run pytest -q` | No new failures attributable to this change |

## Out of scope

- `scripts/shared/config_loader.py` production code.
- `tests/shared/test_config_loader.py`.
- `test_same_subsection_later_file_wins`, `test_deep_nested_same_subsection_replaced`, `test_top_level_section_values_combined`, `test_different_subsections_in_load_all_merged` in the same file.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/done/20260806-104905_plan.md
- Source implementation procedure: N/A
- Generated at: 20260806-120820
- Related target files: tests/shared/test_shared_boundary_conditions.py
