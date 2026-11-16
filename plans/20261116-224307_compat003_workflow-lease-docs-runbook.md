## Goal
Align the workflow-engine and workflow-DB documentation with the strict lease and workflow-definition contract so current sections describe only current behavior, historical compatibility behavior is removed or clearly marked, and the lease contract plus the database-recreation runbook are fully documented.

## Priority
High

## Scope
- **In-Scope**: Remove age-threshold / lease-less-legacy recovery wording from `docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md` and `docs/41_db/db_07_api_and_operations-recovery-and-reference.md`; document the lease-contract behavior in `agent_03_03` and `docs/41_db/db_02_architecture_and_schema-schema-reference.md`; rewrite the manual-recovery text in `agent_03_03`; extend the `db_07` recreation runbook with the workflow-specific gaps; move the age-rule removal history into `adr_02_02_001_agent-workflow-engine-mandatory.md`. Defer the schema-level `NOT NULL` / `retry_on`-required statements to the frozen compat001 and compat002 Plans (see Implementation steps).
- **Out-of-Scope**: Code, schema, or test changes (the lease and definition issues own those); recommending `ALTER TABLE`, null filling, version stamping, automatic migration, or reusing an incompatible archive; regenerating `__docs_all.md` (not present in the repository); terminology standardization for fallback versus compatibility.
- **Dependencies**: The Issue depends on `issues/20261116-114753_compat001_workflow-definition-strict-contract.md` (documented required fields) and `issues/20261116-114834_compat002_mandatory-attempt-leases.md` (documented lease contract). Both have frozen Plans but neither is implemented yet (source still shows `retry_on` optional and `attempts.owner_id`/`lease_expires_at` nullable).
  - **Depends on**: `plans/20261116-214100_compat001_workflow-definition-strict-contract.md` | phase 3 (documentation) | `retry_on` required documentation (`REQ-007`) and the `agent_03_03` retry-on wording must follow the implemented loader/model contract; sequencing-only overlap on `agent_03_03`.
  - **Depends on**: `plans/20261116-221315_compat002_mandatory-attempt-leases.md` | phase 3 (documentation) | schema-level `NOT NULL` / CHECK lease-column documentation (`REQ-008`) would be wrong before the column becomes `NOT NULL`; documenting the always-stamped behavior is safe now.

## Background
Explicit in code: `scripts/agent/workflow/state_store.py::_classify_running_attempts()` classifies every `running` attempt by `lease_expires_at` only; a lease-less row (`lease_expires_at is None`) is classified `live` and never recovered, and its docstring records that "the lease-less legacy age rule was removed (adrrev005)". `scripts/agent/workflow/idempotency_ops.py::begin_stage_if_new()` is the sole producer and always stamps both `owner_id` (`get_owner_id()`) and `lease_expires_at` (`lease_expires_from(now, lease_duration_sec)` = stage `timeout_sec` + `_LEASE_MARGIN_SEC` = 30 s). `scripts/agent/workflow/models.py::AttemptRecord` carries both columns. `adr_02_02_001_agent-workflow-engine-mandatory.md` (ADR-001) INV-07 already states the lease contract: an Attempt is interrupted when its lease has expired, not by wall-clock age, and `recover_stale_attempts()` recovers only lease-expired rows. Confirmed by repository evidence: the contradicting doc text is at `agent_03_03` line 169 (age rule) and `db_07` §9.7 line 92 ("lease-less rows past the legacy age threshold"); the loader still documents `retry_on` as optional (`workflow_loader.py:27,57,74`); the `attempts` DDL keeps `owner_id TEXT` / `lease_expires_at TEXT` nullable (`schema_sql.py:192-193`). A recreation runbook already exists (`db_07` §11 and `db_03` §recreation-impact table); the memo's `__docs_all.md` and `docs/30_agent/` were not found.

## Problem
An operator who reads the current documentation expects a lease-less attempt to be recovered after an age threshold; the implementation never does that, so the operator may wait for a recovery that will not happen. Removed compatibility behavior is mixed into normative text, which blurs history and available behavior. `agent_03_03` still describes `retry_policy.retry_on` as optional ("when present") and gives manual-recovery text for lease-less young rows; `db_07` §9.7 still ties stale recovery to the legacy age threshold; `db_02` §7 names the workflow tables but never mentions `owner_id`, `lease_expires_at`, the lease margin, or the absence of heartbeat renewal; and `db_07` §11 lacks the workflow-specific verification and rollback statements. After the lease columns become `NOT NULL`, nothing in the schema reference explains why an old database is refused and why recreation, not migration, is the response.

