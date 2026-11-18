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
  `test_prose_fallback_reads_continuation_lines` at line 124, `test_structured_line_wins_over_prose` at
  line 129); the gap is the end-to-end `--plan`/`--json` consequence, which no existing test pins.
  (Re-verified 20261118.)
- Fixture facts (re-verified 20261118 against `resolve_dependency` and `readiness`): an unresolvable prose
  path yields `ready` plus a `Needs confirmation` line, not a gate, so the gating test must name an
  existing open Plan; a `plans/done/` path is closed by existence only.

## Design decisions

- Reuse the module's existing helpers and constants (`_plan`, `_plan_text`, `_depends`,
  `PLAN_A`..`PLAN_D`, `capsys`) and the existing class layout; no new fixture helpers.
- Name the tests after the contract, not the implementation: `test_plan_mode_prose_dependency_gates` (new)
  (open prose path under `plans/` -> `gated (prose)` line, `blocked by <path> phase all`, and the
  `prose-dependency` warning in capsys output), `test_prose_by_title_does_not_gate` (new) (prose names the
  sibling Plan by title or id only -> `ready`, no warning), `test_json_mode_exposes_prose_gate_and_warning`
  (new) (the results entry has `label == "gated (prose)"` and a `blocking` entry `<path> phase all`, and
  the payload's `warnings` list carries `prose-dependency: <path>`; re-verified 20261118 against
  `render_json` — the earlier `phase`/`declared` gate-entry claim was wrong, those fields are not
  serialized).
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

- Expected report fragments (current behavior, re-verified 20261118 against `render_text` and
  `render_json`): `gated (prose)` in the `--plan` line with `blocked by <path> phase all`, and a warning
  line `prose-dependency: <path>`; `--json` results entries carry `plan`, `status`, `label`, `blocking`
  (`<path> phase all` strings) and `confirmations`, and the payload's `warnings` list carries the fallback
  warnings.

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
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | — |  |
| 2 | Add or update tests per Validation plan | Completed | — | — |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | — |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | — |  |

### Verification Findings
| ID | Finding | Action |
|----|---------|--------|
| V1 | `render_json` payload: results entries `plan`/`status`/`label`/`blocking`/`confirmations`, top-level `warnings`; no `path`/`phase`/`declared` gate fields | Third test renamed and re-specified in Design decisions/Details |
| V2 | Unresolvable prose paths yield `ready` + `Needs confirmation` (existing `test_json_output_parses` shows `PLAN_B: ready` for `plans/missing.md`); gating needs an existing open Plan | New fixture fact added to Assumptions |
| V3 | Helpers `_write`/`_plan_text`/`_plan`/`_depends`/`_readiness` and `PLAN_A`..`PLAN_D` confirmed; `test_plan_option_limits_the_report` at line 343; `TestMain._repo` is the fixture pattern to reuse | Reuse them; no new helpers |

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