# Let stale detection accept names that sibling procedures create

## Priority
Medium

## Summary
Teach `tools/stale_detector.py` to treat a name as declared when another procedure of the same Plan marks it `(new)`, and to report where it was declared. This removes the false "stale" findings and the boilerplate explanation that every dependent procedure now carries, while keeping unmarked missing names stale.

## Background
- `Explicit in code`: `tools/stale_detector.py` decides per document. A name or import that a procedure creates must be marked `(new)` in that same document; a name created by another procedure is reported as `symbol_missing`.
- `Operationally observed` (2026-10-30, plans `dbmig001`, `wftaskapi001`, `wfrecovery001`): a procedure for a later row routinely uses names that an earlier row creates. The detector flagged them, and each such document needed a hand-written Assumptions sentence ("names flagged by `tools/stale_detector.py` are created by other rows of this Plan and exist when the rows run in order"). 28 archived procedure documents carry that sentence; before the code landed, up to 12 flagged names appeared in a single document.
- `Explicit in code`: `skills/plan-to-implementation-procedure/workflow.md` Step 3c item (2) prescribes the workaround (note it in Assumptions), and `skills/code-implementation/workflow.md` Step 2 aborts the cycle on any mismatch, so the note cannot be skipped in practice.
- Related closed work: `issues/done/20261012-132457_stale001_fix-stale-detector-false-positives.md`, `issues/done/20261012-172916_stale002_allow-new-target-files-in-stale-detector.md`, and `issues/done/20261012-172959_stale003_stop-flagging-non-python-names-as-missing.md` (earlier false-positive fixes of the same tool).

## Problem
The detector cannot tell "this name does not exist and nobody will create it" from "another procedure of this Plan creates it before this one runs". Authors compensate with boilerplate, which carries no checkable claim, and a real stale reference hidden among the flagged names is easy to miss.

## Reason for Change
Plans with many rows are the normal case for schema and API work. The boilerplate grows with Plan size, and the cost is paid again in `code-implementation` Step 2 when the same findings are read at execution time.

## Implementation Intent
Resolve names across the procedures of one Plan. The detector reads the procedure's Traceability `Source plan`, finds the sibling procedures that cite the same Plan (in `implementations/` and `implementations/done/`), and treats a name marked `(new)` in a sibling as declared there. Such a name is not a mismatch; it is reported as an informational line naming the declaring document. A name declared nowhere stays stale. Order should matter: accepting a declaration only from a sibling that runs earlier prevents a procedure from relying on a name that is created later; the order source is the Plan's phase order.

## Target Files or Areas
- `tools/stale_detector.py` and `tests/tools/test_stale_detector.py`
- `skills/plan-to-implementation-procedure/workflow.md` (Step 3c item (2))
- `skills/code-implementation/workflow.md` (Step 2 result handling)
- `templates/implementation-procedure.md` (notes on `(new)`)
- `tools/TOOL_DESCRIPTIONS.md`

## Required Changes
- Add sibling resolution keyed on `Source plan`, with an option to disable it, and an informational output line per name resolved from a sibling.
- Decide and implement the order rule (earlier sibling only, or any sibling) and report it in the output.
- Simplify the two skill texts: the boilerplate Assumptions note is no longer required when the detector reports the declaration.
- Keep every existing behavior for a document without a `Source plan` or without siblings.

## Constraints
- A name declared by no document must remain a mismatch (no silent acceptance).
- The detector stays a lightweight text tool: no AST parsing, no network.
- Reading sibling documents must not make a single run noticeably slower.
- The `(new)` marker syntax does not change.

## Acceptance Criteria
- On fixture procedures where document B uses a name that document A marks `(new)`, the detector reports B as not stale and names A as the declaring document; a name marked nowhere is still reported stale.
- With the order rule set to "earlier only", a name declared only by a later sibling is reported stale with the reason.
- A document without a `Source plan` behaves exactly as before.
- On the archived procedure sets of the three Plans, the count of documents needing the boilerplate sentence drops to zero in a re-run (measured and recorded).
- `check_tool_descriptions_sync.py` passes.

## Testing Expectations
- Unit tests for the cases above, including a cycle of declarations and a sibling that is itself missing.
- A re-run of the detector over the archived procedures of `dbmig001`, `wftaskapi001`, and `wfrecovery001`, with the before and after counts recorded.
- `ruff`, `mypy tools/stale_detector.py`, and `bandit` on the changed tool.

## Documentation Impact
Yes. The two skills and the procedure template state that sibling declarations are resolved by the tool and no longer need a manual note. Intent and failure behavior only.

## Out of Scope
- Changing how `(new)` is written or how target files are declared.
- Checking that a declared name is actually created when the sibling runs.
- Generating the procedures themselves.

## Dependencies
Sequencing with `issues/20261030-191144_flowimp003_plan-dependency-gate.md`: the "earlier sibling only" rule needs the Plan phase order that issue's order view provides; until it lands, the first version may accept any sibling and report that. No other open issue or Plan targets these files (checked with `rg` over `issues/*.md` and `plans/*.md`, 2026-10-30).

## Unresolved Questions
- `不明`: whether "any sibling" is acceptable as a first version or the order rule must ship together.
- `不明`: how to treat a sibling that is archived as `Blocked`; the assumption is that its declarations still count.
- Assumption: `Source plan` is present and accurate in every generated procedure (it is a required template field).

## AI Implementation Instruction
Change the detector, its tests, and the named skill and template text only. Keep unmarked missing names stale and keep documents without siblings unchanged. Report every resolved name with its declaring document. Stop and report if the Plan order cannot be determined and the order rule is required.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261030-191457
- **Related target files**: `tools/stale_detector.py`, `tests/tools/test_stale_detector.py`, `skills/plan-to-implementation-procedure/workflow.md`, `skills/code-implementation/workflow.md`, `templates/implementation-procedure.md`, `tools/TOOL_DESCRIPTIONS.md`
