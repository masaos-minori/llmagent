# Implementation: tests/shared/test_config_loader.py

## Goal
Rewrite the 3 of 4 `TestMergeOrder` tests in `tests/shared/test_config_loader.py` so the class
passes 100% and each test documents `ConfigLoader.load()` / `ConfigLoader.load_all()`'s actual,
current behavior, without changing `scripts/shared/config_loader.py` production logic.

## Scope
**In scope:**
- `tests/shared/test_config_loader.py::TestMergeOrder`:
  - `test_later_file_overrides_earlier` — assertion fix only.
  - `test_nested_dict_merge` — rewrite to call `load_all()` via a `_BASE_CONFIG_FILES`
    monkeypatch, and fix the fixture's TOML table-header nesting.
  - `test_meta_keys_filtered_from_both_files` — fixture redesign to use top-level `_meta` keys.
  - `test_first_file_values_preserved_when_no_overlap` — no change (already passes).

**Out of scope:**
- `scripts/shared/config_loader.py` (read-only reference; no production change).
- `tests/shared/test_shared_boundary_conditions.py` (read-only reference; a gap found there
  is a separate follow-up, not part of this document).
- Any other test class in the same file.

## Assumptions
- No production call site passes multiple filenames to `ConfigLoader.load()` (verified in the
  source plan via `grep`).
- `_BASE_CONFIG_FILES` (`scripts/shared/config_loader.py:28`) currently holds a single entry
  `("agent.toml",)`, so `load_all()`'s one-level-deep merge branch
  (`scripts/shared/config_loader.py:86-89`) is only reachable today via a monkeypatch that
  temporarily widens it to 2+ entries.
- Monkeypatching a private module-level constant via
  `monkeypatch.setattr("shared.config_loader._BASE_CONFIG_FILES", ...)` is an established
  pattern in this suite (precedent: `tests/eventbus_helpers.py:29`).
- `_filter_meta_keys()` (`scripts/shared/config_loader.py:148-150`) strips only top-level keys
  starting with `_`; it does not recurse into nested tables.

## Design decisions
- Keep `load()` and `load_all()` production code byte-for-byte unchanged — the fix is entirely
  in test fixtures/assertions/call choice, since no driving use case justifies changing
  `load()`'s merge depth (per the call-site audit).
- Use `monkeypatch.setattr` on `_BASE_CONFIG_FILES` (rather than adding a filenames parameter to
  `load_all()`) to exercise the real cross-file one-level-deep merge branch through the public
  API, because widening the production API is an unrequested behavior change.
- Redesign `test_meta_keys_filtered_from_both_files`'s fixture to place `_meta` at the file's
  top level (not nested inside `[section]`), so the test exercises `_filter_meta_keys()`'s real,
  documented top-level-only behavior instead of asserting nested-key filtering that does not
  exist.

## Alternatives considered
- Add a `filenames` parameter to `load_all()` so tests can pass fixture paths directly —
  rejected: changes production behavior/signature for a test-only need, and no caller needs it
  today (out of scope per the plan).
- Leave `test_nested_dict_merge` calling `load()` and merely relax its assertions to match flat
  overwrite — rejected: this would stop exercising `load_all()`'s one-level-deep merge branch at
  all, leaving it uncovered by any test.

## Implementation
### Target file
`tests/shared/test_config_loader.py`

### Procedure
1. `test_later_file_overrides_earlier` (`tests/shared/test_config_loader.py:39-47`): replace
   `assert result["section"]["bar"] == 2` with `assert "bar" not in result["section"]`. No
   fixture change.
2. `test_nested_dict_merge` (`tests/shared/test_config_loader.py:58-69`):
   - Add `monkeypatch: pytest.MonkeyPatch` to the signature.
   - Rewrite fixtures to `[mcp_servers.server_a]` / `[mcp_servers.server_b]` (fixes the current
     fixture's missing `mcp_servers.` prefix, which today produces sibling top-level tables, not
     nested ones).
   - Add `monkeypatch.setattr("shared.config_loader._BASE_CONFIG_FILES", ("a.toml", "b.toml"))`
     before constructing the loader.
   - Change the call from `loader.load("a.toml", "b.toml")` to `loader.load_all()`.
