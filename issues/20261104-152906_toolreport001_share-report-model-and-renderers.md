# Share the finding model and renderers across check tools

## Priority
Medium

## Summary
Replace the copy-pasted finding types and `render_json`/`render_text`/`render_csv` functions in `tools/` with one shared reporting layer and a uniform `--format` option.

## Background
Confirmed by repository evidence on 2026-11-04:

- `def render_json(` is defined in 14 files (for example `check_adr_authority.py`, `check_adr_reference.py`, `check_adr_invariant_matrix.py`, `check_workitem_traceability.py`), `render_text` in 7, `render_csv` in 5, `collect_issues` in 7, `make_finding` in 4 (`check_conftest_integrity.py`, `check_mock_patch_targets.py`, `check_plan_target_overlaps.py`, `check_workitem_traceability.py`), and `build_arg_parser` in 9.
- The finding types differ: `tools/_docs_consistency_lib.py` defines a frozen `Issue` dataclass (`file`, `line_no`, `severity`, `message`); other tools define their own finding dataclass (for example `code`, `location`, `message` in `check_adr_authority.py`).
- The JSON payloads therefore differ in key set and sort order between tools: `check_adr_reference.py` emits `file`/`line_no`/`severity`/`message` sorted by file and line, while `check_adr_authority.py` emits `code`/`location`/`message` sorted by code, location, and message. Only 4 tools accept a `--json` flag.

## Problem
Each tool re-implements output formatting, so a formatting fix must be repeated in many files, output contracts diverge, and consumers (hooks, CI, `run_validation_gates.py`, skills) cannot parse results uniformly.

## Reason for Change
Maintenance and consistency risk; no failure is known. Not time-sensitive.

## Implementation Intent
Introduce one shared reporting module (a common finding record that can carry both the `file/line_no/severity` and `code/location` styles, plus text, JSON, and CSV renderers with deterministic ordering) and a common `--format {text,json,csv}` helper. Migrate tools in small batches, preserving each tool's existing default output until its consumers are known.

## Target Files or Areas
- New shared module under `tools/` (name: to be decided; private, `_`-prefixed)
- The 14 files that define `render_json`, plus the files defining `render_text`, `render_csv`, `make_finding`, `collect_issues`
- `tools/_docs_consistency_lib.py` (existing `Issue`)
- `tools/TOOL_DESCRIPTIONS.md`, `tests/tools/`

## Required Changes
- Audit the existing output formats and record which consumers read them (pre-commit, CI workflows, `run_validation_gates.py`, skills).
- Define the shared finding record and renderers with a stable, documented JSON schema and a deterministic sort order.
- Add a shared `--format` option helper and migrate tools in batches, keeping each tool's current default output and exit codes.
- Remove the local copies from migrated tools and add the new module to `TOOL_DESCRIPTIONS.md`.

## Constraints
- Do not change what any tool checks or its exit codes.
- Text output that existing hooks or tests assert on must remain identical unless the consumer is updated in the same batch.
- A change in JSON keys is a contract change and must be listed per tool.
- Do not migrate everything in one change.

## Acceptance Criteria
- One implementation of each renderer exists with unit tests; migrated tools contain no local copy.
- Every migrated tool produces the same exit code and, for its default format, the same text output as before.
- The JSON schema is documented once, and JSON output of every migrated tool is deterministic (identical on repeated runs).
- `uv run pytest tests/tools -q` and the validation gates pass after each batch.

## Testing Expectations
- Unit tests for the shared module (ordering, empty input, unicode, each format); per-tool regression tests that compare pre- and post-migration output on fixed fixtures; a determinism test.
- Run `uv run pytest tests/tools -q`, ruff, and mypy per `rules/toolchain.md`.

## Documentation Impact
Update `tools/TOOL_DESCRIPTIONS.md` with the shared module, the `--format` convention, and the JSON schema (intent and operational notes only).

## Out of Scope
- Bootstrap, repo-root, and git helpers (`issues/20261104-152002_toolcommon001_shared-helper-for-tools.md`).
- Exit-code conventions (`issues/20261104-152002_toolcli001_define-cli-and-exit-code-convention.md`).
- Changing any check's logic or severity model.

## Dependencies
- Depends on `issues/20261104-152002_toolmypy001_add-tools-to-mypy-scope.md` (land first so the shared module is type-checked).
- Coordinate with `issues/20261104-152002_toolcommon001_shared-helper-for-tools.md` and `issues/20261104-152002_toolcli001_define-cli-and-exit-code-convention.md`, which touch the same files.

## Unresolved Questions
- External readers of the current JSON or CSV output (CI, hooks, skills): unknown; an audit is the first step.
- Whether one finding record can model both severity styles without losing information: unknown.

## AI Implementation Instruction
Start with the consumer audit and the shared module with tests; migrate a few tools per change and keep default output byte-identical.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261104-152906
- **Related target files**: `tools/_docs_consistency_lib.py`, `tools/check_adr_authority.py`, `tools/check_adr_reference.py`, `tools/check_adr_invariant_matrix.py`, `tools/check_workitem_traceability.py`, `tools/TOOL_DESCRIPTIONS.md`
