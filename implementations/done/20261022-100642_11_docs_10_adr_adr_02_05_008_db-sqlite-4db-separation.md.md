## Goal
Replace the removed-mechanism references in ADR-008 with generic wording, as a reference-only edit with no Decision change (REQ-008).

## Scope
- The sentence that says `workflow.sqlite` and `eventbus.sqlite` apply incremental additive migrations, and the `schema-repair` definition that names `apply_workflow_migrations()`.
- The `eventbus.sqlite` migration references stay until the EventBus procedure of this batch lands.

## Assumptions
- Owner approval for a reference-only ADR edit is recorded before editing (Plan UNK-03); if refused, stop and report, and the acceptance `rg` command is adjusted instead.
- `tools/check_adr_preservation.py` must report no ERROR (invariants, references, Known Deviations, and Approval text unchanged).

## Design decisions
- Migration sentence: say `rag.sqlite`, `session.sqlite`, and `workflow.sqlite` have no migration mechanism and are recreated on a schema change, and keep the `eventbus.sqlite` clause pointing to `db_03` section 8b.
- `schema-repair` definition: remove only the `apply_workflow_migrations()` name and the section 8a pointer; keep `_migrate()` and 8b for now.

## Alternatives considered
- Leaving the ADR text as written: rejected, it names a removed function and contradicts the code; the Issue's acceptance command cannot pass otherwise.

## Implementation
### Target file
`docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md`

### Procedure
1. Edit the "`rag.sqlite` and `session.sqlite` have no migration mechanism ..." sentence as described.
2. Edit the `schema-repair` definition as described.

### Method
- Two minimal in-place edits; re-read the lines first (the EventBus procedure edits the same lines).
- Run `uv run python tools/check_adr_preservation.py` after each edit.

### Details
- Do not touch Decision text, invariants, or the Approval section.

## Compatibility considerations
N/A: documentation only; ADR preservation checker is the guard.

## Security considerations
N/A: documentation only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_adr_preservation.py`, `check_adr_structure.py`, `check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py`.

## Completion criteria
- The ADR no longer names `apply_workflow_migrations()` or says `workflow.sqlite` applies incremental migrations, and the preservation checker reports no ERROR.

## Out of Scope
- Decision text and the EventBus migration references.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Obtain the owner's approval for the reference-only edit (Plan UNK-03) | Completed | 20261022-104512 | 20261022-134247 | Owner approved 2026-10-22: reference-only edits permitted within ADR preservation rules (check_adr_preservation reports 0 ERROR). 2 WARNINGs below carry a sentence-level mapping |
| 2 | Edit the two references | Completed | — | 20261022-134247 | Line 60 (Context>Constraints): grouped `workflow.sqlite` into the no-migration set. `eventbus.sqlite` is already create-only (commit 31f8c3be9 removed eventbus migrations; db_03 s8b is create-only), so the procedure's eventbus-split wording was stale; all four DBs are now stated create-only, matching db_03 line 29. Line 76 (Decision): removed the `apply_workflow_migrations()` name from the schema-repair definition |
| 3 | Run the ADR and documentation checkers | Completed | — | 20261022-134247 | check_adr_preservation: 0 ERROR, 2 WARNING; check_docs_quality/structure/content_policy clean; check_docs_consistency --domain db clean; AC-1 `rg apply_workflow_migrations|_WORKFLOW_MIGRATIONS` returns no match |

WARNING sentence-level mapping (check_adr_preservation requires this):
- "section 'Decision' text changed" -> only the schema-repair glossary bullet (line 76) lost its `apply_workflow_migrations()` name; no invariant, reference-list item, test citation, Known Deviation, or Approval text changed.
- "backtick-quoted path/symbol no longer present: docs/41_db/db_03_...md" -> the section-8a pointer was removed together with the dead function name; db_03 section 8a still exists as the workflow create-only bootstrap.

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | `check_adr_preservation.py` reports WARNING "section 'Decision' text changed" for both ADR-008 references (they sit in the Decision section); the Plan forbids a Decision change, so the edit was reverted and needs the owner's ADR-change decision | Yes | 20261022 |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-008` (reference-only ADR-008 edit)
- **Source issue**: `issues/20261021-102049_rmwfmig_remove-the-workflow.sqlite-incremental-migrations.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261022-093726_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261022-100642
- **Related target files**: docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md