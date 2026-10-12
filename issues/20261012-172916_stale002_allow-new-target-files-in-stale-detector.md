# Allow new target files in stale detector

## Priority
Medium

## Summary
`tools/stale_detector.py` reports `source_missing` and stops when the procedure's target file does not exist, and the procedure has no way to say that the file is meant to be created. `rules/workflow-lifecycle.md` explicitly allows a Plan row for a file that does not exist yet ("New file"), so every procedure for such a row is reported stale and, per `skills/code-implementation/workflow.md` Step 3, aborts the cycle until a person approves an exception. Let a procedure declare a new target file with the existing `(new)` convention and make the detector handle it.

## Background
- `code-implementation` Step 3 runs `uv run python tools/stale_detector.py {proc_path}`; any mismatch aborts the procedure, and the workflow forbids correcting the procedure and continuing.
- `plans/done/20261012-132739_plan.md` (stale001) taught the detector a `(new)` marker for backticked symbols and import statements that a procedure creates. It did not cover the target file itself. That plan is implemented; its changes were still uncommitted when this issue was written.
- `rules/workflow-lifecycle.md` (Implementation Target Files Validation) accepts a target row for a file not yet created when its Reason for Modification states "New file" and its containing directory exists.
- Writing a backticked path followed by `(new)` is already the repository's practice for new files: 189 occurrences across `plans/done/` and `implementations/done/`.

## Problem
- Evidence (`Verified by run`): a minimal procedure whose "### Target file" names `tools/brand_new_tool.py`, which does not exist, makes `uv run python tools/stale_detector.py` print `Stale: 1 mismatch(es) detected.` and `source_missing: Source file does not exist: tools/brand_new_tool.py`, exit code 1.
- Evidence (`Explicit in code`): `StaleResult.from_procedure` returns `source_missing` as soon as the target path is absent and checks nothing else; there is no way for a procedure to opt out.
- Evidence (`Measured`): 161 of the 2581 plans in `plans/done/` contain a "New file" row (about 6%), so roughly one plan in sixteen produces a procedure that the detector cannot accept as written. The exact number of procedures is not known: the archived procedures can only be examined after implementation, when the new file already exists, so past aborts cannot be counted from the archive.
- Consequence: for those procedures the workflow's abort rule turns a correct, fully verified procedure into a stop that needs a human exception, and the usual workaround (rewording or removing the target) is not available because the target is the point of the procedure.

## Reason for Change
- The gate exists to catch a procedure whose premises changed under it; a file that is supposed to be created is not such a premise, so the abort is a false positive by construction for about 6% of plans.
- The fix reuses a convention authors already follow, so no new syntax is introduced.

## Implementation Intent
- Treat a target file written as a backticked path followed by `(new)` in the "### Target file" section as declared new. For a declared-new target: skip the existence check, run the symbol, import, and "Before:" checks against an empty target (cross-references to other files still resolve through the existing repository-wide presence check), skip line-number checks that cite the target, and verify that the containing directory exists.
- Without the marker, keep reporting `source_missing` exactly as today.
- Document the convention where authors and the workflow meet it, and consider whether the procedure generator should write the marker when the Plan row's reason says "New file" (see Unresolved Questions).

## Target Files or Areas
- `tools/stale_detector.py` (`from_procedure`, the target-file section pattern)
- `tests/tools/test_stale_detector.py`
- `templates/implementation-procedure.md` (Notes on filling sections; the Target file part)
- `skills/code-implementation/workflow.md` (Stale detection result handling)
- `tools/TOOL_DESCRIPTIONS.md` (the `stale_detector.py` entry)
- `tools/generate_workitem.py` — only if the generator is changed to write the marker (Unresolved Questions)

## Required Changes
- Recognize `(new)` after the target path in the "### Target file" section and handle a declared-new target as described under Implementation Intent.
- Keep `source_missing` for an unmarked absent target.
- Add tests for each of the cases in Acceptance Criteria.
- Update the template notes, the workflow's Step 3 text, and the tool description.

