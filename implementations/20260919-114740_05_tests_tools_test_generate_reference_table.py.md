## Goal
Add a new `tests/tools/test_generate_reference_table.py` with unit tests for the
3 new generator functions (`REQ-006`).

## Scope
In scope: creating this one new test file, covering
`generate_agent_reference_table()` and `generate_eventbus_reference_table()`
(the 2 rows actually registered per seq 01's deferred `--type memory`); testing
`generate_memory_reference_table()`'s function directly (not via CLI, since it
is not yet registered). Out of scope: integration/end-to-end tests of the CLI
`--type` dispatch beyond what already exercises `agent`/`eventbus`.

## ⚠ Implementation gate — do not execute before this is satisfied
Same gate as seq 01-04: REQ-008. Additionally depends fully on seq 01's 3
functions existing first (this file's imports fail otherwise).

## Assumptions
- No existing test file for `generate_reference_table.py` — re-confirmed via
  `find tests -iname "*generate_reference*"` (no results).
- `tests/tools/` directory exists and follows a per-function plain-test-function
  convention (confirmed via `tests/tools/test_check_docs_content_policy.py`'s
  style) — no shared fixture framework beyond simple helper functions.

## Design decisions
Mirror `tests/tools/test_check_docs_content_policy.py`'s plain-function test
style (no parametrization, no test classes) as the closest in-repo precedent,
per the source Plan's own stated closest-precedent choice.

## Alternatives considered
Using `pytest`'s `tmp_path` fixture to create real temporary `.py` source files
for the generator functions to scan was considered as more realistic than
mocking, and is the recommended approach here (matches how the existing 3
generators' inputs are real files, not mocks) — an in-memory-mock alternative
was rejected since these generators are fundamentally file-scanning functions,
and a mock would not catch a real glob/path-handling bug.

## Implementation
### Target file
tests/tools/test_generate_reference_table.py

### Procedure
1. Create the file with a module docstring (matching
   `tests/tools/test_check_docs_content_policy.py`'s docstring style) and
   imports of `generate_agent_reference_table`, `generate_eventbus_reference_table`,
   `generate_memory_reference_table` from `tools.generate_reference_table`.
2. Add one test per function using `tmp_path` to create a small, realistic
   fixture module (e.g. a single class with a docstring and one public method)
   and assert the generated table string contains the expected class/method
   name and does not crash on an empty directory.
3. Add one regression test confirming `generate_rag_config_table`/
   `generate_mcp_reference_table`/`generate_deployment_reference_table`'s
   existing behavior is unaffected (import and call each with real repository
   config, per their existing usage — no fixture needed, they already read from
   `config/*.toml`/`config/agent.toml`).

### Method
New file creation (`Write` tool), following the closest in-repo precedent's
style (see Design decisions).

### Details
- Each new-function test: use `tmp_path` to write one `.py` file with a small,
  realistic class/function (docstring + signature), monkeypatch the generator's
  source-directory constant (e.g. `scripts_agent_dir` equivalent — read seq 01's
  actual implementation to find the exact constant name to patch) to point at
  `tmp_path`, call the generator function, and assert the expected content
  appears in the returned Markdown table string.
- Empty-directory case: call each generator against an empty `tmp_path` and
  assert it returns a table with header row only (or an empty string, per
  seq 01's actual implementation) without raising.
- `generate_memory_reference_table()`'s test calls the function directly, not
  via CLI dispatch (since `--type memory` is not yet registered per seq 01).

## Compatibility considerations
New file, no existing test is modified. Depends on seq 01's exact function
signatures and internal constant names — write these tests against the actual
committed implementation, not this document's illustrative sketch.

## Security considerations
N/A: test code only, uses `tmp_path` (no writes outside pytest's managed temp
directory).

## Rollback considerations
`git checkout -- tests/tools/test_generate_reference_table.py` (or delete, since
this is a new file) reverts this row independently.

## Validation plan
- `uv run pytest tests/tools/test_generate_reference_table.py -v` — all tests
  pass.
- `uv run ruff check tests/tools/test_generate_reference_table.py`
- `uv run mypy tests/tools/test_generate_reference_table.py`

## Completion criteria
- One passing test per new generator function (3 total), plus the
  existing-generator regression test.
- `uv run pytest tests/tools/test_generate_reference_table.py -v` is fully
  green.

## Out of scope
CLI-level integration tests for `--type memory` (not yet registered);
performance/large-corpus testing.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Blocked | — | — | Gated on REQ-008; also depends on seq 01's functions existing first |
| 2 | Add or update tests per Validation plan | Pending | — | — | This document's own Target file IS the test file |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | `uv run pytest tests/tools/test_generate_reference_table.py -v` |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: test file only |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | REQ-008 gate not satisfied — re-verified 20260919-121854: guard-detection fix has landed but ADR-015 is still `Proposed`, not `Accepted` (gate requires both); also depends on seq 01 landing first | No | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-006 (unit tests for the 3 new generator functions)
- **Source issue**: issues/done/20260918-130225_docsref01_extend-generate_reference_table-for-agent-eventbus-memory.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260919-105034_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260919-114740
- **Related target files**: tests/tools/test_generate_reference_table.py
