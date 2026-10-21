# Remove dead StartupOrchestrator._classify_memory_failure method

## Priority
Low

## Summary
Delete `StartupOrchestrator._classify_memory_failure` in `scripts/agent/startup.py`. It is defined but never called anywhere; the memory-failure classification it forwards actually lives in `PromptSetup._classify_memory_failure` (`scripts/agent/startup_prompt_setup.py`) and is used there.

## Background
`startup.py` defines:
```python
def _classify_memory_failure(self, exc: Exception) -> str:
    return self._prompt_setup._classify_memory_failure(exc)
```
A repo-wide search for `_classify_memory_failure` returns only its definition and body in `startup.py`, the call inside `PromptSetup.setup_prompt()` (`startup_prompt_setup.py`), and a docstring reference in `startup_validation.py`. No caller invokes `StartupOrchestrator._classify_memory_failure`.

## Problem
Dead code that forwards to another method invites confusion about which classifier is authoritative and accumulates maintenance burden. If the delegation target signature changes, this method silently breaks without any test covering it.

## Reason for Change
Removing it eliminates an unused forwarding shim and removes a symbol that implies a second classification path exists. The real classifier remains reachable through `PromptSetup`.

## Implementation Intent
- Delete the `_classify_memory_failure` method from `StartupOrchestrator`.
- Confirm via grep that nothing references it before removal.
- Do not touch `PromptSetup._classify_memory_failure` or the module-level `_classify_rag_failure` in `startup_validation.py`, which are live.

## Target Files or Areas
- `scripts/agent/startup.py` (remove the method)

## Required Changes
- Delete the two-line `_classify_memory_failure` method and its docstring.
- Verify no test references `StartupOrchestrator._classify_memory_failure`.

## Constraints
- Behavior-preserving: this method is never called, so removing it changes no runtime behavior.
- Do not remove the working classifier in `startup_prompt_setup.py`.

## Acceptance Criteria
- `_classify_memory_failure` no longer exists on `StartupOrchestrator`.
- Grep for `_classify_memory_failure` shows only the `startup_prompt_setup.py` definition/call and the `startup_validation.py` docstring reference.
- Startup unit tests pass.

## Testing Expectations
- Confirm no test references the removed method.
- `uv run ruff check`, `uv run mypy`, `uv run bandit` on edited files.

## Documentation Impact
None required.

## Out of Scope
- Any change to the live memory-failure classifiers.

## Dependencies
- N/A: none

## Unresolved Questions
- N/A: none

## AI Implementation Instruction
- Delete only the `_classify_memory_failure` method in `startup.py`.
- Grep first to prove zero callers; stop and report if a caller exists that the grep missed.

## Traceability
- **Workflow phase**: python-code-review
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261021-220515
- **Related target files**: `scripts/agent/startup.py`
