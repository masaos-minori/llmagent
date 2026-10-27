## Goal
- Remove the resolved EVENTBUS-019 to EVENTBUS-023 Known Issue entries from the ledger and from every ADR `Known Deviations` section in one change, after each entry's Resolution Target is re-verified against current source and tests, so that the ledger, the ADRs and `check_known_deviation_sync.py` agree and no stale High entry blocks EventBus merges.

## Priority
High

## Scope
- **In-Scope**:
  - Re-verify the Resolution Target of each of the five entries (source, tests, and execution of the cited tests).
  - Remove each resolved entry from `governance_03` Part 1, and every ADR citation of it, in the same change.
  - Replace the emptied Part 1 body with the empty-state sentence used by the other Parts.
  - Set an ADR `Known Deviations` section that loses its last citation to `Not applicable`.
  - Update the confirmed-deviations sentence in `adr_00_document-guide.md`.
  - Run the documentation checkers and clear the EVENTBUS-023 sync warning.
- **Out-of-Scope**:
  - Any change to `scripts/`, `deploy/`, `config/` or `tests/`.
  - Registering EventBus issues 006 to 008 or any new Known Issue.
  - Correcting the stale Execution Status tables of the archived EventBus plans.
  - Resolving the CI state of the repository.
- **Dependencies**: N/A: none. No open issue or in-flight plan overlaps; the other issues of the same review batch edit different documents.

## Background
- `governance_03` Part 1 lists EVENTBUS-019 to EVENTBUS-023 as `Status: open`, `Severity: High`, and they are the only active Part 1 entries. `governance_01` Merge Conditions treat a High open Known Issue in the affected area as a Blocking Condition, so stale entries block EventBus merges.
- Implementation commits exist: DLQ requeue atomicity (`39335dc89`), startup fingerprint gate and deployment readiness (`72c83c0db`), fail-fast shutdown (`e5f30fefe`), NACK idempotency key (`dbbd4357d`), and the config loader and duplicate-token guard in `68e9cabd2` (its subject does not describe the change).
- Commit `dbbd4357d` removed the ADR-006 citation of EVENTBUS-023 without removing the ledger entry, so `check_known_deviation_sync.py` reports one warning today.
- Adversarial verification in this cycle found each Resolution Target met by source and tests (read, not executed). The ADR citations remain for EVENTBUS-019, 021, 022 (ADR-006), 021 (ADR-004) and 020 (ADR-013).
- Verification during `plan-to-implementation-procedure` Step 3a re-checked the source symbols (`dlq_repo.py` rollback paths, `auth.py` duplicate-token guard, `schema.py`/`create_schema.py`/`init_db.sh` fingerprint gate, `app.py` refuse-to-close on lock timeout, `ack_route.py` required `idempotency_key`) and the ADR current sections. ADR-006 current sections state the NACK idempotency key (Implementation Notes) but state no requeue-atomicity, stamped-schema shape or refuse-to-close-on-lock-timeout requirement; ADR-013 current sections state no duplicate-token rejection requirement; ADR-004 states no EventBus stamped-schema fail-closed requirement. Removing the citations alone would therefore drop those requirements from the ADRs, so REQ-007 is real work for each ADR row, not a no-op.
- `governance_03` has no Part 1 closing-summary line today, so `check_issue_inventory_conformance.py` `check_closing_summary()` returns without findings; no precedent for the Part 1 empty-state sentence exists yet (Parts 2 to 4 carry it).

## Problem
Ledger entries that describe fixed defects remain open. They block merges in the EventBus area, the ledger and ADR-006 disagree for EVENTBUS-023, and readers are told that defects exist that the code no longer has. Removing an entry without checking its Resolution Target would instead hide a defect that may still exist.

## Reason for Change
The stale High entries gate merges now, and the sync checker already reports an inconsistency. The ledger is the single register of active design-versus-code discrepancies, so an inaccurate entry defeats its purpose.

