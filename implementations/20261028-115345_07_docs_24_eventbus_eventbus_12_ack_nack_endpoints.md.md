# Procedure: add the failed-inline-promotion row to the transition table

## Goal

Add one row to the ACK/NACK State Transition Table for a NACK whose inline promotion file write fails (Plan REQ-004).

## Scope

- Modify only `docs/24_eventbus/eventbus_12_ack_nack_endpoints.md`.
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

`docs/24_eventbus/eventbus_12_ack_nack_endpoints.md`

### Procedure

- In `## ACK/NACK State Transition Table`, after the `Initial NACK` row, add: `Initial NACK, inline DLQ file write failed | 200 (no dlq_promoted) | Per-consumer failure count increases; the event stays live and the next sweep promotes it`.
- Do not edit the Authentication section or the error tables.

### Method

Targeted sentence edits after re-reading the current file state.

### Details

- The Authentication section and error tables are edited by the pairwise-authorization procedures of another Plan; this row touches only the transition table.

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
- **Requirement ID**: REQ-004 (transition table documents the 200 without dlq_promoted)
- **Source issue**: issues/20261027-155846_ebdurable003_define-publish-dlq-durability.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261028-093155_ebdurable003_define-publish-dlq-durability.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261028-115345
- **Related target files**: docs/24_eventbus/eventbus_12_ack_nack_endpoints.md
