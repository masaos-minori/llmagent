## Goal

Change FATAL outcome display in startup.py to use `write_fatal()` instead of `write_warning()`, removing the redundant `OutputTag.FATAL` prefix.

## Scope

- Code change: `scripts/agent/startup.py` — use `write_fatal()` for FATAL outcomes

## Assumptions

1. `CLIView.write_fatal()` already exists and prints `[fatal] {msg}` prefix (confirmed at cli_view.py:60-62, 189-191)
2. No behavioral change beyond visual distinction — FATAL still raises RuntimeError via `_display_pipeline_results` only after logging
3. The existing `OutputTag.FATAL` tag will be removed from the message since `write_fatal()` already adds its own `[fatal]` prefix

## Design decisions

- Replace both `write_warning()` calls with `write_fatal()` for consistent visual distinction
- Remove `OutputTag.FATAL` from the message to avoid double-prefixing (`[FATAL] [fatal]`)
- Keep the remediation message under the same `write_fatal()` call for consistency

## Alternatives considered

- Keeping `OutputTag.FATAL` alongside `write_fatal()` (would result in double-prefixing)
- Only changing the main message but keeping `write_warning()` for remediation (inconsistent visual distinction)

## Implementation

### Target file

- `scripts/agent/startup.py`

### Procedure

#### Step 1: Locate the _display_pipeline_results method

1. Open `scripts/agent/startup.py`
2. Find the `_display_pipeline_results()` method (around line 299-309)

#### Step 2: Replace FATAL display code

Change the existing code from:

```python
elif outcome.status == StartupCheckStatus.FATAL:
    self._view.write_warning(f"{OutputTag.FATAL} {outcome.message}")
    if outcome.remediation:
        self._view.write_warning(f"  Remediation: {outcome.remediation}")
```

To:

```python
elif outcome.status == StartupCheckStatus.FATAL:
    self._view.write_fatal(outcome.message)
    if outcome.remediation:
        self._view.write_fatal(f"  Remediation: {outcome.remediation}")
```

#### Step 3: Remove unused import if applicable

If `OutputTag.FATAL` is no longer used elsewhere in the file after this change, consider removing the import. However, check if it's used in other parts of the file first.

## Compatibility considerations

- Visual change in terminal output: FATAL messages will now show `[fatal]` prefix instead of `[FATAL]` prefix
- The `[fatal]` prefix is semantically equivalent and more visually distinct
- Operators expecting `[FATAL]` text pattern in logs will need to adapt

## Security considerations

- N/A — visual change only, no security impact

## Rollback considerations

- Revert the code change if the new prefix causes issues in log parsing or alerting systems

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/agent/startup.py` | Code review | Manual review | write_fatal() called correctly |
| `tests/test_startup.py` | Test verification | `uv run pytest tests/test_startup.py -v` | No test failures |

## Out of scope

- Changing SKIPPED status handling (keep as `write_warning()`)
- Any documentation updates (handled in separate phases)
- Any other startup.py changes not directly related to FATAL display

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: requires/ready/20260722-124328_require.md
- Source plan: plans/20260722-164224_plan.md
- Source implementation procedure: N/A
- Generated at: 20260722-180606
- Related target files: scripts/agent/startup.py