## Constraints
- Detection for existing targets must not weaken: line references, symbols, imports, and "Before:" blocks are still verified against the real file when the target exists.
- Keep the detector regex-based and dependency-free (the design decision recorded in the tool's docstring).
- Do not change the abort-on-any-mismatch policy or the rule against correcting a procedure and continuing.
- Stay consistent with `rules/workflow-lifecycle.md`, which already defines when a missing target is acceptable.

## Acceptance Criteria
- A procedure whose Target file section is a backticked path followed by `(new)`, naming an absent file in an existing directory, is reported clean when its other references are valid.
- The same procedure without `(new)` is still reported `source_missing`.
- A declared-new target whose containing directory does not exist is reported as a mismatch.
- A procedure that declares a target new but the file already exists is handled according to the decision recorded for the first Unresolved Question, and a test asserts it.
- Symbols cited by a declared-new procedure that exist elsewhere in the repository are not reported; names that exist nowhere and are not marked `(new)` are still reported `symbol_missing`.
- The existing detector tests pass unchanged; the template, the workflow text, and the tool description state the convention; `uv run python tools/check_tool_descriptions_sync.py` and `uv run python tools/check_skills_references.py` report no issues.

## Testing Expectations
- Unit and end-to-end tests in `tests/tools/test_stale_detector.py` using a temporary source tree and a temporary procedure document, one test per acceptance case.
- Run `uv run pytest tests/tools/test_stale_detector.py`, `uv run ruff check tools tests/tools`, `uv run mypy tools/stale_detector.py`.
- Re-run the detector over a sample of archived procedures before and after the change; the verdicts must be identical, because those procedures do not use the marker.

## Documentation Impact
- Yes: `templates/implementation-procedure.md` (how to declare a new target file), `skills/code-implementation/workflow.md` (what the detector does with it), and the `stale_detector.py` entry of `tools/TOOL_DESCRIPTIONS.md`. No `docs/*.md` change is expected.

## Out of Scope
- The false positives on symbol names that are not Python symbols (tracked separately in the sibling issue `stale003`).
- Changing the Plan freeze validation or `rules/workflow-lifecycle.md`.
- Making the detector read the Plan to infer that a row is new.

## Dependencies
- Depends on stale001 (`plans/done/20261012-132739_plan.md`) being committed: it shares `tools/stale_detector.py`, its test file, and the `(new)` convention.
- Sibling issue `stale003` (non-Python names reported as missing symbols) touches the same file and tests; the two are independent and can be done in either order, but the second one rebases onto the first.

## Unresolved Questions
- What should happen when a procedure marks its target `(new)` but the file already exists? Recommended: report it as a mismatch, because creating a file that already exists contradicts the procedure's premise (another change may have created it); the alternative is to accept it and check the file as usual.
- Should `tools/generate_workitem.py` write `(new)` automatically when the Plan row's Reason for Modification says "New file"? It would remove the burden from authors, but it adds a dependency on the Plan's wording; the generator currently does not read that field.
- How often the abort actually happened before is unknown (the archive only shows post-implementation state); only the plan-level frequency (about 6%) is measured.

## AI Implementation Instruction
- Change only the files listed under Target Files or Areas; do not edit archived procedures.
- Keep every existing detector test passing without edits; add tests rather than relaxing them.
- Do not weaken detection for existing targets to make the new case pass; prove each new case with a test and keep the negative case (unmarked absent target) covered.
- Stop and report open questions instead of choosing the "already exists" behavior or the generator change silently.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/done/20261012-132739_plan.md
- **Source implementation procedure**: implementations/done/20261012-170854_01_tools_stale_detector.py.md
- **Generated at**: 20261012-172916
- **Related target files**: tools/stale_detector.py, tests/tools/test_stale_detector.py, templates/implementation-procedure.md, skills/code-implementation/workflow.md, tools/TOOL_DESCRIPTIONS.md, tools/generate_workitem.py
