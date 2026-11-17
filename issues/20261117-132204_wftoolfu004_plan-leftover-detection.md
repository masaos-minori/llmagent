# Design leftover detection for plans and implementation procedures

## Priority
Low

## Summary
The structure checker is being extended to report unfilled template lines of an issue, using a rule that does not transfer to plans or procedures. Choose a rule for those two kinds that reports an unfilled scaffold and never a filled document.

## Background
Filed as a follow-up of `plans/20261117-124139_wftool001_gate-workitem-structure.md` (its Unknowns table, UNK-01). That Plan limits leftover detection to issues because the issue rule (verbatim template lines that no filled issue keeps) does not hold for the other templates.

## Problem
Template lines were compared with filled documents (`Operationally observed`, measured with a script over the newest archived documents). Plan template: 81 candidate lines (not headings, not bullets); across 40 filled plans, 27 never survive, 17 survive in at least 90% of plans, and 37 survive in some plans only, because the Freeze paragraph and multi-line prose are partly rewritten. Procedure template: 13 candidate lines; across 60 filled procedures, 4 never survive (the default `Pending` rows), 8 survive in at least 90%, and 1 survives in some. A rule that matches only bracket-wrapped placeholder text finds 9 plan lines and no procedure line, and none of them survives in the five newest filled plans. The issue rule has 30 lines and a hit rate of zero in the open issues.

## Reason for Change
- An unfilled plan or procedure scaffold can be committed without a signal, and the plan and procedure workflows rely on the author to replace every placeholder.
- A naive extension of the issue rule would report every filled plan, because boilerplate such as the Freeze paragraph legitimately stays; the rule needs a decision before it is coded.
- Plans and procedures are generated far more often than issues, so the gap is exercised often. Nothing makes the change urgent.

## Implementation Intent
- A rule per kind reports an unfilled scaffold with zero reports on filled documents of the current corpus, and the rule's source of truth is stated (the templates, a recorded line list, or markers).
- The rule is built on the issue leftover infrastructure of the first Plan and reports through the same finding category.

## Target Files or Areas
- `tools/check_workitem_structure.py`
- `tests/tools/test_check_workitem_structure.py`
- `tools/TOOL_DESCRIPTIONS.md`
- templates/plan.md and templates/implementation-procedure.md (only if markers are chosen)

## Required Changes
- Decide the rule for plans and for procedures among the options in Unresolved Questions.
- Implement it, deriving its data from one source, and report it as a `template-leftover` finding.
- Add tests: an unfilled scaffold of each kind is reported, a filled document is not, and a document that rewrites the Freeze paragraph is not.
- Re-measure against the current corpus and record the number of false reports (the target is zero).

## Constraints
- A template change is allowed only if the markers option is chosen; otherwise the templates stay as they are.
- The rule MUST NOT report any document in the current active set or in the measured sample of filled documents.
- Follow `routing.md` Tools, section "Adding a new tool", for every changed `tools/*.py`: ruff format and check, mypy, bandit, a smoke run against real repository data, and `tools/TOOL_DESCRIPTIONS.md` sync (`tools/check_tool_descriptions_sync.py`).
- Respect the `tools/` module-size gate (`tools/check_module_size.py --scripts-dir tools --baseline tools/check_module_size_tools_baseline.txt`): the baseline only shrinks, so a tool at or over the limit MUST NOT grow; put new logic in a new module instead.
- Follow the tool CLI conventions recorded in `tools/TOOL_DESCRIPTIONS.md`: exit codes `0` pass, `1` findings, `2` usage or environment error; `--dry-run` and atomic writes for tools that rewrite files.
- Follow the Current-Specification-Only policy: no aliases, shims, or history-style comments for removed behavior.
- Keep code comments, log text, and documentation in English; change only the Target Files and report any other needed file as a scope amendment.

## Acceptance Criteria
- `generate_workitem.py` scaffolds of a plan and of a procedure are reported with their unfilled lines named (tests).
- The newest filled plans and procedures and every active work item produce no leftover finding (test or recorded measurement).
- `tools/check_tool_descriptions_sync.py` passes.

## Testing Expectations
Unit tests under `tests/tools/test_check_workitem_structure.py`; a corpus measurement script run once and its result recorded; ruff, mypy, bandit. Validation sequence: `rules/toolchain.md`; after any `docs/` edit also the checkers listed in `routing.md` Tools.

## Documentation Impact
Yes. The checker's description; the templates only if markers are chosen.

## Out of Scope
- Issue leftover detection (the first Plan).
- Content-quality judgment.
- Rewriting archived documents.

## Dependencies
- `plans/20261117-124139_wftool001_gate-workitem-structure.md` is a prerequisite: depends on its phase 1, which adds the leftover infrastructure and the multi-path form to `tools/check_workitem_structure.py`.

## Unresolved Questions
- Which option is chosen is `不明` and needs a maintainer decision: (A) a line list derived from the lines that never survive in a corpus (27 plan lines, 4 procedure lines in the sample), (B) bracket-wrapped placeholder text only (9 plan lines, none for procedures), or (C) explicit placeholder markers added to the templates.
- How to treat the lines that survive in some documents only (37 plan lines) is `不明`.

## AI Implementation Instruction
- Present the three options with the measured numbers and stop before implementing.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261117-132204
- **Related target files**: `tools/check_workitem_structure.py`; `tests/tools/test_check_workitem_structure.py`; `tools/TOOL_DESCRIPTIONS.md`; templates/plan.md and templates/implementation-procedure.md (only if markers are chosen)
