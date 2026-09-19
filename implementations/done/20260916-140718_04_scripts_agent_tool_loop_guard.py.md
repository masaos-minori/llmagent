## Goal

Add a clarifying docstring note to `scripts/agent/tool_loop_guard.py` near the `check_retry()` method, explicitly stating it is ToolLoopGuard's own per-turn retry suppression distinct from WorkflowEngine's stage-level retry.

## Scope

- Add a clarifying note to `tool_loop_guard.py`'s `check_retry()` method docstring.
- The note must explicitly state that this is ToolLoopGuard's own per-turn retry suppression, distinct from WorkflowEngine's stage-level retry.

## Assumptions

- The `check_retry()` method currently exists at L281-L301 in the file.
- The method has a docstring: "Block retry of already-failed (tool, args); return exit msg when hit."

## Design decisions

- Add the note inline in the existing docstring — do not create a new standalone comment block.
- Keep the note concise — one sentence appended to the existing docstring.

## Alternatives considered

- Adding the note to all guard methods — rejected because the Plan's intent is specifically about the retry mechanism distinction, which is unique to `check_retry()`.

## Implementation
### Target file

`scripts/agent/tool_loop_guard.py`

### Procedure

1. Locate the `check_retry()` method (L281-L301).
2. Update the docstring to include the clarification about the distinction from WorkflowEngine retry.

### Method

Current docstring (L286):
```python
    def check_retry(
        self,
        failed_calls: set[str],
        message: LLMMessage,
    ) -> str | None:
        """Block retry of already-failed (tool, args); return exit msg when hit."""
```

Required update:
```python
    def check_retry(
        self,
        failed_calls: set[str],
        message: LLMMessage,
    ) -> str | None:
        """Block retry of already-failed (tool, args); return exit msg when hit.

        Distinction from WorkflowEngine retry: this is ToolLoopGuard's own
        per-turn retry suppression — it prevents the same (tool, args) pair
        from being retried within a single turn. It is NOT the same as
        WorkflowEngine.retry_policy.max_attempts, which governs stage-level
        retries across turns. These are two independent mechanisms at different
        granularities.
        """
```

### Details

The updated docstring should replace the existing single-line docstring. The additional text should follow the existing style — use double quotes for the docstring, and keep each line under 88 characters per `rules/coding.md` conventions.

## Compatibility considerations

- This is a documentation-only change — no code compatibility impact.
- The cross-reference to `WorkflowEngine.retry_policy` is intentional and stable.

## Security considerations

- No security impact — documentation-only change.

## Rollback considerations

- If the docstring note is found to be misleading, simply revert to the original single-line docstring. No behavioral rollback needed since there is none.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/agent/tool_loop_guard.py` | Code quality | `uv run ruff check scripts/agent/tool_loop_guard.py` | Clean |
| `scripts/agent/tool_loop_guard.py` | Type checking | `uv run mypy scripts/agent/tool_loop_guard.py` | Clean |
| `tests/agent/test_tool_loop_guard.py` | Regression tests | `uv run pytest tests/agent/test_tool_loop_guard.py -v` | All pass |

## Completion criteria

- `scripts/agent/tool_loop_guard.py`'s `check_retry()` docstring explicitly distinguishes it from `WorkflowEngine.retry_policy`.
- `uv run ruff check scripts/agent/tool_loop_guard.py` passes clean.
- `uv run mypy scripts/agent/tool_loop_guard.py` passes clean.
- `uv run pytest tests/agent/test_tool_loop_guard.py -v` passes all tests.

## Out of scope

- Updating the other guard methods' docstrings — out of scope for this specific change.
- Changing any of the three retry mechanisms' behavior — this is documentation-only.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | — | ruff check passed; mypy blocked by pre-existing error |
| 2 | Add or update tests per Validation plan | Blocked | — | — | pytest collection fails due to syntax error in tool_audit.py |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Partially completed | — | — | ruff clean; mypy/pre-existing blocker; pytest/unresolvable |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Skipped | — | — | No docs/*.md mapping for this task |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 2 | tests/agent/test_tool_loop_guard.py collection fails: scripts/agent/tool_audit.py:202 SyntaxError — keyword argument repeated: idempotency_key | No | — |
| 3 | mypy reports: scripts/shared/tool_constants.py error: Source file found twice under different module names ("shared.tool_constants" and "scripts.shared.tool_constants") | No | — |

### Adversarial Review Findings
| # | Category | Severity | Finding |
|---|----------|----------|---------|
| 1 | Scope vs Design contradiction | Medium | Scope says "one sentence appended"; actual addition is 5-sentence paragraph (L53-L61) |
| 2 | Assumption inaccuracy | Low | L12 claims check_retry() at L281-L301; actual location is L281-L309 |
| 3 | Unachievable validation criterion | High | mypy check cannot pass clean due to pre-existing tool_constants.py module conflict |
| 4 | Unachievable validation criterion | High | pytest check cannot collect tests due to SyntaxError in tool_audit.py:202 |
| 5 | API reference stability | Medium | WorkflowEngine.retry_policy.max_attempts reference is not guaranteed stable as an API contract |
| 6 | Line-number dependency | Low | Procedure references L281-L301 which will become stale after any concurrent edit |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| BLOCKER-001 | 2 | Pre-existing SyntaxError in tool_audit.py | Open | — | — |
| BLOCKER-002 | 3 | Pre-existing mypy module conflict in shared.tool_constants | Open | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-004
- **Source issue**: issues/20260914-123659_arch03_retry_ownership_documentation_and_layering.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260916-140718_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260916-140718
- **Related target files**: scripts/agent/tool_loop_guard.py
