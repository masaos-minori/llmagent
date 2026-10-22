## Goal
Remove the legacy-import statements and the import's open decisions from the EventBus semantics document, keeping the file-based-helper decision and the single-resume-source statement (REQ-003).

## Scope
- The sentence in the collision paragraph about the legacy offset-file migration, the sentence in the offset-storage paragraph about the startup migration seeding `consumer_offsets`, and the section "Legacy Offset Import: Open Decisions".

## Assumptions
- After the code change the service never reads offset files; `consumer_offsets` is the only resume source.
- The "File-based helpers" bullet states a decision that stays undecided by this change (its removal is a separate question) and is therefore not moot; the other three bullets (collision handling, completion marker, commit behavior) are moot.
- Inbound anchors: `eventbus_07` links to the heading `#legacy-offset-import-open-decisions`; that link is removed by the `eventbus_07` procedure.

## Design decisions
- Keep one retained open decision about the file-based `write_offset()` / `read_offset()` helpers (they have no production caller); fold it into a short subsection (for example "File-Based Offset Helpers") or a note in the offset-storage text, owner the EventBus service; drop the old heading.
- Offset-storage paragraph: remove the migration sentence and the "After the import" wording; state that `consumer_offsets` is the only source of a consumer's resume position and the service does not read offset files.

## Alternatives considered
- Deleting the helper decision together with the section: rejected, the Issue states removal of the import does not decide helper removal.

## Implementation
### Target file
`docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md`

### Procedure
1. In the consumer-ID collision paragraph remove the sentence beginning "Separately, the legacy offset-file migration (`migrate_legacy_offsets()`) refuses ...".
2. In the offset-storage paragraph replace the "A one-time, idempotent startup migration seeds ..." and "After the import, ..." sentences with the single-resume-source statement and drop the link to the operations section's end condition.
3. Replace the section "Legacy Offset Import: Open Decisions" with the retained helper decision.

### Method
- Minimal in-place edits; no history wording and no counts.
- Re-read the file before editing (it has high churn).

### Details
- Keep the following subsections ("Explicit Ack-only Offset", "Resuming on Reconnection") unchanged.

## Compatibility considerations
N/A: documentation only.

## Security considerations
N/A: documentation only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py`; the anchor check if available.
- `rg "migrate_legacy_offsets|Legacy Offset Import" docs/24_eventbus` returns no match.

## Completion criteria
- No sentence describes the import or its open decisions; the helper decision remains once; no link points to a removed heading in this file; docs checkers pass.

## Out of Scope
- Other sections of the document.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit the two sentences and replace the open-decisions section | Completed | 20261022-114127 | 20261022-114127 | Changed: docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md |
| 2 | Run the documentation checkers named in `routing.md` Tools | Completed | 20261022-114127 | 20261022-114127 | validated; docs checkers pass; generate_reference_table --check passes; full suite 9686 passed |

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
- **Requirement ID**: `REQ-003` (remove import statements and moot open decisions; keep the helper decision)
- **Source issue**: `issues/20261021-102244_rmoffimp_remove-the-legacy-offset-import.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261022-094316_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261022-101417
- **Related target files**: docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md