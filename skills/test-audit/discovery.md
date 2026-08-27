# Test Audit — Discovery (Test Entry Points and Gap Analysis)

Load this file at Step 0 (unconditionally). It covers Step 1's test-entry-point
discovery and Step 5's gap analysis — both Discovery/Analysis phase types (see
`SKILL.md` Phase Boundaries): no command with real side effects runs here.

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

Inspection commands:
- `find . -name "test_*.py" -o -name "*_test.py"` — discover test files
- `grep -r "def test_" --include="*.py"` — discover test functions
- `cat pyproject.toml | grep -A5 "\[tool.pytest\]"` — check pytest configuration
- `python -m pytest --collect-only` — dry-run test collection (Discovery-safe: does
  not execute test bodies)

If multiple test entrypoints exist, identify all of them. Output: the full candidate
command list `safety.md`'s Step 2 will evaluate — do not execute any of them here.

---

## Gap Analysis (Step 5)

After `workflow.md` Steps 3-4, inspect source code and docs to find coverage gaps and
inconsistencies. Do not execute any new command in this step (see `SKILL.md` Phase
Boundaries).

### Missing or weak tests

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
module grouping in `AGENTS.md`'s Test coverage section). Return only each layer's
findings list, not the source read, so one layer's investigation does not accumulate
into the next.

Output: the raw missing/weak and inconsistent/outdated findings, ready for
`evidence.md`'s Step 6 (Consolidate findings) to assign Finding IDs and categories.
