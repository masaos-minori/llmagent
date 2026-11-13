## Goal
Remove `dlq_requeue_count` from the `/dlq` item description so the endpoint doc matches the response after REQ-004 (REQ-006 / AC-6).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The frozen-table anchor (line 32) is current as of the 2026-11-13 revalidation; locate the sentence by its quoted text.
- Run after rows 05 (`20261113-173721_05_scripts_eventbus_event_repo.py.md`) so the doc never describes a field the query no longer selects.

## Design decisions
- The sentence lists what each item carries; removing the field from the list is the whole edit — no other `/dlq` behavior text changes (ordering, pagination envelope, request-local consistency all stay).

## Alternatives considered
- Rewriting the whole Behavior section: rejected — only one listed field is removed; everything else matches the current `fetch_dlq` output after row 05.

## Implementation
### Target file
`docs/24_eventbus/eventbus_04_dlq_endpoint.md`

### Procedure
1. Behavior section (line 32): replace
   `Each item carries event identity, \`dlq_at\` (the time the event was promoted to the DLQ) and \`dlq_requeue_count\`.`
   with
   `Each item carries event identity and \`dlq_at\` (the time the event was promoted to the DLQ).`

### Method
- Text-anchored single-sentence edit; no heading or list renumbering.

### Details
- No other `dlq_requeue_count` mention exists in this file (verified 2026-11-13).

## Compatibility considerations
- `docs/00_index.md`-scoped docs checkers apply; `stale_detector.py` must find no dead reference after the edit.

## Security considerations
N/A: documentation-only change.

## Rollback considerations
N/A: revert the commit.

## Validation plan
| Target | Testing strategy | Tool / command | Expected outcome |
|---|---|---|---|
| Doc staleness | Docs | `uv run python tools/stale_detector.py docs/24_eventbus/eventbus_04_dlq_endpoint.md` | No findings |
| Field removal | Search | `rg -n "dlq_requeue_count" docs/24_eventbus/eventbus_04_dlq_endpoint.md` | No match |

## Completion criteria
- AC-6 for `eventbus_04`: the item description matches the post-REQ-004 `/dlq` response.

## Out of Scope
- The Requeue subsection of this file (already lineage-based), `dlq_route.py` parameter bounds, other `docs/24_eventbus/*.md` files.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: REQ-006 / AC-6
- **Source issue**: issues/20261110-170926_rmcompat005_eventbus-dlq-leftovers.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261112-121134_rmcompat005_eventbus-dlq-leftovers.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261113-173721
- **Related target files**: `docs/24_eventbus/eventbus_04_dlq_endpoint.md`
