# Require explicit retry_on, stages, and retry_policy in workflow definitions

## Priority
High

## Summary
Remove the implicit defaults that let a workflow definition omit `retry_policy.retry_on`, `stages`, or `retry_policy`. The JSON loader and the Python models must enforce one explicit contract, so a missing field fails at the configuration or constructor boundary instead of being synthesized. The shipped retry behavior (exception-only retry) must not change.

## Background
Source: `memo-issue.md` Issue 1 (items H-01, H-02, H-03), re-verified against current source.

- Explicit in code: `scripts/agent/workflow/workflow_loader.py` documents `retry_on` as optional, keeps `_REQUIRED_POLICY_KEYS` at `max_attempts` and `retry_wait_sec`, and `_validate_retry_on()` reads `policy.get("retry_on")`.
- Explicit in code: `scripts/agent/workflow/models.py` gives `RetryPolicy.retry_on` the default `("exception",)`, gives `WorkflowDef.stages` a `default_factory=list`, and gives `WorkflowDef.retry_policy` a default factory that builds `RetryPolicy(max_attempts=3, retry_wait_sec=1)`.
- Explicit in code: `config/workflows/default.json` already declares `retry_on`; the loader is the only production constructor of `WorkflowDef` and `RetryPolicy` under `scripts/` outside `models.py` itself.
- Explicit in code: tests construct these models directly in `tests/agent/test_orchestrator.py`, `tests/agent/workflow/test_workflow_engine.py`, `tests/agent/workflow/test_workflow_models.py`, `tests/agent/workflow/test_adapter_store_ownership.py`, and `tests/agent/workflow/test_session_diagnostics_wiring.py`.
- The memo cited `tests/test_workflow_loader.py`, `tests/test_workflow_models.py`, and `tests/test_workflow_engine.py`. Those paths were not confirmed; the models and engine tests live under `tests/agent/workflow/`. The loader test location is `Needs confirmation`.

## Problem
Loader and models enforce different contracts. An operator who removes `retry_on` from a workflow JSON gets no startup error; the definition silently becomes exception-only retry. A strict loader can also be bypassed by constructing the models directly with implicit defaults, so the strictness is not a real guarantee. Tests that omit these fields inherit unrelated defaults instead of stating the policy they exercise.

## Reason for Change
Correctness and configuration-audit risk: a configuration defect is concealed rather than reported. The obsolete defaults only preserve older input and constructor contracts. Nothing makes the change time-sensitive; doing it first only reduces the number of simultaneous workflow-contract changes when the lease issue is implemented.

## Implementation Intent
Establish one explicit workflow-definition contract across configuration, models, production code, tests, and documentation. Every definition states its stages, supplies a retry policy, and every retry policy states the failure kinds it retries. Missing fields fail at the boundary that receives them. Keep the shipped value `retry_on=("exception",)` but make it explicit and auditable. Do not change retry semantics.

Choose a single owner for empty-stage validation and document it:

- Preferred: `WorkflowDef.__post_init__()` rejects empty `stages`, because direct model construction is exercised by the orchestrator and tests.
- Alternative: the loader is the sole structural validator, which requires proving that production never constructs `WorkflowDef` directly. The loader is currently the only production constructor, so this is viable; the choice is a design decision for the plan.

## Target Files or Areas
- `scripts/agent/workflow/workflow_loader.py`
- `scripts/agent/workflow/models.py`
- `scripts/agent/orchestrator.py` (references `WorkflowDef` or `RetryPolicy`; usage to be confirmed)
- `config/workflows/default.json`
- `tests/agent/test_orchestrator.py`
- `tests/agent/workflow/test_workflow_engine.py`
- `tests/agent/workflow/test_workflow_models.py`
- `tests/agent/workflow/test_adapter_store_ownership.py`
- `tests/agent/workflow/test_session_diagnostics_wiring.py`
- Workflow loader tests (path `Unknown`; locate with a repository search)
- `docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md`

## Required Changes
- Loader: make `retry_on` a required policy key, remove the absent-key fallback in `_validate_retry_on()`, validate it only after required-key validation, and raise `WorkflowLoadError` naming `retry_policy.retry_on` when missing. Keep the supported kinds `exception`, `timeout`, `llm_failure` and keep rejecting unknown kinds. Update the loader's `_RetryPolicyJson` documentation.
- Decide and document whether an empty `retry_on` list means "retry nothing". Do not infer it from existing defaults.
- Models: remove the default from `RetryPolicy.retry_on`, the default factory from `WorkflowDef.stages`, and the default factory from `WorkflowDef.retry_policy`; all three become required constructor arguments.
- Empty stages: implement the chosen owner and test it.
- Update every direct `RetryPolicy(...)` and `WorkflowDef(...)` call site found by repository-wide search (the Target Files tests above, plus any additional hit). Use `retry_on=("exception",)` for fixtures that represent the shipped configuration and policy-specific values for timeout and LLM-failure tests.
- Tests: replace loader tests that accept omitted `retry_on` with rejection tests; remove model tests that pin implicit defaults and add tests for the required constructor surface.
- Documentation: mark `stages`, `retry_policy`, and `retry_policy.retry_on` as required and remove wording that treats omitted `retry_on` as a supported older format.

