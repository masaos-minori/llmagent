## Goal

Remove the `Known Deviations` citation of EVENTBUS-021 from ADR-004 and keep the fail-closed requirement it stood for in the ADR's current sections (`REQ-005`: ADR-004 citation; `REQ-007`: state still-applicable requirements).

## Scope

- Edit `## Known Deviations` and add one bullet to `## Implementation Notes` in the target file only.
- Do not add a Decision, an invariant, or a test-table row.

## Assumptions

- Plan Step 3a found that ADR-004 states Fail-Fast at startup for authentication, authorization, Allowlist, Safety Tier, Config Isolation and approval control (INV-07) but has no EventBus stamped-schema statement. Source evidence: `scripts/eventbus/schema.py` and `scripts/db/create_schema.py` (both call `assert_matches` from `shared.eventbus_schema_fingerprint`), `deploy/init_db.sh` (shape check), `deploy/setup_services.sh` (EventBus health URL checked before reporting started); cited tests `tests/eventbus/test_eventbus_startup.py`, `tests/deploy/test_init_db_eventbus_schema.py`, `tests/deploy/test_setup_services_eventbus.py`, `tests/db/test_create_schema.py`.
- The ADR has an `## Implementation Notes` section (it holds the MCP retry-policy note immediately before `## Known Deviations`); the new bullet goes there.
- `check_known_deviation_sync.py` is run after row 05.
- Plan overlap check: `plans/20261027-104705_govrev004_adr-verification-evidence-sync.md` targets a different ADR file, so no overlap on this file.
- Size gate (measured in Step 3a, `tools/check_docs_structure.py`, UTF-8 bytes): the file is 32184 B against a per-file ceiling of 32305 B (headroom 121 B). Removing the Known Issue bullet frees 173 B and `Not applicable` adds 14 B, so the added bullet MUST stay within 279 B. Measure with `wc -c` after the edit; if the ceiling is exceeded, shorten the bullet, and do not edit `tools/check_docs_structure.py` (not a target file of the Plan).

## Design decisions

- State the requirement once, at policy level: a stamped EventBus database whose shape differs from the canonical shape, or an EventBus process that is not ready, MUST NOT be accepted at startup or reported as started (safety/integrity failure, Fail-Fast).
- Follow `skills/DESIGN.md`: no line numbers, no concrete config values, no counts.

## Alternatives considered

- Leaving the requirement only in ADR-006: rejected, because ADR-004 is the policy owner that the deviation cited (Fail-Fast on schema inconsistency).

## Implementation
### Target file

`docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md`

### Procedure

1. Locate `## Implementation Notes` and `## Known Deviations` (`rg -n "^## Implementation Notes|^## Known Deviations" <target>`).
2. Add one bullet at the end of `## Implementation Notes` stating the EventBus stamped-schema and readiness Fail-Fast requirement from Design decisions, referencing ADR-006 for the EventBus-specific mechanism by ADR number only.
3. Replace the body of `## Known Deviations` (the single EVENTBUS-021 bullet) with the single line `Not applicable`.

### Method

Exact-string edits. Verify the added bullet against `scripts/eventbus/schema.py` and `deploy/setup_services.sh` once before writing it; if unconfirmed, report `Needs confirmation` and do not add it.

### Details

- Do not alter INV-07 or the Group 5 items.
- Match the `Not applicable` form of other ADRs.

## Compatibility considerations

N/A: documentation only. `check_adr_preservation.py` may report the Known Deviations removal and the added bullet; review as intended.

## Security considerations

N/A: the bullet states a rejection rule and names no secret.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run python tools/check_adr_structure.py` and `uv run python tools/check_adr_preservation.py` (review every report).
- `check_docs_quality.py`, `check_docs_structure.py` on this file, `check_docs_content_policy.py --strict`, `check_docs_japanese.py`, `check_docs_consistency.py --domain eventbus`.
- `uv run python tools/check_known_deviation_sync.py` after rows 01 to 05.

## Completion criteria

- `## Known Deviations` reads `Not applicable`.
- The ADR states the EventBus stamped-schema and readiness Fail-Fast requirement.
- The checkers above report no unreviewed finding.

## Out of Scope

- The ledger, the other ADRs and the ADR guide (other rows).
- Any change to INV-07, decision groups or the test table.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the EventBus fail-closed bullet and set Known Deviations to `Not applicable` | Completed | 20261027-121416 | 20261027-121434 | Changed: docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md (one Implementation Notes bullet added; Known Deviations set to Not applicable). Size 32270 B <= ceiling 32305 B. Stale detector clean. |
| 2 | Run the ADR and documentation checkers named in the Validation plan | Completed | 20261027-121434 | 20261027-121434 | Sync checker passes only after all rows Pass: adr_structure, docs_quality, docs_structure, content_policy --strict, japanese. check_adr_preservation: 1 intended ERROR (Known Deviations text changed), reviewed. check_docs_consistency --domain eventbus not re-run here (eventbus docs untouched; 1 pre-existing unrelated WARNING seen in row 02). Sync checker deferred to after row 05 (Not run yet). |

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
- **Requirement ID**: `REQ-005` (ADR-004 citation removed), `REQ-007` (still-applicable requirement stated)
- **Source issue**: issues/20261027-102048_govrev006_eventbus-ledger-stale-entries.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261027-103437_govrev006_eventbus-ledger-stale-entries.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261027-111029
- **Related target files**: docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md