## Goal
- Make hot reload of security-relevant Agent config fields (`allowed_root`, `tool_safety_tiers`, `allowed_tools`, `approval_risk_rules`) validate each candidate value at least as strictly as startup, so an invalid reload is rejected and the previous value stays in force.

## Priority
High

## Scope
- **In-Scope**:
  - Validating the four security-relevant fields on reload with the same rules as startup (rejected reload keeps the previous value).
  - Wiring `validate_tool_safety_tiers` and `validate_approval_risk_rules` to their registry entries and adding `validate_allowed_root` / `validate_allowed_tools`.
  - Routing the `approval` section through the validated (candidate) reload path so registry validators actually run (maintainer-approved DT-01 Option A).
  - Regenerating `registry/manifests/config_ownership.yaml` via `tools/generate_reference_table.py --manifests`.
  - Wording/evidence updates to ADR-002 and ADR-007 clarifying which fields reload via `/reload` and which need a restart (maintainer-approved DT-03).
- **Out-of-Scope**:
  - Approval order or tier-value decisions (closed by the adrchk003 approval-policy work item).
  - Hand edits to `registry/manifests/*.yaml` or guarded doc blocks.
  - Changing the semantics of `hot_reloadable=False` (startup-only fields currently still apply on reload and are only reported — see Unknowns UNK-01).
  - Adding reload validation for the remaining (non-security-relevant) approval fields.
- **Dependencies**: soft dependency on the adrchk003 agent-approval-policy work item, which defines the tier semantics this Plan validates. Verified closed (issue archived in `issues/done/`, Plan archived in `plans/done/`): this Plan does not wait on it.
  - No `Depends on` bullet: the dependency is closed, so nothing here must wait for another Plan or Issue.

## Background
Filed from the consolidated ADR review task list `memo-issue.md` (package `ADRCHK2-H04`; merged from ADRCHK-H04, review finding N6). The review claims carried the evidence label `Documentation only`; every claim was re-verified against current source in Steps 2-3 of this cycle (results recorded in `Design`). The startup side already rejects these values (section builder, `ProductionConfigValidator`, and dataclass `__post_init__`); the reload side bypasses all of it.

## Problem
The four security-relevant fields are registered with `hot_reloadable=True` and `validator_fn=None` (`scripts/agent/services/config_field_registry.py:79,81,87,88`). Deeper than the Issue stated: the `approval` section reloads through the **direct path** (`scripts/agent/services/config_section_reload.py:109-141`), which by design runs no validators and builds no candidate — so wiring validators onto the registry alone would be inert. The reload entry point (`scripts/agent/commands/cmd_config.py:59`) feeds `ConfigLoader().load_all()` directly into `ConfigReloadService.apply_config_dict`, bypassing `load_config()` and therefore `ProductionConfigValidator` and the section builders entirely.

## Reason for Change
- Startup rejects an empty `allowed_root` (`scripts/agent/config_section_builders.py:298-301`), an incomplete or over-complete `tool_safety_tiers` (`scripts/agent/production_config_validator.py:56-84`), and invalid tier/risk values (dataclass `__post_init__`, `scripts/agent/config_dataclasses.py:316-319`); reload applies the same values with none of these checks.
- `tool_safety_tiers` and `approval_risk_rules` decide whether a tool call needs approval and whether plan mode blocks it, so an unvalidated reload can flip live approval behavior.
- ADR-002 and ADR-007 state only that a configuration change requires restarting the owning process (`docs/10_adr/adr_02_01_002_platform-config-isolation.md:165`, `docs/10_adr/adr_02_03_007_mcp-http-adoption-and-stdio-non-support.md:185`), which does not describe the existing hot-reload mechanism.

## Implementation Intent
- Route the `approval` section through the existing validated (candidate) reload path so its registry `validator_fn` entries run before any live mutation, and wire the four security-relevant entries to validators with the same rules startup applies.
- A rejected reload aborts in the candidate phase; the previous value stays in force (the two-phase apply in `apply_config_dict` already guarantees this for validated sections).
- Regenerate the manifest from the registry and clarify the two ADRs' operational-consequence wording against the registry fact.

