# Align workflow and DB documentation with the strict lease and definition contract

## Priority
High

## Summary
After the workflow-definition and attempt-lease contracts become strict, update the workflow and DB documentation so current sections describe only current behavior. Remove the lease-less age-threshold recovery description, document the mandatory lease columns and the recovery conditions, and complete the workflow-specific part of the database recreation runbook.

## Background
Source: `memo-issue.md` Issue 3 (items H-06, M-01, M-04, L-03), re-verified against current docs and source.

- Documentation only: `docs/41_db/db_07_api_and_operations-recovery-and-reference.md` section 9.7 still says stale recovery marks "lease-less rows past the legacy age threshold" failed.
- Documentation only: `docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md` still states that lease-less (pre-migration) rows are stale only after a fixed age (3600 s), describes `retry_policy.retry_on` as optional ("when present"), and gives manual-recovery text for lease-less young rows.
- Explicit in code: `StateStore` stale recovery no longer applies an age rule; its docstrings say the legacy age rule was removed and that lease-less rows stay live (see `issues/done/20261109-112715_adrrev005_schema-fingerprint-unify.md`). The docs contradict the code.
- A recreation runbook already exists: `docs/41_db/db_07_api_and_operations-recovery-and-reference.md` section 11 (archive via `rotate_all_dbs()`, delete, recreate via `create_schema()` or the per-database function) and `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md` already states there is no migration and has a recreation-impact table with a rollback column. The memo asked for a new runbook; this issue narrows to the missing workflow-specific parts (see Required Changes).
- `docs/41_db/db_02_architecture_and_schema-schema-reference.md` section 7 describes the workflow tables but has no mention of `owner_id`, `lease_expires_at`, the lease margin, or the absence of heartbeat renewal.
- The memo's `__docs_all.md` was not found anywhere in the repository, and neither was an aggregation script for it. The memo's `docs/30_agent/` path does not exist; the workflow-engine document is under `docs/23_agent/`.

## Problem
An operator who reads the current documentation expects a lease-less attempt to be recovered after an age threshold; the implementation never does that, so the operator may wait for a recovery that will not happen. Removed compatibility behavior is mixed into normative text, which blurs history and available behavior. After the lease columns become `NOT NULL`, nothing in the schema reference explains why an old database is refused and why recreation, not migration, is the response.

## Reason for Change
Critical documentation/code mismatch: the current text can make an operator take a wrong action (waiting for age-based recovery, or manually repairing rows that the schema will no longer allow). The change must land with or after the lease issue, because the documented contract is the strict one.

## Implementation Intent
Make the documentation an accurate operational contract. Current sections describe only current behavior; historical compatibility behavior is either removed or moved to an ADR or a clearly marked historical section. State the lease contract by responsibility and consequence rather than by copied configuration values, and point to the owning code for specifics. Extend the existing recreation runbook instead of adding a second one.

## Target Files or Areas
- `docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md`
- `docs/41_db/db_02_architecture_and_schema-schema-reference.md`
- `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md`
- `docs/41_db/db_07_api_and_operations-recovery-and-reference.md`
- A workflow-lease ADR or amendment under `docs/10_adr/` (existence `不明`; `adr_02_02_001_agent-workflow-engine-mandatory.md` is the only workflow ADR found)

## Required Changes
- Remove active statements that describe: an age threshold for lease-less attempts, the fixed age fallback, pre-migration rows as supported input, omitted `retry_on` as supported, and lease-less writers as an API option. Move any history worth keeping to an ADR or a section marked `removed` or `historical`.
- Document the workflow lease contract: both lease columns are mandatory; the production lease is the stage timeout plus a fixed margin and is therefore never shorter than that margin; no heartbeat or renewal exists; an attempt is stale only when its explicit lease has expired and an old `started_at` alone never makes it stale; recovery deletes the relevant `processed_events` rows only for attempts it marks failed; physical database recovery and logical stale-attempt recovery are separate mechanisms.
- Document the workflow-definition contract: `stages`, `retry_policy`, and `retry_policy.retry_on` are required; list the allowed retry kinds; describe the shipped choice as explicit, not as a default.
- Extend section 11 of `db_07` with the workflow-specific gaps only: a verification step that the startup fingerprint gate accepts the recreated database, an optional direct check of the lease constraints, and an explicit statement that task, attempt, processed-event, artifact, and tool-call-state history is not migrated and that restoring an old archive is a release rollback, not a migration.
- Do not recommend manual `ALTER TABLE`, null filling, schema version stamping, automatic migration, or reusing an incompatible archive with the new binary.
- Remove or rewrite the manual-recovery text for lease-less rows in `agent_03_03`.

