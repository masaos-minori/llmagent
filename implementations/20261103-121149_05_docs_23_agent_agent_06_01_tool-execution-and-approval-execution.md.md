## Goal

Document the two-case synthesized-row semantics in the tool-execution doc: a call the
round never dispatched keeps the "not executed" text, while a call whose request had
already been sent is answered with the outcome-unknown text and its reason (REQ-002;
AC-001), matching the code landing in seq 01-04.

## Scope
**Release unit**: N/A: not part of a release unit

Covers the `docs/23_agent/agent_06_01_tool-execution-and-approval-execution.md` row (seq
05) of `plans/20261101-144325_inflightcancel001_cancelled-call-reported-unexecuted.md`.
Runs after all four code documents (01 → 02 → 03 → 04 → 05) so the documented behavior
matches the shipped code, and before the plan-wide validation.

## Assumptions
- Verified against current source (20261103): the doc's "Result Reflection in History"
  section (around doc:71-76) states every declared id gets exactly one `role='tool'` row,
  an unexecuted call is answered by a synthesized row saying it was not executed "for one
  of two reasons (`ToolCallStopReason`)", and lists only guard-stop and round-not-completed.
  The following "Tool Call State Recording" section already describes the pending-row
  mechanism (`tool_call_state`, `classify_stale_pending`) — a parallel account this doc
  update must not contradict.
- The dupcallid001 cycle already edited this doc's preparation-checklist section
  (`implementations/done/20261103-080412_03_docs_23_agent_agent_06_01_tool-execution-and-approval-execution.md.md`,
  archived); this document touches only the round-completion/reflection area — no section
  collision (Plan Assumptions overlap note, re-confirmed 20261103).
- Documentation updates for this plan's domain are validated by `uv run python
  tools/check_docs_consistency.py --domain agent` (the shorthand `uv run check-agent-docs`
  is broken; use the explicit command).

## Design decisions
- Update the existing "Result Reflection in History" paragraph in place (no new section):
  state the three synthesized-row cases by reason — loop-guard stop, round not completed
  (never dispatched), and round stopped with the call dispatched (outcome unknown,
  "verify before repeating") — and add one sentence of rationale: a dispatched call's
  server-side execution is ambiguous, mirroring the fail-closed write precedent
  (`scripts/shared/http_transport.py`, ADR-004).
- Keep the sentences about stats/`out_failed_keys`/empty-result-guard invariance and the
  exception-propagation guarantee word-for-word (they still hold).
- Add one cross-reference sentence to the adjacent "Tool Call State Recording" section
  stating the `pending` row and the outcome-unknown text are independent accounts of the
  same in-flight fact — the workflow consumes the stale pending row, the history row keeps
  the human/LLM-facing text (no mechanism change described).

## Alternatives considered
- A separate subsection for in-flight semantics: rejected — the existing paragraph already
  enumerates reasons; splitting sections would fragment the invariants stated there.

## Implementation
### Target file
`docs/23_agent/agent_06_01_tool-execution-and-approval-execution.md`

### Procedure
1. After seq 01-04 are implemented, re-read the "Result Reflection in History" section and
   rewrite its synthesized-row sentence to describe the three reasons and the two texts
   (not-executed vs outcome-unknown), per Design decisions. Intent-level prose; do not
   paste implementation code.
2. Add the one-sentence ADR-004 rationale and the cross-reference sentence to the
   Tool Call State Recording section.
3. Keep the rest of the doc (preparation checklist, scheduling invariant, approval
   sections) byte-identical.

### Method
In-place paragraph rewrite plus two added sentences; documentation-only change.

### Details
- Wording must match the shipped text constants from seq 02 (outcome-unknown text wording)
  and the existing not-executed texts — verify against the code after seq 02 lands rather
  than restating from the Plan.
- `docs/00_index.md` needs no change: the doc is already registered and named by the
  Document References by Task table the Plan cites.

### Companion test files
- None. Documentation row; validation is the docs checker below.

## Compatibility considerations
- The Plan's Documentation Impact section requires exactly this doc; no other docs/ file
  may be edited (frozen table).

## Security considerations
N/A.

## Rollback considerations
- Revert the doc commit restores today's paragraph.

## Validation plan
1. `uv run python tools/check_docs_consistency.py --domain agent` — pass.
2. Manual diff review: only the round-completion/reflection area changed.
3. The plan-wide validation sequence (`rules/toolchain.md`) runs after this document.

## Completion criteria
- The doc distinguishes never-dispatched vs dispatched-unknown synthesized rows and names
  the reason and rationale (AC-001 intent); consistency checker passes.

## Out of Scope
- All code documents (seq 01-04), `docs/00_index.md`, any other docs/ file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Rewrite the synthesized-row paragraph and add the two sentences (Procedure 1-3) | Pending | — | — | Runs after seq 01-04 land |
| 2 | Run the docs consistency checker (Validation plan 1) | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Requirement ID**: REQ-002 (documentation of the two-case synthesized-row semantics)
- **Source issue**: issues/20261101-073608_inflightcancel001_cancelled-call-reported-unexecuted.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261101-144325_inflightcancel001_cancelled-call-reported-unexecuted.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261103-121149
- **Related target files**: `docs/23_agent/agent_06_01_tool-execution-and-approval-execution.md`
