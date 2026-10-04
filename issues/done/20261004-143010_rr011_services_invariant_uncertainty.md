# ReadinessReporter: Accesses services_required without null check before services assignment

## Background

`ReadinessReporter.report_readiness()` in `scripts/agent/startup_reporter.py` reports aggregated readiness status after startup checks complete. It accesses `self._ctx.services_required.runtime_tools` and `self._ctx.services_required.health_registry`.

## Problem

While the code does have null checks for `services_required` in some places (lines 97-101, 107-111), there is a subtle issue: the `services_required` property is accessed multiple times within the same method, and between accesses the context could theoretically be in an inconsistent state (though unlikely in single-threaded asyncio).

More importantly, the docstring says "All required services are non-None" but the reporter still performs defensive null checks, suggesting the invariant is not guaranteed.

## Evidence

- File: `scripts/agent/startup_reporter.py`
- Lines 97-101:

```python
runtime_tools = (
    self._ctx.services_required.runtime_tools
    if self._ctx.services_required
    else None
)
```

## Impact

- Defensive checks add complexity without clear benefit if the invariant holds
- If the invariant doesn't hold, the null checks mask the real problem (missing service injection)
- The inconsistency between docstring claims and defensive coding suggests uncertainty about the invariant

## Recommended action

1. Clarify the invariant: either enforce it in `AppServices.__init__()` or remove the defensive checks.
2. If keeping defensive checks, document why they're needed despite the docstring claim.
3. Consider adding a `@property` assertion in `AgentContext.services_required` that validates all required sub-services are present.

## Acceptance criteria

- [ ] Either invariant enforced at construction OR defensive checks documented
- [ ] No ambiguity between docstring claims and implementation behavior
- [ ] Test verifies consistent behavior under both scenarios

## Out of scope

- Changes to `services_required` property implementation
- Changes to the readiness report format
