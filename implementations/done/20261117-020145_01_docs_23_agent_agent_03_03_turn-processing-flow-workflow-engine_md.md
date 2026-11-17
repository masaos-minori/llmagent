## Goal

Align `agent_03_03` with the strict lease and workflow-definition contract: remove the age-threshold / lease-less-legacy recovery wording (REQ-001, REQ-004), document the lease-contract behavior (REQ-002), and verify the workflow-definition required-fields contract, allowed retry kinds, and `retry_on`-required statement (REQ-003, REQ-007 — already landed via `compat001`'s own documentation row; gate released, verification only).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- `REQ-001`/`REQ-004` edits match current committed source: `_classify_running_attempts()` classifies by `lease_expires_at` only, lease-less rows stay `live`, and the docstring records the adrrev005 age-rule removal (`scripts/agent/workflow/state_store.py:365-419`); the adrrev005 issue removed the lease-less legacy reclaim (`issues/done/20261109-112715_adrrev005_schema-fingerprint-unify.md:43`). Safe to edit now, independent of the compat002 implementation.
- `REQ-002` lease behavior matches current source with one wording correction (re-verified 20261117): stamping of `owner_id` (`get_owner_id()`) and `lease_expires_at` (`lease_expires_from(now, lease_duration_sec)`) happens inside `begin_stage_if_new()` **only when a `lease_duration_sec` is passed**; the helper still accepts `lease_duration_sec: int | None = None` for legacy/test callers and leaves both columns NULL then (`scripts/agent/workflow/idempotency_ops.py:20-45`). The sole production caller `workflow_engine.py` always passes stage `timeout_sec` + `_LEASE_MARGIN_SEC` (30 s) (`workflow_engine.py:31,336`), so every production attempt row is stamped. The doc must attribute "always stamped" to the sole production writer (the engine path), not to an unconditionally-stamping helper — the unconditional helper is `compat002`'s target, not current source.
- `REQ-003` loader contract: `stages` and `retry_policy` are required keys and the allowed retry kinds are `exception`/`timeout`/`llm_failure` (`workflow_loader.py:57,68-80,150-156`; the shipped definition selects `["exception"]` explicitly at `config/workflows/default.json:24`). Re-verification 20261117: this wording **already landed** in `agent_03_03` (lines 152, 156-157 — "required keys"; "`retry_policy.retry_on` is required ... an absent key is rejected") via `compat001`'s own documentation row (`implementations/done/20261117-005004_03_docs_23_agent_agent_03_03_turn-processing-flow-workflow-engine_md.md`, Steps Completed). The old "when present" / "shipped default" wording no longer exists in the doc. REQ-003 is satisfied by verification, not by a new edit.
- `REQ-007` gate is **released** (re-verified 20261117): `compat001` is implemented (`_REQUIRED_POLICY_KEYS` includes `retry_on` with `_validate_retry_on()` at `workflow_loader.py:57,68-80`; `models.py` `retry_on: tuple[str, ...]`), and its procedure documents are archived under `implementations/done/20261117-005004_*`. The required-key statement is already in `agent_03_03` lines 156-157. No new REQ-007 edit; verification only.
- `agent_03_03` overlap with `compat001` is resolved: `compat001`'s loader-validation edits already landed (lines 152-157); this row's remaining edits touch only the Startup Recovery section (lines 168-175) and must not clobber them.

## Design decisions
- **Describe the lease contract by responsibility and consequence, not copied config.** State that both columns are stamped at attempt start by the sole production writer (engine → `begin_stage_if_new()`), the lease equals the stage `timeout_sec` plus a fixed margin and is therefore never shorter than that margin, no heartbeat/renewal exists, an attempt is stale only when its explicit lease expired and an old `started_at` alone never makes it stale, and recovery deletes `processed_events` only for failed attempts — pointing to `state_store.py` / `idempotency_ops.py` for specifics. Do not state the 30 s value as deployed configuration (avoids `check_docs_content_policy.py` "No concrete configuration values").
- **Gate resolved during verification; REQ-003/REQ-007 become verification-only.** The Phase-2 split (gated `retry_on`-required statement) was overtaken by events: `compat001` implemented and its own documentation row landed the required-key wording in `agent_03_03`. This row now verifies that wording instead of writing it, and its edits are confined to the Startup Recovery section.

## Alternatives considered
- **Writing REQ-007 now alongside REQ-003.** Rejected at generation time: the source then still treated `retry_on` as optional, so a required-key statement would have created a doc/source mismatch (the Issue's explicit concern). Superseded 20261117: `compat001` implemented and landed the required-key wording through its own documentation row; nothing left to write here.

## Implementation
### Target file
`docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md`
### Procedure
**Executable now (post-verification):**
1. **REQ-001** — Remove the "Lease-less (pre-migration) rows use the age rule" bullet at line 169.
2. **REQ-004** — Rewrite the manual-recovery paragraph at line 175 to cover only unparseable-timestamp rows; drop the "lease-less and young" path.
3. **REQ-002** — Add the lease-contract behavior to the Startup Recovery section (both lease columns stamped at attempt start by the sole production writer — `WorkflowEngine` calling `begin_stage_if_new()` with an explicit lease duration; lease = stage `timeout_sec` + fixed margin; no heartbeat/renewal; stale only when the explicit lease expired; old `started_at` alone never stale; recovery deletes `processed_events` only for failed attempts; physical vs logical recovery separate). Point to `state_store.py` / `idempotency_ops.py`.
4. **REQ-003 / REQ-007 (verification only)** — Confirm the already-landed loader-validation wording (`agent_03_03:152,156-157`: `stages`/`retry_policy`/`retry_on` required, allowed kinds, absent key rejected) matches the implemented loader (`workflow_loader.py:57,68-80,150-156`); make no edit.
### Method
Two removals, one manual-recovery rewrite, one lease-contract addition (Startup Recovery section); verification-only for the loader-validation wording.
### Details
- **Line 169** — delete the bullet: "Lease-less (pre-migration) rows use the age rule: they are stale only when `started_at` is older than 3600 s."
- **Line 175** — change "Manual recovery for rows left `running` (unparseable or lease-less and young): ..." to cover only unparseable timestamps: "Manual recovery for rows left `running` due to an unparseable `started_at`/`lease_expires_at`: identify the owning process from `owner_id` (`hostname-pid-random`), confirm the process is gone, then correct the row via manual SQL against the workflow database. There is no automated takeover for these rows. Lease-less rows do not exist post-migration (the sole writer always stamps a lease); legacy databases holding them are refused by the fingerprint gate and recreated, not manually repaired."
- **Lease-contract addition** — after the expired-lease bullet (line 168), before the deleted age-rule bullet, insert the lease-contract narrative: (a) both `owner_id` and `lease_expires_at` are stamped in the insert transaction by `begin_stage_if_new()`, and `WorkflowEngine` is the only production caller — it always passes an explicit lease duration, so every production attempt row carries both columns; (b) there is no heartbeat or lease renewal; (c) recovery deletes `processed_events` rows only for the attempts it marks `failed`; (d) physical database recovery is separate from this logical recovery — link `../41_db/db_07_api_and_operations-recovery-and-reference.md`. Keep it responsibility/consequence level; cite `scripts/agent/workflow/state_store.py::_classify_running_attempts()` and `scripts/agent/workflow/idempotency_ops.py::begin_stage_if_new()`.
- **REQ-003 / REQ-007 (verification only)** — the loader-validation section (lines 152-157) already states `stages`/`retry_policy` required and `retry_policy.retry_on` required with "an absent key is rejected" (landed via `compat001`'s row 005004_03). Confirm it matches the implemented loader and do not edit it. The earlier details ("retry_on remains optional", "shipped default" wording at line 134, gated placeholder) are obsolete — removed by this re-verification.

## Compatibility considerations
N/A: documentation only; no runtime blast radius. `deploy.sh` serves docs statically (rsynced). `compat001`'s loader-validation edits to this file already landed (row 005004_03); this row's edits are confined to the Startup Recovery section and do not touch them.

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
- The lease stamping writer, margin policy, heartbeat absence, and lease-only staleness are documented (`REQ-002`).
- Required `stages`/`retry_policy`/`retry_on` and the allowed retry kinds are confirmed present in `agent_03_03` and matching the implemented loader — no duplicate edit (`REQ-003`, `REQ-007`).
- Manual recovery covers only unparseable timestamps (`REQ-004`).

## Out of Scope
Loader/schema/code changes (the lease and definition issues own those); the schema-level `NOT NULL` documentation (`REQ-008`, `db_02`); the `retry_on`-required wording (`REQ-007` — already landed via `compat001`'s row 005004_03; this row only verifies it).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261117-120431 | 20261117-120803 | Verification 20261117: REQ-007 gate released (compat001 implemented); REQ-003/REQ-007 already landed via row 005004_03 — verification only. REQ-001 age-rule bullet removed; REQ-002 lease-contract bullets added (producer stamping, no heartbeat, processed_events scope, physical/logical split); REQ-004 manual-recovery rewrite; REQ-003/REQ-007 verified already landed (no edit). |
| 2 | Add or update tests per Validation plan | Completed | — | 20261117-120804 | N/A: documentation-only row. N/A: documentation-only row. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261117-120804 | Documentation checkers in Validation plan. check_docs_quality/content_policy/consistency --domain agent/structure/japanese all exit 0; check_workitem_structure clean. |

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