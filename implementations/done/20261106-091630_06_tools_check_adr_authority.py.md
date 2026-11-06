## Goal
Make `tools/check_adr_authority.py` render its JSON output and declare its `--format` option through the shared module, with byte-identical output and unchanged exit codes (`REQ-005`; `REQ-006`: batch 2).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: `render_json` (two call sites), the `--format` argument, and the import block.
- Out of scope: `collect_findings`, the inline text loop and its stdout and stderr split, the authority model rules.

## Assumptions
- Verified on 2026-11-06 (Step 3a): the file has the guarded bootstrap and imports `Finding` and other names from `tools._adr_authority_core`; `render_json(findings)` emits `code`, `location`, `message` sorted by `(code, location, message)` with `OPT_INDENT_2`; `main` has `--format` with `choices=["json"]`, `default=None`, and the same help text; the `AuthorityModelError` path builds one `Finding(code="MODEL_INVALID", ...)` and prints it with `render_json` when `--format json` (otherwise `[ERROR] message` on stderr) and returns `1`; the normal path prints `render_json(findings)` and returns `1 if findings else 0`; the text path prints `[code] location: message` lines on stdout, `Found N finding(s).` on stderr, or `Authority model OK: no findings.` on stdout. CI runs it by path (`.github/workflows/ci.yml`: `uv run python tools/check_adr_authority.py`).
- `tests/tools/test_adr_authority.py` exercises `main(...)` with `--format json` through `capsys` and does not use `render_json` directly; no test edit is needed.
- Overlap judgment: no other open Plan targets this file; `tools/generate_adr_authority.py` does not import its renderer (checked with `rg`).
- Shared symbols come from the earlier-`seq` sibling procedure for `tools/_report.py`.

## Design decisions
- Use `PROFILE_AUTHORITY` (sort by `code`, `location`, `message`; keys in that order; no sorted output keys) over `[from_authority_finding(f) for f in findings]` at both call sites. The text loop stays in this tool because it is not a shared layout.

## Alternatives considered
- Adding an authority text layout to `render_text`: rejected, the layout is used by one tool and its stdout and stderr split is not a renderer concern.

## Implementation
### Target file
`tools/check_adr_authority.py`

### Procedure
1. Add `from tools._report import PROFILE_AUTHORITY, add_format_argument, from_authority_finding, render_json` after the existing `tools._adr_authority_core` import.
2. Delete the local `render_json`; remove the `orjson` import only if nothing else uses it.
3. Replace the `--format` `add_argument` call with `add_format_argument(parser, choices=("json",), default=None)`.
4. Replace both `render_json(...)` calls (the `MODEL_INVALID` path and the normal path) with `render_json([from_authority_finding(f) for f in <findings>], PROFILE_AUTHORITY)`.

### Method
- The profile reproduces key order and the three-field sort, so the string is identical, including for the single `MODEL_INVALID` finding.

### Details
- Do not touch the text loop, the stderr summary, or the return values.
- The `Finding` import stays (the error path still builds one).

## Compatibility considerations
- Exit codes, stdout, stderr, JSON keys, and `--help` text are unchanged; the CI by-path invocation keeps working through the existing bootstrap.

## Security considerations
- N/A: output formatting only.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/tools/test_tool_report_output.py tests/tools/test_adr_authority.py -q`, then `uv run pytest tests/tools -q`.
- Before and after on live data: `uv run python tools/check_adr_authority.py` and `... --format json` (exit code, stdout, stderr, and `--help` identical); also a run with `--model` pointing at an invalid file to cover the `MODEL_INVALID` path.
- `routing.md` "Adding a new tool" steps 1-3, then `uv run python tools/run_validation_gates.py`.

## Completion criteria
- No local `render_json` remains; golden tests, existing tests, and the live-data comparison (including the invalid-model path) are identical before and after.

## Out of Scope
- Model rules, text layout, the other three tools.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Capture the before-run (text, JSON, invalid-model JSON, help) on live data, then apply Implementation > Procedure | Completed | 20261106-113908 | 20261106-113908 | Changed: tools/check_adr_authority.py (shared render_json over Finding via from_authority_finding; text loop kept) |
| 2 | Run the golden and existing tests per Validation plan | Completed | 20261106-113908 | 20261106-113908 | golden and existing tests pass |
| 3 | Run the validation sequence (`rules/toolchain.md`) and the after-run comparison | Completed | 20261106-113908 | 20261106-113908 | ruff, mypy, bandit clean; live text, JSON, help identical; MODEL_INVALID JSON checked |
| 4 | N/A: documentation is the `tools/TOOL_DESCRIPTIONS.md` procedure of this Plan | Completed | 20261106-113908 | 20261106-113908 | N/A: documentation is another procedure of this Plan |

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
- **Requirement ID**: `REQ-005` (use the shared renderers), `REQ-006` (batch 2 comparison)
- **Source issue**: issues/20261104-152906_toolreport001_share-report-model-and-renderers.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261105-110046_toolreport001_share-report-model-and-renderers.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261106-091630
- **Related target files**: `tools/check_adr_authority.py`
