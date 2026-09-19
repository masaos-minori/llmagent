## Goal
Classify `docs/adr/ADR-008-sqlite-4db-separation.md`'s 2 real `## Implementation Notes`
bullets against `docs/00_governance_02_documentation-metadata.md`'s Decision Categories
and apply the corresponding action (REQ-001, REQ-003).

## Scope
In scope: the 2 confirmed real bullets in this file's `## Implementation Notes` section.
Out of scope: this file's other sections; any other file.

## Assumptions
Confirmed 20260919 (`plan-to-implementation-procedure` Step 3a): this file's
`## Implementation Notes` section contains exactly 2 real bullets (beyond the standard
boilerplate intro/outro):
1. WAL mode — `PRAGMA journal_mode=WAL` on all connections.
2. Checkpoint mode — the `sqlite_wal_checkpoint_mode` config key, default `TRUNCATE`.

## Design decisions
Per the Decision Categories table: both bullets are "Default values of configuration
settings (if verifiable in code)" — the canonical `Delete or Compress Normally` example
in `docs/00_governance_02_documentation-metadata.md`. Neither bullet states *why* WAL
mode or `TRUNCATE` checkpointing was chosen (that rationale, if it exists, would already
live in `## Rationale`) — these two bullets are pure current-configuration restatement,
the textbook `Delete`/`Compress` case. Verify against `## Rationale` before deleting: if
the "why" is genuinely absent from `## Rationale` too, the deletion is still correct (the
"why" belongs in Rationale, not Implementation Notes — its absence there is a possible
Known Issue only if a design document elsewhere already promised a rationale exists,
which is not expected here).

## Alternatives considered
N/A: the classification mechanism is fixed by REQ-001 — no alternative scheme applies.

## Implementation
### Target file
docs/adr/ADR-008-sqlite-4db-separation.md

### Procedure
1. Read `## Rationale` to confirm it does not already restate these 2 config defaults
   (if it does, this Implementation Notes copy is doubly confirmed as pure duplication).
2. Delete or compress both bullets per the Design decisions reasoning — these are
   config-default restatements verifiable directly from `scripts/db/config.py`/
   `config/agent.toml`, not design rationale.
3. Re-run the Validation plan's checkers.

### Method
`Edit` tool — direct text edit within `## Implementation Notes`.

### Details
Do not invent a "why" and add it to `## Rationale` as part of this row — if no rationale
for WAL mode/TRUNCATE checkpointing exists anywhere in this ADR, that is out of scope for
this row (a documentation-content gap, not an Implementation Notes misclassification);
simply remove the two config-default bullets from Implementation Notes.

## Compatibility considerations
Only `## Implementation Notes` within this file is affected.

## Security considerations
N/A: documentation-only, no credentials or runtime behavior change.

## Rollback considerations
`git checkout -- docs/adr/ADR-008-sqlite-4db-separation.md` reverts this row
independently.

## Validation plan
- `uv run python tools/check_docs_quality.py` — confirm no new finding for this file.
- `uv run python tools/check_docs_structure.py` — confirm no new finding for this file.
- `uv run python tools/check_adr_structure.py` — confirm no new finding for this file.

## Completion criteria
Both bullets are classified (expected: `Delete`/`Compress`) and removed or shortened;
the 3 checkers above report no new finding for this file.

## Out of scope
This file's other sections beyond `## Implementation Notes`; adding a new rationale for
WAL mode/checkpoint mode if one is currently absent from `## Rationale`; any other ADR or
design doc.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Classify and apply action for 2 real bullets (expected: Delete/Compress) |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: documentation-only, no test to add |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | check_docs_quality.py, check_docs_structure.py, check_adr_structure.py |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: this document's own Target file IS the documentation being updated |

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
- **Requirement ID**: REQ-001, REQ-003 (classify 2 real bullets; apply action)
- **Source issue**: issues/20260919-193722_impln01_audit-and-reclassify-docs-implementation-notes-items-per-existing-decision-categories.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260919-194628_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260919-195506
- **Related target files**: docs/adr/ADR-008-sqlite-4db-separation.md
