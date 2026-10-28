# Procedure: state the authority model and the failed-inline-promotion behavior for DLQ state

## Goal

Record that `events.dlq_at` in SQLite is the DLQ authority and the DLQ file is derived, describe the failed-inline-promotion case, and align the sweep wording (Plan REQ-001, REQ-002, REQ-007).

## Scope

- Modify only `docs/24_eventbus/eventbus_03_dlq_operations.md`.
- Documentation-only change; state current behavior only.

## Assumptions

- The code procedures of this Plan (`seq` 01 and 02) have landed before the test procedures run.
- All text stays English (`skills/DESIGN.md` Output language).
- Overlap (compatible): `plans/done/20261028-092616_ebauth001_enforce-pairwise-consumer-authorization.md` (archived, procedures pending) also targets `scripts/eventbus/ack_route.py` (authorization at the start of the routes) and `docs/24_eventbus/eventbus_12_ack_nack_endpoints.md` (Authentication section and error table); this procedure edits only the promotion block of `_nack_and_promote` and one transition-table row.

## Design decisions

- Edit the named sentences after re-reading the current text; do not reflow surrounding paragraphs.

## Alternatives considered

N/A: lightweight row.

## Implementation

### Target file

`docs/24_eventbus/eventbus_03_dlq_operations.md`

### Procedure

- In `## DLQ Promotion Paths`, after the sentence about the shared routine, add: SQLite `events.dlq_at` is the authoritative DLQ state; the JSON file is a derived artifact written first and made visible by setting `dlq_at`.
- In the same section add the failed-inline-promotion case: a NACK is committed before promotion; if the inline file write fails the event stays live (`dlq_at` NULL), the metric `eventbus_dlq_file_write_failure_total` increments and the next sweep promotes the event.
- In `## DLQ Background Sweep`, replace the wording that treats a non-zero sweep count as an inline-promotion problem with: the sweep is the repair path; a non-zero count is expected after a crash or a failed file write.
- In `## DLQ Reconciliation`, add that a persistent file-write failure for one event does not block the others.
- Check the `Missing Files` recovery advice that mentions rebuilding from the JSONL archive against the best-effort status of JSONL stated in the publish durability document, and align or caveat it (UNK-02 in the Plan).

### Method

Targeted sentence edits after re-reading the current file state.

### Details

- The authority statement matches ADR-006 INV-01 (SQLite canonical), INV-08 and INV-13; no ADR edit is made.

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
- **Requirement ID**: REQ-001, REQ-002, REQ-007 (authority model; committed NACK with failed promotion; sweep wording)
- **Source issue**: issues/20261027-155846_ebdurable003_define-publish-dlq-durability.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261028-093155_ebdurable003_define-publish-dlq-durability.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261028-115345
- **Related target files**: docs/24_eventbus/eventbus_03_dlq_operations.md
