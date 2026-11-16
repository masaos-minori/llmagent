## Goal

Remove the age-threshold phrase from `db_07` §9.7 (`REQ-001`), extend the §11 recreation runbook with the workflow-specific gaps — fingerprint-gate verification, the no-migration / data-loss / rollback statement for `workflow.sqlite`, and "old-archive restore is a release rollback, not a migration" (`REQ-005`), and later add an optional direct lease-constraint check (`REQ-008`, gated).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- `REQ-001` matches current committed source: §9.7 line 92 says "marks lease-expired running attempts — and lease-less rows past the legacy age threshold — `failed`"; the implementation recovers only lease-expired rows (`state_store.py:225-274,365-419`). The "lease-less rows past the legacy age threshold" clause is stale after adrrev005 and must go. Safe to edit now.
- §11 (line 117) already describes the generic recreation procedure (archive → delete → recreate via `create_schema()`) but lacks the workflow-specific statements REQ-005 requires: a verification step that the startup fingerprint gate accepts the recreated database, an explicit no-migration statement naming the workflow history tables, and data-loss / rollback coverage for `workflow.sqlite`.
- `REQ-008` (Phase 3) is gated on `compat002` implementing: the optional direct lease-constraint check references the schema-enforced `NOT NULL`/CHECK that does not exist in the shipped DDL yet (`schema_sql.py:192-193`).
- `db_03` (reference file) already covers `workflow.sqlite` data loss and rollback and its no-migration policy, so no edit is required there — verify this while writing, do not add a second runbook.

## Design decisions
- **Extend §11 in place, not a second runbook.** Add the workflow-specific bullets to the existing "Important notes" list under §11: (a) a verification step that the startup fingerprint gate (`check_workflow_schema()`) accepts the recreated database before use; (b) an explicit statement that `tasks`, `attempts`, `processed_events`, `artifacts`, and `tool_call_state` history is not migrated and that restoring an old archive is a release rollback, not a migration; (c) data-loss / rollback coverage specific to `workflow.sqlite`.
- **Split Phase 1 vs Phase 3 within §11.** REQ-005 lands now; REQ-008's lease-constraint check is a gated follow-on.

## Alternatives considered
- **Adding a separate workflow-recreation subsection.** Rejected: the Issue explicitly forbids a second runbook; extend the existing §11 instead.

## Implementation
### Target file
`docs/41_db/db_07_api_and_operations-recovery-and-reference.md`
### Procedure
**Phase 1 (safe-now, executable now):**
1. **REQ-001** — In §9.7 (line 92), remove "— and lease-less rows past the legacy age threshold —", leaving "...marks lease-expired running attempts — `failed` via a compare-and-swap UPDATE...".
2. **REQ-005** — In §11's "Important notes" list (line 123), add three workflow-specific bullets:
   - **Verification:** after recreation, confirm the startup fingerprint gate accepts the database — `agent` startup runs `check_workflow_schema()` and refuses a shape mismatch, so a recreated `workflow.sqlite` is validated before use.
   - **No migration:** recreating `workflow.sqlite` does not migrate `tasks`, `attempts`, `processed_events`, `artifacts`, or `tool_call_state` history; those records are empty in the recreated database.
   - **Rollback:** restoring an old `workflow.sqlite` archive is a release rollback (returning to a prior release's data state), not a schema migration; it must not be used to upgrade across a schema change.
**Phase 3 (gated on `compat002`):**
3. **REQ-008** — Add an optional direct lease-constraint check to §11 (verify `attempts.owner_id`/`lease_expires_at` are `NOT NULL`). Blocked until `compat002` implements.
### Method
One clause removal (§9.7); three workflow-specific bullets (§11); one gated lease-constraint bullet (§11, Phase 3).
### Details
- **Line 92** — delete the "— and lease-less rows past the legacy age threshold —" clause. The surrounding sentence ("...marks lease-expired running attempts ... `failed` via a compare-and-swap UPDATE and deletes the `processed_events` rows...") stays.
- **§11 Important notes (after line 123)** — append:
  - "**Workflow verification.** After recreating `workflow.sqlite`, confirm the startup fingerprint gate accepts it: `agent` startup runs `check_workflow_schema()` and refuses a shape mismatch, so the recreated database is validated before use. A mismatch after recreation means the schema DDL changed without recreation — see [ADR-008](../10_adr/adr_02_05_008_db-sqlite-4db-separation.md)."
  - "**No workflow history is migrated.** Recreating `workflow.sqlite` leaves `tasks`, `attempts`, `processed_events`, `artifacts`, and `tool_call_state` empty; that history is not carried across a recreation. See [db_03](db_03_architecture_and_schema-migration-and-scaling.md) for the no-migration policy."
  - "**Workflow rollback.** Restoring an old `workflow.sqlite` archive is a release rollback (returning to a prior release's data state), not a schema migration; never use it to upgrade across a schema change — recreate against the current schema instead."
- **REQ-008 (Phase 3, gated)** — leave a clearly marked placeholder: "GATED — once `compat002` implements, add an optional direct lease-constraint check to §11: verify `attempts.owner_id` and `lease_expires_at` are `NOT NULL` (with `CHECK(length(owner_id) > 0)`)." Do not write it now.

## Compatibility considerations
N/A: documentation only; no runtime blast radius. `deploy.sh` serves docs statically (rsynced).

## Security considerations
N/A.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_quality.py`, `tools/check_docs_content_policy.py`, `tools/check_docs_consistency.py --domain db` — all pass; §9.7 no longer ties recovery to age; runbook covers verification, data loss, rollback without a second runbook; no migration implied.
- Manual: confirm every command/function named in §11 exists — `rotate_all_dbs()`, `create_workflow_schema()`, `create_schema()`, the startup `check_workflow_schema()` fingerprint gate.
- `uv run python tools/check_docs_structure.py`, `tools/check_docs_japanese.py` — pass.

## Completion criteria
- §9.7 no longer ties stale recovery to the legacy age threshold (`REQ-001`).
- §11 covers fingerprint-gate verification, the no-migration statement for the five workflow tables, and data-loss / rollback for `workflow.sqlite`, without a second runbook (`REQ-005`).
- REQ-008 is recorded as a gated follow-on, not written (`REQ-008`).

## Out of Scope
The optional direct lease-constraint check (`REQ-008`, gated on `compat002`); code/schema/test changes (the lease issue owns those); editing `db_03` (reference file, already current).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Gated: REQ-008 (Phase 3) deferred until compat002 implements; Phase 1 (REQ-001/005) safe-now. |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: documentation-only row. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | Documentation checkers in Validation plan. |

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
- **Requirement ID**: `REQ-001`, `REQ-005`, `REQ-008`
- **Source issue**: `issues/20261116-114912_compat003_workflow-lease-docs-runbook.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/done/20261116-224307_compat003_workflow-lease-docs-runbook.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261117-020145
- **Related target files**: `docs/41_db/db_07_api_and_operations-recovery-and-reference.md`