## Reason for Change
Critical documentation/code mismatch: the current text can make an operator take a wrong action (waiting for age-based recovery, or manually repairing rows the schema will no longer allow). The change must land with or after the lease issue, because the documented contract is the strict one. The age-threshold removal itself is already true in source (adrrev005), so aligning the docs to it is safe now; the schema-level `NOT NULL` and `retry_on`-required statements must wait for their implementations.

## Implementation Intent
Make the documentation an accurate operational contract. Current sections describe only current behavior; historical compatibility behavior is either removed or moved to ADR-001's marked historical section. State the lease contract by responsibility and consequence rather than by copied configuration values, and point to the owning code for specifics. Document the workflow-definition contract (required fields, allowed retry kinds, the shipped explicit choice). Extend the existing `db_07` §11 recreation runbook with the workflow-specific gaps instead of adding a second runbook. Split the edits by dependency: the age-threshold removal, lease-contract behavior, allowed retry kinds, manual-recovery rewrite, and ADR history entry match current committed source and land first; the `retry_on`-required and schema-level `NOT NULL` statements defer to the frozen compat001 and compat002 Plans.

## Requirements
- `REQ-001`: Remove current-tense statements that describe an age threshold or fixed-age fallback for lease-less attempts from `agent_03_03` (the "Lease-less (pre-migration) rows use the age rule" bullet and the "lease-less and young" manual-recovery reference) and from `db_07` §9.7 ("lease-less rows past the legacy age threshold"). (`agent_03_03`, `db_07`)
- `REQ-002`: Document the workflow lease-contract behavior in `agent_03_03` and `db_02` §7: both lease columns are always stamped by the sole producer; the production lease is the stage `timeout_sec` plus a fixed margin and is therefore never shorter than that margin; no heartbeat or renewal exists; an attempt is stale only when its explicit lease has expired and an old `started_at` alone never makes it stale; recovery deletes the relevant `processed_events` rows only for attempts it marks failed; physical database recovery and logical stale-attempt recovery are separate mechanisms. (`agent_03_03`, `db_02`)
- `REQ-003`: Document the workflow-definition contract in `agent_03_03`: `stages` and `retry_policy` are required by the loader; list the allowed retry kinds; describe the shipped exception-only choice as explicit, not as a default. (`agent_03_03`)
- `REQ-004`: Rewrite the manual-recovery text in `agent_03_03` to cover only unparseable-timestamp rows (still valid: the source leaves them `running`); remove the "lease-less and young" manual path, which is stale after adrrev005 (lease-less rows stay live and legacy databases are refused by the fingerprint gate). (`agent_03_03`)
- `REQ-005`: Extend `db_07` §11 with the workflow-specific gaps only: a verification step that the startup fingerprint gate accepts the recreated database, an explicit statement that task, attempt, processed-event, artifact, and tool-call-state history is not migrated and that restoring an old archive is a release rollback, not a migration, and the data-loss / rollback coverage for `workflow.sqlite`. Defer the optional direct lease-constraint check to `REQ-008`. (`db_07`)
- `REQ-006`: Move the age-rule removal history into `adr_02_02_001_agent-workflow-engine-mandatory.md` Known Deviations, marked `historical` / `removed` and non-normative. (`adr_02_02_001_agent-workflow-engine-mandatory.md`)
- `REQ-007`: In `agent_03_03`, state that `retry_policy.retry_on` is a required key once compat001 lands, replacing the current "when present" wording. Defer until `compat001` implements. (`agent_03_03`)
- `REQ-008`: In `db_02` §7, state that `owner_id` and `lease_expires_at` are enforced `NOT NULL` (with `CHECK(length(owner_id) > 0)`) at the schema level once compat002 lands, and add an optional direct lease-constraint check to `db_07` §11. Defer until `compat002` implements. (`db_02`, `db_07`)

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md` | Remove the age-rule bullet (line 169) and the "lease-less and young" manual-recovery reference (line 175); rewrite manual recovery to cover only unparseable timestamps; document the lease-contract behavior and the definition contract (required `stages`/`retry_policy`, allowed retry kinds); later add `retry_on` required once compat001 lands. | REQ-001, REQ-002, REQ-003, REQ-004, REQ-007; AC: no current-tense age-threshold text; lease columns/margin/heartbeat documented; definition required fields match loader; recovery conditions match `recover_stale_attempts()`. | Age rule at `agent_03_03:169`; manual recovery at `agent_03_03:175`; `retry_on` "when present" at `agent_03_03:133,156`. (checked in Step 2) | None | Verified |
| `docs/41_db/db_02_architecture_and_schema-schema-reference.md` | Add the lease contract to §7 (workflow tables): both columns always stamped by the sole producer, lease = stage `timeout_sec` + fixed margin, no heartbeat/renewal; later add the schema-level `NOT NULL` / CHECK once compat002 lands. | REQ-002, REQ-008; AC: lease columns, margin policy, and absence of heartbeat renewal documented. | §7 lists the workflow tables but omits `owner_id`/`lease_expires_at`/margin/heartbeat (Issue Background; confirmed `db_02` §7 read in Step 2). | None | Verified |
| `docs/41_db/db_07_api_and_operations-recovery-and-reference.md` | Remove the age-threshold phrase from §9.7 (line 92); extend §11 with the fingerprint-gate verification step, the no-migration / data-loss / rollback statement for `workflow.sqlite`, and (later) an optional direct lease-constraint check. | REQ-001, REQ-005, REQ-008; AC: §9.7 no longer ties recovery to age; runbook covers verification, data loss, rollback without a second runbook. | §9.7 age phrase at `db_07:92`; §11 exists but lacks the workflow-specific verification/rollback statements (Step 2). | None | Verified |
| `docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md` | Add the age-rule removal history to the Known Deviations section, marked `historical` / `removed` and non-normative. | REQ-006; AC: historical material marked and non-normative. | ADR-001 INV-07 already states the current lease contract; Known Deviations section exists (Step 2). | None | Verified |

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
| `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md` | Verify the recreation-impact table and no-migration statement already cover `workflow.sqlite` data loss and rollback; my Step 2 read confirms they do, so no substantive edit is required. Listed by the Issue as a target area to check. | `docs/41_db/db_07_api_and_operations-recovery-and-reference.md` (`REQ-005`) |
| `scripts/agent/workflow/state_store.py` | Source of truth for lease-based stale recovery and the adrrev005 age-rule removal (`_classify_running_attempts`, `recover_stale_attempts`). | `agent_03_03` (`REQ-001`, `REQ-002`), `db_07` (`REQ-001`) |
| `scripts/agent/workflow/idempotency_ops.py` | Sole producer that stamps `owner_id` and `lease_expires_at` (stage `timeout_sec` + `_LEASE_MARGIN_SEC` = 30 s). | `agent_03_03`, `db_02` (`REQ-002`) |
| `scripts/agent/workflow/models.py` | `AttemptRecord` columns and `ATTEMPT_STATUSES` mirror the DDL; confirm the lease columns are part of the model. | `agent_03_03`, `db_02` (`REQ-002`) |
| `scripts/agent/workflow/workflow_loader.py` | Current loader contract: `retry_on` still optional (`_REQUIRED_POLICY_KEYS`), stages/`retry_policy` required by the loader. Baseline before the compat001 change. | `agent_03_03` (`REQ-003`, `REQ-007`) |
| `issues/done/20261109-112715_adrrev005_schema-fingerprint-unify.md` | Records the committed age-rule removal that makes the doc's age-threshold description stale. | `agent_03_03`, `db_07` (`REQ-001`), `adr_02_02_001` (`REQ-006`) |
| `plans/20261116-214100_compat001_workflow-definition-strict-contract.md` | Frozen contract for the required `retry_on` key that `REQ-007` documents after compat001 implements. | `agent_03_03` (`REQ-007`) |
| `plans/20261116-221315_compat002_mandatory-attempt-leases.md` | Frozen contract for the `NOT NULL` / CHECK lease columns that `REQ-008` documents after compat002 implements. | `db_02` (`REQ-008`), `db_07` (`REQ-008`) |
| `config/workflows/default.json` | Shipped definition; confirm it declares `retry_on: ["exception"]` so the "explicit shipped choice" wording in `REQ-003` is accurate. | `agent_03_03` (`REQ-003`) |

## Acceptance Criteria
- [ ] No current-tense text describes an age threshold or fixed age fallback for lease-less attempts. (`REQ-001`)
- [ ] The lease columns, the margin policy, and the absence of heartbeat renewal are documented. (`REQ-002`, `REQ-008`)
- [ ] Workflow-definition required fields in the docs match the loader and models; allowed retry kinds are listed. (`REQ-003`)
- [ ] Documented recovery conditions match `StateStore.recover_stale_attempts()` behavior. (`REQ-001`, `REQ-002`)
- [ ] The recreation runbook covers verification, data loss, and rollback for `workflow.sqlite`, without creating a second runbook. (`REQ-005`)
- [ ] Manual-recovery text no longer promises automated or manual recovery for lease-less young rows. (`REQ-004`)
- [ ] Historical material, if kept, is marked `removed`, `historical`, or `withdrawn` and is non-normative. (`REQ-006`)
- [ ] No in-place migration is documented or implied. (`REQ-005`)
- [ ] Once compat001 lands, `retry_policy.retry_on` is documented as required; once compat002 lands, the lease columns are documented as schema-enforced `NOT NULL`. (`REQ-007`, `REQ-008`)
- [ ] Searches of `docs/` for `legacy age threshold`, `lease-less`, `pre-migration`, and wording that treats omitted `retry_on` as supported return only marked historical text. (Issue)

## Tests
- Documentation checks: `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py`, `uv run python tools/check_docs_content_policy.py`, `uv run python tools/check_docs_consistency.py --domain agent` and `--domain db`, `uv run python tools/check_docs_japanese.py`, `uv run python tools/check_compat_shims.py`.
- If a Needs Confirmation marker is added or removed: `uv run python tools/check_needs_confirmation_inventory.py`.
- If the ADR Known Deviations entry is added: run the ADR checkers named in `routing.md`.
- Manual: confirm every command and function named in the runbook exists (`rotate_all_dbs()`, `create_workflow_schema()`, the deploy schema gate); dry-review the runbook against a throwaway workflow database.

## Documentation Impact
This is the documentation change. Information to document: intent and boundaries of the lease contract, recovery conditions, failure behavior when an old database is presented, operational notes for recreation (data loss, rollback), and the age-rule removal history in ADR-001. Driven by `REQ-001` through `REQ-008`. The target docs, resolved by task via `docs/00_index.md` / `routing.md`: the workflow-engine document under `docs/23_agent/` (`agent_03_03`), the schema reference and recovery-and-reference doc under `docs/41_db/` (`db_02`, `db_07`), and the workflow-engine ADR under `docs/10_adr/` (`adr_02_02_001`).

## Assumptions
- The age-threshold removal (`REQ-001`, `REQ-006`) is justified by the current committed source (`adrrev005` removed the rule; `_classify_running_attempts` classifies lease-less rows `live`), so those doc edits are safe to execute now, independent of the compat002 implementation. This corrects the Issue's framing that everything must wait for the lease issue.
- `adr_02_02_001_agent-workflow-engine-mandatory.md` (ADR-001) INV-07 already states the full lease contract, so no new workflow-lease ADR is needed; the age-rule removal history goes into ADR-001's Known Deviations as marked, non-normative text. This resolves the Issue's `不明` ADR question.
- The schema-level `NOT NULL` / `retry_on`-required statements (`REQ-007`, `REQ-008`) are deferred to the frozen compat001 and compat002 Plans; their exact wording is pinned there and finalized at implementation time. Documenting the always-stamped lease behavior and the allowed retry kinds now does not contradict the current nullable / optional source.
- The `agent_03_03` overlap with `compat001` is sequencing-only: both want to document the `retry_on` contract in the same file. `compat001` implements the loader/model contract first; `REQ-007` documents the resulting required `retry_on`. The two edits must not clobber each other's lines — `compat001` owns the loader-validation section wording and `REQ-007` adopts it; this is recorded as a sequencing dependency in `Scope`.
- Documentation changes have no runtime blast radius; `deploy.sh` serves docs statically (rsynced), so there is no deploy-gate impact.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Does a workflow-lease ADR or amendment exist, or should history go into a marked section? (`Issue` Unresolved Questions) | None — `adr_02_02_001_agent-workflow-engine-mandatory.md` INV-07 already documents the lease contract. | Resolved: use ADR-001 Known Deviations (`REQ-006`). | False |
| UNK-02 | Is the memo's `__docs_all.md` generated elsewhere or obsolete? (`Issue` Unresolved Questions) | None — the file and any aggregation script are absent from the repository (`Issue` Background). | Resolved: out of scope (`Issue` Out of Scope). | False |

No item from Step 2 remains `Needs confirmation`; nothing is `BLOCKING`.

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md` | Modify | Low — documentation only; high 30-day churn means watch for merge conflict with `compat001`'s edit | 13 | Multiple contributors | not applicable (rsynced) |
| `docs/41_db/db_02_architecture_and_schema-schema-reference.md` | Modify | Low — documentation only | 12 | Multiple contributors | not applicable (rsynced) |
| `docs/41_db/db_07_api_and_operations-recovery-and-reference.md` | Modify | Low — documentation only; highest 30-day churn, actively maintained | 26 | Multiple contributors | not applicable (rsynced) |
| `docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md` | Modify | Low — ADR addition; run ADR checkers | 11 | Multiple contributors | not applicable (rsynced) |