## Requirements
- `REQ-001`: A reload that changes `tool_safety_tiers`, `approval_risk_rules`, or `allowed_root` must run the same validation startup runs; an invalid candidate raises `ConfigReloadValidationError` and the live values stay unchanged.
- `REQ-002`: A reload that changes `allowed_tools` must validate the new value's type (a list of strings); an empty list remains a valid fail-closed setting (maintainer-approved DT-02 Option A).
- `REQ-003`: `validate_tool_safety_tiers` and `validate_approval_risk_rules` are wired to their registry entries; `validate_allowed_root` (non-empty absolute path) and `validate_allowed_tools` (type check) are added to `scripts/agent/services/config_validators.py` and wired. No existing validator signature changes (argument-shape finding reported in `Design` per the Issue constraint).
- `REQ-004`: `registry/manifests/config_ownership.yaml` is regenerated with `tools/generate_reference_table.py --manifests` (never hand-edited) and shows a validator for each of the four fields.
- `REQ-005`: ADR-002 and ADR-007 state which fields can be reloaded via `/reload` and which need a restart, as a wording/evidence edit that does not change their decisions (maintainer-approved DT-03).
- `REQ-006`: Existing reload semantics that are not part of the defect stay unchanged: `gitops_push_blocked` and other `hot_reloadable=False` fields keep their current apply-and-report behavior, and no `ConfigFieldRegistry` entry shape or validator argument shape changes.

