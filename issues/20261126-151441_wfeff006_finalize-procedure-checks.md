# Run the procedure acceptance checks in one command

## Priority
Medium

## Summary
After writing the procedures of a Plan, the author runs four checks per document and then fixes stale-symbol findings by hand. Provide one command that runs them for a whole Plan, prints only failures, and suggests for each stale name whether it needs a `(new)` marker or is not a code symbol.

## Background
Evidence (`Explicit in code`): `skills/plan-to-implementation-procedure/workflow.md` Step 3c and Step 4 require `tools/stale_detector.py`, `tools/check_workitem_structure.py`, and `tools/check_workitem_traceability.py --plan-coverage`, and name `tools/mark_procedure_new_symbols.py` for names a document creates. In one session these were run in loops five or more times for two Plans of 9 and 12 documents. `mark_procedure_new_symbols.py mark --all` marked names that were not code symbols (values, attributes, external library names), so those had to be un-backticked by hand, and a first pass flagged names that a sibling procedure creates.

## Problem
Repeated runs and manual classification of the same findings cost time and tokens, and the classification step is easy to get wrong.

## Reason for Change
Efficiency; no correctness risk. Not urgent.

## Implementation Intent
A thin orchestration tool over the existing checkers: it runs them with their existing semantics and reports a compact summary. Edits happen only with an explicit flag and only for an unambiguous classification.

## Target Files or Areas
- `tools/finalize_procedures.py` (new)
- `tools/TOOL_DESCRIPTIONS.md`
- `skills/plan-to-implementation-procedure/workflow.md` (Step 3c and Step 4 reference to the tool)

## Required Changes
- Run the four checks for every procedure of a Plan and print only failing rows, with the document and the finding.
- For each `symbol_missing` finding, classify it as `created here` (declared as a class, function, or field in the same document's Procedure) or `not a code symbol`, and print the suggested action; apply it only with an explicit flag.
- Print one summary line when everything passes, including the counts the Plan coverage check reports.
- Keep each underlying tool's exit semantics visible in the output.

## Constraints
- The tool must not weaken or skip any underlying check.
- No automatic edit without the explicit flag; an ambiguous name is reported, not changed.

## Acceptance Criteria
- [ ] A Plan whose procedures all pass produces one summary line.
- [ ] A stale name created by the same document is suggested for `(new)`; a name that is a value or an external name is suggested for un-backticking.
- [ ] The result equals running the four tools by hand.

## Testing Expectations
Unit tests with synthetic procedures covering each classification; ruff, mypy, bandit; `tools/check_tool_descriptions_sync.py`; a documented comparison run on one existing Plan.

## Documentation Impact
Yes. The tool row and the two workflow references.

## Out of Scope
- Changing the checkers themselves.
- Generating procedure content.

## Dependencies
- Depends on: issues/20261126-151438_wfeff003_plan-path-citations.md (readable Plan citations make the coverage check reliable).

## Unresolved Questions
- `不明`: whether the classification should live in `mark_procedure_new_symbols.py` instead of a new tool.

## AI Implementation Instruction
Reuse the existing tools as libraries or subprocesses. Stop and report if a check cannot be run without writing a file.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261126-151441
- **Related target files**: `tools/finalize_procedures.py`, `tools/TOOL_DESCRIPTIONS.md`, `skills/plan-to-implementation-procedure/workflow.md`
