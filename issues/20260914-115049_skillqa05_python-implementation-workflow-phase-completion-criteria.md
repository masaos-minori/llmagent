# Add "Completed when" criteria to python-implementation workflow Phases 3, 6, 7, 8, 10, 11, 12

## Priority
High

## Summary
`skills/python-implementation/workflow.md` Phases 1, 2, 4, 5, and 9 each state an explicit "Completed when" condition, but Phases 3 (Architecture Boundary Analysis), 6 (Runtime Contract Validation), 7 (Observability Injection), 8 (Security Validation), 10 (Scope Control), 11 (Production Readiness), and 12 (Knowledge Compression) do not — most notably Phase 8, the security-validation gate.

## Background
This issue follows a skill/workflow design review (5 evaluation criteria, 55 files) requested and conducted in this session; this entry covers the "goal + exit condition" criterion for `python-implementation`'s largest gap set. Companion issues from the same review cover other files.

## Problem
Confirmed by direct reading of `skills/python-implementation/workflow.md`:
- Phase 3 (lines 102-114): describes running `lint-imports` but does not state what "done" means for this Phase.
- Phase 6 (185-213): describes Pydantic boundary usage and Schemathesis commands with no completion condition.
- Phase 7 (215-235): describes logging conventions and an explicit skip condition ("skip this phase unless OTel is requested") but no completion condition for the non-skip case.
- Phase 8 (237-243): the security-validation Phase — states only "see `rules/toolchain.md` section 5 for bandit commands" and "see `rules/coding.md` Bandit priority findings," with no statement of what passing this Phase requires.
- Phase 10 (260-280): describes diff-cover and pytest-benchmark usage with no completion condition.
- Phase 11 (283-291): describes an `rg` check and an MCP-server checklist reference with no completion condition.
- Phase 12 (294-300): describes doc/routing updates with no completion condition.

## Reason for Change
Phase 8's omission is the most significant: a security-validation Phase with no stated pass condition means an agent could run bandit, see findings, and have no explicit rule for whether it may proceed — unlike Phase 9's own explicit "on a task-caused failure, delegate ... do not proceed to Phase 10 with a known failure" pattern, which Phase 8 should mirror for security findings specifically.

## Implementation Intent
Add one "Completed when" line to each of the seven listed Phases, following the style of Phase 1/2/4/5/9, stating the concrete condition specific to that Phase's own tooling/checklist — Phase 8 in particular should state that high/medium-severity bandit findings (per `rules/coding.md` Bandit priority findings) must be resolved or explicitly suppressed with justification (per `rules/coding.md` Suppression governance) before proceeding, mirroring Phase 9's failure-triage pattern.

## Target Files or Areas
- `skills/python-implementation/workflow.md`

## Required Changes
- Phase 3: add "Completed when: `lint-imports` passes, or any new violation is resolved by an explicit, documented contract change in `.importlinter` rather than a suppressed failure."
- Phase 6: add "Completed when: new module-boundary data is validated at a Pydantic boundary where the codebase convention calls for one, and Schemathesis has been run for any changed MCP endpoint (or this Phase does not apply, since no boundary/endpoint changed)."
- Phase 7: add "Completed when: new I/O-bound or cross-service code paths use the `key=value` log format, or this Phase was correctly skipped (no OTel request, no new I/O-bound/cross-service path)."
- Phase 8: add "Completed when: `bandit` has been run and every high/medium-severity finding (per `rules/coding.md` Bandit priority findings) is either resolved or suppressed with an inline justification (per `rules/coding.md` Suppression governance) — do not proceed to Phase 9 with an unresolved, unjustified high/medium finding."
- Phase 10: add "Completed when: `diff-cover`'s reported coverage meets the threshold in `rules/toolchain.md` Completion checklist, and a `pytest-benchmark` regression check has been run for any performance-sensitive change (or this Phase does not apply)."
- Phase 11: add "Completed when: the `rg` search for the old module/symbol name (when renaming/removing) returns no remaining reference, and the MCP-server checklist in `skills/mcp-server-add/workflow.md` is satisfied when a new server was added."
- Phase 12: add "Completed when: `routing.md` and the affected doc (per `docs/00_index.md`'s task mapping) are updated, or the task is confirmed to need no documentation update."

## Constraints
Phase 8's added condition must explicitly gate progression to Phase 9 on resolved/justified findings, mirroring Phase 9's own existing failure-triage wording, rather than merely restating "run bandit."

## Acceptance Criteria
- Each of Phases 3, 6, 7, 8, 10, 11, 12 in `skills/python-implementation/workflow.md` has an explicit "Completed when" line.
- Phase 8's added line explicitly blocks progression on an unresolved high/medium-severity finding, consistent with Phase 9's existing pattern.
- `tools/check_skills_references.py` still passes.

## Testing Expectations
Not applicable — prose-only workflow file. Run `tools/check_skills_references.py` per `routing.md`'s relevant row.

## Documentation Impact
This issue's entire scope is `skills/python-implementation/workflow.md`.

## Out of Scope
- Phases 1, 2, 4, 5, 9 — already have adequate completion conditions.
- Any other evaluation criterion from the same review — tracked in separate issues.

## Dependencies
N/A: none.

## Unresolved Questions
N/A: none.

## AI Implementation Instruction
Add only the completion-condition line per Phase; do not restructure the surrounding content. Match Phase 1/2/4/5/9's existing "Completed when" phrasing style. For Phase 8, explicitly model the gating language on Phase 9's existing "do not proceed ... with a known failure" pattern rather than inventing new wording.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260914-115049
- **Related target files**: skills/python-implementation/workflow.md
