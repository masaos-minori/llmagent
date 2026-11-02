## Goal
- Create `tests/tools/test_amend_plan.py`: unit tests over fixture Plans for the dry run, append-only rule, refusals, edit locations, the repeated-path case, and the four Freeze criteria (`REQ-001`, `REQ-002`, `REQ-003`).

## Scope
- In scope: the new test module. Out of scope: any change to `tools/amend_plan.py` and the AC-8 comparison against reconstructed real Plans (Plan step 4).

## Assumptions
- Step 3a verification: `tests/tools/` holds one module per tool and existing tests import tools as `import tools.<name> as <alias>` and build Plan text with a helper writing to `tmp_path` (`tests/tools/test_check_plan_target_overlaps.py`); this module follows that style.
- `tools/amend_plan.py` is created by the seq 01 procedure of this Plan, so it exists when this row is executed in order; `tools/stale_detector.py` may report it as a name that only an earlier-`seq` row creates (acceptable).
- The tool refuses Plans outside `plans/`, so tests either monkeypatch the tool's plans-root and repository-root constants to `tmp_path` or call its pure functions on text; the procedure of seq 01 names the entry points. Confirm the final names when executing both rows in order.
- Overlap (Step 2): no other Frozen Plan creates this file.

## Design decisions
- A `_plan_text(...)` fixture builder yields a minimal Plan with every section the tool edits, an optional earlier similar path in an unrelated table row, and configurable requirements, so each test states only what differs.
- One test per behavior; assert on text sections, not whole-file equality, so wording tweaks do not break unrelated tests.

## Alternatives considered
N/A: the module style is fixed by the neighboring `tests/tools/` modules.

## Implementation
### Target file
`tests/tools/test_amend_plan.py` (new)

### Procedure
1. Add the fixture builder and a runner helper that invokes `main(argv)` and returns the exit code and captured output.
2. Tests (`REQ-001`): dry run prints every edit and leaves the file byte-identical; the real run appends the new row after the last existing row and never before it; refusal for a file already a target row, for a file that is a reference row, for a `plans/done/` path, for a Plan missing a required section, and for a duplicate amendment line, each leaving the Plan unchanged.
3. Tests (`REQ-002`): each edit location (Freeze note line, Requirement Traceability row, `Related target files`, `Affected areas` row, step N checkbox, `Work Items Created` row replacing the placeholder, and skipped when `--procedure` is absent); the repeated-path case edits only the intended section; the first Freeze token is unchanged on success.
4. Tests (`REQ-003`): all four criteria passing keeps `Frozen` and marks the row `Verified`; each criterion failing in turn (missing path without `New file`, empty reason, empty evidence, unknown requirement ID) sets `Draft`, marks the row `Needs confirmation`, and names the failed criterion; the three checks' output is printed on a real run and only announced on a dry run; a new-file row carries `New file:` in its `Change Responsibility` cell.

### Method
- Use `tmp_path`, `monkeypatch`, and `capsys`; stub the three subprocess checks with a recorded fake in most tests and run them once for real in a single integration test against a fixture Plan.

### Details
- Keep each test under about 25 lines and share the builder; no network and no writes outside `tmp_path`.

## Compatibility considerations
- Additive test module; no existing test changes.

## Security considerations
- Tests write only under `tmp_path`.

## Rollback considerations
- N/A: delete the new file or revert the commit.

## Validation plan
- `uv run pytest tests/tools/test_amend_plan.py -v`: all pass.
- `uv run ruff format tests/tools/test_amend_plan.py`; `uv run ruff check tests/tools/test_amend_plan.py`; `uv run mypy tests/tools/test_amend_plan.py`.

## Completion criteria
- Tests cover the dry run, append-only rule, each refusal, each edit location, the repeated-path case, and each of the four criteria failing plus all passing (AC-1 to AC-4), and the module passes lint and type checks.

## Out of Scope
- Changes to `tools/amend_plan.py`, the real-Plan comparison (AC-8), and tests for other tools.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Write the fixture builder and the `REQ-001` tests in `tests/tools/test_amend_plan.py` | Completed | 20261102-135831 | 20261102-135831 | Step 3a: no correction. Changed: tests/tools/test_amend_plan.py (new) |
| 2 | Write the `REQ-002` and `REQ-003` tests | Completed | 20261102-135831 | 20261102-135831 | — |
| 3 | Run `uv run pytest tests/tools/test_amend_plan.py -v` and the lint and type checks on the module | Completed | 20261102-135831 | 20261102-135831 | pytest 32 passed; ruff format/check, mypy clean; full suite deferred to plan end |

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
- **Requirement ID**: `REQ-001`, `REQ-002`, `REQ-003` (unit tests for the amendment tool)
- **Source issue**: issues/20261030-191737_flowimp011_plan-amend-tool.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261102-081027_flowimp011_plan-amend-tool.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261102-085611
- **Related target files**: tests/tools/test_amend_plan.py
