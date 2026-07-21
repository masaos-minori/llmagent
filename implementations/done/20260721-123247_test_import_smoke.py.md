# Implementation Procedure: tests/test_import_smoke.py

Source plan: `plans/20260721-121054_plan.md` ("Add `from __future__ import annotations` to
`scripts/shared/tool_executor.py`") — Phase 2, second checklist item ("Create
`tests/test_import_smoke.py` with explicit test functions asserting that
`import shared.tool_executor`, `from agent import factory`, and `from agent import
context, repository_gateway` all succeed without raising").

## Goal

Create a new, dedicated regression test file, `tests/test_import_smoke.py`, containing
explicit pytest test functions that assert `shared.tool_executor`, `agent.factory`,
`agent.context`, and `agent.repository_gateway` import successfully without raising an
exception. This locks in the fix for the `NameError: name 'RuntimeToolRegistry' is not
defined` startup crash (caused by a missing `from __future__ import annotations` in
`scripts/shared/tool_executor.py`) so the exact failure mode cannot silently regress
again undetected.

## Scope

**In scope:**
- Add one new test file: `tests/test_import_smoke.py`.
- Test functions cover exactly the four modules named in the plan's Acceptance
  Criteria: `shared.tool_executor`, `agent.factory`, `agent.context`,
  `agent.repository_gateway`.

**Out of scope:**
- No change to `scripts/shared/tool_executor.py` itself (covered by a separate,
  already-tracked implementation item for `tool_executor.py` — this document only
  covers the new test file).
- No change to `tests/conftest.py`, `pyproject.toml`, or any other existing test file.
- No broader "smoke import all modules" test harness — only the four modules named in
  the plan.

## Assumptions

1. `tests/conftest.py` (lines 1-17, confirmed by direct grep/read) inserts
   `scripts/` into `sys.path` via `sys.path.insert(0, str(Path(__file__).parent.parent
   / "scripts"))`, so `import shared.tool_executor` and `from agent import factory`
   resolve correctly during pytest collection without any `PYTHONPATH` env var — this
   mechanism is automatic for every file under `tests/`, no per-file setup needed.
2. `pyproject.toml`'s `[tool.pytest.ini_options]` (confirmed lines ~105-111) sets
   `testpaths = ["tests"]`, `addopts = "-v --tb=short"`, `asyncio_mode = "auto"`; no
   `pythonpath` key is set — the path insertion is entirely via `conftest.py`, not
   pytest config. No new pytest config changes are needed for this file to be
   discovered (standard `test_*.py` naming already matches).
3. `scripts/shared/tool_executor.py` currently (as of this planning pass) does NOT
   have `from __future__ import annotations` — confirmed directly by reading its first
   25 lines. This means that **at the time this test file is first created**, running
   it against current `master` will FAIL with the `NameError` this plan is meant to
   fix. This test file is expected to go from failing to passing once the sibling
   `tool_executor.py` fix (Phase 2's first checklist item, tracked separately) is
   applied. This is expected/intended regression-test behavior (fail before fix,
   pass after), not a defect in this document.
4. No existing test file in `tests/` performs this exact "import 4 named modules and
   assert no exception" smoke check (confirmed via `grep -rln smoke tests/` returning
   no matches, per Explore sub-agent investigation) — this is a genuinely new file,
   not a duplicate.

## Implementation

### Target file

`tests/test_import_smoke.py` (new file)

### Procedure

1. Create `tests/test_import_smoke.py` with a module docstring identifying the file
   and its purpose (regression lock for the `tool_executor.py` `NameError` startup
   crash), following the header convention observed in `tests/test_agent_factory.py`
   (module docstring first, English only per `rules/coding.md`).
2. Add `from __future__ import annotations` after the docstring, matching the
   convention already used in `tests/test_agent_factory.py` (its own `from __future__
   import annotations` on the line right after its docstring).
3. Write one test function per module (or one function covering all four, per the
   "Method" section below) that performs the import inside the test body (not at
   module level) so that an import failure is captured as a clean, labeled test
   failure (with a readable pytest traceback naming this test) rather than a pytest
   *collection* error for the whole file, which is comparatively hard to read and
   would abort collection of any other tests in the same file/session.
4. Do not add any assertions beyond "the import statement did not raise" — per
   the plan's Acceptance Criteria, the test's only job is to prove importability, not
   to exercise any behavior of the imported modules.
5. Save the file. Do not run implementation or modify any other file — this
   procedure document is for `tests/test_import_smoke.py` creation only.

### Method

- Use plain `def test_...():` functions (no fixtures, no parametrize needed — four
  fixed, known module names), each performing an `import <module>` statement inside
  the function body wrapped only by the test's own success/failure semantics (no
  `try/except` needed — an uncaught `ImportError`/`NameError` inside a test body
  already fails that test with a clear traceback, which is exactly the desired
  regression signal).