## Design
Three design decisions the Issue left open are resolved below with rationale and compatibility impact.

### Decision 1 — Where the age-rule history lives: ADR Known Deviations, not a new ADR
- **Choice**: move the age-rule removal history into `adr_02_02_001_agent-workflow-engine-mandatory.md` Known Deviations, marked `historical` / `removed` and non-normative. Do not create a new workflow-lease ADR.
- **Alternatives considered**: a dedicated `adr_02_02_00X_agent-workflow-lease` ADR. This would duplicate INV-07 (which already states the lease contract) and add an ADR that operators must discover.
- **Rationale for the choice**: ADR-001 INV-07 already captures the lease contract completely, and ADR-001 is the single workflow ADR. History belongs in a marked, non-normative section beside the invariant it supplements, per the Issue's "move to an ADR or a section marked `removed`/`historical`" instruction.
- **Compatibility impact**: additive; the ADR checkers in `routing.md` must run (see Tests).

### Decision 2 — Split edits by dependency, not by the Issue's single "after the lease issue" gate
- **Choice**: Phase 1 lands the age-threshold removal, lease-contract behavior, allowed retry kinds, manual-recovery rewrite, and ADR history entry; Phase 2 defers the `retry_on`-required statement to `compat001`; Phase 3 defers the schema-level `NOT NULL` / CHECK statement and the runbook lease-constraint check to `compat002`.
- **Alternatives considered**: defer every edit until both compat001 and compat002 implement. This over-blocks: the age-threshold removal and lease-behavior documentation already match the current committed source (`adrrev005`, `idempotency_ops`), so holding them back adds no safety and leaves a known code/doc mismatch in place longer.
- **Rationale for the choice**: the Issue's constraint "documenting `NOT NULL` before it lands would be wrong" applies only to the schema-enforcement statements, not to the always-stamped behavior or the already-removed age rule. Separating them lets the safe-now edits land immediately while the schema-level statements stay gated.
- **Compatibility impact**: Phase 1 introduces no doc/source mismatch; Phases 2-3 are explicitly gated so they never run before their dependencies.

