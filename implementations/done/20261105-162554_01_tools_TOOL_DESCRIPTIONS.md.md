## Goal
- Audit the exit codes of every `tools/*.py` module and record the CLI and exit-code convention (`0` pass, `1` findings, `2` usage or environment error) with a deviation list in `tools/TOOL_DESCRIPTIONS.md` (`REQ-001`: audit with reasons and callers reviewed; `REQ-002`: documented convention; `REQ-006`: no exit-code change without a caller review).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: one new section in `tools/TOOL_DESCRIPTIONS.md` (the convention, the option names that already exist, and the deviation list). The audit itself is read-only and its result is the deviation list.
- Plan: `plans/done/20261105-105637_toolcli001_define-cli-and-exit-code-convention.md`, Plan steps 1 and 2 (Phases 1 and 2).

## Assumptions
- Verified 2026-11-05: 11 explicit `return 2` sites exist in four tools (`check_ci_results.py` 6, `manage_workitem_stage.py` 2, `mark_procedure_new_symbols.py` 2, `classify_changes.py` 1); argparse-based tools already exit `2` on a usage error.
- Verified 2026-11-05: four of the five tools that get an `argparse` entry later (`check_docs_japanese.py`, `check_dependency_graph_cycles.py`, `check_needs_confirmation_inventory.py`, `check_tool_descriptions_sync.py`) return `1` when their input file or directory is missing, which the convention would call `2`. They are recorded as deviations, not changed (`REQ-006`).
- `check_needs_confirmation_inventory.py` documents that warnings do not produce a non-zero exit and only ERROR findings do; that is a deliberate detection-mode design and is recorded as such.
- `run_validation_gates.py` `classify` maps exit `0` to `Pass` and any other code to `Fail`, and every pre-commit hook and CI step treats any non-zero code alike (`.pre-commit-config.yaml`, `.github/workflows/*.yml`), so no caller distinguishes `1` from `2` (verified 2026-11-05).
- Ordering: the `toolsdocsync001` procedure (the Index heading edit in this same file) is generated but not yet executed; `code-implementation` runs it before this document. This procedure edits only the new section, so the two edits do not overlap. Plan overlap: `tools/TOOL_DESCRIPTIONS.md` is also targeted by the `toolcommon001`, `toolreport001`, `toolwrite001`, and `toolsizegate001` Plans, which edit other rows or sections and depend on this Plan; a sequencing dependency, not a conflict.

## Design decisions
- Place the section `## CLI and Exit-Code Convention` after the naming-convention bullets and before `## Index`, so the Index table stays untouched.
- Record only option names that already exist (`--check`, `--json`, `--format`, `--dry-run`); renaming or unifying options belongs to the `toolreport001` Plan.
- Mention only existing tool files in backticks: `check_tool_descriptions_sync.py` treats every backticked `*.py` name as a documented tool and reports an unknown one as stale.

## Alternatives considered
N/A: the Plan fixes where the convention is written.

## Implementation
### Target file
`tools/TOOL_DESCRIPTIONS.md`

### Procedure
1. Audit: list every `tools/*.py` module that has an entry point (`rg -n "return 2|SystemExit|sys\.exit" tools/*.py` and a read of each `main`); classify it as compliant or deviating, and for each deviation read its callers in `.pre-commit-config.yaml`, `.github/workflows/*.yml`, `tools/run_validation_gates.py`, `tox.ini`, and `skills/` before writing it down.
2. Add the section `## CLI and Exit-Code Convention` with: the three exit codes; the rule that `main(argv: list[str] | None = None) -> int` is the entry point and the `__main__` block calls `sys.exit(main(...))`; the existing common option names; and a deviation table with the columns Tool, Observed behavior, Reason, Callers reviewed.
3. Run `uv run python tools/check_tool_descriptions_sync.py`.

### Method
- Seed the deviation table with the audited findings: the four missing-input `return 1` cases above, the `check_needs_confirmation_inventory.py` warning behavior, and any further deviation the audit finds. A deviation outside the Plan's target rows is only recorded; a code change for it needs `tools/amend_plan.py` and approval (Plan UNK-02).
- State for each deviation which callers were reviewed and that they treat every non-zero code as failure.
- Keep each cell to one line; do not copy the convention into any `docs/*.md` file.

### Details
- Do not edit the Index heading or any Index row (the `toolsdocsync001` procedure owns the heading; the other Plans own their rows).
- Do not mention a file name in backticks unless it exists under `tools/`.

## Compatibility considerations
N/A: documentation only; the sync checker reads backticked file names, and the new section adds only existing names.

## Security considerations
N/A: documentation.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_tool_descriptions_sync.py` reports `No issues found.`
- `uv run pytest tests/tools/test_check_tool_descriptions_sync.py -q` passes.
- Every deviation row names the callers reviewed (manual check).

## Completion criteria
- The convention and the deviation list are in the document, every executable tool is compliant or listed with a reason, and the sync checker passes.
- No tool, test, or other file changed in this cycle.

## Out of Scope
- Changing any tool's exit code or option name, the Index section, and copying the convention into `docs/*.md`.

## Adversarial Verification (20261106)
- Applied `rules/ai-execution.md` Adversarial Verification (Base) to this procedure's factual claims. Claims treated as unverified; searched for refuting evidence in `tools/`, `tools/_docs_consistency_lib.py`, and `tools/run_validation_gates.py`.
- Claim 1 (`Assumptions`: 11 explicit `return 2` sites across `check_ci_results.py` 6, `manage_workitem_stage.py` 2, `mark_procedure_new_symbols.py` 2, `classify_changes.py` 1): CONFIRMED. `grep -c "return 2"` matches exactly; these are the only four tools with `return 2`.
- Claim 2 (`Assumptions`: `check_docs_japanese.py`, `check_dependency_graph_cycles.py`, `check_needs_confirmation_inventory.py`, `check_tool_descriptions_sync.py` return `1` on missing input/file): CONFIRMED. Each `main()` returns `1` when its docs/inventory target is absent (verified source lines); convention would call this `2`, recorded as deviation under `REQ-006`.
- Claim 3 (`Assumptions`: `check_needs_confirmation_inventory.py` warnings do not produce non-zero exit, only ERROR findings do): CONFIRMED. `report_and_exit()` (`tools/_docs_consistency_lib.py`) returns `1` only when `severity == "ERROR"`, else `0` even with warnings.
- Claim 4 (`Assumptions`: `run_validation_gates.py classify` maps exit `0` to `Pass`, any other code to `Fail`): CONFIRMED. `classify()` returns `"Pass"` for returncode `0`, `"Fail"` otherwise.
- Deliverable state: the `## CLI and Exit-Code Convention` section is NOT yet present in `tools/TOOL_DESCRIPTIONS.md`; implementation steps remain `Pending` (not executed under this verify-only task). No claim is stale or inaccurate; no correction required.
- Gate: `uv run python tools/check_tool_descriptions_sync.py` -> `No issues found.` (exit 0).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Audit exit codes and callers; collect the deviations | Pending | — | — | |
| 2 | Write the convention section and the deviation list | Pending | — | — | |
| 3 | Run the sync checker and its tests (`routing.md` "When to run which tool") | Pending | — | — | |

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
- **Requirement ID**: `REQ-001` (audit with reasons), `REQ-002` (documented convention), `REQ-006` (callers reviewed before any exit-code change)
- **Source issue**: issues/20261104-152002_toolcli001_define-cli-and-exit-code-convention.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/done/20261105-105637_toolcli001_define-cli-and-exit-code-convention.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261105-162554
- **Related target files**: `tools/TOOL_DESCRIPTIONS.md`