## Constraints
- The shipped retry behavior stays exception-only; `config/workflows/default.json` must still load.
- No compatibility default, migration shim, or optional-argument overload is added.
- Measure the blast radius before editing (`rules/toolchain.md` Impact-radius check). At least five test files construct these models, so the work likely exceeds the ~10-reference threshold; record it in the plan.
- Documentation edits follow `skills/DESIGN.md` "Docs content policy — remove": describe the contract, do not copy configuration values or implementation locations.

## Acceptance Criteria
- [ ] Workflow JSON without `retry_policy.retry_on` raises `WorkflowLoadError`, and the message identifies `retry_policy.retry_on` as missing.
- [ ] `RetryPolicy(max_attempts=3, retry_wait_sec=1)` raises `TypeError`.
- [ ] `WorkflowDef(name="x", version="1.0.0")` raises `TypeError`.
- [ ] Every repository call site supplies `retry_on`, `stages`, and `retry_policy` explicitly.
- [ ] `config/workflows/default.json` loads and retains exception-only retry behavior.
- [ ] Unknown retry kinds are still rejected.
- [ ] The owner of empty-stage validation is explicit, documented, and tested.
- [ ] The empty-`retry_on` semantics are decided, documented, and tested.
- [ ] Tests and documentation no longer describe omitted fields as supported legacy formats.
- [ ] `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools` reports no new errors.

## Testing Expectations
- Run `rg -n "RetryPolicy\(" scripts tests tools` and `rg -n "WorkflowDef\(" scripts tests tools` and inspect every hit.
- Unit tests: loader rejection of missing `retry_on`; constructor-surface tests for both models; empty-stage owner test; empty-`retry_on` test.
- Regression: `uv run pytest tests/agent/workflow tests/agent/test_orchestrator.py`.
- Run the validation sequence in `rules/toolchain.md` (ruff, mypy, lint-imports, bandit, pytest, diff-cover).
- Documentation: `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_consistency.py --domain agent`, `uv run python tools/check_compat_shims.py`.

## Documentation Impact
Update `docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md`. State intent and boundaries: required fields, allowed retry kinds, who validates empty stages, and the failure behavior when a field is missing. Do not state the shipped retry value as an implicit default.

## Out of Scope
- Changing retry semantics, retry kinds, or `max_attempts` / `retry_wait_sec` handling.
- Attempt lease changes (separate issue for the lease contract).
- Adding a migration path for old workflow JSON files.
- Compatibility-checker rules (separate issue).

## Dependencies
- Recommended before `issues/20261116-114834_compat002_mandatory-attempt-leases.md` (order only; not a technical dependency).
- Sibling check: the only open work item touching related areas is `plans/20261115-054021_dbreview008_artifact-retention-gaps.md` and its issue; it concerns artifact retention and does not overlap these files. No archived issue from the last 30 days was found to overlap the workflow definition files.

## Unresolved Questions
- Empty `retry_on` semantics: "retry nothing" or invalid? `不明`, a design decision to record in the plan.
- Empty-stage owner: model `__post_init__()` or loader only? `不明`, see Implementation Intent.
- Location of the loader test file: `不明` (the memo's path was not confirmed).
- Whether `scripts/agent/workflow_engine_adapter.py` and `scripts/agent/workflow/__init__.py` construct or re-export these models: `Needs confirmation`.
- Whether `scripts/agent/orchestrator.py` constructs these models or only references them: `Needs confirmation`.

## AI Implementation Instruction
Change only the loader, models, their call sites, tests, and the one documentation file listed. Preserve the shipped retry behavior. Do not add defaults, optional parameters, or fallbacks. Stop and report if the empty-`retry_on` or empty-stage decision is unresolved at plan time. Do not touch lease or schema code.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261116-114753
- **Related target files**: `scripts/agent/workflow/workflow_loader.py`, `scripts/agent/workflow/models.py`, `scripts/agent/orchestrator.py`, `config/workflows/default.json`, `tests/agent/test_orchestrator.py`, `tests/agent/workflow/test_workflow_engine.py`, `tests/agent/workflow/test_workflow_models.py`, `tests/agent/workflow/test_adapter_store_ownership.py`, `tests/agent/workflow/test_session_diagnostics_wiring.py`, `docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md`
