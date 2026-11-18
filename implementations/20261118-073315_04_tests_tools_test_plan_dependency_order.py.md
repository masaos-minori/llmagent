# Procedure: tests/tools/test_plan_dependency_order.py - pin the prose fallback in --plan mode

## Goal

Add regression tests that pin the prose-fallback contract end to end: an open prose path gates with
the `gated (prose)` label and a `prose-dependency` warning, a by-title/id prose line does not gate,
and `--json` exposes the undeclared `all` gate. No production code changes in this cycle.

## Scope
**Release unit**: N/A: not part of a release unit

- Add a `--plan`-mode test for an open prose dependency (`gated (prose)` + warning). (REQ-004)
- Add a by-title/id prose test that reports the Plan `ready`. (REQ-004)
- Extend coverage so the machine-readable `all` gate (`--json`) is pinned. (REQ-004)

## Assumptions

- `tools/plan_dependency_order.py` is unchanged (REQ-005); these tests pass against the current tool
  and serve as characterization coverage for the documented contract. (Verified 20261118.)
- Parser-level fallback is already tested (`test_prose_fallback_reads_paths_with_warning` at line 108,
  `test_prose_fallback_reads_continuation_lines`, `test_structured_line_wins_over_prose`); the gap is
  the end-to-end `--plan`/`--json` consequence, which no existing test pins. (Verified 20261118.)

## Design decisions

- Reuse the module's existing helpers and constants (`_plan`, `_plan_text`, `_depends`,
  `PLAN_A`..`PLAN_D`, `capsys`) and the existing class layout; no new fixture helpers.
- Name the tests after the contract, not the implementation: `test_plan_mode_prose_dependency_gates` (new)
  (open prose path under `plans/` -> `gated (prose)` line and `prose-dependency` warning in
  capsys output), `test_prose_by_title_does_not_gate` (new) (prose names the sibling Plan by title/id only
  -> `ready`), `test_json_mode_exposes_undeclared_all_gate` (new) (gate with `phase == "all"` and
  `declared == false`).
- Keep the archived-prerequisite case inside the first test (`plans/done/...` path resolves by
  existence and the plan reports `ready`), documenting why the guidance forbids prose paths: an
  archived-but-unexecuted prerequisite reads `ready` (Plan Revalidation note).

## Alternatives considered

- Parser-level additions only. Rejected: the parser behavior is already pinned; the failure mode this
  plan targets is how the fallback surfaces in the report an agent reads.
- Modifying `test_plan_option_limits_the_report` to also assert the warning. Rejected: that test pins
  `--plan` single-entry output shape; mixing contracts weakens both.

## Implementation

### Target file

`tests/tools/test_plan_dependency_order.py` (exists)

### Procedure

1. Re-read the current test module (helpers at lines 23-73, `test_plan_option_limits_the_report` at
   line 343) to match its style and constants.
2. Add the three tests described in Design decisions, written against the current tool behavior (no
   production change).
3. Run the module and confirm green before and after the sibling guidance edits land (the report must
   stay identical — plan Validation row "identical report before and after the guidance edits").

### Method

Test-only additions inside the existing test classes; no changes to any `tools/` production file.

### Details

- Expected report fragments (current behavior): `gated (prose)` in the `--plan` line, and a warning
  line containing `prose-dependency: <path>`; `--json` gate entries carry `path`, `phase`, `declared`.

## Compatibility considerations

- Tests only; no production or documentation file is touched here. Sibling procedure documents carry
  the guidance edits.

## Security considerations

- None; test additions.

## Rollback considerations

- Delete the added test functions to revert; no shared helper changes.

## Validation plan

- `uv run pytest tests/tools/test_plan_dependency_order.py -v` passes.
- `uv run ruff format tests/tools` and `uv run ruff check tests/tools` clean;
  `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools` clean (plan Validation rows).
- Review: AC-4 — the three contracts are pinned and pass against the unchanged tool.

## Completion criteria

- AC-4: the new tests exist, pass, and pin `gated (prose)` + warning, by-title `ready`, and the JSON
  `all` gate.

## Out of Scope

- `tools/plan_dependency_order.py` (unchanged, REQ-005).
- The existing parser-level fallback tests (unchanged).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: REQ-004
- **Source issue**: issues/20261117-132205_wftoolfu005_plan-prose-dependency-gating.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261117-134609_wftoolfu005_plan-prose-dependency-gating.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-073315
- **Related target files**: `tests/tools/test_plan_dependency_order.py`
