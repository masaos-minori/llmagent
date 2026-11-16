## Goal
Establish one explicit workflow-definition contract across configuration, models, production code, tests, and documentation: every definition states its `stages`, supplies a `retry_policy`, and every `retry_policy` states the failure kinds it retries via `retry_on`. A missing field fails at the boundary that receives it. The shipped exception-only retry behavior is unchanged.

## Priority
High

## Scope
- **In-Scope**: Make `RetryPolicy.retry_on`, `WorkflowDef.stages`, and `WorkflowDef.retry_policy` required constructor arguments; make `retry_policy.retry_on` a required loader key; own and test empty-stage validation; update every call site and the one documentation file.
- **Out-of-Scope**: Changing retry semantics, retry kinds, or `max_attempts` / `retry_wait_sec` handling; attempt-lease changes; a migration path for old workflow JSON; compatibility-checker rules.
- **Dependencies**: The Issue recommends doing this before `issues/20261116-114834_compat002_mandatory-attempt-leases.md` (order only; not a technical dependency). No plan for compat002 exists yet, so freezing this plan first preserves the recommended order. No other open Plan depends on this one.

## Background
Explicit in code: `scripts/agent/workflow/workflow_loader.py` documents `retry_on` as optional, keeps `_REQUIRED_POLICY_KEYS` at `max_attempts` and `retry_wait_sec`, and `_validate_retry_on()` returns `("exception",)` for an absent key. Explicit in code: `scripts/agent/workflow/models.py` gives `RetryPolicy.retry_on` the default `("exception",)`, gives `WorkflowDef.stages` a `default_factory=list`, and gives `WorkflowDef.retry_policy` a default factory that builds `RetryPolicy(max_attempts=3, retry_wait_sec=1)`. Explicit in config: `config/workflows/default.json` already declares `retry_on: ["exception"]`. Confirmed by repository evidence: five test files construct these models directly (`tests/agent/test_orchestrator.py`, `tests/agent/workflow/test_workflow_models.py`, `tests/agent/workflow/test_adapter_store_ownership.py`, `tests/agent/workflow/test_session_diagnostics_wiring.py`, `tests/agent/workflow/test_workflow_engine.py`); the loader test lives at `tests/agent/workflow/test_workflow_loader.py` (the Issue's memo path was unconfirmed). `scripts/agent/orchestrator.py` references `WorkflowDef` only as a type and obtains it via `WorkflowLoader().load()`; `scripts/agent/workflow_engine_adapter.py` does not construct either model; `scripts/agent/workflow/__init__.py` re-exports both as public API.

## Problem
The loader and models enforce different contracts. An operator who removes `retry_on` from a workflow JSON gets no startup error; the definition silently becomes exception-only retry. A strict loader can also be bypassed by constructing the models directly with implicit defaults, so the strictness is not a real guarantee. Tests that omit these fields inherit unrelated defaults instead of stating the policy they exercise. Two model tests pin the implicit defaults (`test_default_retry_policy`, `test_stages_default_empty`), and two loader tests accept an omitted `retry_on` (`test_absent_retry_on_key_loads_default`, `test_older_format_definition_without_retry_on_loads`).

## Reason for Change
Correctness and configuration-audit risk: a configuration defect is concealed rather than reported. The obsolete defaults only preserve older input and constructor contracts. Nothing makes the change time-sensitive; doing it first reduces the number of simultaneous workflow-contract changes when the lease issue is implemented.

## Implementation Intent
Establish one explicit workflow-definition contract. Every definition states its stages, supplies a retry policy, and every retry policy states the failure kinds it retries. Missing fields fail at the boundary that receives them. Keep the shipped value `retry_on=("exception",)` but make it explicit and auditable. Do not change retry semantics. Empty-stage validation and empty-`retry_on` semantics are decided here (see Design) and become tested invariants.

## Requirements
- `REQ-001`: The loader makes `retry_policy.retry_on` a required key and raises `WorkflowLoadError` naming `retry_policy.retry_on` when it is absent. (`workflow_loader.py`)
- `REQ-002`: The loader validates an explicit `retry_on` list and its semantics for an empty list are fixed and tested. (`workflow_loader.py`, `test_workflow_loader.py`)
- `REQ-003`: `RetryPolicy.retry_on`, `WorkflowDef.stages`, and `WorkflowDef.retry_policy` become required constructor arguments; the three implicit defaults are removed. (`models.py`)
- `REQ-004`: Empty-stage validation has one explicit, documented owner and is tested. (`models.py` / `workflow_loader.py`)
- `REQ-005`: Every repository call site supplies `retry_on`, `stages`, and `retry_policy` explicitly. (`test_orchestrator.py`, `test_workflow_models.py`, `test_adapter_store_ownership.py`, `test_session_diagnostics_wiring.py`, `test_workflow_engine.py`, `test_workflow_loader.py`)
- `REQ-006`: Documentation marks `stages`, `retry_policy`, and `retry_policy.retry_on` as required and removes wording that treats an omitted `retry_on` as a supported legacy format. (`docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md`)

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/agent/workflow/models.py` | Remove the default from `RetryPolicy.retry_on`, the `default_factory` from `WorkflowDef.stages`, and the `default_factory` from `WorkflowDef.retry_policy`; all three become required constructor arguments. Add an empty-stage guard here if chosen as owner. | REQ-003; AC: `RetryPolicy(max_attempts=3, retry_wait_sec=1)` raises `TypeError`; `WorkflowDef(name="x", version="1.0.0")` raises `TypeError`. | `RetryPolicy.retry_on` default at `models.py:80`; `WorkflowDef.stages` `default_factory=list` at `models.py:89`; `WorkflowDef.retry_policy` `default_factory` at `models.py:90-92`. (checked in Step 3) | `tests/agent/workflow/test_workflow_models.py` | Verified |
| `scripts/agent/workflow/workflow_loader.py` | Add `retry_on` to `_REQUIRED_POLICY_KEYS`; remove the absent-key fallback in `_validate_retry_on()` so it raises `WorkflowLoadError` naming `retry_policy.retry_on`; keep supported kinds and unknown-kind rejection; update `_RetryPolicyJson` docstring; apply the empty-stage owner. | REQ-001, REQ-002, REQ-004; AC: JSON without `retry_policy.retry_on` raises `WorkflowLoadError` identifying `retry_policy.retry_on`. | `_REQUIRED_POLICY_KEYS` at `workflow_loader.py:57`; absent-key fallback at `workflow_loader.py:74-76`; empty-stages guard at `workflow_loader.py:124`. (checked in Step 3) | `tests/agent/workflow/test_workflow_loader.py` | Verified |
| `tests/agent/test_orchestrator.py` | Add `retry_on=(...)` to every `RetryPolicy(...)` call site that currently omits it (12 sites). | REQ-005; callers must satisfy the new required argument. | 12 `RetryPolicy(` call sites omit `retry_on` (rg, Step 3). | `tests/agent/test_orchestrator.py` | Verified |
| `tests/agent/workflow/test_workflow_models.py` | Remove `test_default_retry_policy` and `test_stages_default_empty` (they pin implicit defaults); add constructor-surface tests that require all three arguments and the empty-stage owner. | REQ-003, REQ-004; AC: constructor-surface tests pass; default-pinning tests removed. | `test_default_retry_policy` at `test_workflow_models.py:89`; `test_stages_default_empty` at `test_workflow_models.py:98`. (checked in Step 3) | `tests/agent/workflow/test_workflow_models.py` | Verified |
| `tests/agent/workflow/test_adapter_store_ownership.py` | Add `retry_on=("exception",)` to the `RetryPolicy(...)` at line 36. | REQ-005. | `RetryPolicy(` at `test_adapter_store_ownership.py:36` omits `retry_on` (Step 3). | `tests/agent/workflow/test_adapter_store_ownership.py` | Verified |
| `tests/agent/workflow/test_session_diagnostics_wiring.py` | Add `retry_on=("exception",)` to the `RetryPolicy(...)` at line 38. | REQ-005. | `RetryPolicy(` at `test_session_diagnostics_wiring.py:38` omits `retry_on` (Step 3). | `tests/agent/workflow/test_session_diagnostics_wiring.py` | Verified |
| `tests/agent/workflow/test_workflow_engine.py` | Add `retry_on=(...)` to every `RetryPolicy(...)` call site that currently omits it. | REQ-005. | Multiple `RetryPolicy(` call sites omit `retry_on` (rg, Step 3). | `tests/agent/workflow/test_workflow_engine.py` | Verified |
| `tests/agent/workflow/test_workflow_loader.py` | Add `retry_on: ["exception"]` to the `_VALID` fixture; convert `test_absent_retry_on_key_loads_default` and `test_older_format_definition_without_retry_on_loads` into rejection tests naming `retry_policy.retry_on`; add an empty-`retry_on` semantics test. | REQ-001, REQ-002, REQ-005. | `_VALID` at `test_workflow_loader.py:21-30` omits `retry_on`; acceptance tests at `test_workflow_loader.py:285`, `:290` (Step 3). | `tests/agent/workflow/test_workflow_loader.py` | Verified |
| `docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md` | Mark `stages`, `retry_policy`, and `retry_policy.retry_on` as required; state allowed retry kinds, the empty-`retry_on` semantics, and the empty-stage owner; remove omitted-`retry_on` legacy wording. | REQ-006; AC: documentation no longer describes omitted fields as supported legacy formats. | File exists under `docs/23_agent/` (Step 3). | None | Verified |

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
| `scripts/agent/orchestrator.py` | References `WorkflowDef` only as a type annotation; obtains instances via `WorkflowLoader().load()`, never constructs the models. Confirms it needs no change. | `scripts/agent/workflow/models.py`, `REQ-005` |
| `scripts/agent/workflow/__init__.py` | Re-exports `RetryPolicy` and `WorkflowDef` as public API; read to confirm the constructor contract surface. | `scripts/agent/workflow/models.py`, `REQ-003` |
| `scripts/agent/workflow/workflow_engine.py` | Takes `WorkflowDef` as a parameter; read to confirm no direct construction and that the required-argument change does not alter its call convention. | `scripts/agent/workflow/models.py`, `REQ-003` |
| `scripts/agent/workflow/validate.py` | Deploy-time CLI that loads via `WorkflowLoader`; read to confirm it needs no change. | `scripts/agent/workflow/workflow_loader.py`, `REQ-001` |
| `scripts/agent/workflow_engine_adapter.py` | Confirmed (Step 3) it does not construct either model; read to close the Issue's "Needs confirmation". | `scripts/agent/workflow/models.py`, `REQ-003` |
| `config/workflows/default.json` | Shipped definition; confirm it already supplies `retry_on` and still loads with the strict contract. | `scripts/agent/workflow/workflow_loader.py`, `REQ-001` |

## Acceptance Criteria
- [ ] Workflow JSON without `retry_policy.retry_on` raises `WorkflowLoadError`, and the message identifies `retry_policy.retry_on` as missing. (`REQ-001`)
- [ ] `RetryPolicy(max_attempts=3, retry_wait_sec=1)` raises `TypeError`. (`REQ-003`)
- [ ] `WorkflowDef(name="x", version="1.0.0")` raises `TypeError`. (`REQ-003`)
- [ ] Every repository call site supplies `retry_on`, `stages`, and `retry_policy` explicitly. (`REQ-005`)
- [ ] `config/workflows/default.json` loads and retains exception-only retry behavior. (`REQ-001`)
- [ ] Unknown retry kinds are still rejected. (`REQ-001`)
- [ ] The owner of empty-stage validation is explicit, documented, and tested. (`REQ-004`)
- [ ] The empty-`retry_on` semantics are decided, documented, and tested. (`REQ-002`)
- [ ] Tests and documentation no longer describe omitted fields as supported legacy formats. (`REQ-005`, `REQ-006`)
- [ ] `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools` reports no new errors. (`REQ-003`)

## Tests
- Loader rejection of missing `retry_on` names `retry_policy.retry_on`; unknown-kind rejection retained; empty-`retry_on` semantics test. (`REQ-001`, `REQ-002`; `test_workflow_loader.py`)
- Constructor-surface tests for both models: `RetryPolicy` and `WorkflowDef` raise `TypeError` when a required argument is omitted; required arguments accepted. (`REQ-003`; `test_workflow_models.py`)
- Empty-stage owner test. (`REQ-004`)
- Regression: `uv run pytest tests/agent/workflow tests/agent/test_orchestrator.py`. (`REQ-005`)
- Run the validation sequence in `rules/toolchain.md` (ruff, mypy, lint-imports, bandit, pytest, diff-cover). (`REQ-003`)

## Documentation Impact
`docs/23_agent/agent_03_03-turn-processing-flow-workflow-engine.md` (the workflow-engine doc referenced by the agent domain in `docs/00_index.md` / `routing.md`). State intent and boundaries: required fields (`stages`, `retry_policy`, `retry_policy.retry_on`), allowed retry kinds, who validates empty stages, the empty-`retry_on` semantics, and the failure behavior when a field is missing. Do not state the shipped retry value as an implicit default. Driven by `REQ-006`.

## Assumptions
- The `rg`/consumer scan covers every Python caller of these models; a non-Python or dynamically loaded consumer that imports them is not expected on this host. If the implementation phase finds one, it is a Fallout amendment (add a row, re-run freeze).
- Making the three arguments required is safe for the shipped `config/workflows/default.json`, which already supplies all three.

## Unknowns
Both items the Issue flagged as `不明` were resolved by design decision at plan time (recorded in the `Design` section below), so no unresolved Unknown remains and nothing is `BLOCKING`.

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/agent/workflow/models.py` | Modify | High — public API re-exported via `workflow/__init__.py`; constructor signature change affects every caller | 4 | Multiple contributors | not applicable (rsynced) |
| `scripts/agent/workflow/workflow_loader.py` | Modify | Medium — sole production constructor of both models | 5 | Multiple contributors | not applicable (rsynced) |
| `tests/agent/test_orchestrator.py` | Modify | Low — test-only | N/A | Multiple contributors | not applicable (rsynced) |
| `tests/agent/workflow/test_workflow_models.py` | Modify | Low — test-only | N/A | Multiple contributors | not applicable (rsynced) |
| `tests/agent/workflow/test_adapter_store_ownership.py` | Modify | Low — test-only | N/A | Multiple contributors | not applicable (rsynced) |
| `tests/agent/workflow/test_session_diagnostics_wiring.py` | Modify | Low — test-only | N/A | Multiple contributors | not applicable (rsynced) |
| `tests/agent/workflow/test_workflow_engine.py` | Modify | Low — test-only | N/A | Multiple contributors | not applicable (rsynced) |
| `tests/agent/workflow/test_workflow_loader.py` | Modify | Low — test-only | N/A | Multiple contributors | not applicable (rsynced) |
| `docs/23_agent/agent_03_03-turn-processing-flow-workflow-engine.md` | Modify | Low — documentation only | N/A | Multiple contributors | not applicable (rsynced) |

## Design
Two design choices the Issue left open (`不明`) are resolved below with rationale and compatibility impact. Both are recorded as resolved at plan time, so neither is a blocking Unknown.

### Decision 1 — Empty-stage validation owner
- **Choice**: `WorkflowDef.__post_init__()` rejects an empty `stages` list; the model owns the invariant. The loader retains its existing `'stages' must be a non-empty list` guard as the config-path error surface.
- **Alternatives considered**: loader-only ownership (the Issue's "Alternative"). The loader is currently the sole production constructor, so loader-only is viable and would be the smaller change.
- **Rationale for the choice**: direct model construction is exercised by the orchestrator and five test files (`confirmed by repository evidence`), so a model-level guard closes the bypass path that makes loader strictness not a real guarantee. The loader's existing check stays because a test pins its message (`test_empty_stages_list` matches `"non-empty list"`); removing it would change a pinned error and is out of scope.
- **Compatibility impact**: additive. Existing valid definitions (which always carry stages) are unaffected. The model now raises `AssertionError` on empty stages instead of silently accepting them.

### Decision 2 — Empty `retry_on` semantics
- **Choice**: an explicit empty list `retry_on: []` is **valid** and means "retry nothing" (the operator explicitly opted out of every failure kind). An absent key remains rejected after REQ-001.
- **Alternatives considered**: treat `[]` as invalid (same as absent). This would collapse the distinct "opt out" signal into the "forgot to set it" error and add branching to distinguish absent vs. empty.
- **Rationale for the choice**: preserves current runtime behavior (`_validate_retry_on` returns `tuple([])` for `[]`), honors explicit operator intent, and keeps the contract one-to-one between JSON and the model. The shipped `default.json` uses `["exception"]`, so shipped behavior is unchanged.
- **Compatibility impact**: none for shipped config. `_validate_retry_on` still validates element kinds; only the absent-key fallback is removed.

### Public API note
`RetryPolicy` and `WorkflowDef` are re-exported from `scripts/agent/workflow/__init__.py` (confirmed in Step 3). Making their constructor arguments required is a breaking change for any external caller that omits them; on this host the only callers are the loader and the test files listed in `Implementation Target Files`.

## Implementation steps
Each step description MUST cite the exact file path(s) it touches by referencing rows
of `Implementation Target Files` above — do not restate file-level detail
independently of that frozen table. A step is a top-level numbered item (a Phase); its
checklist items are sub-tasks, and the Execution Status table has one row per step.
Declare a release unit (see `### Release units` below) when a phase breaks existing callers or
tests until another phase lands (for example a `NOT NULL` column added before its write path):
one line per unit, `**Unit**: {name} | **Phases**: {N, N} | **Reason**: {why the members cannot be
validated alone}`.

1. **Phase 1: Core contract enforcement (loader + models)**
   - [ ] REQ-003; `scripts/agent/workflow/models.py` — remove the default from `RetryPolicy.retry_on`, the `default_factory` from `WorkflowDef.stages`, and the `default_factory` from `WorkflowDef.retry_policy`; all three become required constructor arguments.
   - [ ] REQ-001; `scripts/agent/workflow/workflow_loader.py` — add `retry_on` to `_REQUIRED_POLICY_KEYS`; remove the absent-key fallback in `_validate_retry_on()` so it raises `WorkflowLoadError` naming `retry_policy.retry_on`.
   - [ ] REQ-002; `scripts/agent/workflow/workflow_loader.py` — keep supported-kind validation and unknown-kind rejection; apply Decision 2 (explicit empty list is valid = "retry nothing").
   - [ ] REQ-004; `scripts/agent/workflow/models.py` — add the empty-stage guard to `WorkflowDef.__post_init__()` (Decision 1); keep the loader's existing `'stages' must be a non-empty list` guard intact.
2. **Phase 2: Call-site and test updates**
   - [ ] REQ-005; `tests/agent/test_orchestrator.py` — add `retry_on=(...)` to every `RetryPolicy(...)` call site that currently omits it (12 sites).
   - [ ] REQ-003, REQ-005; `tests/agent/workflow/test_workflow_models.py` — remove `test_default_retry_policy` and `test_stages_default_empty`; add constructor-surface tests requiring all three arguments and the empty-stage owner.
   - [ ] REQ-005; `tests/agent/workflow/test_adapter_store_ownership.py` — add `retry_on=("exception",)` to the `RetryPolicy(...)` at line 36.
   - [ ] REQ-005; `tests/agent/workflow/test_session_diagnostics_wiring.py` — add `retry_on=("exception",)` to the `RetryPolicy(...)` at line 38.
   - [ ] REQ-005; `tests/agent/workflow/test_workflow_engine.py` — add `retry_on=(...)` to every `RetryPolicy(...)` call site that currently omits it.
   - [ ] REQ-001, REQ-002, REQ-005; `tests/agent/workflow/test_workflow_loader.py` — add `retry_on: ["exception"]` to the `_VALID` fixture; convert `test_absent_retry_on_key_loads_default` and `test_older_format_definition_without_retry_on_loads` into rejection tests naming `retry_policy.retry_on`; add an empty-`retry_on` semantics test.
3. **Phase 3: Documentation & verification**
   - [ ] REQ-006; `docs/23_agent/agent_03_03-turn-processing-flow-workflow-engine.md` — mark `stages`, `retry_policy`, and `retry_policy.retry_on` as required; state allowed retry kinds, the empty-`retry_on` semantics, and the empty-stage owner; remove omitted-`retry_on` legacy wording.
   - [ ] REQ-003, REQ-005; run the validation sequence in `rules/toolchain.md` (ruff, mypy, lint-imports, bandit, pytest, diff-cover); run `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_consistency.py --domain agent`, `uv run python tools/check_compat_shims.py`.

### Release units
N/A: no release unit. The loader and model changes land together with their call-site and test updates in the same commit, so there is no phase that breaks callers until another phase lands.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/agent/workflow/workflow_loader.py` | Unit: load JSON without `retry_policy.retry_on` → expect `WorkflowLoadError` naming it; load unknown kind → expect rejection; load explicit empty `retry_on: []` → expect success ("retry nothing"); load `config/workflows/default.json` → expect success with exception-only retry. | `uv run pytest tests/agent/workflow/test_workflow_loader.py` | REQ-001, REQ-002 pass; `test_empty_stages_list` still matches `"non-empty list"`. |
| `scripts/agent/workflow/models.py` | Unit: construct `RetryPolicy(max_attempts=3, retry_wait_sec=1)` without `retry_on` → expect `TypeError`; construct `WorkflowDef(name="x", version="1.0.0")` without `stages`/`retry_policy` → expect `TypeError`; construct with all args → expect success; empty `stages` → expect guard. | `uv run pytest tests/agent/workflow/test_workflow_models.py` | REQ-003, REQ-004 pass; `test_default_retry_policy` and `test_stages_default_empty` removed. |
| `tests/agent/test_orchestrator.py`, `test_adapter_store_ownership.py`, `test_session_diagnostics_wiring.py`, `test_workflow_engine.py` | Regression: every `RetryPolicy(...)` call site supplies `retry_on`; full suite runs. | `uv run pytest tests/agent/workflow tests/agent/test_orchestrator.py` | REQ-005 pass; no `TypeError` from missing required argument. |
| `docs/23_agent/agent_03_03-turn-processing-flow-workflow-engine.md` | Doc quality/consistency: required fields stated, omitted-`retry_on` legacy wording removed. | `uv run python tools/check_docs_quality.py`, `tools/check_docs_consistency.py --domain agent`, `tools/check_compat_shims.py` | All pass; no new errors. |
| Whole change | Validation sequence: ruff format/import gate on changed files, mypy, bandit, diff-cover. | `uv run ruff ...`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`, `uv run bandit`, `uv run pytest --diff-cover` | No new errors vs baseline (`REQ-003`). |

## Risks
- **Risk**: Making the three arguments required surfaces a `TypeError` at any `RetryPolicy(`/`WorkflowDef(` call site missed by the scan. → **Mitigation**: `rg -n "RetryPolicy\(" scripts tests tools` and `rg -n "WorkflowDef\(" scripts tests tools` are run before editing and re-run after; REQ-005 requires every call site to supply all three arguments.
- **Risk**: A new mypy error from the constructor-signature change. → **Mitigation**: `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools` is part of the validation sequence (REQ-003); the only callers are the loader and the listed test files, all updated.
- **Risk**: Removing the loader's empty-stages guard would break the pinned message in `test_empty_stages_list`. → **Mitigation**: Decision 1 keeps the loader guard; only the model guard is added.
- **Risk**: The doc edit drifts from `check_docs_quality.py` / `check_docs_consistency.py`. → **Mitigation**: both checks run in Phase 3; `DESIGN.md` "Docs content policy — remove" governs wording.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Core contract enforcement (loader + models): `workflow_loader.py`, `models.py` | Pending | — | — | |
| 2 | Call-site and test updates: five test files | Pending | — | — | |
| 3 | Documentation (`docs/23_agent/agent_03_03-turn-processing-flow-workflow-engine.md`) and validation sequence | Pending | — | — | |

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
- **Source issue**: `issues/20261116-114753_compat001_workflow-definition-strict-contract.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261116-215105
- **Related target files**: `scripts/agent/workflow/models.py`, `scripts/agent/workflow/workflow_loader.py`, `tests/agent/test_orchestrator.py`, `tests/agent/workflow/test_workflow_models.py`, `tests/agent/workflow/test_adapter_store_ownership.py`, `tests/agent/workflow/test_session_diagnostics_wiring.py`, `tests/agent/workflow/test_workflow_engine.py`, `tests/agent/workflow/test_workflow_loader.py`, `docs/23_agent/agent_03_03-turn-processing-flow-workflow-engine.md` — the full list of `File Path` values from `Implementation Target Files` above, once `Frozen`

### Requirement Traceability
See `templates/requirement-traceability.md` for the canonical column format.

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Issue "Required Changes" (loader bullet); Issue Acceptance Criteria | `scripts/agent/workflow/workflow_loader.py` | Step 1 | JSON without `retry_policy.retry_on` raises `WorkflowLoadError` identifying it | `test_workflow_loader.py` rejection test | Explicit in issue |
| REQ-002 | Issue "Unresolved Questions" (empty `retry_on` semantics) | `scripts/agent/workflow/workflow_loader.py` | Step 1 | Empty-`retry_on` semantics decided, documented, tested | `test_workflow_loader.py` empty-`retry_on` semantics test | Derived from confirmed evidence |
| REQ-003 | Issue "Required Changes" (models bullet); Issue Acceptance Criteria | `scripts/agent/workflow/models.py` | Step 1 | `RetryPolicy(max_attempts=3, retry_wait_sec=1)` and `WorkflowDef(name="x", version="1.0.0")` raise `TypeError` | `test_workflow_models.py` constructor-surface tests | Explicit in issue |
| REQ-004 | Issue "Unresolved Questions" (empty-stage owner) | `scripts/agent/workflow/models.py` | Step 1 | Owner of empty-stage validation explicit, documented, tested | `test_workflow_models.py` empty-stage owner test | Derived from confirmed evidence |
| REQ-005 | Issue "Required Changes" (call-site bullet); repository evidence (`rg` scan) | `tests/agent/test_orchestrator.py` | Step 2 | Every repository call site supplies `retry_on`, `stages`, `retry_policy` explicitly | regression `pytest tests/agent/workflow tests/agent/test_orchestrator.py` | Confirmed by repository evidence |
| REQ-005 | Issue "Required Changes" (call-site bullet); repository evidence (`rg` scan) | `tests/agent/workflow/test_workflow_models.py` | Step 2 | Every repository call site supplies `retry_on`, `stages`, `retry_policy` explicitly | regression `pytest tests/agent/workflow tests/agent/test_orchestrator.py` | Confirmed by repository evidence |
| REQ-005 | Issue "Required Changes" (call-site bullet); repository evidence (`rg` scan) | `tests/agent/workflow/test_adapter_store_ownership.py` | Step 2 | Every repository call site supplies `retry_on`, `stages`, `retry_policy` explicitly | regression `pytest tests/agent/workflow tests/agent/test_orchestrator.py` | Confirmed by repository evidence |
| REQ-005 | Issue "Required Changes" (call-site bullet); repository evidence (`rg` scan) | `tests/agent/workflow/test_session_diagnostics_wiring.py` | Step 2 | Every repository call site supplies `retry_on`, `stages`, `retry_policy` explicitly | regression `pytest tests/agent/workflow tests/agent/test_orchestrator.py` | Confirmed by repository evidence |
| REQ-005 | Issue "Required Changes" (call-site bullet); repository evidence (`rg` scan) | `tests/agent/workflow/test_workflow_engine.py` | Step 2 | Every repository call site supplies `retry_on`, `stages`, `retry_policy` explicitly | regression `pytest tests/agent/workflow tests/agent/test_orchestrator.py` | Confirmed by repository evidence |
| REQ-005 | Issue "Required Changes" (call-site bullet); repository evidence (`rg` scan) | `tests/agent/workflow/test_workflow_loader.py` | Step 2 | Every repository call site supplies `retry_on`, `stages`, `retry_policy` explicitly | regression `pytest tests/agent/workflow tests/agent/test_orchestrator.py` | Confirmed by repository evidence |
| REQ-006 | Issue "Required Changes" (documentation bullet); Issue Documentation Impact | `docs/23_agent/agent_03_03-turn-processing-flow-workflow-engine.md` | Step 3 | Documentation no longer describes omitted fields as supported legacy formats | `check_docs_quality.py`, `check_docs_consistency.py --domain agent` | Explicit in issue |
