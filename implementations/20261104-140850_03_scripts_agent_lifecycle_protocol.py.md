## Goal
- Update the `start_http_subprocess` docstring in `LifecycleManagerProtocol` so the contract says that an implementation refuses a start suppressed by shutdown with a typed error instead of returning `None` (`REQ-006`: protocol contract text describes the raise).

## Scope
**Release unit**: startup-start-contract

- One docstring in `scripts/agent/lifecycle_protocol.py`. The method signature, return annotation, and every other protocol method are unchanged.

## Assumptions
- The docstring currently reads `Start a single HTTP subprocess MCP server; returns the Popen object or None.` and the signature is shared by `_ServerLifecycleRouter` and `_SubprocessLifecycleManager` (checked in Step 3a).
- The typed error is declared (new) by the sibling procedure for `scripts/agent/lifecycle_router.py`; this docstring names it in prose only and does not import it (the protocol module must not import the router).
- Step 2 start conditions held: the Plan is not gated, has no blocking Unknown, and no cross-plan overlap names it.

## Design decisions
- Keep the signature and `| None` return type; `None` still means only that no process was recorded.
- Describe the contract in prose without an import or a code reference, so the protocol module keeps its dependency direction.

## Alternatives considered
N/A: docstring-only change; the signature stays unchanged by the Plan's Decision 1.

## Implementation
### Target file
`scripts/agent/lifecycle_protocol.py`

### Procedure
Replace the one-line docstring of `LifecycleManagerProtocol.start_http_subprocess` with a short multi-line docstring.

### Method
Before:

```python
        """Start a single HTTP subprocess MCP server; returns the Popen object or None."""
        ...
```

After:

```python
        """Start a single HTTP subprocess MCP server and return its Popen object.

        None means only that no process was recorded. A manager that refuses a start
        because shutdown has begun raises a typed error instead of returning None.
        """
        ...
```

### Details
- Keep each docstring line within 88 characters and keep the `...` body line.
- `tools/check_docstrings.py` checks the docstring format of `scripts/` modules; run it after the edit.

## Compatibility considerations
N/A: docstring only; no signature, import, or behavior change.

## Security considerations
N/A: documentation text in a docstring.

## Rollback considerations
N/A: revert the commit (released with the rest of the unit).

## Validation plan
- `uv run ruff format --check scripts/agent/lifecycle_protocol.py` and `uv run ruff check scripts/agent/lifecycle_protocol.py`.
- `uv run python tools/check_docstrings.py` and `uv run mypy --no-namespace-packages scripts/ tests/eventbus` with no new findings.
- `git diff -U0 scripts/agent/lifecycle_protocol.py` shows only the docstring lines changed.

## Completion criteria
- The protocol docstring states that `None` means no recorded process and that a start suppressed by shutdown raises a typed error (`AC-3`).
- No signature or import changed.

## Out of Scope
- The router and starter changes and all tests (separate procedures).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Replace the docstring as described in Implementation > Procedure/Method | Pending | — | — | |
| 2 | Run the validation plan: format, lint, docstring check, mypy, diff check | Pending | — | — | |

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
- **Requirement ID**: `REQ-006` (protocol contract text describes the raise)
- **Source issue**: `issues/20261031-135448_startretry001_startup-retry-blocked-cooldown.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261104-095204_startretry001_startup-retry-blocked-cooldown.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261104-140850
- **Related target files**: `scripts/agent/lifecycle_protocol.py`
