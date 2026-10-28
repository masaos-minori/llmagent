# Procedure: describe ACK/NACK pair authorization and the 403 cases

## Goal

Replace the `Principal.allowed_consumer_ids` wording and add the event-topic check and status codes (Plan REQ-008).

## Scope

- Modify only `docs/24_eventbus/eventbus_12_ack_nack_endpoints.md`.
- Documentation-only change; state current behavior only (no history of the old model).

## Assumptions

- The implementation rows of this Plan have landed, so the text describes shipped behavior.
- All text stays English (`skills/DESIGN.md` Output language).
- Overlap (compatible): `plans/20261028-093155_ebdurable003_define-publish-dlq-durability.md` also targets `scripts/eventbus/ack_route.py` and `docs/24_eventbus/eventbus_12_ack_nack_endpoints.md`; it edits the promotion block of `_nack_and_promote` and one transition-table row, which this procedure does not touch. `plans/20261028-092928_ebshutdown002_close-shutdown-admission-race.md` also targets `scripts/eventbus/app.py` (`_shutdown_lifespan` only).

## Design decisions

- Edit the named sentences after re-reading the current text; do not reflow the surrounding paragraphs.

## Alternatives considered

N/A: lightweight row.

## Implementation

### Target file

`docs/24_eventbus/eventbus_12_ack_nack_endpoints.md`

### Procedure

- In the Authentication section, replace the `Principal.allowed_consumer_ids` sentence with: the caller must hold a grant for the requested `consumer_id` on the topic of the event being acknowledged.
- In the error table, change the `consumer_id` outside the caller's authorization 403 rows to "consumer_id or event topic outside the caller's grants" (both the ACK and the NACK table).
- Do not edit the transition table; another Plan adds a row there.

### Method

Targeted sentence edits after re-reading the current file state.

### Details

- Overlap with the DLQ-durability Plan is limited to the transition table, which this row does not touch.

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

- The document states the pairwise grant model and the behavior described in Details.
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
- **Requirement ID**: REQ-008 (ACK/NACK doc consistency)
- **Source issue**: issues/20261027-155843_ebauth001_enforce-pairwise-consumer-authorization.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261028-092616_ebauth001_enforce-pairwise-consumer-authorization.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261028-114911
- **Related target files**: docs/24_eventbus/eventbus_12_ack_nack_endpoints.md