## Implementation Intent
Treat each entry's `Resolution Target` as the acceptance test. Remove an entry only with source and test evidence, including a passing run of the cited tests; keep and update any entry whose target is not met. Remove the ledger entry and all of its ADR citations together, because the sync checker is bidirectional. Use the existing empty-state wording convention instead of inventing a new one. No code or tests change.

## Requirements
- `REQ-001`: Re-verify the Resolution Target of each of EVENTBUS-019 to EVENTBUS-023 against current source and tests, run the cited tests, and keep any entry whose target is not met.
- `REQ-002`: Remove each resolved entry from `governance_03` Part 1 and replace an emptied Part 1 body with the sentence "No active Known Issue items remain.".
- `REQ-003`: Remove the ADR-006 `Known Deviations` citations of EVENTBUS-019, EVENTBUS-021 and EVENTBUS-022 and set the section to `Not applicable` when no citation remains.
- `REQ-004`: Remove the ADR-013 `Known Deviations` citation of EVENTBUS-020 and set the section to `Not applicable` when no citation remains.
- `REQ-005`: Remove the ADR-004 `Known Deviations` citation of EVENTBUS-021 and set the section to `Not applicable` when no citation remains.
- `REQ-006`: Update the confirmed-deviations sentence of `adr_00_document-guide.md` so it lists only the deviations that remain, or states that none remain.
- `REQ-007`: Leave `check_known_deviation_sync.py` and `check_issue_inventory_conformance.py` without findings, and state any still-applicable requirement of a removed deviation in the ADR's current sections.

## Implementation Target Files
**Freeze status**: Frozen (validated by `issue-to-plan` Step 8's
Implementation Target Files Validation — see `rules/workflow-lifecycle.md`
Implementation Target Files Validation (Plan Freeze)).

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `docs/00_governance/governance_03_issue-and-uncertainty-management.md` | Known Issue ledger (Part 1) | Remove the five resolved entries and replace the emptied body with the empty-state sentence | REQ-002, REQ-007; AC-1, AC-2 | Part 1 `Active Items` holds only `#### EVENTBUS-019` to `#### EVENTBUS-023`, all `Status: open`; Parts 2 to 4 use "No active ... items remain." (checked in Step 3) | `tests/tools/test_check_known_deviation_sync.py` | Verified |
| `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md` | ADR-006 `Known Deviations` | Remove the citations of EVENTBUS-019, 021, 022 and set the section to `Not applicable` | REQ-003; AC-3 | `## Known Deviations` lists exactly those three `Known Issue` bullets; the NACK paragraph of its current sections already states the idempotency-key behavior (checked in Step 3) | `tests/tools/test_check_known_deviation_sync.py` | Verified |
| `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md` | ADR-013 `Known Deviations` | Remove the citation of EVENTBUS-020 and set the section to `Not applicable` | REQ-004; AC-3 | `## Known Deviations` contains the single EVENTBUS-020 `Known Issue` bullet (checked in Step 3) | `tests/tools/test_check_known_deviation_sync.py` | Verified |
| `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md` | ADR-004 `Known Deviations` | Remove the citation of EVENTBUS-021 and set the section to `Not applicable` | REQ-005; AC-3 | `## Known Deviations` contains the single EVENTBUS-021 `Known Issue` bullet (checked in Step 3) | `tests/tools/test_check_known_deviation_sync.py` | Verified |
| `docs/10_adr/adr_00_document-guide.md` | ADR guide sentence | Update the sentence that lists EVENTBUS-019 to EVENTBUS-023 | REQ-006; AC-4 | `## Known Deviations` names "EVENTBUS-019 to EVENTBUS-023 (ADR-004, ADR-006, ADR-013)" (checked in Step 3) | `tests/tools/test_check_known_deviation_sync.py` | Verified |

