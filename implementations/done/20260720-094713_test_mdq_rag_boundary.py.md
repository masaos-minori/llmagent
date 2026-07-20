# Implementation: tests/test_mdq_rag_boundary.py (expand — agent-layer and shared-layer MDQ boundary scans)

Source plan: `plans/20260719-212007_plan.md` ("Expand MDQ concurrency and boundary guardrail tests")

## Goal

Extend the existing `tests/test_mdq_rag_boundary.py` (currently `class TestMdqRagBoundary`
with 3 tests) with two new static-scan tests that guard against future drift:

1. No direct MDQ SQLite access (`"mdq.sqlite"` literal or an `MdqService` import from
   outside `scripts/mcp_servers/mdq/`) from `scripts/agent/`.
2. No direct MDQ/RAG SQLite access (`"mdq.sqlite"`, `"rag.sqlite"`, or a bare
   `sqlite3.connect` call) from `scripts/shared/`, unless the file is in a narrow, empty,
   explicitly-commented allowlist.

Both are guardrails against future drift, not fixes for an existing violation — per the
source plan's Assumption 4, `rg` today finds zero matches for `mdq.sqlite` or `MdqService`
under `scripts/agent/` or `scripts/shared/`, so both new tests are expected to pass
immediately. No production code changes.

## Scope

**In:**
- Add `test_agent_layer_has_no_direct_mdq_sqlite_access` to
  `tests/test_mdq_rag_boundary.py`.
- Add `test_shared_layer_has_no_direct_mdq_rag_sqlite_access` to the same file, with an
  empty allowlist and an inline comment explaining why it starts empty.

**Out:**
- `test_rag_pipeline_layer_has_no_mdq_sqlite_references` — already exists in the current
  file (lines 29-39) and already satisfies the requirement's "no mdq.sqlite reference in
  RAG pipeline code" acceptance criterion. Do not duplicate or rename it.
- Any change to `scripts/mcp_servers/mdq/`, `scripts/agent/`, or `scripts/shared/`
  production code.
- `docs/04_mcp_04_04_mdq.md` — no stale wording found by the source plan's Design section
  §3; no doc edit planned.

## Assumptions

1. Current file structure (`tests/test_mdq_rag_boundary.py`, 54 lines) has a module-level
   `SCRIPTS = Path(__file__).parent.parent / "scripts"` constant and a
   `_py_files(subdir: str) -> list[Path]` helper (`(SCRIPTS / subdir).rglob("*.py")`),
   reused unchanged by the two new tests — confirmed by direct read of the current file.
2. All three existing tests live inside `class TestMdqRagBoundary` and follow the same
   pattern: build a `violations: list[str]` comprehension over `_py_files(subdir)` checking
   file contents against a string pattern, then `assert not violations` with a message
   listing the violating paths joined with `\n`. The two new tests are added as methods on
   this same class, following the identical pattern (confirmed by direct read).
3. Per the source plan's Assumption 2, MDQ has no `DbTarget` entry in
   `scripts/db/helper.py` and manages its own `sqlite3.connect(self.db_path)` directly in
   `mdq_service.py` — so "direct MDQ DB access" cannot be detected via a
   `SQLiteHelper("mdq")` string pattern (that target does not exist). Detection must use
   the `"mdq.sqlite"` literal and/or an import of `MdqService` from outside
   `scripts/mcp_servers/mdq/` (pattern: `"from mcp_servers.mdq"` appearing in a file that
   is not itself under `mcp_servers/mdq/`).
