## Goal
Satisfy `REQ-004` (Plan `plans/20260901-070239_plan.md`): update `docs/adr/ADR-008-sqlite-4db-separation.md`'s
`## Related Documents` → `### Operations` entry to point at the new manual-recovery
runbook subsection (added by seq 01 of this same Plan) specifically, not just the
whole document.

## Scope
Modify exactly the `### Operations` bullet under `## Related Documents` (current lines
499-501) in `docs/adr/ADR-008-sqlite-4db-separation.md`. No other section of this file
is touched. Does not change ADR-008's Decision Details, Rationale, or Invariants
sections (Plan Out-of-Scope: "change ADR-008's recovery policy itself").

## Assumptions
- Re-verified 2026-09-02: `### Operations` (current lines 499-503) confirms the
  existing bullet `[Operations and Observability](05_agent_10_01_operations-and-observability-startup-and-health.md) — 運用と観測`
  as a whole-document reference — matches the Plan's cited "lines 499-501" (2-line
  shift, content unchanged).
- **Ordering dependency on seq 01**: this document's procedure names the exact
  subsection heading seq 01 (`implementations/20260902-183238_01_docs_05_agent_10_01_operations-and-observability-startup-and-health.md.md`)
  specifies — `### Manual Recovery: workflow.sqlite / eventbus.sqlite` — but that
  heading does not exist in the actual repository file until seq 01 is executed by
  `code-implementation`. Per `skills/code-implementation/workflow.md` Multi-file
  processing, seq 01 MUST be executed before this document (seq 02); at
  implementation time, re-read the actual written heading text and independently
  verify (do not assume) the Markdown anchor it produces before writing the link —
  do not trust a pre-computed anchor guess from this procedure-generation-time
  document.

## Design decisions
Link to the specific subsection via a Markdown in-document anchor
(`{doc}#{anchor-slug}`) rather than only naming the document, since REQ-004
specifically requires pointing at the "new runbook subsection... specifically, not
just the document" (Plan Requirements). Keep the existing bullet's Japanese
description text ("運用と観測") unless implementation-time review finds it no longer
describes the (now runbook-inclusive) target document accurately — a judgment left to
`code-implementation`'s own Step 3 adversarial verification, not fixed here.

## Alternatives considered
Adding a second, separate bullet under `### Operations` specifically for the runbook,
alongside the existing whole-document bullet — considered, but rejected: REQ-004 asks
to make the *existing* reference "point at" the subsection, which reads as updating
the current bullet's target, not adding a duplicate second entry for the same
document.

## Implementation
### Target file
docs/adr/ADR-008-sqlite-4db-separation.md

### Procedure
Update the existing `### Operations` bullet's link target to include the runbook
subsection's anchor, once seq 01 has actually written that subsection.

### Method
1. **Precondition (verify before editing)**: confirm seq 01's implementation
   procedure (`implementations/20260902-183238_01_docs_05_agent_10_01_operations-and-observability-startup-and-health.md.md`,
   or its archived location under `implementations/done/` once processed) has been
   executed — i.e. `docs/05_agent_10_01_operations-and-observability-startup-and-health.md`
   actually contains a `### Manual Recovery: workflow.sqlite / eventbus.sqlite`
   heading. If it does not yet exist, this row is **not yet ready**: report `Blocked:
   cross-file conflict with docs/05_agent_10_01_operations-and-observability-startup-and-health.md
   — seq 01 not yet executed` per `skills/code-implementation/workflow.md` Step 3, and
   do not proceed with this row until seq 01 lands.
2. Once the heading exists, read it verbatim and derive its actual Markdown anchor
   (do not assume the anchor computed from this document's own guess of the heading
   text — re-derive it from the real, current heading in the real file, since heading
   wording could have changed during seq 01's own adversarial verification).
3. Locate the current bullet (lines 499-503 area):
   ```
   ### Operations

   - [Operations and Observability](05_agent_10_01_operations-and-observability-startup-and-health.md) — 運用と観測
   ```
4. Replace the bullet's link target with the document-plus-anchor form:
   ```
   ### Operations

   - [Operations and Observability](05_agent_10_01_operations-and-observability-startup-and-health.md) — 運用と観測
   - [Manual Recovery: workflow.sqlite / eventbus.sqlite](05_agent_10_01_operations-and-observability-startup-and-health.md#{actual-verified-anchor}) — workflow.sqlite / eventbus.sqliteの手動復旧手順
   ```
   (Add as a second bullet rather than rewriting the first, since the existing
   whole-document reference remains valid and useful on its own — see Design
   decisions for why REQ-004 is satisfied either way as long as the subsection is
   specifically reachable from this section.)

### Details
This is a documentation cross-reference update only. It has a hard ordering
dependency on seq 01 (see Assumptions) — `code-implementation` must not execute this
row before seq 01's row has landed, per this session's `cip006` cross-file-conflict
handling addition to `skills/code-implementation/workflow.md` Step 3.

## Compatibility considerations
Documentation-only change; no code, schema, or runtime behavior affected.

## Security considerations
N/A: no security-relevant content in an internal cross-reference update.

## Rollback considerations
Trivially revertable via `git revert`/`git checkout` of this single file — should be
reverted together with seq 01 if that subsection is rolled back, to avoid a dangling
anchor link.

## Validation plan
- Manual review: confirm the added link's anchor actually resolves to a real heading
  in the target file (Plan `Validation plan`).
- `uv run python tools/check_docs_quality.py` and `uv run python
  tools/check_docs_structure.py docs/adr/ADR-008-sqlite-4db-separation.md` — confirm
  no new structural issues, including internal link reachability.

## Completion criteria
`### Operations` under `## Related Documents` in
`docs/adr/ADR-008-sqlite-4db-separation.md` links specifically to the manual-recovery
runbook subsection (not only the whole document), and the link's anchor is verified to
resolve to the actual heading `code-implementation` wrote for seq 01 — satisfying
REQ-004.

## Out of scope
Changing ADR-008's Decision Details, Rationale, or Invariants sections (Plan
Out-of-Scope). Rewording the existing whole-document bullet's description text
(left as a judgment call for `code-implementation`'s own Step 3, see Design
decisions).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Verify seq 01's precondition (runbook subsection exists) | Pending | — | — | Blocking precondition — see Method step 1 |
| 2 | Add the anchor-specific `### Operations` bullet per Method | Pending | — | — | |
| 3 | N/A: no automated test for a documentation cross-reference | Pending | — | — | N/A |
| 4 | Run `check_docs_quality.py` / `check_docs_structure.py` | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-004 (cross-reference to the new runbook subsection specifically)
- **Source issue**: `issues/20260831-181721_adr008_03_workflow_eventbus_manual_recovery_runbook.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260901-070239_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260902-183238
- **Related target files**: `docs/adr/ADR-008-sqlite-4db-separation.md`
