## Goal

## Goal

Amend ADR-001 INV-07 in `docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md` so "interrupted Attempt" means a lease-expired attempt (REQ-010 / AC-9).

## Scope

- Amend INV-07 (`:171`) under the ADR change protocol: recovery targets attempts whose `lease_expires_at` has expired (or lease-less legacy rows past the conservative age), never an attempt with an unexpired lease; the test-evidence row (`:187`) gains `tests/agent/workflow/test_stale_recovery_lease.py`.

## Assumptions

- Plan `plans/20261030-114516_wflease001_stale-attempt-lease.md` is Frozen; its 18-row `Implementation Target Files` table (rows 17-18 added by the 2026-11-01 amendment) is the canonical scope and every target of this procedure is a row of that table.
- All baseline cites below were re-verified against branch `master` on 2026-11-01 (Plan Assumptions 'Re-verification record').
- Canonical semantics come from the Plan REQs (Plan `:37-46`): `parse_iso_utc` rejects naive input (REQ-001); no `mktime`/`strptime`/local time in recovery (REQ-002); unparseable timestamps are reported with distinct counts (REQ-003); nullable `owner_id`/`lease_expires_at` via a registered migration (REQ-004); owner and lease stamped at attempt start from the stage timeout plus a 30 s margin constant (REQ-005); staleness means lease expiry and `_STALE_GRACE_SEC` is removed (REQ-006); takeover is a conditional update requiring one row (REQ-007); legacy rows without a lease use the 3600 s age (REQ-008); tests use the production timestamp format (REQ-009); docs and ADR-001 INV-07 are amended (REQ-010).
- Owner decision (Plan UNK-02, 2026-10-30): deadline lease only — no heartbeat renewal, because `asyncio.wait_for` already bounds a normal stage.
- Ledger landing order (Plan UNK-06): `master` records code 2 / "1.2.0" (`migrations_workflow.py:42`); wftaskapi001 procedure 12 (`implementations/20261101-140834_12_scripts_db_migrations_workflow.py.md`, Pending) reserves the next slot. This Plan takes code 3 / "1.3.0" only if its step registers before wftaskapi001's, otherwise 4 / "1.4.0" (same rule as `implementations/20261101-145309_26_scripts_db_migrations_workflow.py.md`).
- Fencing dependency (Plan UNK-06): REQ-007's rejection of a late finish by the fenced owner lands with the wfrecovery001 conditional `finish_attempt` procedure (`implementations/20261101-145309_04_scripts_agent_workflow_attempt_ops.py.md`, Pending); at `master` `finish_attempt` is still unconditional (`attempt_ops.py:44-45`).
- wfrecovery001 procedure 23 amends the same INV-07 first (Pending); the landing order decides which amendment is applied to which baseline text — the later document reconciles (Plan Assumptions overlap record).

## Design decisions

- Accepted ADR: the change is an amendment note with rationale, not a silent rewrite; `check_adr_preservation.py` reports the change and this procedure supplies the explanation line the checker requires.

## Alternatives considered

- Supersede the ADR — rejected: INV-07's intent survives; only its definition of 'interrupted' is refined.

## Implementation
### Target file
`docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md`

### Procedure
1. Apply the amendment on top of the wfrecovery001 amendment baseline.
2. Add the change rationale (timezone defect + live-attempt theft) adjacent to the amended INV-07 line.

### Method
Single-invariant amendment plus test-table row update.

### Details
- Preserve the INV number and table structure (ADR checker contracts).

## Compatibility considerations

- English content.

## Security considerations

- All recovery/attempt SQL stays parameter-bound; owner and lease values are produced by the server (clock, host identity), never by caller-supplied strings.

## Rollback considerations

- Restore from pre-change commit; the ADR checker compares against git history.

## Validation plan

- `uv run python tools/check_adr_preservation.py`

## Completion criteria

- AC-9 for the ADR half.

## Out of Scope

- Other INVs and the decision log.

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
- **Workflow phase**: Phase 4 (Documentation and ADR)
- **Requirement ID**: `REQ-010`
- **Source issue**: issues/20261030-105723_wflease001_stale-attempt-lease.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261030-114516_wflease001_stale-attempt-lease.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261101-163219
- **Related target files**: `docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md`, `docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md`, `tests/agent/workflow/test_stale_recovery_lease.py`
