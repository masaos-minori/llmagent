## Goal

Remove the `Known Deviations` citations of EVENTBUS-019, EVENTBUS-021 and EVENTBUS-022 from ADR-006 and keep the requirements they stood for in the ADR's current sections (`REQ-003`: ADR-006 citations; `REQ-007`: state still-applicable requirements).

## Scope

- Edit `## Known Deviations` and `## Implementation Notes` of the target file only.
- Add short current-behavior statements; do not add a Decision, an invariant ID, or a test-table row.

## Assumptions

- Plan Step 3a found that the current sections state the NACK idempotency key (Implementation Notes) but state no requeue-atomicity, stamped-schema shape, or refuse-to-close-on-lock-timeout requirement. Source evidence: `scripts/eventbus/dlq_repo.py` (explicit rollback on the requeue transition), `scripts/eventbus/dlq_route.py` (all SQLite access inside `run_with_db_lock`), `scripts/eventbus/schema.py` (`assert_matches` from `shared.eventbus_schema_fingerprint`), `scripts/eventbus/app.py` (shutdown refuses to close the connection when the lock is not acquired).
- Row 01 (ledger) may already be applied; `check_known_deviation_sync.py` is run after row 05.
- The ADR lists Known Issue bullets for EVENTBUS-019, 021, 022 only; EVENTBUS-023 was removed earlier by commit `dbbd4357d`.
- Plan overlap check: no other Frozen Plan targets this file.
- Size gate (measured in Step 3a, `tools/check_docs_structure.py`, UTF-8 bytes): the file is 24488 B against a per-file ceiling of 24726 B (headroom 238 B). Removing the three Known Issue bullets frees 464 B and `Not applicable` adds 14 B, so the three added bullets together MUST stay within 687 B (about 229 B each). Measure with `wc -c` after the edit; if the ceiling is exceeded, shorten the new bullets, and do not edit `tools/check_docs_structure.py` (not a target file of the Plan).

## Design decisions

- Put each retained requirement as one bullet in `## Implementation Notes`, in the style of the existing NACK idempotency bullet.
- Follow `skills/DESIGN.md`: no line numbers, no concrete config values (no timeout value), no counts; name symbols only where the boundary is the decision.

## Alternatives considered

- Adding a new numbered Decision or INV entry: rejected, because it would change the ADR's decision surface and trigger `check_adr_preservation.py` ERROR beyond the intended change.
- Dropping the requirements with the citations: rejected, because the ADR would then no longer state requeue atomicity, shape validation or safe shutdown (Plan Risks).

## Implementation
### Target file

`docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`

### Procedure

1. Re-read `## Implementation Notes` and `## Known Deviations` of the target file (`rg -n "^## Implementation Notes|^## Known Deviations" <target>`).
2. Add three bullets after the NACK idempotency bullet in `## Implementation Notes`:
   - DLQ requeue: the requeue state transition commits or rolls back as one unit, and the route performs all SQLite access inside the global database lock (supports INV-08 and INV-16).
   - Schema shape: EventBus startup validates the stamped database against the shared canonical schema shape even when `user_version` matches, and refuses to start on a mismatch; deployment initialization applies the same check, and deployment reports EventBus started only after a health check passes.
   - Shutdown: the shared connection is closed only after the global database lock is acquired within a bounded wait; when the lock is not acquired, shutdown refuses to close the connection (supports INV-01).
3. Replace the body of `## Known Deviations` (the three `- **Known Issue**:` bullets) with the single line `Not applicable`.

### Method

Exact-string edits. Verify each added statement against the cited source file once before writing it; if a statement is not confirmed, write `Needs confirmation` in the progress report and do not add it.

### Details

- Match the form used by other ADRs: the section body is the single word `Not applicable` (for example `docs/10_adr/adr_02_06_010_rag-fallback.md`).
- Do not touch the Test table or invariants.

## Compatibility considerations

N/A: documentation only. `check_adr_preservation.py` may report WARNING or ERROR for the Known Deviations removal and the added bullets; review each as intended and do not suppress the check.

## Security considerations

N/A: no secret or credential is involved; the added text names no token or host.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run python tools/check_adr_structure.py` and `uv run python tools/check_adr_preservation.py` (review every report).
- `uv run python tools/check_docs_quality.py`, `check_docs_structure.py` on this file, `check_docs_content_policy.py --strict`, `check_docs_japanese.py`, `check_docs_consistency.py --domain eventbus`.
- `uv run python tools/check_known_deviation_sync.py` after rows 01 to 05.

## Completion criteria

- `## Known Deviations` reads `Not applicable` and cites no removed ID.
- `## Implementation Notes` states requeue atomicity, stamped-schema shape validation, and refuse-to-close on lock timeout.
- The checkers above report no unreviewed finding.

## Out of Scope

- The ledger, the other ADRs and the ADR guide (other rows).
- Changing any invariant, Decision, or test-table row.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the retained-requirement bullets and set Known Deviations to `Not applicable` | Completed | 20261027-121257 | 20261027-121323 | Changed: docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md (3 Implementation Notes bullets added; Known Deviations set to Not applicable). Size 24556 B <= ceiling 24726 B. Stale detector clean. |
| 2 | Run the ADR and documentation checkers named in the Validation plan | Completed | 20261027-121323 | 20261027-121323 | Sync checker passes only after all rows Pass: adr_structure, docs_quality, docs_structure, content_policy --strict, japanese. check_adr_preservation: 1 intended ERROR (Known Deviations text changed), reviewed. consistency --domain eventbus: 1 pre-existing unrelated WARNING (eventbus_06 to_thread()). Sync checker deferred to after row 05 (Not run yet). |

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
- **Requirement ID**: `REQ-003` (ADR-006 citations removed), `REQ-007` (still-applicable requirements stated)
- **Source issue**: issues/20261027-102048_govrev006_eventbus-ledger-stale-entries.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261027-103437_govrev006_eventbus-ledger-stale-entries.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261027-111029
- **Related target files**: docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md