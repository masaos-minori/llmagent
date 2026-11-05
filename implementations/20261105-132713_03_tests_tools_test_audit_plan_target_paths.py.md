## Goal
- Add `tests/tools/test_audit_plan_target_paths.py` so that a break in the missing-path audit of `tools/audit_plan_target_paths.py` fails a test, including a missing-path case (`REQ-003`: tests for the path audit and its `main`; `REQ-004`: tests write only inside `tmp_path`).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: one new test file. No change to `tools/audit_plan_target_paths.py`; the create-hint cell question is filed separately (Plan UNK-02).
- Plan: `plans/20261105-105344_toolstest001_add-tests-for-untested-tools.md`, Plan step 1 (Phase 1).

## Assumptions
- `audit` resolves target paths against the current working directory, so every test calls `monkeypatch.chdir(tmp_path)` (`Path(target).exists()`).
- `ROW_RE` captures the first two table cells and `CREATE_HINTS` is matched against the second one only; a hint in the third cell ("Reason for Modification" in the current Plan template) does not exempt a missing path. The tests pin this behavior and do not change it (verified by running the tool on its own Plan, 2026-11-05).
- `main()` takes no argument and reads `sys.argv[1:]`, so its tests monkeypatch `sys.argv`. The `toolcli001` Plan later adds an `argparse` entry that reads the same `sys.argv`, so the tests keep working after it.
- Plan overlap: `tools/audit_plan_target_paths.py` is a target of the `toolcli001` Plan, which depends on this Plan (a sequencing dependency, not a conflict); `tests/tools/test_amend_plan.py` only fakes the subprocess call, so no test is duplicated.

## Design decisions
- Write small Plan files into `tmp_path` with an `## Implementation Target Files` table, create the "existing" target files under `tmp_path`, and call `audit` with the Plan path.
- Assert the exact finding strings, which carry the Plan file name, the 1-based line number, and the target.

## Alternatives considered
- N/A: a single fixture style covers the whole tool.

## Implementation
### Target file
`tests/tools/test_audit_plan_target_paths.py` (new)

### Procedure
1. Create the module with a docstring, `from __future__ import annotations`, and imports of `pytest`, `pathlib.Path`, and `from tools.audit_plan_target_paths import audit, main`.
2. Add a helper `_plan(tmp_path, rows, *, trailing="")` that writes `plan.md` with the heading, the table header, the separator, the given rows, and an optional following section.
3. Add the tests below, each starting with `monkeypatch.chdir(tmp_path)`.

### Method
- Existing target: a row whose file exists under `tmp_path` produces no finding.
- Missing target: a row naming an absent `scripts/x.py` produces `plan.md:<line>: missing target path: scripts/x.py` with the right line number.
- Create-hint exemption: a missing path whose second cell contains `create`, `new`, `generated`, `manifest;`, or `registry;` produces no finding (one parametrized case per hint); the same hint only in the third cell still produces the missing-path finding.
- Registry branch: a missing `registry/x.yaml` without a hint produces `missing (no create hint): registry/x.yaml`; with a hint it produces nothing; an existing `registry/` path produces nothing.
- Skipped rows: the header row (`File Path`), the separator row, a row with a non-path first cell such as `TBD` (no `/` and no `.`), and a row that does not match `ROW_RE` are all ignored.
- Section bounds: a missing path in a table under a different `## ` heading before or after the section is ignored; a row after a later `## Reference Files` heading is ignored.
- `main`: with `sys.argv` set to the tool name plus one Plan path with a finding, it prints the finding and `1 finding(s) across 1 plan(s).` and returns 1; with a clean Plan it prints `0 finding(s) across 1 plan(s).` and returns 0; with no argument it reads `plans/*.md` from `tmp_path` in sorted order.

### Details
- Write the Plan fixtures as plain strings; do not read any real file under `plans/`.
- Parametrize the hints with `pytest.mark.parametrize`; keep each test under about 15 lines.
- Use `capsys` for `main` output and `monkeypatch.setattr("sys.argv", [...])` for its arguments.

## Compatibility considerations
N/A: new test file; no tool, schema, or public contract changes.

## Security considerations
N/A: tests read and write only inside `tmp_path`.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/tools/test_audit_plan_target_paths.py -q` passes.
- `uv run ruff format` and `uv run ruff check` on the file are clean.
- `uv run python tools/check_mock_patch_targets.py` reports no finding.
- Mutation check: temporarily negate the `Path(target).exists()` test in `audit`, confirm a test fails, revert, and confirm `git diff --stat tools/` is empty.
- `uv run pytest tests/tools -q` shows no new failure.

## Completion criteria
- Existing, missing, create-hinted, registry, skipped, out-of-section rows and both `main` exit codes are covered, including a missing-path test.
- `git status` shows no change outside the new file.
- The mutation check failed a test and was reverted.

## Out of Scope
- Changes to `tools/audit_plan_target_paths.py`, including which table cell carries the create hint.
- Cross-plan overlap and body-reference auditing, which this tool does not do.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Create the file with the Plan fixture helper and the existing, missing, and skipped-row tests | Pending | — | — | |
| 2 | Add the create-hint, registry, and section-bound tests | Pending | — | — | |
| 3 | Add the `main` tests with a patched `sys.argv` | Pending | — | — | |
| 4 | Run the validation sequence (`rules/toolchain.md`) and the mutation check | Pending | — | — | |

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
- **Requirement ID**: `REQ-003` (tests for the path audit), `REQ-004` (tests stay inside `tmp_path`)
- **Source issue**: issues/20261104-152002_toolstest001_add-tests-for-untested-tools.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261105-105344_toolstest001_add-tests-for-untested-tools.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261105-132713
- **Related target files**: `tests/tools/test_audit_plan_target_paths.py`
