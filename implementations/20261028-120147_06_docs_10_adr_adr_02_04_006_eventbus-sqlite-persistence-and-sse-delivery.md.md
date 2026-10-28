# Procedure: record database enforcement in the ADR-006 implementation notes

## Goal

State in Implementation Notes that the database enforces uniqueness of the redelivery source (Plan REQ-006).

## Scope

- Modify only `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`.
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

`docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`

### Procedure

- In `## Implementation Notes`, add one or two sentences: `events.redelivered_from` carries a partial unique index, so the database guarantees at most one redelivery descendant per original event; a violation is reported as the typed `already_redelivered` result.
- Do not change `## Decision`, the Invariants list or the Verification tables, and add no new invariant (that needs owner approval).
- Run `uv run python tools/check_adr_preservation.py` after the edit; it must report no ERROR.

### Method

Targeted sentence edits after re-reading the current file state.

### Details

- The Verification table of this ADR is edited by another Plan; keep this edit inside Implementation Notes.

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
- **Requirement ID**: REQ-006 (ADR-006 notes; no Decision or Invariant change)
- **Source issue**: issues/20261027-155850_ebdlqunique007_enforce-dlq-redelivery-uniqueness.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261028-094441_ebdlqunique007_enforce-dlq-redelivery-uniqueness.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261028-120147
- **Related target files**: docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md
