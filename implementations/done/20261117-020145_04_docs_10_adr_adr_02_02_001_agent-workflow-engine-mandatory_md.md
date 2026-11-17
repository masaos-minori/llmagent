## Goal

Move the age-rule removal history into `adr_02_02_001_agent-workflow-engine-mandatory.md` Known Deviations, marked `historical` / `removed` and non-normative (`REQ-006`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- `REQ-006` matches current committed source: the ADR-001 INV-07 already states the full current lease contract (an Attempt is interrupted when its lease has expired, not by wall-clock age; `recover_stale_attempts()` recovers only lease-expired rows — `adr_02_02_001:70,172`; `state_store.py:365-419`). The age-rule removal was committed by adrrev005 (`issues/done/20261109-112715_adrrev005_schema-fingerprint-unify.md`; recorded in code as the `_classify_running_attempts()` / `recover_stale_attempts()` docstrings at `state_store.py:230-231,369-370`).
- The Known Deviations section currently reads "Not applicable" (`adr_02_02_001:229-231`).
- Adding a Known Deviations entry triggers the ADR checkers in `routing.md` (see Validation plan).
- **BLOCKED (adversarial verification 20261117): the planned edit conflicts with two enforced governance rules and must not be implemented as written.** (a) `check_known_deviation_sync.py` (rule GV-022, pre-commit blocking): a top-level Known Deviations bullet must cite a canonical Known Issue ledger ID (`docs/00_governance/governance_03_issue-and-uncertainty-management.md` Part 1) — a history note has no such ID (ERROR) — and resolved/removed items are not allowed in active documents (Current-Specification-Only Policy, ERROR). (b) `governance_01_documentation-policy.md` "ADR Responsibilities and Historical Content": "an ADR holds no Amendment section, and **history stays in version control**". No ledger entry exists for the removed age rule, and none of the active docs cites one (verified 20261117: the age-rule wording was removed from `agent_03_03` and `db_07` by procedures 020145_01/03). A compliant variant of REQ-006 would need a governance amendment or a ledger entry for a resolved item, which the Current-Specification-Only Policy forbids. The history is already preserved in version control, `issues/done/20261109-112715_adrrev005_schema-fingerprint-unify.md`, the code docstrings, and INV-07's current wording.

## Design decisions
- **Blocked — do not append to Known Deviations.** The original decision (append a single marked, non-normative history entry beside INV-07) is overridden by the 20261117 verification: GV-022 (Known Deviations bullets require a canonical Known Issue ledger ID; resolved/removed items are ERROR) and governance_01's "history stays in version control" make the planned placement non-compliant. Keep INV-07 as the sole normative statement of the current lease contract; the removed age-rule's history remains in version control and `issues/done/20261109-112715_adrrev005_schema-fingerprint-unify.md`. Landing REQ-006 would require a governance amendment or an open ledger item — an owner decision, recorded in the Blocker Log.

## Alternatives considered
- **Creating a dedicated workflow-lease ADR.** Rejected: it would duplicate INV-07 (which already states the lease contract) and add an ADR operators must discover; history belongs in ADR-001's marked Known Deviations section.

## Implementation
### Target file
`docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md`
### Procedure
1. Replace the "Not applicable" body of the Known Deviations section (line 231) with a single marked, non-normative entry recording the age-rule removal history.
### Method
One section body replacement.
### Details
- Replace line 231 ("Not applicable") with:
  ```markdown
  - **Historical — removed age-based stale-recovery rule (adrrev005).** Before adrrev005, a pre-migration rule reclaimed lease-less legacy attempt rows after a fixed wall-clock age, independent of lease. That rule was removed: the sole attempts writer always stamps a lease, so post-migration staleness is decided by `lease_expires_at` only (see INV-07). This entry records the removed behavior for history; it is non-normative and describes no current behavior.
  ```
  The marker words `Historical` / `removed` make the non-normative status explicit.
- Run the ADR checkers named in `routing.md` for the Known Deviations addition (see Validation plan).

## Compatibility considerations
N/A: documentation only; no runtime blast radius. `deploy.sh` serves docs statically (rsynced). The ADR edit triggers ADR checkers.

## Security considerations
N/A.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- ADR checkers in `routing.md` for the Known Deviations addition (e.g. `check_known_deviation_sync.py`, `check_adr_structure.py`, and any ADR-invariant checkers the addition touches) — pass; history section marked non-normative.
- `uv run python tools/check_docs_quality.py`, `tools/check_docs_structure.py`, `tools/check_docs_japanese.py` — pass.

## Completion criteria
- The age-rule removal history is recorded in Known Deviations, marked `historical` / `removed` and non-normative (`REQ-006`).

## Out of Scope
Creating a new workflow-lease ADR; changing INV-07 or any invariant wording; code/schema changes.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Superseded | — | — | Blocked by governance conflict (GV-022 + governance_01 historical-content rule). Target file untouched; no non-compliant edit applied. Superseded: REQ-006 has no compliant placement: GV-022 requires a canonical Known Issue ledger ID in Known Deviations bullets and forbids resolved/removed items; governance_01 keeps ADR history in version control. INV-07 already states the current lease contract; the age-rule removal history stays in version control and issues/done/20261109-112715_adrrev005_schema-fingerprint-unify.md. Owner decision 2026-11-17. |
| 2 | Add or update tests per Validation plan | Superseded | — | — | N/A: documentation-only row. Superseded: REQ-006 has no compliant placement: GV-022 requires a canonical Known Issue ledger ID in Known Deviations bullets and forbids resolved/removed items; governance_01 keeps ADR history in version control. INV-07 already states the current lease contract; the age-rule removal history stays in version control and issues/done/20261109-112715_adrrev005_schema-fingerprint-unify.md. Owner decision 2026-11-17. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Superseded | — | — | ADR checkers + doc checkers in Validation plan. Superseded: REQ-006 has no compliant placement: GV-022 requires a canonical Known Issue ledger ID in Known Deviations bullets and forbids resolved/removed items; governance_01 keeps ADR history in version control. INV-07 already states the current lease contract; the age-rule removal history stays in version control and issues/done/20261109-112715_adrrev005_schema-fingerprint-unify.md. Owner decision 2026-11-17. |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | REQ-006's planned placement (historical entry in Known Deviations) conflicts with GV-022 (`check_known_deviation_sync.py`: Known Deviations bullets require a canonical Known Issue ledger ID; resolved/removed items are ERROR) and governance_01 "history stays in version control". No compliant edit exists without a governance amendment or an open ledger item — owner decision required. | No | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-006`
- **Source issue**: `issues/20261116-114912_compat003_workflow-lease-docs-runbook.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/done/20261116-224307_compat003_workflow-lease-docs-runbook.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261117-020145
- **Related target files**: `docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md`