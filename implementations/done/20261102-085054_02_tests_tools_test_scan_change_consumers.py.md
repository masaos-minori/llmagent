## Goal
- Create `tests/tools/test_scan_change_consumers.py`, unit tests over temporary trees for the scan tool (`REQ-001`: candidate notice and text/JSON output; `REQ-002`: one test per category and the unrelated-seed case; `REQ-003`: testmon states).

## Scope
- In scope: the new test module only, using `tmp_path` trees and an injected file list so no git repository or real testmon data is needed.
- Out of scope: tests of the live repository (a manual run, `REQ-006`), the registration tests (`tests/tools/test_run_validation_gates.py` is not edited), and the tool itself (row 01).

## Assumptions
- Step 3a verification: `tests/tools/` exists and holds one module per tool (54 `test_*.py` files); `tests/tools/test_check_plan_target_overlaps.py` imports the tool as `import tools.check_plan_target_overlaps as cpto` and builds trees with a small `_write` helper, so the same style applies.
- The tests import names that only row 01's procedure creates: `scan`, `testmon_state` (new), `render_text`, `render_json`, `main`, `Candidate`, and the category constants; this is acceptable because row 01 runs first (earlier-`seq` row).
- The testmon table layout is unconfirmed (Plan UNK-01, non-blocking `Needs confirmation`); the `used` test builds a minimal SQLite file with the table names row 01 settles on, and the `unrecognized` test builds a file without them. If row 01 changes the expected tables after inspecting a real file, update the fixture to match.
- Overlap (Step 2): this new file is not shared with another Plan.

## Design decisions
- One class per concern (`TestSeedCategories` (new), `TestTestmonState` (new), `TestOutput` (new), `TestReadOnly` (new)), each case building its own tiny tree with a `_write(path, text)` helper.
- Use `monkeypatch`/explicit `now` arguments and `os.utime` to make a testmon file stale or fresh deterministically, never real sleeps.

## Alternatives considered
- N/A: structure fixed by the Plan Tests section and the sibling test modules.

## Implementation
### Target file
`tests/tools/test_scan_change_consumers.py` (new)

### Procedure
1. Create the module with the docstring header used by sibling tests and `import tools.scan_change_consumers as scc`.
2. Add the helpers `_write` and `_files(root)` (relative paths of every file under `root`, the injected tracked-file list).
3. Add the test cases below; run them with `uv run pytest tests/tools/test_scan_change_consumers.py -v`.

### Method
- Categories (`REQ-002`), one test each over a tree holding the seed in one place only: `scripts/`, `tests/`, `tools/`, `deploy/`, and `docs/` direct hits; a `tests/` file with `patch("agent.mod.SEED")` and another with `from agent.mod import SEED` (defining file `scripts/agent/mod.py` containing `def SEED`); an inventory hit in `tools/check_x.py` and in a `*baseline*.txt`; an ADR line citing `tests/test_a.py::test_b` where that file contains the seed.
- Unrelated seed: a seed that appears nowhere yields no candidates and an empty `categories`; a seed with no defining module yields the "no defining Python module" limit.
- Testmon (`REQ-003`): no file gives `absent`; a file whose mtime is older than the threshold (set with `os.utime`) gives `stale` and is not opened; a fresh minimal SQLite file gives `used`; a fresh file that is not a database, or lacks the expected tables, gives `unrecognized` with a limit.
- Output (`REQ-001`): text output and `json.loads` of the JSON output both contain the candidates-only notice and the testmon state; JSON has the keys `notice`, `seeds`, `testmon`, `limits`, `candidates`, `categories`; `main([...])` with `--format json --report <path>` writes the same content to the report path.
- Read-only (`REQ-005`): snapshot every file's bytes and mtime in the tree (including the testmon file) before and after a scan and assert equality; assert the testmon file's bytes are unchanged after the `used` case.
- File enumeration: one test runs `git init` in `tmp_path`, adds a tracked and an untracked file, and asserts `list_tracked_files` (new) returns only the tracked one.

### Details
- Keep fixtures small (a few lines per file). The `used` fixture creates the SQLite file with `sqlite3.connect` in the test, then closes it before the scan.
- No network and no use of the real repository root: every `scan`/`main` call passes `root=tmp_path` (`--root`).

## Compatibility considerations
- N/A: new test module; it fails only if row 01's public names or output keys change.

## Security considerations
- N/A: tests write only under `tmp_path`.

## Rollback considerations
- N/A: delete the new file.

## Validation plan
- `uv run pytest tests/tools/test_scan_change_consumers.py -v` passes.
- `uv run ruff format tests/tools/test_scan_change_consumers.py`; `uv run ruff check tests/tools/test_scan_change_consumers.py`; `uv run mypy tests/tools/test_scan_change_consumers.py`.

## Completion criteria
- Every category, the unrelated-seed case, the three testmon states plus the unrecognized case, text and JSON output, the report path, the tracked-file listing, and the no-write assertion each have a passing test.

## Out of Scope
- Live-repository assertions, performance timing, and edits to any other test file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Create `tests/tools/test_scan_change_consumers.py` with helpers and the category, unrelated-seed, testmon, output, read-only, and listing tests | Completed | 2026-11-02 | 2026-11-02 | Created tests/tools/test_scan_change_consumers.py (26 tests); stale check clean; files changed: tests/tools/test_scan_change_consumers.py |
| 2 | Run `uv run pytest tests/tools/test_scan_change_consumers.py -v` and fix failures | Completed | 2026-11-02 | 2026-11-02 | 26 passed; full suite deferred to plan end |
| 3 | Run format, lint, and mypy on the test file (`rules/toolchain.md`) | Completed | 2026-11-02 | 2026-11-02 | ruff format and check clean; mypy clean on the test file; Step 5 N/A: no docs/00_index.md mapping for tests/tools |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-001` (candidate notice, text/JSON), `REQ-002` (category tests), `REQ-003` (testmon states)
- **Source issue**: issues/20261030-191006_flowimp001_consumer-impact-scan.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261102-080004_flowimp001_consumer-impact-scan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261102-085054
- **Related target files**: tests/tools/test_scan_change_consumers.py
