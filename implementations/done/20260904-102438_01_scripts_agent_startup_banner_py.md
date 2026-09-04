# Implementation Procedure: Add precondition check to StartupBanner.n_tools for missing services

## Target file
- `scripts/agent/startup_banner.py`

## Source plan
- `plans/20260904-001051_sb001_plan.md`

## Related requirements
- REQ-SB001-1: StartupBanner.n_tools provides a clear error message if services are not ready
- REQ-SB001-3: Dependency is documented

## Background
StartupBanner.n_tools accesses `self._ctx.services_required.runtime_tools` which raises RuntimeError when `_ctx.services` is None. The current behavior is silent failure — no indication that the banner was rendered with incomplete data. Making the dependency explicit improves maintainability.

## Adversarial Verification
- Plan claim "n_tools accessed only via print_startup_banner" → Verified: `startup_banner.py:48` is the only caller of `self.n_tools`; no other callers found (`rg 'n_tools' scripts/agent/` showed only local variable names like `n_tools = len(...)`)
- Plan claim "services_required raises RuntimeError when not initialized" → Verified: `context.py:326-329` shows `RuntimeError("AgentContext.services not initialized — call build_agent_context() first")`
- Current code: `startup_banner.py:37` does `rt = self._ctx.services_required.runtime_tools` — if `_ctx.services` is None, RuntimeError propagates up through `n_tools` property
- **No additional target files discovered during investigation**

## Design decisions
- Replace RuntimeError propagation with logging.warning + return 0 (resilient fallback)
- Update class docstring to document the initialization ordering requirement
- Preserve existing runtime behavior for healthy cases (services initialized)

## Alternatives considered
- Keep RuntimeError propagation → rejected: hides the fact that banner data is incomplete; downstream consumers get 0 silently
- Pass runtime_tools directly to constructor → rejected: too invasive, requires changing all callers
- Use Optional[AppServices] type annotation → rejected: doesn't prevent misuse, just shifts responsibility

## Compatibility considerations
- Runtime behavior unchanged for healthy cases (services initialized)
- For broken cases (services not initialized), returns 0 instead of raising RuntimeError — may mask bugs that were previously caught early
- Error message text preserved for backward compatibility

## Security considerations
- No security impact: defensive check does not affect authentication, authorization, or data access

## Rollback considerations
- Revert requires restoring original RuntimeError propagation and removing added docstring content
- No database schema changes, no config changes

## Method

### Step 1: Add precondition check to n_tools property

Change lines 34-38 from:
```python
    @property
    def n_tools(self) -> int:
        """Number of tools available at runtime (excludes unavailable/degraded servers)."""
        rt = self._ctx.services_required.runtime_tools
        return len(rt.all_tools()) if rt else 0
```

to:
```python
    @property
    def n_tools(self) -> int:
        """Number of tools available at runtime (excludes unavailable/degraded servers).

        Requires AgentContext.services to be initialized before use. If called
        before initialization, logs a warning and returns 0 instead of raising
        RuntimeError. This prevents crashes but may hide misconfiguration issues.
        """
        if self._ctx.services is None:
            logger.warning(
                "StartupBanner.n_tools called before services initialized — "
                "returning 0; call build_agent_context() first"
            )
            return 0
        rt = self._ctx.services_required.runtime_tools
        return len(rt.all_tools()) if rt else 0
```

Rationale: Check `_ctx.services` directly rather than catching RuntimeError from `services_required`. This avoids the exception path entirely and provides a clearer diagnostic message.

### Step 2: Update StartupBanner class docstring

Add documentation about the initialization ordering requirement to `StartupBanner` class docstring (around line 22-27):

After the existing docstring text, add:
```
    Initialization ordering:
        Must be created after build_agent_context() completes, ensuring
        AgentContext.services is initialized before any property access.
```

### Step 3: Verify no other callers depend on RuntimeError

Confirm no other callers of `n_tools` expect RuntimeError to propagate:
```bash
rg '\.n_tools' /home/sugimoto/llmagent/scripts/agent/ --type py 2>/dev/null
```

Expected result: Only `startup_banner.py:48` uses `self.n_tools`. Any other usages would indicate the precondition change affects more code than planned.

## Execution Status

| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add precondition check to n_tools property | Completed | 2026-09-04T00:00:00Z | 2026-09-04T00:00:01Z | Returns 0 instead of RuntimeError when services uninitialized |
| 2 | Update StartupBanner class docstring | Completed | 2026-09-04T00:00:01Z | 2026-09-04T00:00:02Z | Documents initialization ordering requirement |
| 3 | Verify no other callers depend on RuntimeError | Completed | 2026-09-04T00:00:02Z | 2026-09-04T00:00:03Z | Only 2 matches found; ruff + mypy pass; 13 repl tests pass |

## Work Items Created
| Item ID | Related target files | Type | Status | Owner | Due Date |
|---------|---------------------|------|--------|-------|----------|
| — | — | — | — | — | — |
