# Reject non-dict workflow elements and unvalidated retryable coercion

## Priority
Medium

## Summary
The workflow definition loader validates keys and numeric values but does not verify that `stages` and `retry_policy` elements are dicts, and coerces `retryable` with a bare `bool()`. Close both validation gaps so malformed definitions fail as `WorkflowLoadError` at load time.

## Background
Code review evidence (Verified):
- `_validate` checks required keys per stage by membership (`"id" in s`), which passes for strings and other containers; `load` then does subscript access and raises `TypeError`/`AttributeError` outside the loader's own error type.
- The startup preflight wraps loading in a broad `except (WorkflowLoadError, ValueError, TypeError, AttributeError)`, so the crash class is logged as a generic "invalid definition" message; the orchestrator's own catch covers only `(WorkflowLoadError, FileNotFoundError)` and would propagate the raw error at construction.
- `bool(s["retryable"])` turns any non-empty value into True — a config writing `"false"` as a string yields retryable=True. The numeric fields were hardened against exactly this class of coercion (strict int checks, tests parametrized over `"120"`, `2.5`, `True`), but `retryable` was not.
- Existing loader tests cover required keys, duplicates, required-stage sets, numeric coercion, and `retry_on` element types; no test covers a non-dict stage/policy element or a non-bool `retryable`.
Context: the numeric hardening originated from `issues/done/20261103-134147_wfreview003_workflow-loader-bare-int-coercion.md` (resolved); this issue covers the remaining gaps in the same validator.

## Problem
- A definition with `stages: ["plan"]` or `retry_policy: "default"` crashes with a raw `TypeError`/`AttributeError` whose message does not name the definition file; behavior differs between the startup gate (masked) and direct orchestrator construction (crash).
- `retryable: "false"` silently means True — a configuration truthiness bug opposite to its text.

## Reason for Change
The loader is a config-boundary validator; its contract is that every malformed definition raises `WorkflowLoadError` naming the file. Two known holes remain from the earlier coercion-hardening work, and the broad `except` in the preflight actively hides the class of the failure.

## Implementation Intent
Extend the existing validator: element-type checks (each stage and the retry policy must be mapping objects) and strict boolean acceptance for `retryable` (accept JSON true/false only, mirroring the strict-int pattern). No new error types; reuse `WorkflowLoadError` wording conventions. The broad `except` tuple in the startup gate can then keep its shape, but the loader's own contract no longer relies on it.

## Target Files or Areas
- scripts/agent/workflow/workflow_loader.py
- tests/agent/workflow/test_workflow_loader.py
- scripts/agent/services/workflow_schema.py (broad except around loading, review only)

## Required Changes
- Validate that each `stages` element and `retry_policy` is a dict-like mapping; raise `WorkflowLoadError` naming the file otherwise.
- Require `retryable` to be a JSON boolean; reject any other type.
- Add loader tests for both cases.

## Constraints
- Error messages must follow the existing "file + key + expectation" wording pattern used by the numeric checks.
- Do not change the strict-int rules already in place.
- Keep the shipped `config/workflows/default.json` loading unchanged.

## Acceptance Criteria
- `stages` containing a non-dict element raises `WorkflowLoadError` (not `TypeError`/`AttributeError`).
- A non-dict `retry_policy` raises `WorkflowLoadError`.
- `retryable` values other than true/false raise `WorkflowLoadError`.
- All existing loader tests remain green.

## Testing Expectations
- Parametrized unit tests mirroring the existing numeric-coercion parametrization (string, number, list, bool where relevant).
- `validate_path` (the preflight entry point) raises `WorkflowLoadError` for the new cases without needing the broad except.
- Ruff/mypy clean on the touched files.

## Documentation Impact
No doc content changes required beyond what already describes load-time validation semantics; if a workflow-definition docs page enumerates accepted value types, state that `retryable` must be a JSON boolean.

## Out of Scope
- Adding new definition keys or defaults.
- Changing the startup preflight's error handling design.
- Approval of any new retry kinds.

## Dependencies
- Builds on the resolved coercion-hardening work: `issues/done/20261103-134147_wfreview003_workflow-loader-bare-int-coercion.md` (patterns to mirror; already archived).

## Unresolved Questions
- Should the startup preflight's broad `except` tuple be narrowed once the loader contract is complete, or is defense-in-depth intentional here? (Needs confirmation; out of scope for this issue either way.)

## AI Implementation Instruction
Change only `workflow_loader.py` validation and its tests. Reuse the established `WorkflowLoadError` message style. Do not weaken any existing validation. If the preflight's broad except tuple becomes provably redundant, note it in the PR text only — do not remove it in this issue.

## Traceability
- **Workflow phase**: python-code-review
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261107-203217
- **Related target files**: scripts/agent/workflow/workflow_loader.py, tests/agent/workflow/test_workflow_loader.py, scripts/agent/services/workflow_schema.py

## Adversarial Validation

Validated against current source on 2026-11-08 (issue-to-plan Step 2 cycle), including live repro in the project venv.

- Non-dict element escape confirmed with corrected mechanism: `stages: ["plan"]` raises raw `AttributeError: 'str' object has no attribute 'get'` (from `stage_ids = [s.get("id") for s in stages_data]`, `scripts/agent/workflow/workflow_loader.py:103`); `retry_policy: "default"` raises raw `AttributeError: 'str' object has no attribute 'keys'` (L118). Current `_validate` uses `.keys()` set-difference, not the `"id" in s` membership form the issue describes — the escape is real but crashes one line earlier than stated. — Evidence: `Verified by test` (live repro) — Confidence: High
- `retryable: "false"` → `retryable=True` confirmed live: `bool(s["retryable"])` at `workflow_loader.py:158`; repro loaded the definition and observed `retryable is True`. No test pins a non-bool `retryable` (grep: all test fixtures use JSON booleans). — Evidence: `Verified by test` — Confidence: High
- Broad preflight except confirmed: `scripts/agent/services/workflow_schema.py:38` wraps loading in `except (WorkflowLoadError, ValueError, TypeError, AttributeError)`; the orchestrator catch is `except (WorkflowLoadError, FileNotFoundError)` (`scripts/agent/orchestrator.py:130`) and would propagate the raw error at construction. — Evidence: `Verified by test` — Confidence: High
- Name correction: `validate_path` no longer exists; the preflight entry points are `check_workflow_definition()` / `check_workflow_schema()` (`workflow_schema.py:21,86`). Tests must target `check_workflow_definition`. — Evidence: `Verified by test` — Confidence: High
- Strict-int pattern to mirror confirmed and test-pinned (`_require_int`, L84-95; parametrized tests at `tests/agent/workflow/test_workflow_loader.py:236,254`). — Evidence: `Verified by test` — Confidence: High