## Implementation Target Files
**Freeze status**: Frozen (audit_plan_target_paths returned 0 findings; all rows `Verified`; `check_plan_target_overlaps.py` reports no active overlap).

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/agent/services/config_field_registry.py` | Modify: attach `validate_tool_safety_tiers`, `validate_approval_risk_rules`, `validate_allowed_root` (new), `validate_allowed_tools` (new) to their four entries | All four entries are `hot_reloadable=True` with `validator_fn=None` | REQ-003 | `scripts/agent/services/config_field_registry.py:79,81,87,88` (entries without validators); `:90` (`gitops_push_blocked` already `hot_reloadable=False`, unchanged) (checked in Step 3) | `tests/agent/services/test_config_reload.py` | Verified |
| `scripts/agent/services/config_validators.py` | Modify: add `validate_allowed_root(cfg: ApprovalConfig)` (non-empty, `os.path.isabs`) and `validate_allowed_tools(cfg: ToolConfig)` (`list[str]` type check; empty list valid); retain `validate_tool_safety_tiers` / `validate_approval_risk_rules` unchanged | The two approval validators exist but are wired only via `__post_init__`; no validator exists for `allowed_root` / `allowed_tools` | REQ-001, REQ-002, REQ-003 | `scripts/agent/services/config_validators.py:211-231` (both validators take the section dataclass); `scripts/agent/config_dataclasses.py:316-319` (`__post_init__` callers) (checked in Step 2) | `tests/agent/services/test_config_reload.py` | Verified |
| `scripts/agent/services/config_reload.py` | Modify: move `"approval"` from the direct-section loop to the validated-section loop in `apply_config_dict` (scope amendment vs the Issue's target list) | The direct path runs no validators and builds no candidate, so registry wiring is inert without this move | REQ-001, REQ-006 | `scripts/agent/services/config_reload.py:111-123` (validated loop), `:126-129` (direct loop includes `"approval"`); `scripts/agent/services/config_section_reload.py:115-119` ("No validators run and no candidate is built") (checked in Step 2) | `tests/agent/services/test_config_reload.py` | Verified |
| `scripts/agent/services/config_section_reload.py` | Modify docstrings only (scope amendment): module docstring and `prepare_validated_section` / `prepare_direct_section` docstrings list `approval` under the direct path; after the move they must describe it as a validated section | Docstring claims become false if left unchanged (factual statements about the path split) | REQ-001 | `scripts/agent/services/config_section_reload.py:1,21,115-119` (docstrings naming `approval` as a direct section) (checked in Step 3) | `tests/agent/services/test_config_reload.py` | Verified |
| `registry/manifests/config_ownership.yaml` | Regenerate with `tools/generate_reference_table.py --manifests` (no hand edit) | The committed manifest currently shows `validator: null` for the four fields; it is generated from the registry | REQ-004 | `registry/manifests/config_ownership.yaml:2-9,30-33,142-145` (`validator: null` rows); `tools/generate_reference_table.py:469` (`config_ownership` source is the registry file) (checked in Step 3) | `tools/generate_reference_table.py --check` | Verified |
| `tests/agent/services/test_config_reload.py` | Modify: add rejection tests first (invalid tier value, invalid risk level, empty `allowed_root`, non-absolute `allowed_root`, non-string `allowed_tools` entry); convert the fixtures of approval-applying tests from `MagicMock` to real `ApprovalConfig` instances | Rejection coverage does not exist (the two current fail-closed tests tolerate both outcomes); candidate construction needs a real dataclass (`dataclasses.replace` raises `TypeError` on a mock) | REQ-001, REQ-002 | `tests/agent/services/test_config_reload.py:663-712` (tolerant dual-branch tests), `:715-784` (`gitops_push_blocked` applied via mock fixture) (checked in Step 3) | this file (new tests) | Verified |
| `docs/10_adr/adr_02_01_002_platform-config-isolation.md` | Modify wording/evidence only: add a clause to the Operational Consequences bullet naming the config field registry as the source that determines which fields reload via `/reload` and which need a restart | The bullet states every configuration change needs a restart, which contradicts the hot-reload mechanism the Plan hardens (wording/evidence edit, decision text unchanged; DT-03) | REQ-005 | `docs/10_adr/adr_02_01_002_platform-config-isolation.md:165` ("A configuration change requires restarting the owning process") (checked in Step 2) | `tools/check_adr_structure.py` (pre-commit hook) | Verified |
| `docs/10_adr/adr_02_03_007_mcp-http-adoption-and-stdio-non-support.md` | Modify wording/evidence only: same clarification on the identical Operational Consequences bullet | Same contradictory statement in this ADR | REQ-005 | `docs/10_adr/adr_02_03_007_mcp-http-adoption-and-stdio-non-support.md:185` (identical bullet) (checked in Step 2) | `tools/check_adr_structure.py` (pre-commit hook) | Verified |

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
Files that must be read to implement the targets above, but MUST NOT be modified.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/agent/config_dataclasses.py` | `ApprovalConfig` / `ToolConfig` field definitions and `__post_init__` validators (`:316-319`, `:219-225`); `dataclasses.replace` runs them on the candidate | `scripts/agent/services/config_reload.py`, REQ-001 |
| `scripts/agent/config_section_builders.py` | Startup rule for `allowed_root` (`:298-301`) that the new reload validator must mirror | `scripts/agent/services/config_validators.py`, REQ-001 |
| `scripts/agent/production_config_validator.py` | Startup tier completeness checks (`:56-84`) and posture checks (`:88-126`); confirms reload never runs them | `scripts/agent/services/config_validators.py`, REQ-001 |
| `scripts/agent/commands/cmd_config.py` | `/reload` entry point (`:43-105`): calls `load_all()` directly and already surfaces `ValueError` (which `ConfigReloadValidationError` subclasses) as "Reload failed: ..." | `scripts/agent/services/config_reload.py`, REQ-001 |
| `scripts/agent/services/exceptions.py` | `ConfigReloadValidationError(ValueError)` (`:17`) — the rejection path the tests assert | `tests/agent/services/test_config_reload.py`, REQ-001 |
| `scripts/shared/config_loader.py` | `load_all` merge shape (`:89-110`): flat top-level keys plus one-level dict tables — the reload payload the section helpers read | `scripts/agent/services/config_reload.py`, REQ-001 |
| `scripts/agent/services/config_outcome_classification.py` | `classify_startup_only_fields` (`:48-65`): proves `hot_reloadable=False` is report-only; this Plan must not change it | `scripts/agent/services/config_reload.py`, REQ-006 |
| `scripts/agent/tool_policy.py` | Live consumer of `tool_safety_tiers` / `allowed_root` read per call; defines the safety behavior a rejected reload must keep intact | REQ-001 |
| `scripts/agent/services/config_service_sync.py` | Re-applies `RuntimeToolRegistry.apply_policy` with `ctx.cfg.approval.tool_safety_tiers` (`:78`) after commit | `scripts/agent/services/config_reload.py`, REQ-001 |
| `docs/00_governance/governance_01_documentation-policy.md` | ADR Change Protocol and ADR conventions gating the ADR edits (`:304-310`) | `docs/10_adr/adr_02_01_002_platform-config-isolation.md`, `docs/10_adr/adr_02_03_007_mcp-http-adoption-and-stdio-non-support.md`, REQ-005 |
| `scripts/agent/services/typed_validators.py` | Startup-side typed extraction helpers (`_get_str_or_default` forms) that mirror the startup rules the new reload validators state | `scripts/agent/services/config_validators.py`, REQ-002 |

