## Goal

Move the age-rule removal history into `adr_02_02_001_agent-workflow-engine-mandatory.md` Known Deviations, marked `historical` / `removed` and non-normative (`REQ-006`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- `REQ-006` matches current committed source: the ADR-001 INV-07 already states the full current lease contract (an Attempt is interrupted when its lease has expired, not by wall-clock age; `recover_stale_attempts()` recovers only lease-expired rows — `adr_02_02_001:70,172`; `state_store.py:365-419`). The age-rule removal was committed by adrrev005 (`issues/done/20261109-112715_adrrev005_schema-fingerprint-unify.md:43`).
- The Known Deviations section currently reads "Not applicable" (`adr_02_02_001:229-231`); adding marked, non-normative history is appropriate there.
- Adding a Known Deviations entry triggers the ADR checkers in `routing.md` (see Validation plan).

## Design decisions
- **Append a single marked, non-normative entry** to Known Deviations describing that a pre-migration age-threshold rule existed (lease-less rows recovered after a fixed age) and was removed by adrrev005; it is historical and non-normative and does not describe current behavior. Keep it beside INV-07, which already captures the current lease contract.

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
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: documentation-only row. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | ADR checkers + doc checkers in Validation plan. |

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
- **Requirement ID**: `REQ-006`
- **Source issue**: `issues/20261116-114912_compat003_workflow-lease-docs-runbook.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/done/20261116-224307_compat003_workflow-lease-docs-runbook.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261117-020145
- **Related target files**: `docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md`
