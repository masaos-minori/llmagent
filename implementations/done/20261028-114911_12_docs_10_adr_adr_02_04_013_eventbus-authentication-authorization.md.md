# Procedure: describe pairwise grants in ADR-013 implementation notes

## Goal

State the pairwise (consumer_id, topic) grant model and the omitted-topic behavior in ADR-013's Implementation Notes (Plan REQ-008).

## Scope

- Modify only `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`.
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

`docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`

### Procedure

- Add one or two sentences to `## Implementation Notes`: a Consumer principal holds explicit (consumer_id, topic) grants built from `consumer_authorization` and `topic_authorization`; an unlisted pair returns HTTP 403; a subscribe request without `topic` is narrowed to the topics granted to its `consumer_id`.
- Leave `## Decision`, Decision Details, Invariants and the verification tables untouched.

### Method

Targeted sentence edits after re-reading the current file state.

### Details

- INV-02 and INV-07 already require explicit consumer_id and topic authorization; the added text records how it is represented, not a new rule.
- Run `uv run python tools/check_adr_preservation.py` after the edit; it must report no ERROR.

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
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261028-130500 | 20261028-130500 | Out-of-scope support: tests/eventbus/eventbus_helpers.py TEST_TOPICS, test_eventbus_crash_ack.py and test_eventbus_dlq_pagination.py consumer_authorization |
| 2 | Run the documentation checkers named in `routing.md` Tools "When to run which tool" | Completed | 20261028-130500 | 20261028-130500 |  |

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
- **Requirement ID**: REQ-008 (ADR consistency, non-Decision text only)
- **Source issue**: issues/20261027-155843_ebauth001_enforce-pairwise-consumer-authorization.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261028-092616_ebauth001_enforce-pairwise-consumer-authorization.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261028-114911
- **Related target files**: docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md