## Acceptance Criteria
- `AC-001` (REQ-001): a `/reload` payload with an invalid `tool_safety_tiers` value or an empty `allowed_root` raises `ConfigReloadValidationError`, and the previous live value stays in force (test evidence).
- `AC-002` (REQ-002): a reload with a non-string `allowed_tools` entry is rejected the same way; an empty list is accepted and stays fail-closed (test evidence).
- `AC-003` (REQ-004): `registry/manifests/config_ownership.yaml` shows a `validator` name for each of the four security-relevant fields (or `hot_reloadable: false`), and `uv run python tools/generate_reference_table.py --check` reports no drift.
- `AC-004` (REQ-005): ADR-002 and ADR-007 state which fields reload and which need a restart, and `tools/check_adr_structure.py` passes.
- `AC-005` (REQ-003, REQ-006): no validator or registry entry signature changes; the argument-shape finding is recorded in this Plan's `Design` section.
- `AC-006` (all): the full validation sequence (`rules/toolchain.md`, `uv run python tools/run_validation_gates.py --full`) passes, including `diff-cover` ≥ 90 % on the implementation diff, and after the `docs/` edits the `routing.md` Tools doc checkers run.

## Tests
- New rejection tests in `tests/agent/services/test_config_reload.py`, written before the code change (Issue constraint): invalid `tool_safety_tiers` value (REQ-001), invalid `approval_risk_rules` level (REQ-001), empty `allowed_root` (REQ-001), non-absolute `allowed_root` (REQ-001), non-string `allowed_tools` entry (REQ-002). Each asserts `ConfigReloadValidationError`, the untouched live value, and that an unchanged approval section survives an unrelated invalid reload.
- Fixture conversion: approval-applying tests (`TestApprovalGitopsPushBlocked` at `:715-784`, the fail-closed tests at `:663-712`) use a real `ApprovalConfig` instance because candidate construction calls `dataclasses.replace` (REQ-006: `gitops_push_blocked` keeps applying on reload).
- Regression: the two existing dual-branch fail-closed tests must pass via their rejection branch after the change (their accept-branch documents the old unvalidated behavior and is no longer reached).
- Validation items: `uv run python tools/generate_reference_table.py --check` for the manifest (REQ-004); `tools/check_adr_structure.py` (pre-commit hook) for the ADR edits (REQ-005).

## Documentation Impact
Yes. `docs/10_adr/adr_02_01_002_platform-config-isolation.md` and `docs/10_adr/adr_02_03_007_mcp-http-adoption-and-stdio-non-support.md` must state which fields reload and which need a restart (REQ-005); both files are named by the Source Issue's Target Files. `config_ownership.yaml` has no guarded doc block (it is a fact manifest with no document-backed domain — `tools/generate_reference_table.py:455-459`), so regenerating it changes no other doc. After the `docs/` edits, run the checkers listed in `routing.md` Tools → "When to run which tool".

## Assumptions
- The reload validators can mirror startup rules exactly for these four fields because startup enforces them in code reachable from the dataclass and section builders, not only inside `ProductionConfigValidator` (verified in Step 2); the reload path reuses the dataclass-level rules via candidate construction rather than calling `ProductionConfigValidator`.
- Replacing the `approval` section object on commit is safe: every consumer reads `ctx.cfg.approval` through `ctx` per call — `scripts/agent/tool_approval.py:94,153`, `scripts/agent/tool_audit.py:56,64`, `scripts/agent/wal_checkpoint_manager.py:51`, `scripts/agent/services/mcp_status.py:63`, `scripts/agent/services/config_service_sync.py:78`, `scripts/agent/services/routing_drift.py:50` — no consumer captures the `ApprovalConfig` instance at init (checked in Step 3).
- The ADR edits are wording/evidence edits that do not reopen approval, per the maintainer's DT-03 decision and `governance_01`'s ADR Change Protocol; decision, invariant, and Blocking texts stay untouched.
- Overlap judgment: no other active Plan exists under `plans/` (only `plans/done/`), so the frozen table overlaps nothing active (verified by `tools/check_plan_target_overlaps.py` after freeze).

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | `hot_reloadable=False` fields (e.g. `gitops_push_blocked`, `context_token_limit`) are currently applied by `/reload` and only reported as `startup_only`, while `cmd_config.py:88` displays them as "Startup-only (ignored)"; whether this report/apply mismatch should be closed by a follow-up is not decided | No maintainer decision exists; the existing `gitops_push_blocked` test expects application on reload | Out of scope here (REQ-006 freezes current semantics); file a follow-up Issue if the maintainer decides to enforce non-application | False |
| UNK-02 | Production `/reload` behavior with an invalid approval value after deploy has not been observed end-to-end | No runtime evidence yet | Phase 4 deploy hand-off includes the `/reload` spot check | False |

