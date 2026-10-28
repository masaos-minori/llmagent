# Procedure: state the index, version 2 and the recreate procedure in the schema document

## Goal

Document the unique index, schema version 2 and the operator procedure for recreating `eventbus.sqlite` (Plan REQ-003, REQ-006).

## Scope

- Modify only `docs/24_eventbus/eventbus_06_persistence_schema_and_replay.md`.
- Documentation-only change; state current behavior only.

## Assumptions

- The tests-first rows (seq 03 to 05) have been written and fail on the unmodified code before the source rows are applied (ordering note).
- All text stays English (`skills/DESIGN.md` Output language).
- Overlap (compatible): `plans/done/20261028-093931_adrgate005_enforce-adr-evidence-checks.md` (archived, procedures pending) also targets the ADR-006 file; it renames two stale test citations in the Verification table while this procedure edits Implementation Notes only. Any citation added here must resolve to an existing test node once that Plan's node validation is in force.

## Design decisions

- Edit the named sentences after re-reading the current text; do not reflow surrounding paragraphs.

## Alternatives considered

N/A: lightweight row.

## Implementation

### Target file

`docs/24_eventbus/eventbus_06_persistence_schema_and_replay.md`

### Procedure

- In `## Schema`, add: `events.redelivered_from` has a partial unique index, so the database enforces uniqueness of the redelivery source.
- In the same section, state that the schema version is 2 and a database stamped with another version is refused at startup and must be recreated (no migration).
- Add an operator procedure: back up `eventbus.sqlite`; check for duplicate descendants with a read-only query (`SELECT redelivered_from, COUNT(*) FROM events WHERE redelivered_from IS NOT NULL GROUP BY redelivered_from HAVING COUNT(*) > 1;`); stop and report any row; recreate the database with `deploy/init_db.sh`; restart the service.

### Method

Targeted sentence edits after re-reading the current file state.

### Details

- Keep the language factual and current-state only (`skills/DESIGN.md` Docs content policy).

## Compatibility considerations

N/A: documentation-only.

## Security considerations

N/A: documentation-only.

## Rollback considerations

N/A: revert the commit.

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| 1 | `uv run python tools/check_docs_quality.py`; `uv run python tools/check_docs_structure.py`; `uv run python tools/check_docs_content_policy.py --strict`; `uv run python tools/check_docs_japanese.py`; `uv run python tools/check_docs_consistency.py --domain eventbus` | No finding |

## Completion criteria

- The document states the behavior described in Details.
- All listed documentation checkers report no finding.

## Out of Scope

- Every other document.
- Code changes.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Run the documentation checkers named in `routing.md` Tools "When to run which tool" | Pending | — | — | |

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
- **Requirement ID**: REQ-003, REQ-006 (schema doc and operator procedure)
- **Source issue**: issues/20261027-155850_ebdlqunique007_enforce-dlq-redelivery-uniqueness.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261028-094441_ebdlqunique007_enforce-dlq-redelivery-uniqueness.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261028-120147
- **Related target files**: docs/24_eventbus/eventbus_06_persistence_schema_and_replay.md
