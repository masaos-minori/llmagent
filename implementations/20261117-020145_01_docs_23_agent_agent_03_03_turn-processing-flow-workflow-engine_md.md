## Goal

Align `agent_03_03` with the strict lease and workflow-definition contract: remove the age-threshold / lease-less-legacy recovery wording (REQ-001, REQ-004), document the lease-contract behavior (REQ-002), document the workflow-definition required-fields contract and allowed retry kinds (REQ-003), and later add the `retry_on`-required statement once `compat001` implements (REQ-007, gated).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- `REQ-001`/`REQ-004` edits match current committed source: `_classify_running_attempts()` classifies by `lease_expires_at` only, lease-less rows stay `live`, and the docstring records the adrrev005 age-rule removal (`scripts/agent/workflow/state_store.py:365-419`); the adrrev005 issue removed the lease-less legacy reclaim (`issues/done/20261109-112715_adrrev005_schema-fingerprint-unify.md:43`). Safe to edit now, independent of the compat002 implementation.
- `REQ-002` lease behavior matches the sole producer `idempotency_ops::begin_stage_if_new()`: both `owner_id` (`get_owner_id()`) and `lease_expires_at` (`lease_expires_from(now, lease_duration_sec)` = stage `timeout_sec` + `_LEASE_MARGIN_SEC` = 30 s) are always stamped (`scripts/agent/workflow/idempotency_ops.py:9,38,51-55,64-67`).
- `REQ-003` loader contract: `stages` and `retry_policy` are **required** keys (`_validate` rejects a missing `stages`/`retry_policy` at `workflow_loader.py:119-121`; `retry_policy` is `_require_dict`'d and its `_REQUIRED_POLICY_KEYS` checked at `:150-154`); the allowed retry kinds are `exception`/`timeout`/`llm_failure`; the shipped default is `["exception"]` (`config/workflows/default.json:24`). The current doc line 154 says "`retry_policy`, when present" — that is a doc/source mismatch this row corrects.
- `REQ-007` (Phase 2) is gated on `compat001` implementing: the exact required-key wording is pinned in `plans/done/20261116-214100_compat001_workflow-definition-strict-contract.md`. The current source still treats `retry_on` as optional (`_REQUIRED_POLICY_KEYS = {"max_attempts", "retry_wait_sec"}`, no `retry_on` at `workflow_loader.py:57`), so the required statement must not land yet.
- `agent_03_03` overlaps `compat001` on the same file (sequencing-only): `compat001` owns the loader-validation section wording; this row's Phase 1 edits touch different sections and must not clobber it.

## Design decisions
- **Describe the lease contract by responsibility and consequence, not copied config.** State that both columns are always stamped by the sole producer, the lease equals the stage `timeout_sec` plus a fixed margin and is therefore never shorter than that margin, no heartbeat/renewal exists, an attempt is stale only when its explicit lease expired and an old `started_at` alone never makes it stale, and recovery deletes `processed_events` only for failed attempts — pointing to `state_store.py` / `idempotency_ops.py` for specifics. Do not state the 30 s value as deployed configuration (avoids `check_docs_content_policy.py` "No concrete configuration values").
- **Split Phase 1 vs Phase 2 within this file.** Phase 1 (REQ-001/002/003/004) lands now; REQ-007 (Phase 2) is documented as a gated follow-on whose wording is adopted from `compat001` once it implements.

## Alternatives considered
- **Writing REQ-007 now alongside REQ-003.** Rejected: the source still treats `retry_on` as optional, so a required-key statement would create a doc/source mismatch (the Issue's explicit concern). Deferred to `compat001`.

## Implementation
### Target file
`docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md`
### Procedure
**Phase 1 (safe-now, executable now):**
1. **REQ-001** — Remove the "Lease-less (pre-migration) rows use the age rule" bullet at line 169.
2. **REQ-004** — Rewrite the manual-recovery paragraph at line 175 to cover only unparseable-timestamp rows; drop the "lease-less and young" path.
3. **REQ-002** — Add the lease-contract behavior to the Startup Recovery section (both columns always stamped by the sole producer; lease = stage `timeout_sec` + fixed margin; no heartbeat/renewal; stale only when the explicit lease expired; old `started_at` alone never stale; recovery deletes `processed_events` only for failed attempts; physical vs logical recovery separate). Point to `state_store.py` / `idempotency_ops.py`.
4. **REQ-003** — In "Workflow Loader Validation Rules", state `stages` and `retry_policy` are **required** by the loader (correct the current "when present" wording at line 154); list the allowed retry kinds (`exception`/`timeout`/`llm_failure`); describe the shipped `["exception"]` choice as an explicit shipped selection, not a fallback default (correct the "shipped default" wording at line 134).
**Phase 2 (gated on `compat001`):**
5. **REQ-007** — Replace the "when present" `retry_on` wording with a required-key statement matching the implemented loader/model contract from `compat001`. Blocked until `compat001` implements.
### Method
Two removals, one manual-recovery rewrite, one lease-contract addition, two loader-wording corrections (Phase 1); one required-key replacement (Phase 2, gated).
### Details
- **Line 169** — delete the bullet: "Lease-less (pre-migration) rows use the age rule: they are stale only when `started_at` is older than 3600 s."
- **Line 175** — change "Manual recovery for rows left `running` (unparseable or lease-less and young): ..." to cover only unparseable timestamps: "Manual recovery for rows left `running` due to an unparseable `started_at`/`lease_expires_at`: identify the owning process from `owner_id` (`hostname-pid-random`), confirm the process is gone, then correct the row via manual SQL against the workflow database. There is no automated takeover for these rows. Lease-less rows do not exist post-migration (the sole writer always stamps a lease); legacy databases holding them are refused by the fingerprint gate and recreated, not manually repaired."
- **Lease-contract addition** — after the expired-lease bullet (line 168), before the deleted age-rule bullet, insert the lease-contract narrative. Keep it responsibility/consequence level; cite `scripts/agent/workflow/state_store.py::_classify_running_attempts()` and `scripts/agent/workflow/idempotency_ops.py::begin_stage_if_new()`.
- **Loader rules (lines 152-157)** — make `stages` and `retry_policy` required (they are, per `workflow_loader.py:119-121,150-154`); change "`retry_policy`, when present, must itself be an object" to "`retry_policy` is required and must itself be an object"; keep "`retry_policy.retry_on`, when present, must be a list of strings ...; an absent key loads the default `["exception"]`" (retry_on remains optional within a required retry_policy — unchanged).
- **Line 134** — change "(shipped default: `["exception"]`)" to describe the shipped explicit choice without calling it a default, e.g. "(the shipped definition selects `["exception"]` explicitly)".
- **REQ-007 (Phase 2, gated)** — leave a clearly marked placeholder: "GATED — once `compat001` implements, replace the required-`retry_policy` wording above with a statement that `retry_policy.retry_on` is a required key, adopting `compat001`'s loader-validation wording." Do not write the required-key statement now.

## Compatibility considerations
N/A: documentation only; no runtime blast radius. `deploy.sh` serves docs statically (rsynced). The `agent_03_03` edit sequences after `compat001`'s edit to the same file — do not clobber its loader-validation wording.

## Security considerations
N/A.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_quality.py`, `tools/check_docs_content_policy.py`, `tools/check_docs_consistency.py --domain agent` — all pass; no current-tense age-threshold text; lease columns/margin/heartbeat documented; required fields match loader; recovery conditions match `recover_stale_attempts()`.
- `uv run python tools/check_docs_structure.py`, `tools/check_docs_japanese.py` — pass.
- Regression: `uv run pytest tests/agent/workflow/` unaffected (docs-only).

## Completion criteria
- No current-tense text describes an age threshold or fixed-age fallback for lease-less attempts (`REQ-001`).
- The lease columns, margin policy, and heartbeat absence are documented (`REQ-002`).
- Required `stages`/`retry_policy`, allowed retry kinds, and the shipped explicit choice are documented; the "when present" loader wording is corrected (`REQ-003`).
- Manual recovery covers only unparseable timestamps (`REQ-004`).
- REQ-007 is recorded as a gated follow-on, not written (`REQ-007`).

## Out of Scope
The `retry_on`-required statement (`REQ-007`, gated on `compat001`); code/loader/schema changes (the lease and definition issues own those); the schema-level `NOT NULL` documentation (`REQ-008`, `db_02`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Gated: REQ-007 (Phase 2) deferred until compat001 implements; Phase 1 (REQ-001/002/003/004) safe-now. |
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
- **Requirement ID**: `REQ-001`, `REQ-002`, `REQ-003`, `REQ-004`, `REQ-007`
- **Source issue**: `issues/20261116-114912_compat003_workflow-lease-docs-runbook.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/done/20261116-224307_compat003_workflow-lease-docs-runbook.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261117-020145
- **Related target files**: `docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md`