## Affected areas
Per `skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/agent/services/config_field_registry.py` | Modify | Low (read by 2 production modules + the manifest generator) | 1 | 1 author / 1 commit (high) | not applicable (rsynced) |
| `scripts/agent/services/config_validators.py` | Modify | Low (new functions; existing validators unchanged) | 1 | 1 author / 1 commit (high) | not applicable (rsynced) |
| `scripts/agent/services/config_reload.py` | Modify | Medium (`apply_config_dict` is the `/reload` orchestrator; 4 test files exercise it) | 2 | 1 author / 2 commits (high) | not applicable (rsynced) |
| `scripts/agent/services/config_section_reload.py` | Modify (docstrings only) | Low (no behavior change in this Plan) | 1 | 1 author / 1 commit (high) | not applicable (rsynced) |
| `registry/manifests/config_ownership.yaml` | Modify (regenerated) | Low (fact manifest; no guarded doc block) | 2 | 1 author / 2 commits (high) | not applicable (rsynced) |
| `tests/agent/services/test_config_reload.py` | Modify | Low (suite-local) | 4 | 2 authors / 4 commits | not applicable (rsynced) |
| `docs/10_adr/adr_02_01_002_platform-config-isolation.md` | Modify | Low (docs; ADR-cited test chain unchanged — no ADR cites these bullets as gates) | 7 | 2 authors / 7 commits | not applicable (rsynced) |
| `docs/10_adr/adr_02_03_007_mcp-http-adoption-and-stdio-non-support.md` | Modify | Low (docs) | 4 | 2 authors / 4 commits | not applicable (rsynced) |

## Design
**Classification: Path B** — cross-module wiring plus a generated manifest, two ADRs, and test-fixture migration (more than 3 target rows; two modules plus docs and manifest).

### Step 2/3 verification results (replace the Issue's `Documentation only` claims)
- Confirmed: the four entries are `hot_reloadable=True`, `validator_fn=None` (`config_field_registry.py:79,81,87,88`). Corrected: the Issue's "and the other approval fields" is not universal — `gitops_push_blocked` is `hot_reloadable=False` (`:90`).
- Confirmed and deepened: `validate_tool_safety_tiers` / `validate_approval_risk_rules` exist (`config_validators.py:211-231`) and run at startup via `ApprovalConfig.__post_init__` (`config_dataclasses.py:316-319`), but the approval reload path never runs any `validator_fn`: `prepare_direct_section` states "No validators run and no candidate is built" (`config_section_reload.py:115-119`). Registry wiring alone is inert without moving the section to the validated path.
- Argument-shape report (Issue constraint, AC-005): `validator_fn` entries are invoked with the **section dataclass candidate** — `validator(replaced)` at `config_section_reload.py:60-67` — and the two approval validators take `ApprovalConfig`. Shapes are compatible under DT-01 Option A; no signature change is needed or made.
- Reload bypasses the whole startup validation stack: `_cmd_reload` calls `ConfigLoader().load_all()` (flat top-level keys plus one-level tables, `config_loader.py:89-110`) and hands the raw dict to `apply_config_dict` (`cmd_config.py:59-60`), never `load_config()`, so `ProductionConfigValidator` (`config_builders.py:104`) and the section builders (`config_section_builders.py:298-301`) never run.
- `hot_reloadable=False` does not block application: `classify_startup_only_fields` (`config_outcome_classification.py:48-65`) only reports, and neither prepare helper filters by `hot_reloadable`; `test_config_reload.py:715-784` expects `gitops_push_blocked` to apply on reload. The Issue's "make it restart-only" alternative would therefore require changing reload semantics (rejected as DT-01 Option C).
- Fail-closed nuance: today, reloading an empty `allowed_root` applies it and path-carrying calls are then denied (`test_config_reload.py:686-712`); the defect is startup/reload divergence and runtime inconsistency of tier/risk values, not a fail-open jail.

