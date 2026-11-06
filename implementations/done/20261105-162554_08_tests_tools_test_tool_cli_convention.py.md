## Goal
- Add `tests/tools/test_tool_cli_convention.py` covering the six tools changed by the Plan. NOTE (20261106 adversarial verification): the six tools do **not** share an `argparse` CLI — five define `main() -> int` with no argument and no argparse, `audit_plan_target_paths` reads `sys.argv[1:]` directly, and `generate_reference_table` parses `--type/--dry-run/--manifests/--check` only inside its `__main__` block (it has no `main()`). A parametrized `--help`/unknown-flag test against a uniform `main(argv)`/`_parse_args()` API therefore cannot be written. See the Adversarial Verification section. (`REQ-005`: tests call `--help` and the main exit paths of the six tools).

## Adversarial Verification (20261106; superseded by the correction below)

**Result: the document's core premise is false; the described tests cannot be written or
run against the current code.** Verified by reading the six target modules directly
(`tools/*.py`).

The document assumes every one of the six tools exposes an `argparse`-based CLI with a
`main(argv)` entry point and a module-level `_parse_args()`. None of the six do:

| Tool | `def main` | `argparse` | `_parse_args` |
|------|-----------|-----------|---------------|
| `check_docs_japanese` | `main() -> int`, no params | none | none |
| `check_dependency_graph_cycles` | `main() -> int`, no params | none | none |
| `check_needs_confirmation_inventory` | `main() -> int`, no params | none | none |
| `check_tool_descriptions_sync` | `main() -> int`, no params | none | none |
| `audit_plan_target_paths` | `main() -> int`, reads `sys.argv[1:]` directly | none | none |
| `generate_reference_table` | **no `main()` at all**; argparse lives in `if __name__ == "__main__":` (lines 974-1024) | only in `__main__` | none |

Consequences for the calls the document prescribes:

- `main(["--help"])` raises `TypeError` on the first five (they take zero arguments) and
  `AttributeError` on `generate_reference_table` (no `main`).
- `_parse_args(None)` raises `AttributeError` on all six modules.
- `audit_plan_target_paths._parse_args(["a.md", "b.md"]).plans` raises `AttributeError`
  (no `_parse_args`, no `.plans` attribute; `main` reads `sys.argv[1:]` directly).
- The mutation check ("temporarily change one tool's `_parse_args` to ignore its `argv`
  argument") is impossible: there is no `_parse_args` to change.

How the inputs actually flow: the first four tools read fixed paths under `docs/`
(`DOCS_DIR`, `INVENTORY_DOC_PATH`, `DESCRIPTIONS_DOC`); `audit_plan_target_paths` reads
`sys.argv[1:]`; `generate_reference_table` parses `--type/--dry-run/--manifests/--check`
only inside its `__main__` block, where `--type is required` comes from `parser.error()`.
There is no uniform `--help`/unknown-flag convention to regress, so the parametrized
`--help` + unknown-flag test this document proposes does not apply to the current code.

Implementation steps were left `Pending`; nothing was executed. The inline claims below
were corrected to match the code.

## Correction (code-implementation Step 3b, 2026-11-06)

The Adversarial Verification above held against the code as it was when it was written, before the procedures `02` to `07` of this Plan were executed. They are now executed: the five tools expose `_parse_args(argv)` and `main(argv)`, and `generate_reference_table.py` exposes `_build_parser()` and `main(argv)`. So the calls this document prescribes exist, and the Method, Details, and Completion criteria are restored to what the Plan asks (see below). Two facts differ from the original wording and are used here: the four fixed-input tools' `_parse_args(None)` parses `[]` (it never reads `sys.argv`), while `audit_plan_target_paths._parse_args(None)` reads `sys.argv[1:]` and returns the `plans` list; and `generate_reference_table.main([])` ends in `parser.error` (exit `2`) before any work.

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: one new test file. The per-tool exit-path tests already exist in the tools' own test files and are not edited.
- Plan: `plans/done/20261105-105637_toolcli001_define-cli-and-exit-code-convention.md`, Plan step 5 (Phase 5).

## Assumptions
- This document runs after the five tool documents (seq 02-06) and the `generate_reference_table.py` document (seq 07), because filenames sort in implementation order and a cycle cannot end with a failing test; the earlier plan to add the tests first and let them fail was replaced in Step 3a (see the Plan). The tests' discriminating power is shown by a mutation check instead.
- `argparse` exits instead of returning: `--help` raises `SystemExit(0)` and an unknown flag raises `SystemExit(2)`, so the tests use `pytest.raises(SystemExit)` and `capsys`.
- Verified 2026-11-06: none of the six tools expose `argparse`, `main(argv)`, or `_parse_args()`. The first four read fixed paths under `docs/` (`DOCS_DIR`, `INVENTORY_DOC_PATH`, `DESCRIPTIONS_DOC`); `audit_plan_target_paths` reads `sys.argv[1:]`; `generate_reference_table` parses `--type/--dry-run/--manifests/--check` only inside its `__main__` block. So the `--help`/unknown-flag convention this document assumed does not exist (see Adversarial Verification).
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
- `--help` raises `SystemExit(0)` and prints usage; an unknown flag raises `SystemExit(2)`: parametrize `main(["--help"])` and `main(["--bogus"])` over all six tools with `pytest.raises(SystemExit)` and `capsys`. Neither path does any work (argparse exits first), so no live data is read.
- `sys.argv` independence: for the four fixed-input tools, patch `sys.argv` to `["prog", "--bogus"]` and assert `_parse_args(None)` returns a namespace without exiting.
- `audit_plan_target_paths._parse_args(["a.md", "b.md"]).plans == ["a.md", "b.md"]`, and `_parse_args(None)` reads the patched `sys.argv[1:]`.
- `generate_reference_table.main([])` raises `SystemExit(2)` (`--type` required) and its `_build_parser()` still lists `--type`, `--dry-run`, `--manifests`, and `--check`.

### Details
- Use `capsys` for output and `monkeypatch.setattr(sys, "argv", [...])` for the argv case.
- Keep the file free of subprocess calls and of live-data runs; each test is a few lines.
- Mutation check: temporarily change one tool's `_parse_args` to ignore its `argv` argument, confirm a test fails, then restore it.

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
- Each of the six tools answers `--help` with exit `0` and rejects an unknown flag with exit `2` in tests; the four fixed-input tools' `_parse_args(None)` ignores `sys.argv`; the `audit_plan_target_paths` and `generate_reference_table` cases above pass; the mutation check fails as expected; and the validation checks pass.

## Out of Scope
- Tests of the tools' main logic, which their own test files cover.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Create the file with the `--help` and unknown-flag tests | Completed | 20261106-112640 | 20261106-112839 | Changed: tests/tools/test_tool_cli_convention.py (new, 20 tests); procedure corrected at Step 3b to the code after 02-07 |
| 2 | Add the `sys.argv`-independence and per-tool parser tests | Completed | 20261106-112839 | 20261106-112839 | 20 tests pass; mutation check (argv ignored in check_docs_japanese) failed as expected |
| 3 | Run the validation sequence (`rules/toolchain.md`) and the mutation check | Completed | 20261106-112839 | 20261106-112839 | ruff, mypy, mock-patch checker clean; tests/tools 1704 passed; gates no Fail |

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
- **Source plan**: plans/done/20261105-105637_toolcli001_define-cli-and-exit-code-convention.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261105-162554
- **Related target files**: `tests/tools/test_tool_cli_convention.py`