3. `test_meta_keys_filtered_from_both_files` (`tests/shared/test_config_loader.py:71-80`):
   replace the fixture with top-level `_meta = "from_a"` / `_meta = "from_b"` keys alongside a
   flat `[section]` table in each file; assert `"_meta" not in result`, `result["section"] ==
   {"bar": 2}`, and `"foo" not in result["section"]` (documents `load()`'s flat overwrite plus
   `_filter_meta_keys()`'s top-level-only stripping in one test).
4. Run each rewritten test individually after its edit, then the full `TestMergeOrder` class,
   then the full file, then the sibling regression file (see Validation plan).

### Method
- Direct in-place edits to the three test methods using exact source and target snippets
  (already reproduced end-to-end against the real, unmodified `config_loader.py` in the source
  plan's Design section) — no new fixtures/conftest entries, no production code edits.
- `pytest.MonkeyPatch`'s `setattr` auto-reverts `_BASE_CONFIG_FILES` at test teardown, so no
  manual cleanup or `autouse` fixture change is needed.

### Details
- `ConfigLoader.load(*names)` (`scripts/shared/config_loader.py:58-66`): flat `dict.update()`
  per file, filtered by `_filter_meta_keys()` first — a later file's top-level key wholly
  replaces an earlier file's value at that key, even if both are dicts.
- `ConfigLoader.load_all(strict=False)` (`scripts/shared/config_loader.py:68-94`): iterates
  `_BASE_CONFIG_FILES`, merging dict-valued keys one level deep
  (`merged[key] = {**merged[key], **val}` when both sides are dicts at that key) — this is the
  branch `test_nested_dict_merge` must exercise, currently unreachable without widening
  `_BASE_CONFIG_FILES` past its single production entry.
- `_filter_meta_keys(data)` (`scripts/shared/config_loader.py:147-150`): a one-line dict
  comprehension over `data.items()` — top-level only, confirmed by reading the code directly.

## Compatibility considerations
- No production code or public API changes; `ConfigLoader.load()` / `load_all()` signatures and
  behavior are unchanged.
- The `_BASE_CONFIG_FILES` monkeypatch is scoped to `test_nested_dict_merge` only and reverts
  automatically at teardown; no cross-test state leakage expected (verified in Validation plan).

## Security considerations
N/A — test-only change, no new file I/O paths, no secrets or credentials involved, no change to
`ConfigPermissionError`/`restrict_to()` handling.

## Rollback considerations
- Each of the three method rewrites is an independent, self-contained edit; reverting any one
  method (e.g. via `git checkout -- tests/shared/test_config_loader.py` for that hunk) does not
  affect the other two or any other test class in the file.
- No production file is touched, so no rollback is needed outside this single test file.

## Validation plan
| Target | Command | Expected outcome |
|---|---|---|
| Each rewritten test individually | `PYTHONPATH=scripts pytest tests/shared/test_config_loader.py::TestMergeOrder::<name> -v` | passes after its own edit |
| `TestMergeOrder` class | `PYTHONPATH=scripts pytest tests/shared/test_config_loader.py::TestMergeOrder -v` | 4/4 pass |
| Full file | `PYTHONPATH=scripts pytest tests/shared/test_config_loader.py -v` | all classes pass, 0 collection errors |
| No production change | `git diff --stat -- scripts/shared/config_loader.py` | empty |
| Sibling regression | `PYTHONPATH=scripts pytest tests/shared/test_shared_boundary_conditions.py -v` | unchanged pass/fail status |
| No monkeypatch leakage | `PYTHONPATH=scripts pytest tests/shared/ -v` | full directory green |
| Lint / format / type check | `ruff check`, `ruff format --check`, `mypy` on the test file | 0 errors / 0 diffs / no new errors |

## Out of scope
- Rewriting `tests/shared/test_shared_boundary_conditions.py::TestDictMergeConflictResolution`
  (filed as a separate follow-up per the source plan's R3 risk).
- Any change to `scripts/shared/config_loader.py`.
- `docs/*.md` updates.

## Traceability
- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/done/20260804-105925_plan.md
- Source implementation procedure: N/A
- Generated at: 20260804-112059
- Related target files: test_config_loader.py
