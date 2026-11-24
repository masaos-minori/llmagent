# Teach the work item structure checker the unknowns and risks companion kinds

## Priority
High

## Summary
`tools/check_workitem_structure.py` recognizes only the `issue`, `plan`, and `implementation` kinds,
so it validates `issues/{timestamp}[_NN]_unknowns.md` companion documents against
`templates/issue.md` and reports 31 false `missing required section` findings. The
`workitem-structure` pre-commit hook therefore fails, and the CI lint step that runs
`pre-commit run --all-files` cannot pass. Teach the checker the companion kinds (or scope them out
deliberately) so the gate judges companion documents against the template they were generated from.

## Background
- The companion documents are a distinct work-item kind with their own canonical templates:
  `templates/unknowns-issue.md` requires `## Summary`, `## Evidence Missing`, `## Resolution Path`,
  `## Blocking Impact`, `## Related`, `## Traceability`; `templates/risks-issue.md` requires
  `## Priority`, `## Context`, `## Risk`, `## Suggested resolution`, `## Traceability`.
- `tools/generate_workitem.py` writes them from those templates (`--kind unknowns`,
  `--kind risks --seq 01`; template constants at `tools/generate_workitem.py:94-95`).
- `tools/check_metadata_field_policy.py:67-72` already lists `risks-issue.md` and
  `unknowns-issue.md` as their own field-policy profiles, so the companion kind is a known concept
  elsewhere in the tooling.
- `skills/issue-creator/SKILL.md` (Issue Filename Generation) explicitly excludes those companion
  files from the Issue naming convention.
- `tools/check_workitem_structure.py` defines only three kinds in `_WORK_ITEM_KINDS`
  (`tools/check_workitem_structure.py:119-124`: issue / plan / implementation) and `infer_kind()`
  maps a document to a kind from its top-level directory, so a companion document under `issues/`
  is judged as kind `issue`.
- `rules/tool-gates.md:31` describes the structure gate in terms of the same three canonical
  templates, so the companion kind is undocumented in the gate table as well.

## Problem
Measured on 2026-11-24 at commit `f16ffc975`:
- `uv run python tools/check_workitem_structure.py` (discover mode) → `45 finding(s) total`, exit 1.
  - 31 findings are `missing required section` on the two live companion documents:
    `issues/20261123-120131_unknowns.md` (15 findings) and
    `issues/20261123-120131_02_unknowns.md` (16 findings). Each is asked for the 15 `## ` sections of
    `templates/issue.md` (`## Priority`, `## Summary`, `## Background`, `## Problem`,
    `## Reason for Change`, `## Implementation Intent`, `## Target Files or Areas`,
    `## Required Changes`, `## Constraints`, `## Acceptance Criteria`, `## Testing Expectations`,
    `## Documentation Impact`, `## Out of Scope`, `## Dependencies`, `## Unresolved Questions`,
    `## AI Implementation Instruction`, `## Traceability`).
  - The remaining 14 findings are `procedure-length` advisories on the
    `implementations/20261124-122732_*` documents (a documentation-only procedure over the 60-line
    limit). They do not change the exit code: `--file` on one of them exits 0.
- `issues/20261123-120131_unknowns.md` in fact carries exactly the `templates/unknowns-issue.md`
  heading set, so every finding on it is a false positive.
- `uv run pre-commit run workitem-structure --all-files` → `Failed` on the same two documents. The
  hook (`tools/check_workitem_structure.py --file`, `.pre-commit-config.yaml:126-130`) matches
  `^(issues|plans|implementations)/[^/]+\.md$`, so a commit that touches a companion document is
  blocked by findings that the companion template never requires. CI runs
  `uv run pre-commit run --all-files` as the lint job's `Pre-commit` step
  (`.github/workflows/ci.yml:54-55`), so the lint job fails the same way. The GitHub Actions run
  status is not observed from this environment (no `gh` authentication); the failure is confirmed by
  local reproduction of the command CI runs.
- 32 companion documents are already archived under `issues/done/` and 2 are live under `issues/`, so
  the gap affects every future companion document, not only these two.
