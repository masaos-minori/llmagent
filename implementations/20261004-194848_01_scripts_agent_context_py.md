## Goal

Preserve the original exception traceback when `AgentContext.__init__()` fails to load configuration, enabling proper root cause diagnosis.

## Scope

- Modify `scripts/agent/context.py`: remove `from None` clause to preserve exception chain
- Update callers that depend on the wrapper exception only (review only, no code changes expected)

## Assumptions

- Callers catching `RuntimeError` will still receive the wrapper exception (type unchanged)
- The exception chain adds verbosity but does not break existing error handling

## Design decisions

- Remove `from None` to preserve the original exception chain — this is the desired behavior per REQ-001
- Keep the wrapper RuntimeError with contextual information about the config directory

## Alternatives considered

- Using `logging.exception()` instead of raising — loses the ability for callers to handle the exception
- Adding a custom exception class — over-engineering for this use case

## Implementation
### Target file
`scripts/agent/context.py`

### Procedure
Remove `from None` clause to preserve the original exception chain.

### Method
1. Locate line 313 in `scripts/agent/context.py`
2. Change `raise RuntimeError(...) from None` to `raise RuntimeError(...)` (remove `from None`)

### Details
```python
# Before (line 313):
raise RuntimeError(f"Failed to load agent config from {config_dir}") from None

# After:
raise RuntimeError(f"Failed to load agent config from {config_dir}")
```

The key change is removing `from None` to preserve the original exception chain. This allows debugging tools and CI/CD pipelines to see the full stack trace including the root cause.

## Compatibility considerations

Callers catching `RuntimeError` will still receive the wrapper exception (type unchanged). However, the exception chain adds verbosity to stack traces — this is the desired behavior per REQ-001.

## Security considerations

N/A: No security impact.

## Rollback considerations

Revert to `from None` if callers rely on the wrapper exception being the sole exception. This would restore the previous behavior but lose exception chain visibility.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/agent/context.py | Unit test — verify exception chain preservation | uv run pytest tests/agent/test_context.py | New tests pass, existing tests pass |

## Completion criteria

- [ ] Original exception chain is preserved in stack traces (REQ-001)
- [ ] All new tests pass when run individually

## Out of scope

- Changes to `build_agent_config()` error messages
- Changes to logging format
- Creating new test file (handled in separate document)

## execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Source issue**: issues/20261004-143004_ac005_traceback_suppression.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261004-182812_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261004-194848
- **Related target files**: scripts/agent/context.py
