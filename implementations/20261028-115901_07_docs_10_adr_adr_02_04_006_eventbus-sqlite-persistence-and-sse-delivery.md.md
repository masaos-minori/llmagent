# Procedure: correct the two stale test names in the ADR-006 verification table

## Goal

Rename the two cited test methods to their current names (Plan REQ-002).

## Scope

- Modify only `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`.
- Documentation-only change; state current behavior only.

## Assumptions

- The renamed tests exist (they carry `consumer_delivery_failure_count` in their names today).
- Overlap (compatible): `plans/20261028-094441_ebdlqunique007_enforce-dlq-redelivery-uniqueness.md` edits only the ADR-006 Implementation Notes, while this Plan edits ADR-006's Verification table. Any citation added by that Plan must resolve to an existing test node once the node validation of this Plan is in force.

## Design decisions

- Edit the named sentences after re-reading the current text; do not reflow surrounding paragraphs.

## Alternatives considered

N/A: lightweight row.

## Implementation

### Target file

`docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`

### Procedure

- In the row "NACK counters and requeue counters are persisted per Event" (INV-08), replace `test_nack_increments_delivery_failure_count` (new) with `test_nack_increments_consumer_delivery_failure_count` (new) and `test_dlq_requeue_increments_dlq_requeue_count_not_delivery_failure_count` (new) with `test_dlq_requeue_increments_dlq_requeue_count_not_consumer_delivery_failure_count` (new); both live in `tests/eventbus/test_eventbus_dlq_promotion.py::TestDLQPromotionSemantics`.
- Confirm with `rg -n "def test_nack_increments_consumer_delivery_failure_count|def test_dlq_requeue_increments_dlq_requeue_count_not_consumer" tests/eventbus/test_eventbus_dlq_promotion.py`.
- Do not edit any other text; the Implementation Notes of this ADR are edited by another Plan.

### Method

Targeted sentence edits after re-reading the current file state.

### Details

- Only the cited identifiers change.

## Compatibility considerations

N/A: documentation-only.

## Security considerations

N/A: documentation-only.

## Rollback considerations

N/A: revert the commit.

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| 1 | `uv run python tools/check_docs_quality.py`; `uv run python tools/check_docs_structure.py`; `uv run python tools/check_docs_content_policy.py --strict`; `uv run python tools/check_docs_japanese.py`; `uv run python tools/check_docs_consistency.py --domain governance` | No finding |

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
- **Requirement ID**: REQ-002 (stale citations)
- **Source issue**: issues/20261027-155848_adrgate005_enforce-adr-evidence-checks.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261028-093931_adrgate005_enforce-adr-evidence-checks.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261028-115901
- **Related target files**: docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md
