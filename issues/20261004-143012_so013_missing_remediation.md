# StartupOrchestrator: FATAL error message omits remediation steps

## Background

`StartupOrchestrator._check_services()` in `scripts/agent/startup.py` raises a `RuntimeError` when the validation pipeline has FATAL outcomes.

## Problem

The error message only includes the fatal outcome messages but not their associated remediation steps. Users see the error but don't know how to fix it.

## Evidence

- File: `scripts/agent/startup.py`
- Lines 115-121:

```python
if pipeline.has_fatal:
    fatal_str = "; ".join(pipeline.fatal_messages())
    logger.error(...)
    raise RuntimeError(f"Startup validation failed: {fatal_str}")
```

Compare with `startup_reporter.py` lines 66-67 where remediation IS displayed:

```python
elif outcome.status == StartupCheckStatus.FATAL:
    self._view.write_fatal(outcome.message)
    if outcome.remediation:
        self._view.write_fatal(f"  Remediation: {outcome.remediation}")
```

## Impact

- Users cannot determine how to resolve the error from the exception alone
- CI/CD pipelines cannot parse remediation steps from error output
- Support burden increases because users must consult documentation separately

## Recommended action

Include remediation steps in the error message:

```python
if pipeline.has_fatal:
    fatal_parts = []
    for o in pipeline.outcomes:
        if o.status == StartupCheckStatus.FATAL:
            part = o.message
            if o.remediation:
                part += f"\n  Remediation: {o.remediation}"
            fatal_parts.append(part)
    fatal_str = "\n".join(fatal_parts)
    logger.error("FATAL pipeline outcomes: %s", [(o.source, o.status, o.message) for o in pipeline.outcomes])
    raise RuntimeError(f"Startup validation failed:\n{fatal_str}")
```

## Acceptance criteria

- [ ] Error message includes remediation steps for each FATAL outcome
- [ ] Test verifies error message contains remediation text
- [ ] Test verifies formatting matches existing display format
- [ ] No regression in error parsing by external tooling

## Out of scope

- Changes to the validation pipeline itself
- Changes to the remediation content generation