- `uv run python tools/check_workitem_structure.py --archived-status` reports `No findings.`: the
  archived-status pass is not affected, which confirms the finding is specific to kind selection in
  the live-document pass.

## Reason for Change
A gate that cannot pass green makes the CI lint job permanently red and teaches contributors to
ignore its output. It also wastes every future companion document: the pipeline keeps generating
documents the gate cannot judge correctly, so a genuinely malformed companion document would be
indistinguishable from these 31 false positives.

## Implementation Intent
Make kind selection recognize companion documents, using the precedent already set by
`tools/generate_workitem.py` and `tools/check_metadata_field_policy.py`:
- Prefer adding companion kinds to the checker so a `{timestamp}_unknowns.md` /
  `{timestamp}[_NN]_risks.md` path is checked against its own template (`infer_kind()` would need to
  read the filename suffix before falling back to the directory).
- Alternative shapes, if the maintainer prefers them: narrow the hook's `files:` regex so companion
  documents are out of the changed-file gate, or grandfather the two live documents in a baseline
  file like `tools/check_archived_status_baseline.txt` / `tools/check_status_value_baseline.txt`.
- Decide and record what a companion document with a non-template shape must look like:
  `issues/20261123-120131_02_unknowns.md` is structured as a decision record (`## D-1` ... `## D-9`,
  `## Corrections the decisions above depend on`, `## Related`, `## Traceability`) and matches
  neither companion template, so it needs either a documented companion shape or a migration.
Keep the fix inside the checker and its tests; do not rewrite the companion documents as part of the
gate fix.

## Target Files or Areas
- `tools/check_workitem_structure.py`
- `tests/tools/test_check_workitem_structure.py`
- `.pre-commit-config.yaml` (only if the hook-scope shape is chosen)
- `rules/tool-gates.md` (the gate row that names the canonical templates)
- `issues/20261123-120131_unknowns.md`, `issues/20261123-120131_02_unknowns.md` (read-only reference
  for the shapes involved; migration only if the maintainer chooses that shape)

## Required Changes
- Reproduce and record the current state: `uv run python tools/check_workitem_structure.py` (45
  findings, exit 1) and `uv run pre-commit run workitem-structure --all-files` (`Failed`).
- Add companion-kind detection to `tools/check_workitem_structure.py`: a `{timestamp}_unknowns.md`
  or `{timestamp}[_NN]_risks.md` path must resolve to a spec whose required headings come from
  `templates/unknowns-issue.md` or `templates/risks-issue.md`.
- Keep the existing kind-inference behavior for ordinary Issue, Plan, and procedure documents.
- Extend `tests/tools/test_check_workitem_structure.py`, which currently has no companion-document
  case: at least one passing companion document per template, and one companion document that is
  genuinely malformed (a required companion section removed) so the gate still reports it.
- If the hook-scope or baseline shape is chosen instead, record the decision in
  `rules/tool-gates.md` so the gate table and `.pre-commit-config.yaml` stay in parity, and re-run
  `uv run python tools/run_validation_gates.py drift`.
- Confirm the 14 `procedure-length` advisories are still reported as advisories (exit code unchanged)
  and are not hidden by the change.

## Constraints
- The gate MUST keep reporting a companion document that is missing a section its own template
  requires; making the findings disappear by skipping companion documents entirely is not acceptable.
- The `--file`, `--archived-status`, `--kind`, and `--include-done` invocation forms must keep
  working for the three existing kinds; `tools/run_validation_gates.py` and the pre-commit hooks call
  them per `rules/tool-gates.md`.
- `tools/run_validation_gates.py drift` must stay green: gate table and hook parity is a checked
  invariant of this repository.
- Existing baselines (`tools/check_archived_status_baseline.txt`,
  `tools/check_status_value_baseline.txt`) must not be widened as a side effect.
- Do not edit the content of the archived companion documents (32 files under `issues/done/`).

## Acceptance Criteria
- `uv run python tools/check_workitem_structure.py` exits 0, or reports only findings that a maintainer
  has accepted as real (no `missing required section` finding that the document's own template does
  not require).