## Constraints
- Follows `skills/DESIGN.md` "Docs content policy — remove" and "No concrete configuration values": no implementation-location mapping, no signature tables, no copied timeout or margin values stated as deployed configuration. Describe the policy and point to code.
- Docs are written in English (`skills/DESIGN.md` Output language).
- Every command and function named in the runbook must exist (`rotate_all_dbs()`, `create_workflow_schema()` and the deploy schema gate exist at the time of filing; re-verify).
- Must be implemented after, or together with, the lease issue; documenting `NOT NULL` before it lands would be wrong.

## Acceptance Criteria
- [ ] No current-tense text describes an age threshold or fixed age fallback for lease-less attempts.
- [ ] Workflow-definition required fields in the docs match the loader and models.
- [ ] The lease columns, the margin policy, and the absence of heartbeat renewal are documented.
- [ ] Documented recovery conditions match `StateStore.recover_stale_attempts()` behavior.
- [ ] The recreation runbook covers verification, data loss, and rollback for `workflow.sqlite`, without creating a second runbook.
- [ ] No in-place migration is documented or implied.
- [ ] Historical material, if kept, is marked `removed`, `historical`, or `withdrawn` and is non-normative.
- [ ] Searches of `docs/` for `legacy age threshold`, `lease-less`, `pre-migration`, and wording that treats omitted `retry_on` as supported return only marked historical text.

## Testing Expectations
- Documentation checks: `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py`, `uv run python tools/check_docs_content_policy.py`, `uv run python tools/check_docs_consistency.py --domain agent` and `--domain db`, `uv run python tools/check_docs_japanese.py`, `uv run python tools/check_compat_shims.py`.
- Run `uv run python tools/check_needs_confirmation_inventory.py` if a Needs Confirmation marker is added or removed.
- Manual: confirm every command and function named in the runbook exists; dry-review the runbook against a throwaway workflow database.

## Documentation Impact
This is the documentation change. Information to document: intent and boundaries of the lease contract, recovery conditions, failure behavior when an old database is presented, operational notes for recreation (data loss, rollback), and any Known Issues. If an ADR amendment is chosen for history, run the ADR checkers named in `routing.md`.

## Out of Scope
- Code, schema, or test changes (lease and definition issues).
- Compatibility-checker rules (separate issue).
- Terminology standardization for fallback versus compatibility (separate issue).
- Producing a combined documentation file: `__docs_all.md` does not exist in the repository.

## Dependencies
- Depends on `issues/20261116-114753_compat001_workflow-definition-strict-contract.md` (documented required fields) and `issues/20261116-114834_compat002_mandatory-attempt-leases.md` (documented lease contract).
- Sibling check: no other open issue or in-flight plan touches these documents.

## Unresolved Questions
- Does a workflow-lease ADR or amendment exist, or should history go into a marked section? `不明`.
- The memo requires regenerating `__docs_all.md`; no such file or aggregation process was found. Is it generated elsewhere or obsolete? `不明`; treated as out of scope until confirmed.
- Whether the memo's `docs/41_db/db_04` file needs a change belongs to the checker issue, not here.

## AI Implementation Instruction
Edit only the listed documents. Describe current behavior only; do not copy values or implementation locations. Extend the existing runbook rather than adding a new one. Run the documentation checkers named above before finishing. Stop and report if the ADR question changes the plan.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261116-114912
- **Related target files**: `docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md`, `docs/41_db/db_02_architecture_and_schema-schema-reference.md`, `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md`, `docs/41_db/db_07_api_and_operations-recovery-and-reference.md`