### Decision 3 — `db_03` is a reference file, not a target
- **Choice**: list `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md` under Reference Files and make no edit.
- **Rationale for the choice**: my Step 2 read confirms its recreation-impact table already covers `workflow.sqlite` data loss and rollback and its no-migration policy is current; the Issue itself notes it "already states there is no migration and has a recreation-impact table with a rollback column." No modification-target row is added for a file that needs no change.

## Implementation steps
Each step description MUST cite the exact file path(s) it touches by referencing rows
of `Implementation Target Files` above — do not restate file-level detail
independently of that frozen table. A step is a top-level numbered item (a Phase); its
checklist items are sub-tasks, and the Execution Status table has one row per step.
Declare a release unit (see `### Release units` below) when a phase breaks existing callers or
tests until another phase lands (for example a `NOT NULL` column added before its write path):
one line per unit, `**Unit**: {name} | **Phases**: {N, N} | **Reason**: {why the members cannot be
validated alone}`.

1. **Phase 1: Safe-now doc alignment (matches current committed source)**
   - [ ] REQ-001; `docs/23_agent/agent_03_03-turn-processing-flow-workflow-engine.md` — remove the "Lease-less (pre-migration) rows use the age rule" bullet (line 169) and the "lease-less and young" manual-recovery reference (line 175).
   - [ ] REQ-001; `docs/41_db/db_07_api_and_operations-recovery-and-reference.md` — remove the "lease-less rows past the legacy age threshold" phrase from §9.7 (line 92).
   - [ ] REQ-002; `agent_03_03` — document the lease-contract behavior: both columns always stamped by the sole producer, lease = stage `timeout_sec` + fixed margin, no heartbeat/renewal, stale only when the explicit lease expired, recovery deletes `processed_events` only for failed attempts, physical vs logical recovery separate. Point to `state_store.py` / `idempotency_ops.py`.
   - [ ] REQ-002; `docs/41_db/db_02_architecture_and_schema-schema-reference.md` — add the lease-contract behavior to §7 (workflow tables).
   - [ ] REQ-003; `agent_03_03` — state `stages` and `retry_policy` are required by the loader, list the allowed retry kinds, and describe the shipped exception-only choice as explicit (confirm against `config/workflows/default.json`).
   - [ ] REQ-004; `agent_03_03` — rewrite the manual-recovery text to cover only unparseable-timestamp rows; drop the "lease-less and young" path.
   - [ ] REQ-006; `docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md` — add the age-rule removal history to Known Deviations, marked `historical` / `removed`, non-normative.
   - [ ] REQ-005; `db_07` — extend §11 with the fingerprint-gate verification step, the no-migration / data-loss / rollback statement for `workflow.sqlite`, and the "old archive restore is a release rollback, not a migration" statement. Defer the optional direct lease-constraint check to Phase 3.
   - [ ] Run the documentation checks in `Tests`; run the ADR checkers named in `routing.md` for the ADR edit.
