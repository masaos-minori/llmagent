# Fix SignalHandler.ctx type annotation from object to AgentContext

## Summary

SignalHandler.__init__ accepts ctx: object, which prevents type checking of attribute access on self._ctx.conv.shutdown_requested. The # type: ignore[attr-defined] comment admits this is unsafe. At runtime this works because AgentREPL passes an actual AgentContext, but any future caller passing a different type will get a silent AttributeError.

## Background

N/A: covered by Summary

## Problem

SignalHandler has a type annotation mismatch that hides potential runtime errors. The object type allows any value through, masking incorrect callers.

## Reason for Change

Type safety concern: the current pattern relies on duck typing without compile-time guarantees. Future code changes could introduce subtle bugs that pass CI but fail in production.

## Implementation Intent

Change SignalHandler.__init__ parameter from ctx: object to ctx: AgentContext. Remove the # type: ignore[attr-defined] comment. Verify all callers pass AgentContext instances.

## Target Files or Areas

- scripts/agent/signal_handler.py

## Required Changes

- Change SignalHandler.__init__(self, ctx: object, ...) to SignalHandler.__init__(self, ctx: AgentContext, ...)
- Remove # type: ignore[attr-defined] on line 46
- Verify all instantiation sites pass AgentContext

## Constraints

- Must not change public API surface beyond the type annotation fix
- Must preserve existing behavior exactly

## Out of Scope

- Adding new validation logic or error handling
- Changing other type annotations in the file

## Dependencies

N/A: none

## Acceptance Criteria

- [ ] Type checker passes without suppressions on shutdown_requested access
- [ ] All SignalHandler instantiation sites verified to pass AgentContext
- [ ] No regressions in REPL shutdown behavior

## Testing Expectations

- Run type checker (e.g., mypy) against changed file
- Manual verification of REPL shutdown paths

## Documentation Impact

Update docstring for SignalHandler.__init__ to reflect the stricter type requirement.

## Priority

Medium

## AI Implementation Instruction

Change only the type annotation in SignalHandler.__init__. Do not rewrite unrelated files. Preserve public behavior. Stop and report open questions if any instantiation site does not clearly pass AgentContext.
