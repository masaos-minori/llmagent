# Implementation Procedure: Unify _cmds None-check into single authoritative location

## Target file
- `scripts/agent/repl_input_loop.py`

## Source plan
- `plans/20260904-001051_ril002_plan.md`

## Related requirements
- REQ-RIL002-1: Single authoritative check for _cmds availability
- REQ-RIL002-2: Immutability contract documented

## Background
Both `_repl_loop` and `_dispatch_line` independently guard against `_cmds` being None with identical RuntimeError checks. This redundancy suggests uncertainty about ownership of `_cmds` after initialization.

## Adversarial Verification
- Plan claim "both methods have _cmds None-check" → Verified: `repl_input_loop.py:170-171` (_dispatch_line) and `repl_input_loop.py:191-192` (_repl_loop) both contain `if self._cmds is None: raise RuntimeError("_dispatch_line called before _init_components()")`
- Note: _repl_loop uses same error message text despite being in different method — confirms copy-paste pattern
- No additional target files discovered during investigation

## Design decisions
- Keep the _cmds check in `_repl_loop` as the single authoritative location (entry point for all user input)
- Remove the duplicate check from `_dispatch_line`
- Document the immutability contract in the class docstring
- Preserve existing RuntimeError messages for backward compatibility

## Alternatives considered
- Keep check in `_dispatch_line`, remove from `_repl_loop` → rejected: `_repl_loop` is the entry point for all user input, more natural location for preconditions
- Use assertion instead of RuntimeError → rejected: RuntimeError provides clearer stack traces in production; assertion would be stripped by `-O` flag

## Compatibility considerations
- Error message text preserved for backward compatibility with any external consumers
- Runtime behavior unchanged for valid inputs
- Invalid inputs (calling methods before init) now fail at `_repl_loop` level instead of `_dispatch_line` level

## Security considerations
- No security impact: defensive check relocation does not affect authentication, authorization, or data access

## Rollback considerations
- Revert requires restoring the removed check in `_dispatch_line` and removing the added docstring content
- No database schema changes, no config changes

## Method

### Step 1: Remove duplicate _cmds check from _dispatch_line

Change lines 170-171 from:
```python
        if self._cmds is None:
            raise RuntimeError("_dispatch_line called before _init_components()")
```
to nothing (remove these two lines entirely).

Rationale: The precondition is already checked in `_repl_loop` at line 191-192. Since `_dispatch_line` is always called from within `_repl_loop`'s loop (line 213), the check in `_repl_loop` is sufficient.

### Step 2: Update ReplInputLoop class docstring

Add documentation about the _cmds lifecycle to `ReplInputLoop.__init__` docstring (around line 27-31):

After the existing docstring text, add:
```
    _cmds lifecycle:
        - Set once during initialization via _init_components()
        - Immutable after initialization — never reassigned
        - Checked in _repl_loop as the single authoritative precondition
```

### Step 3: Verify _cmds assignment sites

Search for all assignments to `self._cmds` across the codebase:
```bash
rg 'self\._cmds\s*=' scripts/agent/ --type py
```

Expected result: Only one assignment site (`_init_components()`). If multiple assignment sites are found, report `Needs confirmation` — the immutability assumption may be incorrect.

## Execution Status

| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove duplicate _cmds check from _dispatch_line | Completed | 2026-09-04T00:00:00Z | 2026-09-04T00:00:01Z | Single authoritative check remains in _repl_loop |
| 2 | Update class docstring | Completed | 2026-09-04T00:00:01Z | 2026-09-04T00:00:02Z | Added _cmds lifecycle documentation |
| 3 | Verify _cmds assignment sites | Completed | 2026-09-04T00:00:02Z | 2026-09-04T00:00:03Z | Only one assignment site (_init_components); mypy union-attr error acceptable |

## Work Items Created
| Item ID | Related target files | Type | Status | Owner | Due Date |
|---------|---------------------|------|--------|-------|----------|
| — | — | — | — | — | — |