### Decision records (maintainer = repository owner, approved 2026-11-19 in the planning session)
- **DT-01 Option A approved**: move `approval` from the direct loop to the validated loop in `apply_config_dict`. `dataclasses.replace` builds the candidate, which runs `ApprovalConfig.__post_init__`, and the wired registry validators then run on the candidate before commit; a rejection aborts with no live mutation (the two-phase apply at `config_reload.py:91-174` already guarantees this). Rejected alternatives: Option B (per-field value-shape validators in the direct path — would put two argument shapes into one registry contract) and Option C (`hot_reloadable=False` enforcement — changes `startup_only` semantics and contradicts the existing `gitops_push_blocked` test).
- **DT-02 Option A approved**: `validate_allowed_tools` checks type (`list[str]`) and accepts an empty list as the fail-closed setting (matches REQ-002 semantics already tested at `test_config_reload.py:622-682`); the Issue's "non-empty" phrasing would forbid a safe setting startup accepts.
- **DT-03 Option A approved**: ADR-002/ADR-007 edits are wording/evidence updates citing the registry as the canonical per-field restart/reload source; per `governance_01`'s ADR Change Protocol ("an edit that does not change the decision ... does not reopen approval"), decision and invariant texts stay byte-identical, so no new Approval Record is fabricated.

### Scope amendment (reported per the Issue's constraint)
The Issue's target list omits `scripts/agent/services/config_reload.py` and `scripts/agent/services/config_section_reload.py`; DT-01 Option A makes both unavoidable (loop move; docstrings would otherwise state a false path split). They are recorded as frozen target rows with evidence. No other file changes.

### Consumer inspection (Path B dependency graphing; `scan_change_consumers.py` not run: no persisted schema, public API, or shared constant changes)
- `CONFIG_FIELD_REGISTRY` / `registry_for`: consumed only by `config_section_reload.py:11` and `config_outcome_classification.py:53` (reads `hot_reloadable` only — not affected), `tools/generate_reference_table.py` (manifest source — regenerated, not code-changed), and `tests/agent/services/test_config_reload.py:912-1031` (registry-content assertions to keep in sync).
- `config_validators.py` exported validators: imported by `config_dataclasses.py` (not affected — no signature changes) and `config_field_registry.py` (target).
- Approval value consumers: `tool_approval.py`, `tool_audit.py`, `wal_checkpoint_manager.py`, `mcp_status.py`, `config_service_sync.py`, `routing_drift.py` — all read `ctx.cfg.approval` per call (Assumptions) → not affected.
- Architecture gate: `lint-imports` currently reports 6 contracts kept, 0 broken; this Plan moves no imports across layers → the contract set is unchanged.

### Validation quality baseline (Step 5)
- Suite baseline: `12895 passed, 7 skipped` (clean tree, `-n logical`, filtered markers).
- radon: `apply_config_dict` C (16), `prepare_validated_section` C (11), `prepare_direct_section` B (6), all validators A — the changed functions stay within these existing hotspots; the `config_reload.py` edit adds no new branch (section-path list only).
- vulture (`--min-confidence 80`): pre-existing unused-argument findings in `config_reload.py:199-201` and `config_service_sync.py:36,38` recorded as baseline; not fixed here (out of scope).
- bandit: 45 low / 0 medium / 0 high severity findings, 35 suppressed via reviewed `#nosec` (baseline; no new findings expected — no new subprocess/exec patterns).
- diff-cover: clean tree has no diff (`No lines with coverage information in this diff`); the gate applies to the implementation diff at ≥ 90 % (`rules/toolchain.md` Completion checklist).

## Implementation steps
1. **Phase 1: Rejection tests first** (RED against current code)
   - [ ] Add the five rejection tests and their real-`ApprovalConfig` fixtures to `tests/agent/services/test_config_reload.py` (REQ-001, REQ-002; expect `ConfigReloadValidationError` failures pre-change)
