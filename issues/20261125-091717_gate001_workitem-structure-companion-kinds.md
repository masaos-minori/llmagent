# Teach the work item structure checker the unknowns and risks companion kinds

## Priority
High

## Summary
`tools/check_workitem_structure.py` knows only the `issue`, `plan`, and `implementation` kinds, so it
checks the Unknown/Risk companion documents under `issues/` against `templates/issue.md` and reports
false `missing required section` findings. The `workitem-structure` pre-commit hook therefore fails.
Make the checker judge a companion document against the template it was generated from, and decide what
shape a multi-decision unknowns document must have.

## Background
- Companion documents are a distinct work-item kind: `skills/issue-to-plan` Step 6 writes
  `issues/{timestamp}[_{NN}]_unknowns.md` / `_risks.md` through `tools/generate_workitem.py --kind
  unknowns|risks` from `templates/unknowns-issue.md` and `templates/risks-issue.md`.
  `skills/issue-creator/SKILL.md` (Issue Filename Generation) already excludes them from the Issue naming
  convention, and `tools/check_metadata_field_policy.py` already treats both templates as their own
  profiles. Only the structure checker lacks the concept.
- The checker defines three kinds in `_WORK_ITEM_KINDS` (`tools/check_workitem_structure.py:119-124`),
  `infer_kind()` (`:372-384`) maps a path to a kind by its top-level directory only, and the required
  headings are taken from the first fenced block of the template (`_extract_template_headings`), so a
  template's `## Field notes` outside the fence is not required.
- Required headings of the companion templates (measured): unknowns = `Summary`, `Evidence Missing`,
  `Resolution Path`, `Blocking Impact`, `Related`, `Traceability`; risks = `Priority`, `Context`, `Risk`,
  `Suggested resolution`, `Traceability`.
- `rules/tool-gates.md` (structure-gate row) names only the three canonical templates, so the gate table
  does not mention companion documents either.
- Supersedes the unverified parts of `issues/20261124-155017_qa002_workitem-structure-unknowns-kind.md`,
  whose measured counts were re-verified on 2026-11-25 at `321546be3`; the figures below are the
  re-verified ones.

## Problem
Measured on master at `321546be3`:
- `uv run python tools/check_workitem_structure.py` -> `41 finding(s) total`, exit 1.
  - 31 are `missing required section`: `issues/20261123-120131_unknowns.md` (15) and
    `issues/20261123-120131_02_unknowns.md` (16).
  - 10 are `procedure-length` advisories on `implementations/20261125-000005_*`; they are advisory and do
    not change the exit code.
- `issues/20261123-120131_unknowns.md` carries exactly the six `templates/unknowns-issue.md` headings, so
  all 15 of its findings are false positives.
- `issues/20261123-120131_02_unknowns.md` is a decision record (`## D-1` ... `## D-9`,
  `## Corrections the decisions above depend on`, `## Related`, `## Traceability`) and matches neither
  companion template. Fixing kind detection alone turns its 16 false findings into companion-template
  findings (e.g. missing `## Summary`, `## Evidence Missing`); a shape decision is needed.
- `uv run pre-commit run workitem-structure --all-files` -> `Failed` (hook files regex
  `^(issues|plans|implementations)/[^/]+\.md$`, `.pre-commit-config.yaml`). CI's lint job runs
  `pre-commit run --all-files` (`.github/workflows/ci.yml:55`); the CI run status is not observed from
  this environment (no `gh` authentication), only the local reproduction of the same command.
- 32 companion documents already sit in `issues/done/`, so every future companion document is affected.
- The two live files differ in name shape: `{timestamp}_unknowns.md` and `{timestamp}_02_unknowns.md`;
  kind detection must accept the optional `_NN` for both `unknowns` and `risks`.

## Reason for Change
A gate that cannot pass keeps the pre-commit hook and the CI lint job red and trains contributors to
ignore its output; a genuinely malformed companion document would be indistinguishable from the false
positives. The pipeline keeps generating companion documents, so the gap grows with each plan.

## Implementation Intent
- Prefer adding companion kinds to the checker: resolve the kind from the filename suffix
  (`_unknowns.md`, `_risks.md`, with optional `_NN`) before falling back to the directory, and take the
  required headings from the matching companion template. Keep the existing behavior for Issue, Plan, and
  procedure documents.
- Alternatives, only if the maintainer prefers them: narrow the hook's `files:` regex, or grandfather the
  two live documents in a baseline file. Either alternative must be recorded in `rules/tool-gates.md`.
- The decision-record shape of `20261123-120131_02_unknowns.md` must be decided and recorded (document it,
  migrate it, or grandfather it); this is the open question below, not something to guess.
- Keep the fix inside the checker, its tests, and the documentation rows named below; do not rewrite the
  companion documents as part of the gate fix.

## Target Files or Areas
- `tools/check_workitem_structure.py`
- `tests/tools/test_check_workitem_structure.py` (no companion case exists today)
- `.pre-commit-config.yaml` (only if the hook-scope shape is chosen)
- `rules/tool-gates.md` (structure-gate row), `tools/TOOL_DESCRIPTIONS.md` (`check_workitem_structure.py` row)
- `templates/unknowns-issue.md` (only if a decision-record shape is adopted)
- `issues/20261123-120131_unknowns.md`, `issues/20261123-120131_02_unknowns.md` (read-only reference)