4. Per the source plan's Assumption 4, `rg -l "mdq.sqlite|MdqService" scripts/agent/
   scripts/shared/` returns zero matches today — both new tests are expected to start
   green.
5. Per the source plan's UNK-03, `scripts/shared/` has zero `SQLiteHelper(` references
   today, so the shared-layer allowlist starts as an empty `set[str]` with an inline
   comment ("empty pending a real, reviewed exception") rather than pre-populating any
   entry.

## Implementation

### Target file

`tests/test_mdq_rag_boundary.py` (existing file, currently 54 lines, one module-level
helper plus `class TestMdqRagBoundary` with 3 test methods — extend the class, do not
rewrite the file).

### Procedure

1. Keep the existing module docstring, `SCRIPTS` constant, `_py_files()` helper, and all 3
   existing test methods unchanged.
2. Add `test_agent_layer_has_no_direct_mdq_sqlite_access` as a new method on
   `TestMdqRagBoundary`, placed after the existing
   `test_agent_layer_rag_sqlite_access_only_in_maintenance_service` method.
3. Add `test_shared_layer_has_no_direct_mdq_rag_sqlite_access` as a new method after that.
4. No new imports required — both new tests only need `Path` (already imported) and
   `_py_files()` (already defined at module level).

### Method

Both new tests follow the exact violations-list + descriptive-assert pattern already
established by the file's 3 existing tests: scan a layer's `.py` files for one or more
forbidden substrings, collect violating paths, and assert the list is empty with a
message enumerating the offending file paths (satisfies the requirement's "Test failure
messages include violating file paths" acceptance criterion).

### Details

**`test_agent_layer_has_no_direct_mdq_sqlite_access`:**
- Scan `_py_files("agent")`.
- For each file's text, check for either the literal `"mdq.sqlite"` or the substring
  `"from mcp_servers.mdq"` (catches `from mcp_servers.mdq.mdq_service import MdqService`
  and similar import forms).
- Build `violations: list[str]` of `str(p)` for files matching either pattern.
- `assert not violations, ("Direct MDQ DB/import access found in scripts/agent/:\n" + "\n".join(f"  {v}" for v in violations))`.
- Docstring should note this is a static string/import scan, not a runtime guarantee (per
  source plan's Risks section — matches the same caveat already implicit in the file's
  existing tests).

**`test_shared_layer_has_no_direct_mdq_rag_sqlite_access`:**
- Define a local `ALLOWED: set[str] = set()  # empty today; add a filename here only with an inline comment explaining the reviewed exception` at the top of the test method (or as a class-level constant next to the existing `ALLOWED` pattern used in
  `test_agent_layer_rag_sqlite_access_only_in_maintenance_service`, lines 43-49 of the
  current file, which uses a local `ALLOWED = {"rag_maintenance_service.py"}` inside the
  method body — follow that same local-variable convention for consistency).
- Scan `_py_files("shared")`.
- For each file's text (excluding files whose `p.name` is in `ALLOWED`), check for any of:
  `"mdq.sqlite"`, `"rag.sqlite"`, or `"sqlite3.connect"`.
- Build `violations: list[str]` of `str(p)` for matching, non-allowlisted files.
- `assert not violations, ("Direct MDQ/RAG SQLite access found in scripts/shared/ (not in allowlist):\n" + "\n".join(f"  {v}" for v in violations))`.
- Inline comment on the `ALLOWED` set must explain it is intentionally empty pending a
  real, reviewed exception (per source plan's Implementation steps, Phase 2).

## Validation plan

| Check | Command | Expected |
|---|---|---|
| New tests pass | `uv run pytest tests/test_mdq_rag_boundary.py -v` | all pass (3 existing + 2 new = 5) |
| Lint | `uv run ruff format tests/ && uv run ruff check tests/` | 0 errors |
| Type check | `uv run mypy scripts/` (tests/ covered by pre-commit's mypy run) | no new errors |
| Boundary gate | `uv run pytest tests/test_mdq_rag_boundary.py -v` | boundary clean, per `rules/toolchain.md` step 6 |
| Regression | `uv run pytest tests/test_mdq_tool_layer_consistency.py tests/test_tool_server_layer_consistency.py -v` | unchanged, all pass |
| Full suite | `uv run pytest -v` | no new failures |
| MCP docs consistency | `uv run check-mcp-docs` | pass (no doc changes made) |
