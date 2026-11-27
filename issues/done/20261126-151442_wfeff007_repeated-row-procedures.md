# Generate identical lightweight procedures from one row template

## Priority
Low

## Summary
When several Plan rows need the same small change (for example one added key in ten configuration files), each row still needs its own procedure document. Provide a way to generate those documents from one template so the author writes the shared content once.

## Background
Evidence (`Explicit in code`): `skills/plan-to-implementation-procedure/SKILL.md` Core Execution Rules require one document per `Implementation Target Files` row. `tools/generate_workitem.py --kind implementation-procedure` scaffolds one empty document per call. In one session ten configuration procedures were identical except for the path, and were produced with an ad hoc script.

## Problem
The shared content is rewritten per document, and an ad hoc script is not reviewed or reusable.

## Reason for Change
Token and time cost for large repeated-row Plans; low urgency.

## Implementation Intent
Keep the one-document-per-row rule and each document's own traceability and Execution Status; generate the shared body from one template with a path placeholder.

## Target Files or Areas
- `tools/generate_workitem.py` or a new tool `tools/generate_repeated_procedures.py`
- `tools/TOOL_DESCRIPTIONS.md`
- `skills/plan-to-implementation-procedure/workflow.md` (Step 3c)

## Required Changes
- Accept a Plan, a list of its row paths, and a body template with placeholders, and write one document per row using the Plan's shared pass timestamp and the row's own sequence number.
- Refuse rows whose `Change Responsibility` text differs, so a row-specific change cannot be hidden in a shared body.
- Run `tools/check_workitem_structure.py` on the created files and print the result.

## Constraints
- No merged documents; each row keeps its own file.
- The generated documents must pass the same checks as hand-written ones.

## Acceptance Criteria
- [ ] Ten rows with identical `Change Responsibility` produce ten valid documents in one call.
- [ ] A row with a different `Change Responsibility` makes the tool refuse.
- [ ] Sequence numbers and the timestamp match what `generate_workitem.py` would assign.

## Testing Expectations
Unit tests with a synthetic Plan; ruff, mypy, bandit; `tools/check_tool_descriptions_sync.py`.

## Documentation Impact
Yes. The tool row and the Step 3c pointer.

## Out of Scope
- Changing the one-document-per-row rule or the lightweight-fill criteria.

## Dependencies
- N/A: none

## Unresolved Questions
- `不明`: whether this belongs in `generate_workitem.py` or a separate tool.

## AI Implementation Instruction
Reuse the existing sequence and timestamp logic. Stop and report if the refusal rule cannot be decided from the Plan text alone.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261126-151442
- **Related target files**: `tools/generate_workitem.py`, `tools/TOOL_DESCRIPTIONS.md`, `skills/plan-to-implementation-procedure/workflow.md`