Rules (see `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan
Freeze) for the full validation procedure):
- One row per file. A directory, glob pattern (`*`, `**`), component/module name, file
  group, or a vague phrase (e.g. "related files", "as necessary", "etc.") MUST NOT
  appear as a row — list each file individually by its exact repository-relative path.
- Record a test, configuration, schema, migration, deployment, or documentation file as
  its own row when it requires modification — do not fold it into the row for the
  source file it accompanies.
- `Validation Status` is `Verified` or `Needs confirmation` per row; every row must be
  `Verified` before this section may be marked `Frozen`.

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same
one-file-per-row discipline as `Implementation Target Files` above — no directories,
glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/eventbus/dlq_repo.py` | Confirm explicit rollback paths of the requeue transition | REQ-001 (EVENTBUS-019) |
| `scripts/eventbus/dlq_route.py` | Confirm the route issues no SQLite call outside `run_with_db_lock` | REQ-001 (EVENTBUS-019) |
| `scripts/eventbus/config.py` | Confirm `load_config()` passes both authorization mappings | REQ-001 (EVENTBUS-020) |
| `scripts/eventbus/auth.py` | Confirm the duplicate-token guard | REQ-001 (EVENTBUS-020) |
| `scripts/eventbus/schema.py` | Confirm the fingerprint gate for a stamped database | REQ-001 (EVENTBUS-021) |
| `scripts/shared/eventbus_schema_fingerprint.py` | Confirm the shared canonical-shape validator | REQ-001 (EVENTBUS-021) |
| `scripts/db/create_schema.py` | Confirm the deployment-side shape gate | REQ-001 (EVENTBUS-021) |
| `deploy/init_db.sh` | Confirm the EventBus shape gate in database initialization | REQ-001 (EVENTBUS-021) |
| `deploy/setup_services.sh` | Confirm the process and readiness gate before reporting started | REQ-001 (EVENTBUS-021) |
| `scripts/eventbus/app.py` | Confirm refuse-to-close shutdown on lock timeout | REQ-001 (EVENTBUS-022) |
| `scripts/eventbus/ack_route.py` | Confirm the caller-supplied idempotency key reaches the repository | REQ-001 (EVENTBUS-023) |
| `docs/24_eventbus/eventbus_12_ack_nack_endpoints.md` | Confirm the NACK contract matches the API and tests | REQ-001 (EVENTBUS-023) |
| `docs/24_eventbus/eventbus_07_configuration-and-operations.md` | Confirm the documented bounded-shutdown policy | REQ-001 (EVENTBUS-022) |
| `tests/eventbus/test_eventbus_requeue_edge_cases.py` | Cited negative tests for requeue rollback | REQ-001 (EVENTBUS-019) |
| `tests/eventbus/test_eventbus_concurrent.py` | Cited concurrent requeue tests | REQ-001 (EVENTBUS-019) |
| `tests/eventbus/test_eventbus_consumer_authorization.py` | Cited file-loading test for the authorization mapping | REQ-001 (EVENTBUS-020) |
| `tests/eventbus/test_eventbus_config.py` | Cited duplicate-token load-path test | REQ-001 (EVENTBUS-020) |
| `tests/eventbus/test_eventbus_startup.py` | Cited startup shape-gate tests | REQ-001 (EVENTBUS-021) |
| `tests/deploy/test_init_db_eventbus_schema.py` | Cited deployment shape-gate tests | REQ-001 (EVENTBUS-021) |
| `tests/deploy/test_setup_services_eventbus.py` | Cited readiness-gate tests | REQ-001 (EVENTBUS-021) |
| `tests/db/test_create_schema.py` | Cited create-schema shape-gate tests | REQ-001 (EVENTBUS-021) |
| `tests/eventbus/test_eventbus_shutdown.py` | Cited shutdown tests | REQ-001 (EVENTBUS-022) |
| `tests/eventbus/test_eventbus_ack_endpoint.py` | Cited NACK idempotency endpoint tests | REQ-001 (EVENTBUS-023) |
| `tests/eventbus/test_eventbus_ack_nack.py` | Cited NACK idempotency repository tests | REQ-001 (EVENTBUS-023) |
| `tools/check_known_deviation_sync.py` | Behavior of the bidirectional sync checks | REQ-007 |
| `tools/check_issue_inventory_conformance.py` | Behavior of the inventory conformance checks, including the emptied Part 1 | REQ-002, REQ-007 |

## Acceptance Criteria
- AC-1 (REQ-001): For each of the five entries, a recorded verification names the source and tests that meet its Resolution Target, and the cited tests pass; an entry whose target is not met is kept and its current-state fields are updated.
- AC-2 (REQ-002): `governance_03` Part 1 contains no resolved entry, and an emptied Part 1 body is the sentence "No active Known Issue items remain.".
- AC-3 (REQ-003, REQ-004, REQ-005): No ADR `Known Deviations` section cites a removed ID, and a section with no remaining citation reads `Not applicable`.
- AC-4 (REQ-006): `adr_00_document-guide.md` lists exactly the deviations that remain, or states that none remain.
- AC-5 (REQ-007): `check_known_deviation_sync.py` and `check_issue_inventory_conformance.py` report no finding, and the other documentation checkers listed under Tests pass.

## Tests
- `uv run pytest tests/eventbus tests/db tests/deploy -q` (read-only evidence for REQ-001; no test is added or changed).
- `uv run python tools/check_known_deviation_sync.py` (REQ-002 to REQ-007).
- `uv run python tools/check_issue_inventory_conformance.py` (REQ-002, REQ-007).
- `uv run python tools/check_adr_structure.py` and `uv run python tools/check_adr_preservation.py` (REQ-003 to REQ-005; the Known Deviations changes are intended and are reviewed one by one).
- `uv run python tools/check_needs_confirmation_inventory.py`, `check_docs_quality.py`, `check_docs_structure.py` on the changed files, `check_docs_content_policy.py --strict`, `check_docs_consistency.py --domain eventbus`, `check_docs_japanese.py` (REQ-002 to REQ-007).

## Documentation Impact
Yes. `docs/*.md` change: the Known Issue register (`governance_03` Part 1) and the `Known Deviations` sections of ADR-004, ADR-006 and ADR-013, plus the confirmed-deviations sentence of the ADR document guide (`adr_00_document-guide.md`). Requirements REQ-002 to REQ-006 drive this. The kind of information is Known Issues. All text is written in English.

## Assumptions
- A Known Issue is removed only when its Resolution Target is met; the repository owner remains the accountable Owner of these entries (`Repository owner`).
- The sentence "No active Known Issue items remain." follows the empty-state convention of Parts 2 to 4 and is accepted by `check_issue_inventory_conformance.py` (to be confirmed by running it).
- Execution of the cited tests in the implementation phase uses the existing test environment; `uv run` may need `UV_NO_SYNC=1` on this host because of a certificate error during dependency sync.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Do the cited tests pass in the current environment? | The tests were read, not executed, during planning | Run `uv run pytest tests/eventbus tests/db tests/deploy -q` in Phase 1 before any removal; keep an entry whose tests fail | False |
| UNK-02 | Who is the accountable approver for removing High Known Issues? | No stated approval channel for ledger removal beyond the `Repository owner` Owner value | Record the repository owner's acknowledgement on this plan before the removal commit, per the sign-off channel of `rules/coding.md` Explicit sign-off gates | False |
| UNK-03 | Does the "CI Evidence" expectation applicable to these entries hold while main-branch CI was recorded as failing for an unrelated runner reason? | Current CI state is not available in this session | Confirm the CI state with the repository owner; record the answer in the commit message | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `docs/00_governance/governance_03_issue-and-uncertainty-management.md` | Modify | High | 93 | 2 authors (1y), share not measured | not applicable (rsynced) |
| `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md` | Modify | Medium | 5 | 2 authors (1y), share not measured | not applicable (rsynced) |
| `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md` | Modify | Medium | 3 | 2 authors (1y), share not measured | not applicable (rsynced) |
| `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md` | Modify | Medium | 3 | 1 author (1y), flagged as high | not applicable (rsynced) |
| `docs/10_adr/adr_00_document-guide.md` | Modify | Low | 14 | 1 author (1y), flagged as high | not applicable (rsynced) |

## Design
- Path B (five target files). Architecture analysis and operational dependency inspection are not applicable: no Python module, import, database or server changes. The baseline for validation quality is `N/A: no Python target`.
- Dependency graphing: the ledger document is referenced by 43 files under `docs/`, `tools/`, `tests/`, `skills/` and `rules/`, and read by `check_known_deviation_sync.py`, `check_needs_confirmation_inventory.py`, `check_issue_inventory_conformance.py` and two other tools. Only the three ADRs and the ADR guide cite the five IDs.
- Historical analysis: `governance_03` has 93 commits in 30 days, so the change is small, committed once, and the checkers are re-run after any sync.
- Decision (empty Part 1): use the existing one-sentence empty-state form of Parts 2 to 4. Alternative rejected: keeping a placeholder entry, which would violate the rule that a resolved item is removed, not kept closed.
- Decision (ADR sections): set an emptied `Known Deviations` section to `Not applicable`, the form used by ADRs without deviations.
- Removal is gated per entry on the Resolution Target; an unmet target keeps the entry and updates its `Observed Implementation`.

## Implementation steps
Each step description MUST cite the exact file path(s) it touches by referencing rows
of `Implementation Target Files` above — do not restate file-level detail
independently of that frozen table. A step is a top-level numbered item (a Phase); its
checklist items are sub-tasks, and the Execution Status table has one row per step.

1. **Phase 1: Re-verify the Resolution Targets**
   - [ ] Run `uv run pytest tests/eventbus tests/db tests/deploy -q` and record the result (REQ-001; read-only, no target file modified)
   - [ ] For each entry, record the source and test evidence for its Resolution Target in the commit message draft, and decide remove or keep (REQ-001; `docs/00_governance/governance_03_issue-and-uncertainty-management.md`)
   - [ ] Record the repository owner's acknowledgement (UNK-02, UNK-03) (REQ-001)
2. **Phase 2: Remove the resolved entries**
   - [ ] Remove the resolved entries from Part 1 and write the empty-state sentence if Part 1 is empty (REQ-002; `docs/00_governance/governance_03_issue-and-uncertainty-management.md`)
   - [ ] Remove the citations from ADR-006, ADR-013 and ADR-004 and set emptied sections to `Not applicable` (REQ-003, REQ-004, REQ-005; `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`, `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`, `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md`)
   - [ ] State any still-applicable requirement of a removed deviation in the ADR's current sections (REQ-007; the three ADR files above)
   - [ ] Update the confirmed-deviations sentence (REQ-006; `docs/10_adr/adr_00_document-guide.md`)
3. **Phase 3: Verification (no deployment)**
   - [ ] Run the checkers listed under Tests, review every `check_adr_preservation.py` report as an intended change, and confirm no finding remains (REQ-007; the five target files). No `scripts/` or `config/` file changes, so no deploy step applies.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `docs/00_governance/governance_03_issue-and-uncertainty-management.md` | Documentation checks | `uv run python tools/check_issue_inventory_conformance.py`; `uv run python tools/check_needs_confirmation_inventory.py` | No finding with Part 1 empty |
| Five target files | Bidirectional sync of ledger and ADR citations | `uv run python tools/check_known_deviation_sync.py` | No warning or error |
| Three ADR files | Structure and preservation | `uv run python tools/check_adr_structure.py`; `uv run python tools/check_adr_preservation.py` | No structure issue; only Known Deviations changes reported |
| Five target files | Quality, structure, content policy, language, consistency | `check_docs_quality.py`; `check_docs_structure.py` (changed files); `check_docs_content_policy.py --strict`; `check_docs_japanese.py`; `check_docs_consistency.py --domain eventbus` | No finding |
| EventBus, DB and deploy tests | Read-only evidence for the Resolution Targets | `uv run pytest tests/eventbus tests/db tests/deploy -q` | All pass |

## Risks
- **Risk**: A still-present defect is hidden by removing its entry → **Mitigation**: Each removal needs source and test evidence and a passing test run; an unmet target keeps the entry (REQ-001).
- **Risk**: `governance_03` is edited by other work (93 commits in 30 days), so a sync or rebase conflict is likely → **Mitigation**: Make one small commit, and re-run the checkers after any sync.
- **Risk**: Emptying Part 1 is rejected by `check_issue_inventory_conformance.py`, which runs in CI → **Mitigation**: Run it before committing and use the established empty-state sentence.
- **Risk**: `check_adr_preservation.py` reports ERROR for the Known Deviations changes → **Mitigation**: Review each report and confirm it is intended; do not suppress the check.
- **Risk**: A removed deviation still states a requirement that applies and no current ADR section carries it → **Mitigation**: Check ADR-004, ADR-006 and ADR-013 current sections and state the requirement there (REQ-007). Confirmed in Step 3a: ADR-006 lacks requeue-atomicity, stamped-schema shape and refuse-to-close requirements; ADR-013 lacks duplicate-token rejection; ADR-004 lacks the EventBus stamped-schema fail-closed requirement. Each ADR row adds these as a short current-section statement (an Implementation Notes or Failure Policy bullet, not a new Decision), and `check_adr_preservation.py` WARNING or ERROR output for these additions is reviewed as intended.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Re-verify the Resolution Targets of EVENTBUS-019 to 023 | Pending | — | — |  |
| 2 | Remove resolved entries and ADR citations | In Progress | — | — |  |
| 3 | Run the documentation checkers (no deployment) | Pending | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261027-111029_01_docs_00_governance_governance_03_issue-and-uncertainty-management.md.md | 2 | Procedure | Pending | — | — |
| implementations/20261027-111029_02_docs_10_adr_adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md.md | 2 | Procedure | Pending | — | — |
| implementations/20261027-111029_03_docs_10_adr_adr_02_04_013_eventbus-authentication-authorization.md.md | 2 | Procedure | Pending | — | — |
| implementations/20261027-111029_04_docs_10_adr_adr_02_01_004_platform-environment-failure-handling-policy.md.md | 2 | Procedure | Pending | — | — |
| implementations/20261027-111029_05_docs_10_adr_adr_00_document-guide.md.md | 2 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261027-102048_govrev006_eventbus-ledger-stale-entries.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261027-103437
- **Related target files**: `docs/00_governance/governance_03_issue-and-uncertainty-management.md`, `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`, `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`, `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md`, `docs/10_adr/adr_00_document-guide.md`

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Implementation Intent; Required Changes (verify each Resolution Target) | `docs/00_governance/governance_03_issue-and-uncertainty-management.md` | Phase 1 | AC-1 | `uv run pytest tests/eventbus tests/db tests/deploy -q` | Confirmed by repository evidence |
| REQ-002 | Required Changes (remove resolved entries); Constraints | `docs/00_governance/governance_03_issue-and-uncertainty-management.md` | Phase 2 | AC-2 | `check_issue_inventory_conformance.py` | Confirmed by repository evidence |
| REQ-003 | Required Changes; Constraints (remove ledger entry and citations together) | `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md` | Phase 2 | AC-3 | `check_known_deviation_sync.py` | Confirmed by repository evidence |
| REQ-004 | Required Changes; Constraints | `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md` | Phase 2 | AC-3 | `check_known_deviation_sync.py` | Confirmed by repository evidence |
| REQ-005 | Required Changes; Constraints | `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md` | Phase 2 | AC-3 | `check_known_deviation_sync.py` | Confirmed by repository evidence |
| REQ-006 | Required Changes (update the guide sentence) | `docs/10_adr/adr_00_document-guide.md` | Phase 2 | AC-4 | `check_known_deviation_sync.py`, `check_docs_quality.py` | Confirmed by repository evidence |
| REQ-007 | Acceptance Criteria; Testing Expectations | `docs/00_governance/governance_03_issue-and-uncertainty-management.md` | Phase 2, Phase 3 | AC-5 | Checkers listed under Tests | Derived from confirmed evidence |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261027-111029 -->