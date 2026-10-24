# Test Audit — Discovery (Test Entry Points and Gap Analysis)

Load this file at Step 0 (unconditionally). It covers Step 1's test-entry-point
discovery and Step 5's gap analysis (see `SKILL.md` Phase Boundaries): no command with
real side effects runs here.

---

## Test Entry Point Discovery (Step 1)

Inspect the repository and identify:
- test framework(s)
- test commands
- package manager / build tool
- CI workflows
- test directories
- coverage tooling
- lint / typecheck / import-lint / schema-check commands
- unit / integration / e2e / smoke test structure

Inspection commands. Scope every search to the test directories named by `testpaths` in
`pyproject.toml`; MUST NOT search the whole repository, because that also matches
third-party tests under `.venv/`:
- `rg --files tests -g 'test_*.py' -g '*_test.py'` — discover test files
- `rg -n 'def test_' tests` — discover test functions
- `rg -n -A12 '^\[tool\.pytest' pyproject.toml` — check pytest configuration. The section
  is `[tool.pytest.ini_options]`, so a search for the literal `[tool.pytest]` finds
  nothing. Note `addopts`, `markers`, and the pytest plugins declared in the dev
  dependencies.

`pytest --collect-only` is NOT run in this step: collection imports `conftest.py` and
every test module, which executes module-level code. List it as a candidate command
instead, so Step 2 classifies it and Step 3 runs it.

If multiple test entrypoints exist, identify all of them. Output: the full candidate
command list `safety.md`'s Step 2 will evaluate — MUST NOT execute any of them here.

---

## Gap Analysis (Step 5)

After `workflow.md` Steps 3-4, inspect source code and docs to find coverage gaps and
inconsistencies. MUST NOT execute any new command in this step (see `SKILL.md` Phase
Boundaries).

### Missing or weak tests

Coverage evidence: read coverage figures from Step 3's recorded coverage summary. If no
coverage was collected, a claim of weak or missing coverage is `Needs confirmation:
coverage not measured` — MUST NOT infer it from file names or test counts.

Look for:
- important modules with no tests
- complex branches with weak coverage
- fallback paths with no tests
- failure/recovery logic with no tests
- boundary conditions with no tests
- config/reload behavior with no tests
- persistence / schema / migration behavior with no tests
- plugin or extension behavior with no tests
- CLI command behavior with no tests
- concurrency / retry / timeout / fail-open / fail-fast paths with no tests
- doc/code mismatches that should be protected by tests
- tests with weak assertions (e.g. only checking non-empty output)

### Inconsistent or outdated tests

Find tests that are:
- inconsistent with current implementation
- inconsistent with current documentation
- duplicative but asserting different behavior
- over-mocked and not validating real behavior
- dependent on execution order
- silently skipping important cases
- missing regression coverage for known bugs

Perform this analysis sequentially by layer (agent, shared, mcp, rag, db — per the
module grouping in `rules/env.md`, section "Architecture"). Return only each layer's
findings list, not the source read.

Output: the raw missing/weak and inconsistent/outdated findings, ready for
`evidence.md`'s Step 6 (Consolidate findings) to assign Finding IDs and categories.
