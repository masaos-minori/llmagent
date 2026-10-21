## Goal
Update the `Offset Seeding` paragraph of `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md` so it states that the service keeps the legacy offset files and points to the end condition and retention rule, consistent with the supported baseline of section 8e (REQ-001).

## Scope
- In: the `Offset Seeding` paragraph under section 9, one added sentence.
- Out: section 8e and every other section; the EventBus documents (rows 01 and 02); any code.

## Assumptions
- Row 01 of the compat002 plan adds the `Legacy Offset Files` section to `eventbus_07_configuration-and-operations.md` first, so the link target exists.
- Section 8e (added by the compat001 change) already defines the supported baseline.
- The document is 15764 B (plus the compat001 section), under the 24576 B limit.

## Design decisions
- Append one sentence rather than restating the rules; the operations document is the single place for the end condition and retention.

## Alternatives considered
N/A: one-sentence pointer by design.

## Implementation
### Target file
`docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md`

### Procedure
1. Append the sentence below to the end of the `Offset Seeding` paragraph (after "It does not modify or delete the offset files.").
2. Run the documentation checkers.

### Method
Sentence to append: "The service keeps the files; the end condition of the import, the retention rule, and the owner are in [EventBus configuration and operations](../24_eventbus/eventbus_07_configuration-and-operations.md#legacy-offset-files), and the supported baseline is in section 8e."

### Details
- The paragraph already says the import is idempotent and leaves the files untouched; do not repeat it.

## Compatibility considerations
N/A: documentation only.

## Security considerations
N/A: documentation only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_quality.py`, `check_docs_structure.py` (the link must resolve), `check_docs_content_policy.py --strict`, `check_docs_japanese.py`, `check_needs_confirmation_inventory.py`, `check_db_separation.py`.

## Completion criteria
- The paragraph points to the end condition, retention rule, and baseline (AC-1).
- The listed checkers pass (AC-5).

## Out of Scope
- Editing section 8e or any other paragraph.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Append the pointer sentence to `Offset Seeding` (REQ-001) | Completed | 20261021-101955 | 20261021-102013 | Changed: docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md (Offset Seeding pointer sentence) |
| 2 | Run the documentation checkers (REQ-005) | Completed | 20261021-101955 | 20261021-102013 | check_docs_quality, check_docs_structure, check_docs_content_policy --strict, check_docs_japanese, check_needs_confirmation_inventory, check_db_separation all exit 0; no scripts/, tests/, config/ change. Docs-only: no test run. |

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
- **Requirement ID**: `REQ-001` (offset seeding notes consistent with the baseline), `REQ-005` (checkers pass)
- **Source issue**: `issues/20261020-122817_compat002_define-the-end-condition-and-retention-policy-for-the-eventbus-legacy-offset-import.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261020-233641_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261021-101632
- **Related target files**: `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md`