2. **Phase 2: `retry_on` required documentation (gated on `compat001` implementing)**
   - [ ] REQ-007; `agent_03_03` — replace the "when present" `retry_on` wording with a required-key statement that matches the implemented loader/model contract from `plans/20261116-214100_compat001_workflow-definition-strict-contract.md`. Coordinate the wording with `compat001`'s edit to the same file so the two do not clobber each other. Blocked until `compat001` implements.
3. **Phase 3: Schema-level lease-column documentation (gated on `compat002` implementing)**
   - [ ] REQ-008; `docs/41_db/db_02_architecture_and_schema-schema-reference.md` — state `owner_id` and `lease_expires_at` are enforced `NOT NULL` (with `CHECK(length(owner_id) > 0)`) at the schema level, matching `plans/20261116-221315_compat002_mandatory-attempt-leases.md`. Blocked until `compat002` implements.
   - [ ] REQ-008; `db_07` — add the optional direct lease-constraint check to §11. Blocked until `compat002` implements.
   - [ ] Re-run `check_docs_consistency.py --domain db` after Phase 3.

### Release units
N/A: no release unit. The doc edits do not break callers or tests; the gated Phases 2-3 are blocked by external dependencies, not by intra-plan validation ordering.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `agent_03_03` | Doc quality/consistency: no age-threshold text, lease contract documented, definition required fields match loader, manual recovery narrowed. | `uv run python tools/check_docs_quality.py`, `tools/check_docs_content_policy.py`, `tools/check_docs_consistency.py --domain agent` | All pass; no new errors. |
| `db_02`, `db_07` | Doc quality/consistency: lease columns/margin documented; runbook covers verification/data-loss/rollback; no migration implied. | `uv run python tools/check_docs_quality.py`, `tools/check_docs_content_policy.py`, `tools/check_docs_consistency.py --domain db` | All pass; no new errors. |
| `adr_02_02_001` | ADR structure/history-marking checks per `routing.md`. | ADR checkers in `routing.md` | Pass; history section marked non-normative. |
| Whole change | Documentation checks + compat-shim + needs-confirmation inventory if a marker changes. | `tools/check_docs_structure.py`, `tools/check_docs_japanese.py`, `tools/check_compat_shims.py`, `tools/check_needs_confirmation_inventory.py` | All pass. |