2. **Phase 2: Core wiring** (lands with Phase 1 as one validated unit)
   - [ ] Add `validate_allowed_root` and `validate_allowed_tools` to `scripts/agent/services/config_validators.py` (REQ-001, REQ-002)
   - [ ] Wire all four validators in `scripts/agent/services/config_field_registry.py` (REQ-003)
   - [ ] Move `"approval"` to the validated-section loop in `scripts/agent/services/config_reload.py::apply_config_dict` (REQ-001, REQ-006)
   - [ ] Update the now-false path-split docstrings in `scripts/agent/services/config_section_reload.py` (REQ-001)
   - [ ] Convert the approval fixtures in `tests/agent/services/test_config_reload.py` and confirm the new tests plus the dual-branch tests pass through their rejection branch (REQ-006)
3. **Phase 3: Manifest, ADRs, full validation**
   - [ ] `uv run python tools/generate_reference_table.py --manifests` to regenerate `registry/manifests/config_ownership.yaml` (REQ-004)
   - [ ] Wording/evidence edits to `docs/10_adr/adr_02_01_002_platform-config-isolation.md` and `docs/10_adr/adr_02_03_007_mcp-http-adoption-and-stdio-non-support.md` (REQ-005; no decision/invariant text touched)
   - [ ] Run the full validation sequence (`uv run python tools/run_validation_gates.py --full`) plus `tools/generate_reference_table.py --check` and the `routing.md` Tools doc checkers after the doc edits (AC-006)
4. **Phase 4: Deploy hand-off**
   - [ ] Hand off to `skills/deploy/SKILL.md`; prerequisite: the change is committed and pushed first, and deploying is the user's decision (approval gate). Post-deploy spot check: `/reload` with an invalid `allowed_root` shows "Reload failed: ..." and the live jail root is unchanged (UNK-02)

### Release units
**Unit**: hot-reload-validation | **Phases**: 1, 2 | **Reason**: Phase 1's rejection tests fail until Phase 2's wiring lands, and Phase 2 breaks the mock-fixture tests until Phase 1's fixture conversion lands; the two phases are validated only together in one commit.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/agent/services/config_validators.py` | Unit (validator rejections on candidate instances) | `uv run pytest tests/agent/services/test_config_reload.py` | Five new tests pass; pre-change they fail (Phase 1 evidence) |
| `scripts/agent/services/config_field_registry.py` | Unit (wiring presence) + manifest comparison | `uv run pytest tests/agent/services/test_config_reload.py`; `uv run python tools/generate_reference_table.py --check` | Registry assertions at `test_config_reload.py:912-1031` stay green; no drift |
| `scripts/agent/services/config_reload.py` | Unit (two-phase abort, untouched live values) | `uv run pytest tests/agent/services/` | Rejected reload leaves `ctx.cfg.approval`/`ctx.cfg.tool` unchanged |
| `registry/manifests/config_ownership.yaml` | Generated-artifact check | `uv run python tools/generate_reference_table.py --check` | Four fields show their validator names |
| `docs/10_adr/adr_02_01_002_platform-config-isolation.md`, `docs/10_adr/adr_02_03_007_mcp-http-adoption-and-stdio-non-support.md` | Doc structure checkers | `routing.md` Tools doc checkers incl. `tools/check_adr_structure.py` | Pass; no pending-amendment bullet needed (decision texts unchanged) |
| Whole diff | Full sequence + coverage gate | `uv run python tools/run_validation_gates.py --full` (includes `diff-cover --fail-under=90`) | All gates pass; diff coverage ≥ 90 % |

