# Fix stale detector false positives

## Priority
Medium

## Summary
`tools/stale_detector.py` reports a procedure as stale when its prose contains a `from X import Y` phrase, and when it names a symbol that the procedure itself is about to create. Neither is a stale reference to existing source, but `code-implementation` Step 3 requires aborting on any mismatch, so each false positive blocks the cycle until a person approves an exception. Make the detector distinguish references to existing code from prose and from symbols the procedure introduces, without weakening detection of genuinely stale references.

## Background
- `skills/code-implementation/workflow.md` Step 3 runs `uv run python tools/stale_detector.py {proc_path}`; any reported mismatch aborts the procedure, and the workflow forbids correcting the procedure and continuing.
- While executing the nine mock001 procedures (`implementations/done/20261012-121424_01_*` to `_09_*`), 2 of 9 were reported stale by this tool although current source was unchanged since the Plan. The user had to approve an explicit exception ("fix the wording and continue") before work could proceed. The other 7 passed.
- The two reports, verbatim:
  - Procedure 01: `import_missing: Import 'from __future__ import annotations` style and type hints; no new CLI option.' not found in source`. The source text was the bullet "Keep `from __future__ import annotations` style and type hints; no new CLI option." under Details.
  - Procedure 02: `symbol_missing` for three backticked names of tests that the procedure instructs to add (`test_marker_with_reason_suppresses_the_finding` and two siblings).
- The workaround used was rewording the procedures (dropping the backticks and rewriting the sentence). That removes information the author wanted to convey and has to be repeated for every similar procedure.
- The detector already carries narrowing heuristics (a tool-vocabulary allowlist, a minimum symbol shape, a repository-wide presence check before reporting a symbol missing), so this is a further class of false positive, not a new design.

## Problem
Two distinct false-positive classes, both from treating every matching piece of text as a claim about existing source:
- Import references (`_IMPORT_RE` in `tools/stale_detector.py`) match any line that contains "from X import ..." followed by the end of the line or a comment. Prose that happens to contain that phrase is captured together with the rest of the sentence, then reported as an import that is "not found in source".
- Symbol references (`_check_symbol_refs`) check every backticked snake_case or CamelCase token against the repository. A procedure that adds a function, class, or test must name it, and by definition that name does not yet exist, so it is reported `symbol_missing`.
- Evidence (`Explicit in code`): `_IMPORT_RE` and `_check_symbol_refs` in `tools/stale_detector.py`; the detector has no notion of a symbol the procedure creates. Evidence (`Verified by run`): the two outputs quoted in Background, reproduced by `uv run python tools/stale_detector.py implementations/20261012-121424_01_tools_check_mock_patch_targets.py.md` and the `_02_` procedure before they were reworded.
- Consequence: every procedure that adds new code is at risk of an abort that has nothing to do with staleness, and the abort rule makes the recovery a human decision.

## Reason for Change
- Throughput and trust: a gate that raises false alarms on a routine kind of procedure (adding a test or function) is either bypassed or reworded around, which erodes its value for the real case it exists for (another change landing under the procedure).
- The two classes are mechanical and testable, so the fix is cheap relative to repeated manual exceptions.

## Implementation Intent
- Keep the rule that a genuinely missing referenced construct makes the procedure stale; only stop reporting things that are not references to existing code.
- For import references: recognize an import citation only where it is plausibly a code citation (a complete import statement in a code block or an inline code span that is itself the statement), not where the phrase appears inside a sentence.
- For new symbols: give procedure authors a way to state that a name will be created, and exempt those names from the existence check. The exact convention (for example a wording rule or a dedicated field) is a design choice to settle in planning; prefer one the generated procedures can follow without extra effort.
- Preserve the existing design decisions: regex/string matching rather than AST parsing, all failures reported in one pass.

## Target Files or Areas
- `tools/stale_detector.py`
- `tests/tools/test_stale_detector.py`
- `tools/TOOL_DESCRIPTIONS.md` (the `stale_detector.py` entry)
- If a new-symbol convention needs authoring guidance: `templates/implementation-procedure.md` and `skills/plan-to-implementation-procedure/workflow.md` (likely, not confirmed)
- If the Step 3 text needs to mention the convention: `skills/code-implementation/workflow.md` (likely, not confirmed)

