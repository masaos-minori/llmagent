## Goal
Add `tests/tools/test_check_workitem_traceability.py` using fixture directories,
covering a valid chain (issue -> plan -> procedure, all present), a missing-source-
file case, an issue with no plan yet, and a plan with no procedure yet (REQ-008).

## Scope
- In scope: unit tests for the four scenarios in Requirements/Acceptance criteria,
  built against fixture directories (not the live `issues/`/`plans/`/
  `implementations/` trees).
- Out of scope: testing the stale-target heuristic's regex-matching corpus
  exhaustively (REQ-005's own scenario coverage is one representative fixture, per
  the Plan's Tests section); testing the sibling tools tracked as separate issues.

## Assumptions
- `tools/check_workitem_traceability.py` (seq 01 of this Plan) exposes its
  discovery/parsing/per-category-check logic as importable functions (`from
  tools.check_workitem_traceability import ...`), matching the sibling test
  precedent `tests/tools/test_check_compat_shims.py`'s fixture/`tmp_path`-based,
  direct-import structure.
- Fixture directories are built under `tmp_path`, mirroring the real
  `issues/`/`plans/`/`implementations/` (and `done/`) directory layout, with
  minimal synthetic Traceability sections — not copies of real repository files.

## Design decisions
- Each scenario builds its own isolated `tmp_path` fixture tree rather than sharing
  one large fixture across tests, so a fixture change for one scenario cannot
  silently affect another's assertions.
- The missing-source-file test asserts on the parsed finding's referenced path
  string, not on stdout formatting, so the test remains stable if the
  human-readable summary's wording changes later.

## Alternatives considered
- Running tests against a snapshot/copy of the live `issues/`/`plans/`/
  `implementations/` trees: rejected — the Plan's Scope explicitly requires fixture
  directories, not the live trees, to keep tests independent of ongoing repository
  churn.

## Implementation
### Target file
`tests/tools/test_check_workitem_traceability.py`

### Procedure
1. **Valid chain** (REQ-001, REQ-002; AC-001 precedent): build a fixture tree with
   one issue, one plan whose Traceability `Source issue` points to that issue, and
   one implementation procedure whose Traceability `Source plan` points to that
   plan. Assert zero missing-source-file, no-plan-yet, and no-procedure-yet
   findings for this chain.
2. **Missing-source-file** (REQ-002; AC-002): build a fixture plan whose `Source
   issue` value points to a path that does not exist in the fixture tree. Assert
   the missing-source-file check reports that exact path.
3. **No-plan-yet** (REQ-003; AC-003): build a fixture issue with no plan
   referencing it, with a filename timestamp older than the configured age
   threshold. Assert it is reported. Build a second fixture issue with a filename
   timestamp younger than the threshold and no plan referencing it; assert it is
   NOT reported.
4. **No-procedure-yet** (REQ-004; AC-003): symmetric to scenario 3, for a fixture
   plan with no implementation procedure referencing it.

### Method
`pytest` test module using `tmp_path` for isolated fixture directories; imports
`tools.check_workitem_traceability`'s discovery/parsing/check functions directly
(not via `subprocess`), matching `tests/tools/test_check_compat_shims.py`'s
precedent. Each scenario is its own test function (not parametrized together,
since each builds a structurally distinct fixture tree).

### Details
- Fixture issue/plan/procedure files need only a minimal `## Traceability` section
  (the fields this tool parses) plus a filename following the real naming
  convention (`{timestamp}_..._{slug}.md` for issues, `{timestamp}_plan.md` for
  plans, `{timestamp}_{seq}_{slug}.md` for procedures) — full document bodies are
  not required for these tests.
- The age-threshold boundary tests (scenario 3) pass an explicit
  `age_threshold_days` value to `find_no_plan_yet`/`find_no_procedure_yet`.
  **Adversarial-verification correction (2026-09-01):** the current
  `tools/check_workitem_traceability.py` source has no "now" parameter on
  either function — both call `datetime.now()` internally with no injection
  point. Passing a fixed reference "now" therefore uses `freezegun.freeze_time`
  around the `discover_documents()`/`find_no_plan_yet`/`find_no_procedure_yet`
  calls (freezegun is already a declared dev dependency in `pyproject.toml`;
  not previously used under `tests/tools/`), not a function parameter. Fixture
  filename timestamps are computed as fixed offsets from that frozen "now"
  (well clear of the threshold boundary — e.g. threshold+10 days for the
  "old" case, threshold-25 days for the "young" case) so the test remains
  deterministic without depending on wall-clock date.
- **Adversarial-verification correction (2026-09-01):** `ROOT_DIR` in
  `tools/check_workitem_traceability.py` is a module-level constant read by
  `discover_documents()` and `_source_path_exists()` as a global, not an
  injectable parameter — there is no `from tools.check_workitem_traceability
  import discover_documents, ...` call shape that can redirect it to
  `tmp_path`. Each test therefore does `import tools.check_workitem_traceability
  as cwt` and `monkeypatch.setattr(cwt, "ROOT_DIR", tmp_path)` before calling
  `cwt.discover_documents()`/`cwt.find_*(...)` — still a direct import and
  direct function call (not `subprocess`), just module-qualified so the
  monkeypatch target is addressable.
- Confirm no fixture file under `tmp_path` writes back to or reads from the real
  `issues/`/`plans/`/`implementations/` trees — every path passed to the function
  under test is rooted at `tmp_path` (via the `ROOT_DIR` monkeypatch above).

## Compatibility considerations
New test file; no existing test module imports it. Adding it does not change any
existing test's behavior.

## Security considerations
Tests use `tmp_path` fixtures only — no writes outside pytest's managed temporary
directory, no network access, no subprocess with untrusted input.

## Rollback considerations
New file only; rollback is deleting
`tests/tools/test_check_workitem_traceability.py`. No other test or module depends
on it.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tests/tools/test_check_workitem_traceability.py` | Unit | `uv run pytest tests/tools/test_check_workitem_traceability.py -v` | All four scenarios pass |
| `tests/tools/test_check_workitem_traceability.py` | Regression | `uv run pytest tests/tools/ -v` | No new failures (note: `tests/tools/test_check_agent_docs_consistency.py` has a pre-existing, unrelated collection error per this Plan's Design section — not something this file is responsible for fixing) |

## Completion criteria
- `tests/tools/test_check_workitem_traceability.py` exists and covers the
  valid-chain, missing-source-file, no-plan-yet, and no-procedure-yet scenarios
  against fixture directories.
- `uv run pytest tests/tools/test_check_workitem_traceability.py -v` passes with no
  failures (requires `tools/check_workitem_traceability.py` from seq 01 of this
  Plan to exist first).

## Out of scope
- Exhaustive stale-target heuristic corpus testing.
- Testing the sibling tools tracked as separate issues.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260901-151829 | 20260901-152500 | Adversarial verification corrected two Assumptions/Details items: no "now" injection parameter on `find_no_plan_yet`/`find_no_procedure_yet` (use `freezegun.freeze_time` instead) and `ROOT_DIR` requires `monkeypatch.setattr` on the imported module (`import ... as cwt`), not a bare-name import — see Assumptions/Details |
| 2 | Add or update tests per Validation plan | Completed | 20260901-151829 | 20260901-152500 | This document's own subject is the test file; 7 test functions across 4 scenario classes |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260901-151829 | 20260901-152500 | `ruff format`/`ruff check`/`mypy` clean; `pytest tests/tools/test_check_workitem_traceability.py -v` 7/7 passed; `pytest tests/tools/ -v --continue-on-collection-errors` 68 passed, 1 pre-existing collection error (`test_check_agent_docs_consistency.py`, unrelated) |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260901-151829 | 20260901-152500 | N/A: no `docs/00_index.md` task-scope mapping for `tests/tools/test_check_workitem_traceability.py` (checked "Document References by Task"; the `tools/01_overview.md` row targets `tools/` scripts themselves, not their test files) |

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
- **Requirement ID**: REQ-008
- **Source issue**: `issues/20260831-194739_tool003_check_workitem_traceability.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260901-110301_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260901-114312
- **Related target files**: `tests/tools/test_check_workitem_traceability.py`