- Follow the repo's `# noqa: F401` convention observed in
  `tests/test_stage_observability.py` (`# noqa: F401 — imported to verify public
  symbol`) for any import that is bound to a local name but not otherwise used in the
  test body, since `ruff` (rule `F401`, unused import) would otherwise flag it. Add an
  inline justification per `rules/coding.md` ("Suppression governance" — every `# noqa`
  requires an inline justification).
- Split responsibilities across four small test functions (one per module named in
  the Acceptance Criteria) rather than one large function, so a future regression in
  any single module produces an unambiguous, individually-named failing test (e.g.
  `test_import_shared_tool_executor` fails specifically, rather than a combined
  `test_all_imports` failing without indicating which import broke).
- Import style: match `tests/test_agent_factory.py`'s convention of `from <module>
  import <name>` for symbol-level imports where a symbol is needed for the assertion;
  for a pure "module resolves" smoke check, a bare `import shared.tool_executor` /
  `from agent import factory` (etc.) is sufficient and matches the plan's Acceptance
  Criteria wording exactly.

### Details

Target file skeleton (illustrative signatures only, not full production code, per
`skills/python-design` rule against writing production code blocks in a design
document — the actual file content is straightforward enough that the procedure above
plus this skeleton fully specifies it):

```python
"""
tests/test_import_smoke.py
Regression lock: shared.tool_executor, agent.factory, agent.context, and
agent.repository_gateway must import without raising. Prevents silent
regression of the NameError('RuntimeToolRegistry' undefined) startup crash
caused by a missing `from __future__ import annotations` in
scripts/shared/tool_executor.py.
"""

from __future__ import annotations


def test_import_shared_tool_executor() -> None:
    import shared.tool_executor  # noqa: F401 — imported to verify module resolves cleanly


def test_import_agent_factory() -> None:
    from agent import factory  # noqa: F401 — imported to verify module resolves cleanly


def test_import_agent_context() -> None:
    from agent import context  # noqa: F401 — imported to verify module resolves cleanly


def test_import_agent_repository_gateway() -> None:
    from agent import repository_gateway  # noqa: F401 — imported to verify module resolves cleanly
```

Notes for the implementer:
- Function names above are suggestions matching repo test-naming conventions
  (`test_<verb>_<subject>`); keep them descriptive enough that a failing test name
  alone identifies which module broke.
- No fixtures, mocks, or `conftest.py` changes are needed — `sys.path` setup is
  already handled globally by the existing `tests/conftest.py`.
- Do not add a `pytest.mark.integration` marker — this is a pure in-process import
  check with no external I/O, matching the "unit test, no I/O, fast" category from
  `skills/python-design/workflow.md` Step 7.

## Validation plan

| Check | Command | Expected outcome |
|---|---|---|
| New test file passes (after the sibling `tool_executor.py` fix lands) | `uv run pytest tests/test_import_smoke.py -v` | All 4 test functions pass |
| New test file fails cleanly before the fix (sanity-check the test itself is a real regression lock, not a no-op) | `uv run pytest tests/test_import_smoke.py -v` run against current `master` (fix not yet applied) | `test_import_shared_tool_executor` (and downstream `agent.*` tests, since they transitively import `shared.tool_executor`) fail with the `NameError` — confirms the test actually detects the bug it is meant to guard against |
| Lint | `uv run ruff format tests/` / `uv run ruff check tests/` | Clean; no unused-import (F401) warnings due to the `# noqa: F401` justification comments |
| Type check | `uv run mypy tests/` | No new errors (file has no complex typing; `from __future__ import annotations` avoids any forward-reference issues) |
| Full suite regression check | `uv run pytest -q` | New test collected and passing; no unrelated regressions introduced |
| Pre-commit | `uv run pre-commit run --all-files` | Passes |
