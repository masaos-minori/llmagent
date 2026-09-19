## Goal
Classify `docs/adr/ADR-004-environment-failure-handling-policy.md`'s 2 real
`## Implementation Notes` bullets against `docs/00_governance_02_documentation-metadata.md`'s
Decision Categories and apply the corresponding action (REQ-001, REQ-003).

## Scope
In scope: the 2 confirmed real bullets in this file's `## Implementation Notes` section.
Out of scope: this file's other sections; any other file.

## Assumptions
Confirmed 20260919 (`plan-to-implementation-procedure` Step 3a): this file's
`## Implementation Notes` section contains exactly 2 real, ADR-specific bullets (beyond
the standard boilerplate intro/outro paragraphs):
1. `StartupOrchestrator`-built `StartupValidationResult` (`scripts/agent/shared/health_models.py`)
   is a per-process, in-memory aggregate object, never persisted to `workflow.sqlite` or
   elsewhere.
2. The current retry behavior on MCP server unreachability is a single fixed-delay retry
   (`HEALTH_CHECK_RETRY_DELAY_SEC`), not a configurable-attempt-count general Retry Policy.

## Design decisions
Per `skills/python-design/SKILL.md`'s "Avoid implementation-reference duplication": bullet
1 is a statement about object lifetime/persistence scope (a design-relevant fact about
what durability guarantee does NOT exist) rather than a pure code-location fact — this
makes it a candidate for `Retain` under the Decision Categories' "Correlated constraints
and their rationale" / "the absence of a documented rationale, when that absence is
itself operationally significant" criteria, since it documents a *deliberate absence* of
persistence a reader could otherwise assume exists. Bullet 2 similarly describes a
current behavioral choice (fixed single retry vs. configurable policy) that could be
`Retain` (if this is a deliberate simplicity choice) or `Move to Known Issues` (if a
general Retry Policy was intended but not yet implemented) — the actual bucket depends on
information this document does not have (was this a deliberate scope decision, or
unfinished work?); classify per whichever the file's own `## Rationale`/`## Known
Deviations` sections already indicate, not by assumption.

## Alternatives considered
N/A: the classification mechanism (apply the existing Decision Categories table) is fixed
by the Plan's REQ-001 — no alternative classification scheme applies.

## Implementation
### Target file
docs/adr/ADR-004-environment-failure-handling-policy.md

### Procedure
1. Read `## Implementation Notes`, `## Rationale`, `## Invariants`, and `## Known
   Deviations` in full to determine whether bullet 2's fixed-retry behavior is already
   documented elsewhere as a deliberate choice or an acknowledged gap.
2. Classify bullet 1 (`StartupValidationResult` non-persistence) against the Decision
   Categories table.
3. Classify bullet 2 (fixed-delay retry, not configurable) against the same table,
   informed by step 1's finding.
4. Apply each bullet's action: if `Retain`, move the bullet's content into `## Rationale`
   or `## Invariants` (whichever the content fits) without duplicating it in
   Implementation Notes; if `Move to Known Issues`, file an entry per
   `docs/00_governance_03_issue-and-uncertainty-management.md` Part 1's Entry Template
   and replace the bullet with a short cross-reference; if `Delete`/`Compress`, remove or
   shorten in place; if `Move to Needs Confirmation`, file an entry per that document's
   Part 2 and cross-reference.
5. Re-run the Validation plan's checkers against this file.

### Method
`Edit` tool — direct text edit within `## Implementation Notes` and, depending on
classification outcome, `## Rationale`/`## Invariants` (this file) and possibly
`docs/00_governance_03_issue-and-uncertainty-management.md` (see that file's own
procedure document, row 21, for the counterpart edit if a Known Issues/Needs Confirmation
entry is filed).

### Details
Do not duplicate a promoted bullet's content in both Implementation Notes and its new
location — remove the Implementation Notes copy once the content is moved (a short
cross-reference sentence is acceptable, not a repeated full restatement).

## Compatibility considerations
Only `## Implementation Notes` and, depending on classification, `## Rationale`/
`## Invariants` within this same file are affected. No other file is modified by this
row alone (a Known Issues/Needs Confirmation entry, if filed, is this row's contribution
to `docs/00_governance_03_issue-and-uncertainty-management.md`'s own procedure row, not a
second target file for this document).

## Security considerations
N/A: documentation-only, no credentials or runtime behavior change.

## Rollback considerations
`git checkout -- docs/adr/ADR-004-environment-failure-handling-policy.md` reverts this
row independently.

## Validation plan
- `uv run python tools/check_docs_quality.py` — confirm no new finding for this file.
- `uv run python tools/check_docs_structure.py` — confirm no new finding for this file.
- `uv run python tools/check_adr_structure.py` — confirm no new finding for this file
  (in particular, confirm no Implementation Notes vs Implementation References drift if
  a promoted bullet's path citation moves).

## Completion criteria
Both bullets are classified into exactly one Decision Categories bucket and the
corresponding action applied; no content is lost or duplicated; the 3 checkers above
report no new finding for this file.

## Out of scope
This file's other sections beyond `## Implementation Notes` and the promotion
destinations named above; any other ADR or design doc.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260919-215525 | 20260919-215525 | Classify and apply action for 2 real bullets Bullet 1 (StartupValidationResult non-persistence) classified Retain -> moved to new Rationale item 6. Bullet 2 (fixed-delay retry) had no supporting Rationale/Known Deviations either way -> classified Move to Needs Confirmation, reserved NC-037 (created by row 21's cycle), Implementation Notes bullet replaced with cross-reference. |
| 2 | Add or update tests per Validation plan | Completed | 20260919-215525 | 20260919-215525 | N/A: documentation-only, no test to add N/A: documentation-only, no test to add |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260919-215525 | 20260919-215525 | check_docs_quality.py, check_docs_structure.py, check_adr_structure.py check_docs_quality.py: 0 error/3 pre-existing warnings; check_docs_structure.py: 9 pre-existing findings (out of scope, incl. pre-existing size-limit); check_adr_structure.py: No issues found (drift warning resolved by removing health_models.py ref); check_needs_confirmation_inventory.py: no new finding |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260919-215525 | 20260919-215525 | N/A: this document's own Target file IS the documentation being updated Edited this file's own Rationale + Implementation Notes only, per Compatibility considerations |

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
- **Requirement ID**: REQ-001, REQ-003 (classify 2 real bullets; apply Retain/promote action if applicable)
- **Source issue**: issues/20260919-193722_impln01_audit-and-reclassify-docs-implementation-notes-items-per-existing-decision-categories.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260919-194628_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260919-195506
- **Related target files**: docs/adr/ADR-004-environment-failure-handling-policy.md