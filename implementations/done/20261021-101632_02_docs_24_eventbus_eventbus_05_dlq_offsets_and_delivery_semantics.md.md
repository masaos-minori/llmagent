## Goal
Record in `docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md` that the database is authoritative after the legacy offset import and the files are never a resume source (REQ-001), and list the collision-handling, completion-marker, commit-behavior, and helper-removal decisions as open decisions with an owner (REQ-003).

## Scope
- In: the `Consumer Offset` paragraph (the sentence about the startup migration and the "retention period"), and one new subsection `Legacy Offset Import: Open Decisions` directly after it.
- Out: `Offset Semantics`, `Resume Behavior`, the ACK/NACK rules, any code, the other two documents.

## Assumptions
- Facts to state, all verified 2026-10-21: the import never modifies or deletes the files; two files without a `.map` companion whose names sanitize to the same consumer ID make the function raise, and the startup logs it and continues; the function never calls `commit()` (a test run showed the connection still holding an open transaction and the rows invisible to a second connection); `write_offset()`/`read_offset()` have no production caller; there is no completion marker.
- The existing sentence refers to a "retention period" that no document defines; the retention rule now lives in the EventBus operations document.
- The document is 18238 B, under the 24576 B limit with room for about 6 KB.

## Design decisions
- Keep the authority rule in the existing paragraph (one place readers already look) and put the decisions in a short list, not prose.
- Mark every decision "moot if the import is removed", because the follow-up issue removes it.

## Alternatives considered
N/A: the Plan fixes this document for authority and the open decisions.

## Implementation
### Target file
`docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md`

### Procedure
1. In the `Consumer Offset` paragraph, replace the clause "which remains in place (not deleted) during the retention period." with the text below.
2. Insert the new subsection directly after that paragraph, before `### Explicit Ack-only Offset`.
3. Run the documentation checkers.

### Method
Replacement clause: "which the service never modifies or deletes. After the import, `consumer_offsets` is the only source of a consumer's resume position and the files are never read for resume. The end condition, retention rule, and owner are in [Legacy Offset Files](eventbus_07_configuration-and-operations.md#legacy-offset-files)."

New subsection:

```markdown
### Legacy Offset Import: Open Decisions

Owner: the EventBus service. Each item is moot if the import is removed.

- **Collision handling:** two legacy files without a `.map` companion whose names sanitize to the same consumer ID make the import raise; startup logs the failure and continues, and the rest of the import is skipped. Whether a collision should stop startup is undecided.
- **Completion marker:** none exists; the import runs on every start. Whether it should stop once a completion condition holds is undecided.
- **Commit behavior:** the import does not commit its inserts; they become durable through a later commit on the same connection. A restart before that commit loses them, and the retained files are imported again on the next start. Whether the import should commit explicitly is undecided.
- **File-based helpers:** `write_offset()` and `read_offset()` have no production caller. Whether they are removed together with the import is undecided.
```

### Details
- Anchor `#legacy-offset-import-open-decisions` is linked from row 01; keep the heading text exact.
- The sentence must not contradict ADR-006 (`docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`, read only); re-read its offset statements before finishing.
- Do not write the word "Needs confirmation".

## Compatibility considerations
N/A: documentation only.

## Security considerations
N/A: documentation only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py --strict`, `check_docs_japanese.py`, `check_docs_consistency.py --domain overview`, `check_needs_confirmation_inventory.py`.
- `rg "retention period" docs/24_eventbus` returns no match after the edit.

## Completion criteria
- The authority rule is stated and links to the operations document (AC-1).
- The four decisions are listed as open decisions with an owner (AC-3).
- The listed checkers pass (AC-5).

## Out of Scope
- Deciding any of the four items; changing code or tests; editing other sections.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Replace the retention clause and add the open-decisions subsection (REQ-001, REQ-003) | Completed | 20261021-101904 | 20261021-101946 | Changed: docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md (authority clause; subsection Legacy Offset Import: Open Decisions). ADR-006 offset statements re-read: no contradiction. |
| 2 | Run the documentation checkers and re-read ADR-006's offset statements (REQ-005) | Completed | 20261021-101904 | 20261021-101946 | check_docs_quality, check_docs_structure, check_docs_content_policy --strict, check_docs_japanese, check_docs_consistency --domain overview, check_needs_confirmation_inventory all exit 0; no 'retention period' text left. Docs-only: no test run. |

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
- **Requirement ID**: `REQ-001` (authority rule after import), `REQ-003` (open decisions), `REQ-005` (checkers pass)
- **Source issue**: `issues/20261020-122817_compat002_define-the-end-condition-and-retention-policy-for-the-eventbus-legacy-offset-import.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261020-233641_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261021-101632
- **Related target files**: `docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md`