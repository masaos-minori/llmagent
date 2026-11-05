## Goal
- Add `tests/tools/test_tool_cli_convention.py` with parametrized `--help` and unknown-flag tests for the six tools changed by the Plan, so the `argparse` entries cannot regress (`REQ-005`: tests call `--help` and the main exit paths of the six tools).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: one new test file. The per-tool exit-path tests already exist in the tools' own test files and are not edited.
- Plan: `plans/20261105-105637_toolcli001_define-cli-and-exit-code-convention.md`, Plan step 5 (Phase 5).

## Assumptions
- This document runs after the five tool documents (seq 02-06) and the `generate_reference_table.py` document (seq 07), because filenames sort in implementation order and a cycle cannot end with a failing test; the earlier plan to add the tests first and let them fail was replaced in Step 3a (see the Plan). The tests' discriminating power is shown by a mutation check instead.
- `argparse` exits instead of returning: `--help` raises `SystemExit(0)` and an unknown flag raises `SystemExit(2)`, so the tests use `pytest.raises(SystemExit)` and `capsys`.
- Verified 2026-11-05: `argparse.ArgumentParser().parse_args()` inside a pytest run exits `2` with `unrecognized arguments` taken from pytest's `sys.argv`; therefore for the four tools that take no argument `_parse_args(None)` must ignore `sys.argv`, and a test pins that.
- Plan overlap: no other open Plan targets this file.

## Design decisions
- One module-level list of `(module, takes_no_argument)` pairs for the six tools, imported as `tools.<name>`, and parametrized tests over it, which avoids editing six existing test files.
- Do not run any tool's real `main` on live repository data from this file; the `--help` and unknown-flag paths exit inside argparse before any work.

## Alternatives considered
- Editing each tool's own test file: rejected in the Plan to avoid touching five existing files.

## Implementation
### Target file
`tests/tools/test_tool_cli_convention.py` (new)

### Procedure
1. Create the module with a docstring, `from __future__ import annotations`, imports of `sys`, `pytest`, and the six tool modules (`check_docs_japanese`, `check_dependency_graph_cycles`, `check_needs_confirmation_inventory`, `check_tool_descriptions_sync`, `audit_plan_target_paths`, `generate_reference_table`) from `tools`.
2. Add `TOOLS` (new), a list of the six modules, and `NO_ARGUMENT_TOOLS` (new), the first four.
3. Add the parametrized tests below.

### Method
- `--help`: for each of the six, `main(["--help"])` raises `SystemExit` with code `0` and the captured output contains `usage:`.
- Unknown flag: for each of the six, `main(["--no-such-flag"])` raises `SystemExit` with code `2` and stderr mentions the flag.
- No-argument default: for each of the four no-argument tools, with `sys.argv` patched to `["prog", "--bogus"]`, `_parse_args(None)` returns a namespace and does not raise.
- `audit_plan_target_paths`: `_parse_args(["a.md", "b.md"]).plans == ["a.md", "b.md"]`.
- `generate_reference_table`: `main(["--type"])` and `main([])` exit `2` through argparse (`--type` needs a value; `--type is required` when no mode is given), without reading any file.

### Details
- Use `capsys` for output and `monkeypatch.setattr(sys, "argv", [...])` for the argv case.
- Keep the file free of subprocess calls and of live-data runs; each test is a few lines.
- Mutation check: temporarily change one tool's `_parse_args` to ignore its `argv` argument (`parse_args([])`), confirm a test in this file fails, then revert the tool and confirm `git diff --stat tools/` shows only the planned changes.

## Compatibility considerations
N/A: new test file.

## Security considerations
N/A: no file or network access beyond argparse's output.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/tools/test_tool_cli_convention.py -q` passes, in the default randomized order and with `-p no:randomly`.
- `uv run ruff format`, `uv run ruff check`, `uv run mypy tests/tools/test_tool_cli_convention.py`, and `uv run python tools/check_mock_patch_targets.py` are clean.
- `uv run pytest tests/tools -q` shows no new failure.

## Completion criteria
- All six tools have `--help` and unknown-flag tests, the four no-argument tools have the `sys.argv`-independence test, and the mutation check failed a test and was reverted.

## Out of Scope
- Tests of the tools' main logic, which their own test files cover.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Create the file with the `--help` and unknown-flag tests | Pending | — | — | |
| 2 | Add the `sys.argv`-independence and per-tool parser tests | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) and the mutation check | Pending | — | — | |

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
- **Requirement ID**: `REQ-005` (tests for `--help` and the exit paths of the six tools)
- **Source issue**: issues/20261104-152002_toolcli001_define-cli-and-exit-code-convention.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261105-105637_toolcli001_define-cli-and-exit-code-convention.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261105-162554
- **Related target files**: `tests/tools/test_tool_cli_convention.py`