## Required Changes
- Record the current state before changing anything: 41 findings / exit 1, and the hook `Failed`.
- Add companion-kind detection so a `{timestamp}[_NN]_unknowns.md` or `{timestamp}[_NN]_risks.md` path
  under `issues/` (and `issues/done/`) resolves to a spec built from its own template.
- Keep `infer_kind()` behavior for ordinary Issue, Plan, and procedure documents unchanged.
- Add tests: one passing companion document per template, one malformed companion document (a required
  companion section removed) that is still reported, and no-regression cases for the three existing kinds
  and the `--file`, `--kind`, `--include-done`, `--archived-status` forms.
- Resolve the decision-record shape question (see Unresolved Questions) and apply the chosen shape.
- Update the two documentation rows, and `templates/unknowns-issue.md` if a new shape is adopted.
- Confirm the `procedure-length` advisories are still reported and the exit code is unchanged by them.

## Constraints
- The gate MUST keep reporting a companion document that lacks a section its own template requires;
  skipping companion documents wholesale is not acceptable.
- The existing invocation forms must keep working for the three existing kinds; `tools/run_validation_gates.py`
  and the pre-commit hooks call them.
- `uv run python -m tools.run_validation_gates drift` must stay green (gate table and hook parity).
- Existing baselines (`tools/check_archived_status_baseline.txt`, `tools/check_status_value_baseline.txt`)
  must not be widened as a side effect.
- Do not edit the 32 archived companion documents under `issues/done/`.

## Acceptance Criteria
- `uv run python tools/check_workitem_structure.py` exits 0, or reports only findings a maintainer accepted
  as real; no `missing required section` finding that the document's own template does not require.
- `uv run pre-commit run workitem-structure --all-files` passes.
- `uv run pytest tests/tools/test_check_workitem_structure.py -q` passes, including the new companion cases;
  the malformed-companion case proves the gate still fires.
- `uv run python -m tools.run_validation_gates drift` reports parity.
- `uv run pre-commit run --all-files` is run and any remaining failure outside this issue's scope is
  reported, not hidden.

## Testing Expectations
- Unit tests in `tests/tools/test_check_workitem_structure.py` as listed in Required Changes.
- Regression check on the two live companion documents against the decided shape.
- Ruff, mypy, and bandit on the changed tool per `routing.md` "Adding a new tool" (items 1-3), the
  whole-suite run per `rules/toolchain.md`, and `uv run python tools/check_tool_descriptions_sync.py`.

## Documentation Impact
- `rules/tool-gates.md`: the structure-gate row must name the companion templates (or state that companion
  documents are outside the changed-file gate if that shape is chosen).
- `tools/TOOL_DESCRIPTIONS.md`: the `check_workitem_structure.py` row must describe the kinds it recognizes.
- If a decision-record shape is adopted, state it in `templates/unknowns-issue.md`; if the existing 02
  document is migrated instead, record that in its own `## Related` section.

## Out of Scope
- The `procedure-length` advisories on the `implementations/20261125-000005_*` documents.
- Rewriting the substance of the two live companion documents.
- Any change to `skills/issue-to-plan` companion-document generation.
- The 42 `stale-target-heuristic` findings of `tools/check_workitem_traceability` (advisory).

## Dependencies
- Supersedes `issues/20261124-155017_qa002_workitem-structure-unknowns-kind.md` (same problem and target
  files); that file should be archived or removed once this issue is accepted, so `issue-to-plan` does not
  take two issues for one problem.
- `docs/00_governance/governance_03_issue-and-uncertainty-management.md` owns the Unknown/Risk follow-up
  workflow (context only).
- No other open issue or plan overlaps the target files (checked: `rg -l check_workitem_structure issues plans`).

## Unresolved Questions
- `不明`: the canonical shape of a multi-decision unknowns document. `20261123-120131_unknowns.md` follows
  `templates/unknowns-issue.md`; `20261123-120131_02_unknowns.md` follows a per-decision structure that no
  template defines. Options: document the shape, migrate the 02 file, or grandfather it.
- `不明`: whether the maintainer wants companion documents in the commit-time gate at all (checker kind,
  hook-scope narrowing, or baseline grandfathering differ on this).
- Assumption to confirm: `skills/issue-to-plan` Step 6 is the only producer of
  `issues/{timestamp}[_NN]_unknowns.md` / `_risks.md` files.
- Not measured: the CI lint job status, and whether `pre-commit run --all-files` has other failing hooks.

## AI Implementation Instruction
Fix kind selection inside `tools/check_workitem_structure.py` and cover it with tests before touching any
document. Do not delete or restructure companion documents to satisfy the wrong template, do not add a
suppression list, and do not change the hook regex without updating `rules/tool-gates.md` and re-running
the drift check. Stop and ask the maintainer for the decision-record shape instead of choosing one. Keep
changes to the checker, its tests, and the documentation rows named above.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261125-091717
- **Related target files**: `tools/check_workitem_structure.py`, `tests/tools/test_check_workitem_structure.py`, `.pre-commit-config.yaml`, `rules/tool-gates.md`, `tools/TOOL_DESCRIPTIONS.md`, `templates/unknowns-issue.md`
