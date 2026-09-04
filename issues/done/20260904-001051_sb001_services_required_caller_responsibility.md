# Clarify StartupBanner.n_tools services_required caller responsibility

## Summary

StartupBanner.n_tools accesses self._ctx.services_required.runtime_tools. If AgentContext.services is None (not yet initialized), services_required raises RuntimeError. During startup, if print_startup_banner() is called before build_agent_context() completes, this will crash the banner display.

## Background

The banner callback is invoked after component initialization in AgentREPL.run(). The current call order is safe, but the dependency is implicit.

## Problem

Fragile design: changing the call order breaks silently. Future modifications could introduce the same crash pattern elsewhere.

## Reason for Change

Maintainability concern: implicit dependencies between components make the codebase harder to reason about and modify safely.

## Implementation Intent

Make the dependency explicit. Options: (1) Add a precondition check in n_tools property that logs a clear error message instead of raising RuntimeError, (2) Pass the runtime tools directly to the banner callback instead of accessing via ctx, (3) Add a @property or method that documents the initialization requirement. Choose the approach that least changes existing behavior while making the dependency visible.

## Target Files or Areas

- scripts/agent/startup_banner.py
- scripts/agent/context.py

## Required Changes

- Make the services_required dependency explicit in StartupBanner.n_tools
- Either add a precondition check or restructure the data flow
- Document the initialization ordering requirement

## Constraints

- Must not change the banner output format
- Must not break existing callers

## Out of Scope

- Adding new configuration options
- Changing the banner display logic

## Dependencies

N/A: none

## Acceptance Criteria

- [ ] StartupBanner.n_tools provides a clear error message if services are not ready
- [ ] No regression in banner display during normal startup
- [ ] Dependency is documented

## Testing Expectations

- Manual verification of banner display during startup
- Type checker pass (if precondition check is added)

## Documentation Impact

Document the initialization ordering requirement in both StartupBanner and AgentContext.

## Priority

Low

## AI Implementation Instruction

Clarify the dependency only. Do not change banner output or add new features. Preserve existing behavior during normal startup. Stop and report if the current call order is unclear.
