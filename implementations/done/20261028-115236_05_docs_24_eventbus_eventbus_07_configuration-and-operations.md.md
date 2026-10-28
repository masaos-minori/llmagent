# Procedure: correct the Shutdown section for the queued-worker rule

## Goal

Fix step 3 of the Shutdown sequence ("with no worker queued on it") and add the queued-worker rule (Plan REQ-005).

## Scope

- Modify only `docs/24_eventbus/eventbus_07_configuration-and-operations.md`.
- Documentation-only change; state current behavior only.

## Assumptions

- The procedures with a lower `seq` of the same Plan have landed.
- All text stays English (`skills/DESIGN.md` Output language).
- Overlap (compatible): `plans/20261028-094217_ebmetrics006_correct-db-timing-health.md` also targets `scripts/eventbus/route_helpers.py` (timing statements around the lock acquisition) and `docs/24_eventbus/eventbus_07_configuration-and-operations.md` (Metrics section); `plans/20261028-092616_ebauth001_enforce-pairwise-consumer-authorization.md` (archived) targeted `scripts/eventbus/app.py` (ACK/NACK wiring only). This procedure edits the shutdown re-check, the shutdown state and the Shutdown section.

## Design decisions

- Edit the named sentences after re-reading the current text; do not reflow surrounding paragraphs.

## Alternatives considered

N/A: lightweight row.

## Implementation

### Target file

`docs/24_eventbus/eventbus_07_configuration-and-operations.md`

### Procedure

- In the Shutdown numbered list, rewrite step 3 so it says shutdown serializes behind any worker holding the lock by acquiring `get_db_lock()` (`_db_lock`), without claiming that no worker is queued.
- After the list, add a sentence: a worker that was admitted before shutdown but acquires the lock after the shutdown flag is set exits with the shutdown error and runs no SQL.
- After step 4, add: the shared connection reference is cleared once it is closed.
- Do not edit the Metrics section (another Plan edits it).

### Method

Targeted sentence edits after re-reading the current file state.

### Details

- The current text claims exclusive ownership "with no worker queued on it"; the code only acquires the lock, so the wording was stricter than the implementation.

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
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261028-153121 | 20261028-153121 |  |
| 2 | Run the documentation checkers named in `routing.md` Tools "When to run which tool" | Completed | 20261028-153121 | 20261028-153121 |  |

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
- **Requirement ID**: REQ-005 (Shutdown text matches behavior)
- **Source issue**: issues/20261027-155845_ebshutdown002_close-shutdown-admission-race.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261028-092928_ebshutdown002_close-shutdown-admission-race.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261028-115236
- **Related target files**: docs/24_eventbus/eventbus_07_configuration-and-operations.md