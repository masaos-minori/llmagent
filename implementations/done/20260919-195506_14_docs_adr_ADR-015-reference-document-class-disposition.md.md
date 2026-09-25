## Goal
Classify `docs/adr/ADR-015-reference-document-class-disposition.md`'s real
`## Implementation Notes` content against `docs/00_governance_02_documentation-metadata.md`'s
Decision Categories and apply the corresponding action (REQ-001, REQ-003).

## Scope
In scope: the confirmed real content block in this file's `## Implementation Notes`
section. Out of scope: this file's other sections; any other file.

## Assumptions
Confirmed 20260919 (`plan-to-implementation-procedure` Step 3a): this file's
`## Implementation Notes` section contains one real content block — a 3-item candidate
list for Reference-class migration under Option B (Agent: `docs/agent_13_reference-api.md`;
EventBus: `docs/06_eventbus_06_reference-api.md`; Memory: 6 candidate chapter files under
`docs/05_agent_12_*.md`, exact target unresolved), explicitly sourced from
`plans/done/20260919-105034_plan.md`'s target list rather than re-derived here. This is
not boilerplate — it is real, ADR-specific content.

## Design decisions
Per the Decision Categories table, this content does not cleanly fit `Delete`/`Compress`
(it is not a bare code/line/function citation) nor obviously `Retain` (it is a list of
migration *candidates*, not an architectural rationale). It most closely resembles
`Move to Needs Confirmation`: the Memory row's own text states "exact target
document(s) unresolved — see that Plan's `UNK-01`" — an explicit, still-open unknown.
The Agent/EventBus rows, by contrast, describe already-completed migrations (per
`plans/done/20260919-105034_plan.md` and this session's own prior work on
`docs/agent_14_reference-api-generated.md`/`docs/06_eventbus_06_reference-api.md`) —
classify each of the 3 sub-items independently rather than the whole block as one unit:
the Agent/EventBus items may now be `Delete`/`Compress` candidates (their migration is
done, so a static candidate list restates history rather than live rationale), while the
Memory item is a live `Move to Needs Confirmation` entry (or already covered by an
existing NC entry — check `docs/00_governance_03_issue-and-uncertainty-management.md`
Part 2 for `UNK-01` before filing a duplicate).

## Alternatives considered
N/A: the classification mechanism is fixed by REQ-001 — no alternative scheme applies.
Per-sub-item classification (rather than one classification for the whole block) is the
only approach consistent with the block's own internal mix of resolved vs. unresolved
items — treating it as a single unit would either wrongly resolve the Memory row or
wrongly leave the Agent/EventBus rows unresolved.

## Implementation
### Target file
docs/adr/ADR-015-reference-document-class-disposition.md

### Procedure
1. Re-verify current status of each of the 3 sub-items against live repository state:
   confirm `docs/agent_13_reference-api.md`'s companion `docs/agent_14_reference-api-generated.md`
   and `docs/06_eventbus_06_reference-api.md` reflect completed migrations (per this
   session's own prior work, plans/done/20260919-105034_plan.md); confirm whether the
   Memory row's `UNK-01` has since been resolved by checking
   `plans/done/20260919-105034_plan.md`'s own Unknowns table and
   `docs/00_governance_03_issue-and-uncertainty-management.md` Part 2 for an existing
   entry.
2. Classify the Agent/EventBus sub-items (expected: `Delete`/`Compress`, since their
   migration is complete and this list now restates history) and the Memory sub-item
   (expected: `Move to Needs Confirmation`, unless an NC entry already exists for
   `UNK-01`, in which case cross-reference it instead of filing a duplicate).
3. Apply each sub-item's action.
4. Re-run the Validation plan's checkers.

### Method
`Edit` tool — direct text edit within `## Implementation Notes`; possibly
`docs/00_governance_03_issue-and-uncertainty-management.md` (see that file's own
procedure document, row 21) if a new Needs Confirmation entry is required and none
already exists for `UNK-01`.

### Details
Do not file a duplicate Needs Confirmation entry if `UNK-01` is already tracked
elsewhere — cross-reference the existing entry instead. Do not silently delete the
Memory sub-item merely because the Agent/EventBus sub-items are resolved — its
`Blocking: False`-style unresolved status (per the source Plan's own Unknowns framing)
must be preserved somewhere, not lost.

## Compatibility considerations
Only `## Implementation Notes` within this file is affected, plus possibly
`docs/00_governance_03_issue-and-uncertainty-management.md` if a new NC entry is filed
(that file's own procedure document, row 21, covers that side of the edit).

## Security considerations
N/A: documentation-only, no credentials or runtime behavior change.

## Rollback considerations
`git checkout -- docs/adr/ADR-015-reference-document-class-disposition.md` reverts this
row independently.

## Validation plan
- `uv run python tools/check_docs_quality.py` — confirm no new finding for this file.
- `uv run python tools/check_docs_structure.py` — confirm no new finding for this file.
- `uv run python tools/check_adr_structure.py` — confirm no new finding for this file.
- `uv run python tools/check_needs_confirmation_inventory.py` — run if a new Needs
  Confirmation entry is filed for the Memory sub-item.

## Completion criteria
All 3 sub-items are classified into exactly one Decision Categories bucket and the
corresponding action applied; the Memory sub-item's unresolved status is preserved
(either as a cross-reference to an existing NC entry, or a newly filed one); the checkers
above report no new finding.

## Out of scope
This file's other sections beyond `## Implementation Notes`; resolving `UNK-01` itself
(only tracking/cross-referencing its current status is in scope here); any other ADR or
design doc.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260919-220112 | 20260919-220112 | Classify 3 sub-items independently; expected split outcome Verified: docs/agent_14_reference-api-generated.md and docs/06_eventbus_06_reference-api.md's AUTO-GENERATED block both confirm Agent/EventBus migrations complete -> Delete/Compress applied (removed as static candidate bullets, replaced with a brief completed-status statement). Memory sub-item confirmed still In Progress in plans/done/20260919-105034_plan.md Step 4/UNK-01, no existing NC entry found -> Move to Needs Confirmation, reserved NC-038 (added by row 21). NOTE (out of scope, not edited): this file's own Known Deviations section still states no Reference-class doc has been migrated -- now stale vs Agent/EventBus completion; left unedited per this row's explicit Out of scope (other sections). |
| 2 | Add or update tests per Validation plan | Completed | 20260919-220112 | 20260919-220112 | N/A: documentation-only, no test to add N/A: documentation-only |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260919-220112 | 20260919-220112 | check_docs_quality.py, check_docs_structure.py, check_adr_structure.py, check_needs_confirmation_inventory.py (conditional) check_docs_quality.py: 0 error; check_docs_structure.py: 2 pre-existing findings (out of scope); check_adr_structure.py: No issues found; check_needs_confirmation_inventory.py: no new finding for this file |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260919-220112 | 20260919-220112 | N/A: this document's own Target file IS the documentation being updated Edited this file's own Implementation Notes only |

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
- **Requirement ID**: REQ-001, REQ-003 (classify real content; apply action, split by sub-item)
- **Source issue**: issues/20260919-193722_impln01_audit-and-reclassify-docs-implementation-notes-items-per-existing-decision-categories.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260919-194628_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260919-195506
- **Related target files**: docs/adr/ADR-015-reference-document-class-disposition.md