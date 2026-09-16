## Goal

Correct `ToolRouteResolver.__init__`'s docstring in `scripts/shared/route_resolver.py` to state precisely that `strict_mode=True` both (a) raises a stricter-worded `ValueError` and (b) bypasses the `warn_on_missing` warning log via the `NoReturn` `_raise_strict_error()` path, and that both `strict_mode` states always raise `ValueError` on an unresolved tool — replacing any implication that `strict_mode` affects only message wording.

## Scope

- Correct the docstring for `ToolRouteResolver.__init__` (lines 79-87) in `scripts/shared/route_resolver.py`
- No other files are modified in this row

## Assumptions

- The sole production construction site (`scripts/shared/tool_executor.py:54`) passes no `strict_mode` argument.
- The sole `strict_mode=True` call site is `tests/agent/services/test_runtime_tool_routing_integration.py::test_strict_mode_error_message_mentions_runtime_registry`, whose own docstring already frames the difference as message-only.
- This is a docstring-only change — no import, signature, schema, or control-flow change.

## Design decisions

- Correction rather than renaming/removal: the Issue's own stated condition for renaming/removing the parameter ("it changes only error wording") does not hold — `strict_mode=True` also suppresses the warning log that `warn_on_missing=True` would otherwise emit. Because the Issue's stated condition for renaming/removal does not hold, and because a full rename/removal is itself an interface change beyond this Issue's declared "documentation/wording correction, not a behavior change" scope, this Plan instead documents both effects precisely.

## Alternatives considered

- Renaming or removing `strict_mode` — rejected: inconsistent with this Issue's own "documentation/wording correction, not a behavior change" framing; the parameter has two distinct effects (message wording + warning-log suppression), so renaming it would still be an interface change.
- Adding a new parameter to separate the two effects — rejected: unnecessary complexity; documenting the existing behavior precisely is sufficient.

## Implementation

### Target file

`scripts/shared/route_resolver.py`

### Procedure

Correct `ToolRouteResolver.__init__`'s docstring to state `strict_mode`'s full effect (message wording + warning-log suppression).

### Method

1. Re-verify, immediately before editing, that each target row's cited line/content is unchanged since this Plan's evidence-gathering (per `rules/workflow-lifecycle.md` Revalidation): `scripts/shared/route_resolver.py` lines 79-106.
2. Correct the docstring for `ToolRouteResolver.__init__` (lines 79-87):
   - Change the `strict_mode` description from "When True, raise on unresolved tools in `resolve()` with a stricter error message." to state both effects: raising a stricter-worded `ValueError` AND bypassing the `warn_on_missing` warning log via the `NoReturn` `_raise_strict_error()` path.
   - Clarify that both `strict_mode` states always raise `ValueError` on an unresolved tool.

### Details

```python
# Lines 79-87: correct the docstring:
# Before:
"""Initialize the resolver.

Args:
    warn_on_missing: When True, log a warning on unresolved tools in `resolve()`.
    strict_mode: When True, raise on unresolved tools in `resolve()` with a
        stricter error message.
    runtime_registry: Optional RuntimeToolRegistry from live /v1/tools discovery;
        the sole routing source consulted by resolve().
"""

# After:
"""Initialize the resolver.

Args:
    warn_on_missing: When True, log a warning on unresolved tools in `resolve()`.
        Note: if `strict_mode=True`, this warning is never emitted because
        `strict_mode=True` causes `resolve()` to raise `ValueError` directly
        via `_raise_strict_error()` before reaching the `warn_on_missing` check.
    strict_mode: When True, raise on unresolved tools in `resolve()` with a
        stricter error message. Also bypasses the `warn_on_missing` warning log
        entirely: when `strict_mode=True`, `resolve()` calls `_raise_strict_error()`
        (a `NoReturn` path) before ever reaching the `warn_on_missing` check, so
        both `strict_mode=True` and `strict_mode=False` always raise `ValueError`
        on an unresolved tool — the difference is in error-message wording only.
    runtime_registry: Optional RuntimeToolRegistry from live /v1/tools discovery;
        the sole routing source consulted by resolve().
"""
```

## Compatibility considerations

- No production code depends on the specific docstring text being changed.
- The sole production construction site (`scripts/shared/tool_executor.py:54`) passes no `strict_mode` argument, so no caller needs updating.
- The sole `strict_mode=True` call site (`tests/agent/services/test_runtime_tool_routing_integration.py::test_strict_mode_error_message_mentions_runtime_registry`) must continue to pass unmodified — no test change in this Plan.

## Security considerations

- No security impact. This is a docstring correction, not a security boundary change.

## Rollback considerations

- Reverting this change restores the original docstring. If needed later, the docstring should be corrected again to match the current `resolve()` control flow.

## Validation plan

- Regression: run `uv run pytest tests/agent/services/test_runtime_tool_routing_integration.py -v` to confirm no failures introduced.
- Static analysis: `uv run ruff check scripts/shared/route_resolver.py`, `uv run mypy scripts/shared/route_resolver.py`.
- Import lint: `PYTHONPATH=scripts uv run lint-imports` to confirm no broken contracts introduced.

## Completion criteria

- `ToolRouteResolver.__init__`'s docstring correctly states both of `strict_mode`'s actual effects (message wording and warning-log suppression).
- The parameter itself is unchanged (no rename or removal).
- All existing tests in `tests/agent/services/test_runtime_tool_routing_integration.py` continue to pass without modification.
- No new lint/type errors introduced.

## Out of scope

- Renaming or removing `strict_mode` — an interface-level change beyond this Issue's declared "documentation/wording correction, not a behavior change" scope.
- Changes to `docs/*.md` — not applicable to this row.
- Modifying any other file — covered by separate rows (REQ-002, REQ-003, REQ-004).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Correct ToolRouteResolver.__init__ docstring to state strict_mode's full effect | Pending | — | — | |
| 2 | Run the validation sequence (rules/toolchain.md) | Pending | — | — | |

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
- **Requirement ID**: REQ-001
- **Source issue**: issues/20260914-103349_mcpagent09_routing-discovery-test-config-documentation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260916-131528_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260916-231122
- **Related target files**: scripts/shared/route_resolver.py
