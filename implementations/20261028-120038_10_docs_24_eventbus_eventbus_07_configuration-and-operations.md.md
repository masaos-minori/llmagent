# Procedure: correct the slow-consumer metric name and point readiness at the contract

## Goal

Replace `eventbus_slow_consumer_total` with `eventbus_slow_consumer_current` and link the readiness text to the health contract (Plan REQ-007).

## Scope

- Modify only `docs/24_eventbus/eventbus_07_configuration-and-operations.md`.
- Documentation-only change; state current behavior only.

## Assumptions

- The tests-first rows (seq 05 and 06) have been written and fail on the unmodified code before the source rows are applied (ordering note).
- All text stays English (`skills/DESIGN.md` Output language).
- Overlap (compatible): `plans/done/20261028-092928_ebshutdown002_close-shutdown-admission-race.md` (archived, procedures pending) also targets `scripts/eventbus/route_helpers.py` (a post-lock shutdown re-check placed right after lock acquisition and before the active-user bump) and `docs/24_eventbus/eventbus_07_configuration-and-operations.md` (Shutdown section). This procedure changes the timing statements around the lock and the Metrics section; whichever lands first, re-read the file and keep the other's lines.

## Design decisions

- Edit the named sentences after re-reading the current text; do not reflow surrounding paragraphs.

## Alternatives considered

N/A: lightweight row.

## Implementation

### Target file

`docs/24_eventbus/eventbus_07_configuration-and-operations.md`

### Procedure

- In the Metrics section, replace the name `eventbus_slow_consumer_total` with `eventbus_slow_consumer_current` and describe it as a gauge.
- Where the operations text mentions the deployment readiness gate, say it follows the `liveness and readiness` contract in the health endpoint document.
- Do not edit the Shutdown section (another Plan edits it).

### Method

Targeted sentence edits after re-reading the current file state.

### Details

- The metric `eventbus_slow_consumer_total` does not exist in `broker.py`; the doc named a metric that is never exported.

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
- **Requirement ID**: REQ-007 (operations doc)
- **Source issue**: issues/20261027-155849_ebmetrics006_correct-db-timing-health.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261028-094217_ebmetrics006_correct-db-timing-health.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261028-120038
- **Related target files**: docs/24_eventbus/eventbus_07_configuration-and-operations.md
