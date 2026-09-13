# BgTaskMonitor.consecutive_bg_failures property always defaults to "unknown_bg_task" sentinel

## Priority
Low

## Summary
Fix `BgTaskMonitor.consecutive_bg_failures` property so it can operate on arbitrary task names instead of always defaulting to the `"unknown_bg_task"` sentinel string.

## Background
The property getter/setter pair (`bg_task_monitor.py:65-72`) hardcodes `"unknown_bg_task"` as the task name, making them useless for monitoring specific tasks.

## Problem
No mechanism exists to set the task name for this property. Any code that accesses `monitor.consecutive_bg_failures` will always read/write the counter for the sentinel task name, not the caller's intended task.

## Reason for Change
This property appears designed to provide convenient access to the default task's failure count, but without a way to specify which task, it cannot serve that purpose reliably.

## Implementation Intent
Add a `task_name` parameter to the property setter, or replace the property with a method `get_consecutive_failures(task_name)` / `reset_consecutive_failures(task_name)` that already exist as regular methods. The simplest fix is to remove the property and have callers use the existing methods directly.

## Target Files or Areas
- `/home/sugimoto/llmagent/scripts/agent/bg_task_monitor.py`

## Required Changes
- Remove or deprecate the `consecutive_bg_failures` property getter/setter
- Have callers use `get_consecutive_failures(task_name)` and `reset_consecutive_failures(task_name)` methods instead
- If the property is needed for backward compatibility, add a `task_name` parameter to the setter

## Constraints
- Must preserve backward compatibility for any existing callers using `monitor.consecutive_bg_failures`
- Cannot introduce breaking changes to the public API

## Acceptance Criteria
- Code can monitor failure counts for any named task, not just the sentinel
- Existing callers using the property continue to work (or are migrated with deprecation warning)
- No regression in consecutive failure tracking logic

## Testing Expectations
- Unit test verifying `get_consecutive_failures("specific_task")` returns correct count
- Unit test verifying `reset_consecutive_failures("specific_task")` resets only that task's counter
- Regression test for property access pattern if kept for backward compatibility

## Documentation Impact
Update class docstring to clarify that `consecutive_bg_failures` property is deprecated in favor of the explicit methods.

## Out of Scope
- Adding new failure tracking features
- Changing the BG_FAILURE_THRESHOLD constant

## Dependencies
N/A: none

## Unresolved Questions
- Who added this property and what was their intent?
- Are there existing callers relying on the property accessing the sentinel task name?

## AI Implementation Instruction
First search the codebase for usages of `consecutive_bg_failures` property before removing or modifying it.

## Traceability
- **Workflow phase**: python-code-review + issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260913-160745
- **Related target files**: scripts/agent/bg_task_monitor.py
