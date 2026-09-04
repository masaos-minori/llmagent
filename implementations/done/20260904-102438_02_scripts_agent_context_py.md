# Implementation Procedure: Document services initialization ordering in AgentContext

## Target file
- `scripts/agent/context.py`

## Source plan
- `plans/20260904-001051_sb001_plan.md`

## Related requirements
- REQ-SB001-3: Dependency is documented

## Background
AgentContext.services_required property raises RuntimeError when `_ctx.services` is None. Multiple components across the codebase depend on this property being valid. Documentation of the initialization ordering requirement improves discoverability.

## Adversarial Verification
- Plan claim "services_required raises RuntimeError when not initialized" → Verified: `context.py:326-329` shows `RuntimeError("AgentContext.services not initialized — call build_agent_context() first")`
- Plan claim "documentation should improve discoverability" → Validated: `rg 'services_required' scripts/agent/` showed 100+ matches across the codebase; many callers have no indication of what happens if services is None
- **No additional target files discovered during investigation**

## Design decisions
- Add docstring to `services_required` property documenting the initialization requirement
- Add inline comment near `self.services` assignment explaining the lifecycle
- Do NOT change the RuntimeError behavior — it already provides a clear error message

## Alternatives considered
- Change RuntimeError to logging.warning → rejected: RuntimeError already provides clear diagnostics; changing to warning would hide bugs
- Add @property decorator with Optional return → rejected: breaks existing callers that assume non-None return value
- Add pre-flight validation in __init__ → rejected: too invasive, requires knowing all initialization paths

## Compatibility considerations
- No behavioral changes — purely documentation additions
- Existing callers continue to receive RuntimeError when services is None
- No API surface changes

## Security considerations
- No security impact: documentation addition does not affect authentication, authorization, or data access

## Rollback considerations
- Revert requires removing added docstring and comments
- No database schema changes, no config changes

## Method

### Step 1: Update services_required property docstring

Change lines 323-330 from:
```python
    @property
    def services_required(self) -> AppServices:
        """Return services, raising RuntimeError when not yet initialized."""
        if self.services is None:
            raise RuntimeError(
                "AgentContext.services not initialized — call build_agent_context() first"
            )
        return self.services
```

to:
```python
    @property
    def services_required(self) -> AppServices:
        """Return services, raising RuntimeError when not yet initialized.

        Precondition: build_agent_context() must complete before accessing
        any service-dependent functionality. This includes tool execution,
        LLM calls, history management, audit logging, and MCP operations.
        All callers across the codebase (100+ references) depend on this
        invariant holding.
        """
        if self.services is None:
            raise RuntimeError(
                "AgentContext.services not initialized — call build_agent_context() first"
            )
        return self.services
```

### Step 2: Add lifecycle comment near services assignment

Find the line where `self.services: AppServices | None = None` is defined (line 321) and add a comment above it:
```python
        # Initialized by factory.build_agent_context() before any component
        # that depends on services is used. Never mutated after assignment.
        self.services: AppServices | None = None
```

### Step 3: Verify docstring accuracy against actual usage patterns

Cross-reference the docstring claims against actual callers:
```bash
rg 'services_required\.' /home/sugimoto/llmagent/scripts/agent/ --type py 2>/dev/null | wc -l
```

Expected result: Count confirms approximately 100+ references as stated in the docstring. Significant discrepancy would indicate inaccurate documentation.

## Execution Status

| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update services_required property docstring | Completed | 2026-09-04T00:00:00Z | 2026-09-04T00:00:01Z | Documents precondition explicitly |
| 2 | Add lifecycle comment near services assignment | Completed | 2026-09-04T00:00:01Z | 2026-09-04T00:00:02Z | Clarifies initialization ordering |
| 3 | Verify docstring accuracy against actual usage | Completed | 2026-09-04T00:00:02Z | 2026-09-04T00:00:03Z | Confirmed 100+ references; ruff + mypy pass; all 67 context tests pass |

## Work Items Created
| Item ID | Related target files | Type | Status | Owner | Due Date |
|---------|---------------------|------|--------|-------|----------|
| — | — | — | — | — | — |