## Risks
- **Risk**: The `agent_03_03` edit overlaps with `compat001`'s edit to the same file (both touch the `retry_on` / loader-validation section), risking a merge conflict or clobbered wording when both implement. → **Mitigation**: `compat001` implements first and owns the loader-validation section wording; `REQ-007` (Phase 2) adopts that wording and touches only the sections `compat001` does not; the overlap is recorded as a sequencing dependency in `Scope` and re-checked by `check_plan_target_overlaps.py` at freeze.
- **Risk**: Documenting the schema-level `NOT NULL` / `retry_on`-required statements before their implementations land would create a doc/source mismatch (the Issue's explicit concern). → **Mitigation**: Phases 2-3 are explicitly gated behind `compat001`/`compat002` implementing; only the always-stamped lease behavior and allowed retry kinds (true in current source) land in Phase 1.
- **Risk**: Removing the age-threshold text could over-delete legitimate historical context. → **Mitigation**: the history is preserved in `adr_02_02_001` Known Deviations (`REQ-006`), marked historical and non-normative.
- **Risk**: Doc wording drifts from `check_docs_content_policy.py` ("No concrete configuration values") by copying timeout/margin values. → **Mitigation**: describe the policy (lease = stage timeout + fixed margin) and point to `idempotency_ops.py` / `workflow_engine._LEASE_MARGIN_SEC`; do not state the 30 s value as deployed configuration.
- **Risk**: Naming a runbook command/function that does not exist. → **Mitigation**: manual confirmation that `rotate_all_dbs()`, `create_workflow_schema()`, and the deploy fingerprint gate exist before finishing (`Tests`).

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Safe-now doc alignment: `agent_03_03`, `db_02`, `db_07`, `adr_02_02_001` | Pending | — | — | Matches current committed source; runs now |
| 2 | `retry_on` required documentation in `agent_03_03` | Pending | — | — | Gated on `compat001` implementing |
| 3 | Schema-level lease-column documentation in `db_02`/`db_07` | Pending | — | — | Gated on `compat002` implementing |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: `issues/20261116-114912_compat003_workflow-lease-docs-runbook.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261116-224307
- **Related target files**: `docs/23_agent/agent_03_03-turn-processing-flow-workflow-engine.md`, `docs/41_db/db_02_architecture_and_schema-schema-reference.md`, `docs/41_db/db_07_api_and_operations-recovery-and-reference.md`, `docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md` — the full list of `File Path` values from `Implementation Target Files` above, once `Frozen`

### Requirement Traceability
See `templates/requirement-traceability.md` for the canonical column format.

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Issue "Required Changes" (age-threshold bullet); Issue AC line 50, 53 | `agent_03_03`, `db_07` | Step 1 | No current-tense age-threshold text; recovery conditions match `recover_stale_attempts()` | `check_docs_consistency.py --domain agent/--domain db` | Confirmed by repository evidence |
| REQ-002 | Issue "Required Changes" (lease contract bullet); Issue AC line 52 | `agent_03_03`, `db_02` | Step 1 | Lease columns, margin policy, heartbeat absence documented | `check_docs_content_policy.py` | Confirmed by repository evidence |
| REQ-003 | Issue "Required Changes" (definition contract bullet); Issue AC line 51 | `agent_03_03` | Step 1 | Definition required fields match loader and models | `check_docs_consistency.py --domain agent` | Confirmed by repository evidence |
| REQ-004 | Issue "Required Changes" (manual-recovery bullet); Issue AC line 56 | `agent_03_03` | Step 1 | Manual recovery no longer promises lease-less young-row recovery | `check_docs_consistency.py --domain agent` | Derived from confirmed evidence |
| REQ-005 | Issue "Required Changes" (runbook bullet); Issue AC line 54, 56 | `db_07` | Step 1 | Runbook covers verification, data loss, rollback without a second runbook | `check_docs_consistency.py --domain db`; manual runbook existence check | Confirmed by repository evidence |
| REQ-006 | Issue "Unresolved Questions" (ADR existence); Issue AC line 56 | `adr_02_02_001` | Step 1 | Historical material marked and non-normative | ADR checkers in `routing.md` | Resolved at plan time |
| REQ-007 | Issue "Required Changes" (definition contract); Issue Constraints line 47 | `agent_03_03` | Step 2 | `retry_on` documented as required after compat001 | `check_docs_consistency.py --domain agent` | Derived from confirmed evidence |
| REQ-008 | Issue "Required Changes" (lease columns); Issue Constraints line 47 | `db_02`, `db_07` | Step 3 | Lease columns documented as schema-enforced `NOT NULL` after compat002 | `check_docs_consistency.py --domain db` | Derived from confirmed evidence |
