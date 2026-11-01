## Goal

Rewrite the "Startup Recovery" section of `docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md` with lease semantics, the timestamp format contract, and the manual recovery path (REQ-010 / AC-9).

## Scope

- Rewrite the section starting at `:143` (currently describing elapsed-time recovery that never changes task status): staleness = expired `lease_expires_at` (stamped at attempt start from the stage `timeout_sec` plus the 30 s margin); legacy lease-less rows use the 3600 s age rule; unparseable timestamps are reported and left for the manual path.
- Document the timestamp contract: workflow timestamps are `YYYY-MM-DDTHH:MM:SSZ` written by the shared clock and parsed only by `scripts/shared/json_utils.parse_iso_utc`.
- Document the operational manual recovery for rows left `running` (unparseable or legacy-young): identify the owning process from `owner_id` (host:pid:suffix), inspect, and correct via the documented manual SQL path — no automated takeover.

## Assumptions

- Plan `plans/20261030-114516_wflease001_stale-attempt-lease.md` is Frozen; its 18-row `Implementation Target Files` table (rows 17-18 added by the 2026-11-01 amendment) is the canonical scope and every target of this procedure is a row of that table.
- All baseline cites below were re-verified against branch `master` on 2026-11-01 (Plan Assumptions 'Re-verification record').
- Canonical semantics come from the Plan REQs (Plan `:37-46`): `parse_iso_utc` rejects naive input (REQ-001); no `mktime`/`strptime`/local time in recovery (REQ-002); unparseable timestamps are reported with distinct counts (REQ-003); nullable `owner_id`/`lease_expires_at` via a registered migration (REQ-004); owner and lease stamped at attempt start from the stage timeout plus a 30 s margin constant (REQ-005); staleness means lease expiry and `_STALE_GRACE_SEC` is removed (REQ-006); takeover is a conditional update requiring one row (REQ-007); legacy rows without a lease use the 3600 s age (REQ-008); tests use the production timestamp format (REQ-009); docs and ADR-001 INV-07 are amended (REQ-010).
- Owner decision (Plan UNK-02, 2026-10-30): deadline lease only — no heartbeat renewal, because `asyncio.wait_for` already bounds a normal stage.
- Ledger landing order (Plan UNK-06; fixed by the 2026-11-01 pre-execution verification): wftaskapi001 procedure 12 has landed (`implementations/done/20261101-140834_12_scripts_db_migrations_workflow.py.md`) and registered code 3 / "1.3.0" (`migrations_workflow.py:42`, `WORKFLOW_TARGET_VERSION` = 3 at `:49`). This Plan takes code 4 / "1.4.0": procedure 17 registers `workflow_attempt_lease` with `from_version=3, to_version=4`, and procedure 06 sets `WORKFLOW_SCHEMA_VERSION` to "1.4.0". The still-Pending wfrecovery001 procedure 26 (`implementations/20261101-145309_26_scripts_db_migrations_workflow.py.md`) takes 5 / "1.5.0" when it lands after this Plan.
- Fencing dependency (Plan UNK-06): REQ-007's rejection of a late finish by the fenced owner lands with the wfrecovery001 conditional `finish_attempt` procedure (`implementations/20261101-145309_04_scripts_agent_workflow_attempt_ops.py.md`, Pending); at `master` `finish_attempt` is still unconditional (`attempt_ops.py:44-45`).
- Baseline wording (fixed by the 2026-11-01 verification): wfrecovery001 procedure 24 (`implementations/20261101-145309_24_docs_23_agent_agent_03_03_turn-processing-flow-workflow-engine.md.md`) is still Pending, so this rewrite applies to the current "Startup Recovery" section text (`:143`); the wfrecovery001 document carries the reconciliation note when it lands (Plan Assumptions).

## Design decisions

- Intent and ownership only — no DDL or code restatement (Plan Documentation Impact).

## Alternatives considered

- A new dedicated lease document — rejected: the Plan names this section as the home.

## Implementation
### Target file
`docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md`

### Procedure
1. Apply this rewrite on top of the wfrecovery001 rewrite (or on the current text if wfrecovery001's lands second, in which case its document carries the reconciliation note).
2. Run the docs checkers listed in the Validation plan after the edit.

### Method
Section-level documentation rewrite.

### Details
- The Needs-Confirmation marker for UNK-01 (multi-process support) stays recorded if unresolved (Plan Documentation Impact).
- `docs/41_db/db_02` is not a target (names tables only, Plan Documentation Impact).

## Compatibility considerations

- English content per `skills/DESIGN.md` Output language.

## Security considerations

- All recovery/attempt SQL stays parameter-bound; owner and lease values are produced by the server (clock, host identity), never by caller-supplied strings.

## Rollback considerations

- Restore the section text from the pre-change commit.

## Validation plan

- `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py --strict`, `check_docs_consistency.py --domain agent`, `check_docs_japanese.py`.

## Completion criteria

- AC-9 for the docs half: the section describes lease semantics and the manual path.

## Out of Scope

- Other sections of the same document.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | — | Startup Recovery section rewritten with lease semantics, timestamp contract, and manual recovery path; Known Limitations bullet updated (stale grace period -> lease expiry). |
| 2 | Add or update tests per Validation plan | Completed | — | — | N/A: documentation-only procedure. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | — | check_docs_quality/structure/content_policy --strict/consistency --domain agent/japanese all exit 0. |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | — | N/A: this procedure is the documentation update. |

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
- **Related target files**: `docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md`, `docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md`, `scripts/agent/workflow/state_store.py`