## Required Changes
- Tighten import-reference detection so a prose sentence containing "from X import ..." is not reported, while a real import citation that is missing from source still is.
- Add a way for a procedure to declare symbols it will create, and skip the existence check for those names; a name that is not declared and is absent from the repository must still be reported.
- Add regression tests for both false-positive classes and for the unchanged true-positive cases.
- Update the tool's documentation entry and, if a convention is added, the procedure template guidance.

## Constraints
- Detection of real staleness must not weaken: out-of-range line references, a cited existing symbol that has been removed, and a missing "Before:" block must still be reported.
- Keep the detector regex-based and dependency-free; do not add AST parsing (an earlier design decision recorded in the tool's docstring).
- Procedures already archived under `implementations/done/` must not become a reason to change their content.

## Acceptance Criteria
- A procedure whose Details contain a sentence with "from X import ..." prose is not reported stale because of it.
- A procedure that names a symbol it declares as to-be-created is not reported stale for that symbol; the same name without the declaration, and absent from the repository, is still reported `symbol_missing`.
- The existing true-positive tests in `tests/tools/test_stale_detector.py` still pass unchanged, and a procedure citing a removed existing symbol, an out-of-range line number, or a missing "Before:" block is still reported stale.
- The two original procedures from the mock001 batch (their pre-reword text, reproduced as test fixtures) are reported clean.
- `uv run pytest tests/tools/test_stale_detector.py` passes and `uv run python tools/check_tool_descriptions_sync.py` reports no issues.

## Testing Expectations
- Unit tests for each false-positive class built from the exact text that triggered it, plus negative tests proving the true positives remain.
- Run `uv run ruff check tools tests/tools`, `uv run mypy tools/stale_detector.py`, and `uv run pytest tests/tools`.
- Run `uv run python tools/stale_detector.py` against a few current `implementations/` procedures to confirm the verdicts do not regress.

## Documentation Impact
- `tools/TOOL_DESCRIPTIONS.md` must describe the changed detection rules.
- If a new-symbol convention is added, the procedure authoring guidance (`templates/implementation-procedure.md` notes and, if needed, `skills/plan-to-implementation-procedure/workflow.md`) must state it; no `docs/*.md` change is expected.

## Out of Scope
- Changing the abort-on-any-mismatch policy or the rule against correcting a procedure and continuing.
- Making the detector verify behavior beyond the existence of cited constructs.
- Changing other false-positive heuristics that already pass.

## Dependencies
- Depends on no other issue. Sibling-issue check: the open files under `issues/` are the `start001` to `start005` startup review issues and five design memos; none concerns this tool.
- Related, already completed: the mock001 batch that exposed the problem (`plans/done/20261012-120856_plan.md`).

## Unresolved Questions
- Which convention should mark a to-be-created symbol (a wording rule such as "add"/"create" near the name, a dedicated bullet or field, or a marker next to the name) is open; it affects whether the procedure template must change.
- Whether any other false-positive class exists in procedures generated by earlier cycles is unknown; only the two seen in the mock001 batch are confirmed.
- Whether the import-reference class should also require the cited import to be inside a code span or fence is a design choice for planning.

## AI Implementation Instruction
- Change only the files under Target Files or Areas; do not edit archived procedures or unrelated tools.
- Keep every existing true-positive test passing without edits; add tests rather than relaxing them.
- Do not weaken the detector to hide the reported cases (for example by ignoring all backticked names); prove each exemption with a test and keep the negative case covered.
- Stop and report open questions instead of choosing a convention that requires changing the procedure template without noting it.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/done/20261012-120856_plan.md
- **Source implementation procedure**: implementations/done/20261012-121424_01_tools_check_mock_patch_targets.py.md
- **Generated at**: 20261012-132457
- **Related target files**: tools/stale_detector.py, tests/tools/test_stale_detector.py, tools/TOOL_DESCRIPTIONS.md, templates/implementation-procedure.md, skills/plan-to-implementation-procedure/workflow.md, skills/code-implementation/workflow.md