- `uv run pre-commit run workitem-structure --all-files` passes.
- `uv run pre-commit run --all-files` passes (the CI lint step's command) — this issue's own scope is
  the `workitem-structure` hook; any remaining hook failure must be reported, not hidden.
- `uv run pytest tests/tools/test_check_workitem_structure.py -q` passes, including the new companion
  cases, and the malformed-companion case proves the gate still fires.
- `uv run python tools/run_validation_gates.py drift` reports the gate table and hooks in parity.

## Testing Expectations
- Unit tests in `tests/tools/test_check_workitem_structure.py`: companion document against each of the
  two companion templates (pass), missing companion section (fail), and no regression for
  Issue/Plan/procedure kind inference.
- Regression check on the two live companion documents: the false-positive count must drop to 0.
- Gate verification: `uv run pre-commit run --all-files` and `uv run python tools/run_validation_gates.py drift`.
- No production code or coverage gate impact is expected (checker-only change); confirm with the
  standard whole-suite run per `rules/toolchain.md`.

## Documentation Impact
Documentation must record the gate's real scope:
- `rules/tool-gates.md`: the structure-gate row must name the companion templates (or state that
  companion documents are outside the changed-file gate), so the table matches the checker.
- `tools/TOOL_DESCRIPTIONS.md`: the `check_workitem_structure.py` row must describe the kinds it now
  recognizes.
- If a decision-record companion shape is adopted, `templates/unknowns-issue.md` (or the governance
  document that owns companion documents) must state that shape; if the existing
  `issues/20261123-120131_02_unknowns.md` is migrated instead, record the migration in that document's
  own `## Related` section.

## Out of Scope
- The 14 `procedure-length` advisories on the `implementations/20261124-122732_*` documents; they are
  upstream `cliplc003` batch output and are advisory, not gate failures.
- The 6 failing `tests/tools/test_append_plan_work_items.py` tests
  (`issues/20261124-155017_qa001_append-plan-attr-mismatch.md`).
- The 42 `stale-target-heuristic` findings reported by
  `uv run python -m tools.check_workitem_traceability --active-only`, which exit 0 and are advisory.
- Rewriting the substance of the two live companion documents, and any change to
  `skills/issue-to-plan` companion-document generation.

## Dependencies
- Depends on: nothing blocking. The fix is independent of `issues/20261124-155017_qa001_append-plan-attr-mismatch.md`,
  though both must land for CI to be green.
- Related context: `docs/00_governance/governance_03_issue-and-uncertainty-management.md` owns the
  Unknown/Risk follow-up workflow that produces companion documents.

## Unresolved Questions
- `不明`: which companion shape is canonical for a multi-decision unknowns document.
  `issues/20261123-120131_unknowns.md` follows `templates/unknowns-issue.md`;
  `issues/20261123-120131_02_unknowns.md` follows a per-decision structure that no template defines.
- `不明`: whether the maintainer wants companion documents inside the commit-time gate at all, or
  reviewed only through the archived-status pass. The three candidate shapes (checker kind detection,
  hook-scope narrowing, baseline grandfathering) differ in that respect.
- Assumption to confirm: `skills/issue-to-plan` Step 6 remains the only producer of companion
  documents; no other workflow writes `issues/{timestamp}_*_unknowns.md` paths.

## AI Implementation Instruction
Fix kind selection inside `tools/check_workitem_structure.py` and cover it with tests before touching
any document. Do not delete or restructure the companion documents to satisfy the wrong template, do
not add a new suppression list, and do not change the hook regex without also updating
`rules/tool-gates.md` and re-running the drift check. Keep changes confined to the checker, its tests,
and the documentation rows named above.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261124-155017
- **Related target files**: `tools/check_workitem_structure.py`, `tests/tools/test_check_workitem_structure.py`, `.pre-commit-config.yaml`, `rules/tool-gates.md`, `issues/20261123-120131_unknowns.md`, `issues/20261123-120131_02_unknowns.md`
