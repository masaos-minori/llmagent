## Goal

Amend the decision text of ADR-008 for the migration contract and record the approval, without a silent edit (`REQ-008`, approval record; `REQ-009`, registered upgrades preserve rows).

## Scope

- Modify only `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md`.

## Assumptions

- Verified (Step 3a): ADR-008 states under Context/Decision that the four databases have no migration mechanism and are recreated on a schema change, and has Decision Details, Consequences, and Operational Consequences sections.
- Ordering (Plan Dependencies, owner-confirmed in this cycle): `plans/20261029-214650_adrauth001_adr-authority-model.md` lands before this row; `config/adr_authority.toml`'s ADR-008 primary claim is unchanged. Execute this row after code phases 1-5 and after adrauth001, rebasing on `HEAD` first (Plan Risks: ADR-008 churn).
- `tools/check_adr_preservation.py` compares against `HEAD`: an intentional decision change reports ERROR/WARNING by design; record the approval instead of silencing it. Write in English; state intent, boundaries, constraints, and failure behavior only, not implementation detail (`skills/DESIGN.md` Docs content policy). Edit only the sections named below (`docs/00_index.md` task scope: DB layer spec and the ADR index).
- Names that `tools/stale_detector.py` flags in this document are created by other rows of this Plan (the framework row 01 and the domain, drill, and schema rows it names) and exist when `code-implementation` executes the rows in Plan phase order.

## Design decisions

- Add a dated amendment record to the Status section and update Decision Details: `workflow` and `eventbus` upgrade through an ordered forward-only migration behind a verified backup; unregistered paths keep the refusal; `rag` and `session` keep the recreate policy.

## Alternatives considered

- Replace the old text silently: rejected (REQ-008).

## Implementation

### Target file

`docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md`

### Procedure

1. Edit the Status section to add the amendment entry and approval note.
2. Edit Decision Details and the recreate-only statements in Context and Consequences to match; keep Alternatives unchanged and add the rejected alternative of permanent recreation if absent.

### Method

- Keep Front Matter and `related:` unchanged unless a new document is referenced.

### Details

- Preserve invariants and test citations (`tools/check_adr_preservation.py`); only the migration decision text changes.

## Compatibility considerations

- Governance record; other ADRs referencing ADR-008 remain valid.

## Security considerations

- N/A: documentation.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run python tools/check_docs_quality.py`
- `uv run python tools/check_docs_structure.py`
- `uv run python tools/check_docs_content_policy.py`
- `uv run python tools/check_docs_japanese.py`
- `uv run python tools/check_docs_consistency.py --domain deployment`
- `uv run python tools/check_adr_preservation.py` (expected findings limited to the amended decision text)
- `uv run python tools/check_needs_confirmation_inventory.py`

## Completion criteria

- ADR-008 states the migration contract and carries a dated approval record; the checkers above report no new findings other than the intended decision-text deltas.

## Out of Scope

- Code changes; the ADR index row (row 21).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit the ADR per Procedure | Pending | — | — | Plan Phase 6; after adrauth001 and code phases 1-5 |
| 2 | Run the documentation checkers (`routing.md` Tools) | Pending | — | — |  |

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
- **Requirement ID**: REQ-008, REQ-009
- **Source issue**: issues/20261029-104500_dbmig001_forward-only-db-migrations.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261029-214108_dbmig001_forward-only-db-migrations.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-151746
- **Related target files**: docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md
