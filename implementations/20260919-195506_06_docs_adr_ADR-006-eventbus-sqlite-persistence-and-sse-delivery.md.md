## Goal
Classify `docs/adr/ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md`'s 3 real
`## Implementation Notes` bullets against `docs/00_governance_02_documentation-metadata.md`'s
Decision Categories and apply the corresponding action (REQ-001, REQ-003).

## Scope
In scope: the 3 confirmed real bullets in this file's `## Implementation Notes` section.
Out of scope: this file's other sections; any other file.

## Assumptions
Confirmed 20260919 (`plan-to-implementation-procedure` Step 3a): this file's
`## Implementation Notes` section contains exactly 3 real bullets (beyond the standard
boilerplate intro/outro):
1. Transaction guarantee — cross-references INV-16 (single transaction inside
   `ack_event_for_consumer()`).
2. Monotonicity enforcement — cross-references INV-05/INV-09, naming the exact
   `INSERT ... ON CONFLICT(consumer_id) DO UPDATE SET offset = excluded.offset WHERE
   excluded.offset > consumer_offsets.offset` statement.
3. Legacy migration — points to `migrate_legacy_offsets()` and cross-references Known
   Deviations entry EVENTBUS-007 for details.

## Design decisions
Per `skills/python-design/SKILL.md`'s "Avoid implementation-reference duplication": all 3
bullets are primarily *pointers* to invariants/deviations already recorded elsewhere in
this ADR (INV-16, INV-05/09, EVENTBUS-007), not code-location trivia in their own right.
Bullet 2 additionally names a specific SQL statement, which leans toward `Delete`/
`Compress` per the Decision Categories' "verifiable from code... alone" criterion (the
exact SQL text will drift if the query changes, and a wrong restatement would be caught
by a failing test, not review) — but the cross-reference to INV-05/09 itself should be
retained as navigation. Bullets 1 and 3 are purely navigational pointers to
already-documented invariants/deviations; classify each against whether the pointer adds
information beyond what `## Invariants`/`## Known Deviations` already state on their own.

## Alternatives considered
N/A: the classification mechanism is fixed by REQ-001 — no alternative scheme applies.

## Implementation
### Target file
docs/adr/ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md

### Procedure
1. Read `## Invariants` and `## Known Deviations` to confirm whether INV-16, INV-05,
   INV-09, and EVENTBUS-007 already state what these 3 bullets restate, or whether the
   bullets add navigation value not otherwise present.
2. Classify each of the 3 bullets against the Decision Categories table using that
   finding.
3. Apply each bullet's action (delete/compress the literal SQL restatement if it adds
   nothing beyond the INV reference; retain a bare cross-reference if useful navigation;
   move to Known Issues only if a genuine implementation/design mismatch is found, which
   is not expected here — these read as accurate pointers, not mismatches).
4. Re-run the Validation plan's checkers.

### Method
`Edit` tool — direct text edit within `## Implementation Notes`.

### Details
Do not remove a cross-reference that is the only place a reader would learn "this
invariant/deviation exists" — only remove/compress the parts that are pure code
restatement (e.g. the literal SQL text) if the referenced INV/Known Deviation entry
already contains it.

## Compatibility considerations
Only `## Implementation Notes` within this file is affected (or, if a bullet is promoted,
`## Rationale`/`## Invariants` within this same file — no cross-references here are
expected to require a Known Issues/Needs Confirmation entry based on the content read).

## Security considerations
N/A: documentation-only, no credentials or runtime behavior change.

## Rollback considerations
`git checkout -- docs/adr/ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md`
reverts this row independently.

## Validation plan
- `uv run python tools/check_docs_quality.py` — confirm no new finding for this file.
- `uv run python tools/check_docs_structure.py` — confirm no new finding for this file.
- `uv run python tools/check_adr_structure.py` — confirm no new finding for this file.

## Completion criteria
All 3 bullets are classified into exactly one Decision Categories bucket and the
corresponding action applied; no content is lost; the 3 checkers above report no new
finding for this file.

## Out of scope
This file's other sections beyond `## Implementation Notes`; any other ADR or design doc.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260919-215638 | 20260919-215638 | Classify and apply action for 3 real bullets Bullets 1,3 already minimal navigational pointers (Compress/Retain, already compliant, no change). Bullet 2 compressed: removed literal SQL restatement, kept INV-05/INV-09 cross-reference (Compress). |
| 2 | Add or update tests per Validation plan | Completed | 20260919-215638 | 20260919-215638 | N/A: documentation-only, no test to add N/A: documentation-only |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260919-215638 | 20260919-215638 | check_docs_quality.py, check_docs_structure.py, check_adr_structure.py check_docs_quality.py: 0 error/1 pre-existing warning; check_docs_structure.py: 9 pre-existing findings (out of scope); check_adr_structure.py: No issues found |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260919-215638 | 20260919-215638 | N/A: this document's own Target file IS the documentation being updated Edited this file's own Implementation Notes only |

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
- **Requirement ID**: REQ-001, REQ-003 (classify 3 real bullets; apply action)
- **Source issue**: issues/20260919-193722_impln01_audit-and-reclassify-docs-implementation-notes-items-per-existing-decision-categories.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260919-194628_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260919-195506
- **Related target files**: docs/adr/ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md