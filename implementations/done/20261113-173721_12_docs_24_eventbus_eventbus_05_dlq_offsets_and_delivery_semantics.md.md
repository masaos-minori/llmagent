## Goal
Remove the requeue-count audit-trail step from the Requeue (Redelivery) description so the delivery doc matches the lineage-only requeue write (REQ-006 / AC-6).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The frozen-table anchor (line 227) has drifted to line 231 in the current file (re-verified 2026-11-13); locate the step by its quoted text.
- rmcompat007 (which follows this plan) does not target this file; no concurrent-edit concern here.
- Run after rows 04 (`20261113-173721_04_scripts_eventbus_dlq_repo.py.md`) so the doc never describes a write the repository layer no longer performs.

## Design decisions
- The numbered step list keeps only the insert step; the following paragraph already states the one-requeue-per-original-event rule, which is the surviving single requeue fact (Plan Design), so no replacement text is needed.

## Alternatives considered
- Replacing the step with "Records the requeue through the new row's `redelivered_from`": rejected — the insert step already names `redelivered_from`; adding a restatement duplicates the fact (against the plan's intent of each fact stored and returned once).

## Implementation
### Target file
`docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md`

### Procedure
1. Requeue (Redelivery) section (line 231 region): delete the whole line
   `2. Increments \`dlq_requeue_count\` on the original row as audit trail.`
   leaving the numbered list with the single insert step (and its two sub-bullets) intact.

### Method
- Single-line deletion; no renumbering needed (the removed item is the last step).

### Details
- The paragraph after the list ("The original row keeps its `dlq_at`, so only one requeue succeeds per original event; a second requeue returns HTTP 409.") is unchanged; it is the doc-side counterpart of the preserved `dlq_at` guard asserted by the row 17 tests.

## Compatibility considerations
- `docs/00_index.md`-scoped docs checkers apply; `stale_detector.py` must find no dead reference after the edit.

## Security considerations
N/A: documentation-only change.

## Rollback considerations
N/A: revert the commit.

## Validation plan
| Target | Testing strategy | Tool / command | Expected outcome |
|---|---|---|---|
| Doc staleness | Docs | `uv run python tools/stale_detector.py docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md` | No findings |
| Field removal | Search | `rg -n "dlq_requeue_count" docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md` | No match |

## Completion criteria
- AC-6 for `eventbus_05`: the requeue description lists only the lineage insert.

## Out of Scope
- The Consumer Offset section and the delivery-state/`consumer_delivery_failure_count` descriptions (unchanged semantics; outside this plan's scope).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20261114-003323 | numbered step 2 line deleted; insert step + sub-bullets intact (verified in the requeue section) |
| 2 | Add or update tests per Validation plan | Completed | — | 20261114-003323 | no test changes (docs row) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261114-003324 | rg dlq_requeue_count no match; check_docs_consistency --domain eventbus No issues; stale_detector reports only the pre-existing /subscribe endpoint-path false positive (identical on the HEAD version) |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20261114-003324 | the target is the documentation itself (applied in step 1) |

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
- **Related target files**: `docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md`