## Risks
- **Risk**: converting mock fixtures to real `ApprovalConfig` could mask behavioral regressions in the approval reload path → **Mitigation**: rejection tests written first (Phase 1) pin the new behavior; the two dual-branch tests must pass through their rejection branch, keeping their fail-closed assertions observable.
- **Risk**: replacing the `approval` section object on commit could leave a consumer holding a stale instance → **Mitigation**: every consumer verified to read `ctx.cfg.approval` through `ctx` per call (Assumptions, consumer inspection); no captured references exist.
- **Risk**: operators can no longer apply previously-accepted invalid approval values via `/reload` (behavior change) → **Mitigation**: `ConfigReloadValidationError` subclasses `ValueError`, which `_cmd_reload` already surfaces as "Reload failed: {message}" (`cmd_config.py:101-103`); the ADR wording update documents the gate.
- **Risk**: `apply_config_dict` is already C(16) complexity → **Mitigation**: the edit only moves one entry in the section-path lists; radon is re-run after the change (`rules/toolchain.md` gates).
- **Risk**: two files added to scope beyond the Issue's list (scope amendment) could surprise the implementer → **Mitigation**: the amendment is reported here with evidence and frozen as target rows before procedure generation.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`.

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: rejection tests first (`tests/agent/services/test_config_reload.py`) | Pending | — | — | Expected RED pre-change |
| 2 | Phase 2: core wiring (`config_validators.py`, `config_field_registry.py`, `config_reload.py`, `config_section_reload.py`, fixtures) | Pending | — | — | Release unit with Phase 1 |
| 3 | Phase 3: manifest regeneration, ADR edits, full validation sequence | Pending | — | — | After docs edits: routing.md Tools doc checkers |
| 4 | Phase 4: deploy hand-off to `skills/deploy/SKILL.md` + `/reload` spot check | Pending | — | — | User decision gate; commit+push prerequisite |

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
- **Source issue**: issues/20261117-123004_adrchk004_hot-reload-validation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261119-094759
- **Related target files**: `scripts/agent/services/config_field_registry.py`; `scripts/agent/services/config_validators.py`; `scripts/agent/services/config_reload.py`; `scripts/agent/services/config_section_reload.py`; `registry/manifests/config_ownership.yaml`; `tests/agent/services/test_config_reload.py`; `docs/10_adr/adr_02_01_002_platform-config-isolation.md`; `docs/10_adr/adr_02_03_007_mcp-http-adoption-and-stdio-non-support.md`

### Requirement Traceability
See `templates/requirement-traceability.md` for the canonical column format.

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Issue "Reason for Change" bullets 1-3; startup enforcement at `config_section_builders.py:298-301`, `config_dataclasses.py:316-319`; direct-path gap at `config_section_reload.py:115-119` (Confirmed by repository evidence) | `scripts/agent/services/config_validators.py`; `scripts/agent/services/config_field_registry.py`; `scripts/agent/services/config_reload.py`; `scripts/agent/services/config_section_reload.py` | Phase 2 | AC-001 | New rejection tests in `tests/agent/services/test_config_reload.py` | Confirmed by repository evidence |
| REQ-002 | Issue "Required Changes" bullet 3; fail-closed semantics at `test_config_reload.py:622-682` (Confirmed by repository evidence; DT-02 resolved) | `scripts/agent/services/config_validators.py`; `scripts/agent/services/config_field_registry.py` | Phase 2 | AC-002 | Non-string `allowed_tools` rejection test | Confirmed by repository evidence |
| REQ-003 | Issue "Required Changes" bullets 2-3; entry state at `config_field_registry.py:79,81,87,88` (Confirmed by repository evidence) | `scripts/agent/services/config_field_registry.py` | Phase 2 | AC-003, AC-005 | Registry wiring assertions (`test_config_reload.py:912-1031` stay in sync) | Confirmed by repository evidence |
| REQ-004 | Issue "Required Changes" bullet 4; manifest rows `config_ownership.yaml:2-9,30-33,142-145` (Confirmed by repository evidence) | `registry/manifests/config_ownership.yaml` | Phase 3 | AC-003 | `tools/generate_reference_table.py --check` | Confirmed by repository evidence |
| REQ-005 | Issue "Documentation Impact"; ADR bullets at `adr_02_01_002...md:165`, `adr_02_03_007...md:185` (Confirmed by repository evidence; DT-03 resolved) | `docs/10_adr/adr_02_01_002_platform-config-isolation.md`; `docs/10_adr/adr_02_03_007_mcp-http-adoption-and-stdio-non-support.md` | Phase 3 | AC-004 | `tools/check_adr_structure.py` | Confirmed by repository evidence |
| REQ-006 | Issue "Constraints" bullet 1 (argument-shape report) and the no-signature-change constraint; shape evidence `config_section_reload.py:60-67`, `config_validators.py:211,221`; `gitops_push_blocked` test `test_config_reload.py:715-784` (Confirmed by repository evidence) | `scripts/agent/services/config_reload.py`; `tests/agent/services/test_config_reload.py` | Phase 2 | AC-005 | Fixture-conversion regression run of `tests/agent/services/` | Confirmed by repository evidence |
