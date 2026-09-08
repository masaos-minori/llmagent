# Implementation Procedure: Remove duplicate _cmds check from _dispatch_line

## Goal

Remove `_dispatch_line`'s independent `_cmds is None` check so that `_repl_loop` remains the single authoritative precondition, matching the design documented in the class docstring.

## Scope

- **In-Scope**: Remove `_dispatch_line`'s `_cmds is None` check; confirm no bypass caller exists; ensure docstring accuracy after the change
- **Out-of-Scope**: Any other REPL command dispatch behavior change; re-verifying REQ-RIL002B-2 (the immutability-contract docstring itself); changes to `startup.py` or `startup_component_init.py` which also check `_cmds is None` (different class, different lifecycle)

## Assumptions

- `_dispatch_line` is only ever called from within `_repl_loop`'s loop (confirmed by grep: only call site is line 224)
- Removing the `_dispatch_line` check does not break any existing behavior (the check was redundant per the original design)
- The `_repl_loop` check is sufficient because it runs before any user input reaches `_dispatch_line`

## Design decisions

- Keep the `_cmds` check in `_repl_loop` as the single authoritative location (entry point for all user input)
- Remove the duplicate check from `_dispatch_line`
- Preserve existing error messages for backward compatibility
- Do not modify `startup.py` or `startup_component_init.py` — their `_cmds is None` checks are in different classes with different lifecycles

## Alternatives considered

- Keep check in `_dispatch_line`, remove from `_repl_loop` → rejected: `_repl_loop` is the entry point for all user input, more natural location for preconditions
- Use assertion instead of RuntimeError → rejected: RuntimeError provides clearer stack traces in production; assertion would be stripped by `-O` flag

## Implementation

### Target file

`scripts/agent/repl_input_loop.py`

### Procedure

#### Step 1: Verify no bypass caller exists

Search for all references to `_dispatch_line` across the codebase:

```bash
rg -n "_dispatch_line" scripts/ tests/ --type py
```

Expected result: Only one call site found — `_repl_loop` at line 224. If additional callers exist outside `_repl_loop`, report `Blocked: additional caller discovered` — removing the check would be unsafe without confirming those callers also satisfy the precondition.

#### Step 2: Remove duplicate _cmds check from _dispatch_line

Change lines 183-185 from:

```python
        if self._cmds is None:
            self._view.write_fatal("Command registry not initialized")
            return
```

to nothing (remove these three lines entirely).

Rationale: The precondition is already checked in `_repl_loop` at line 202. Since `_dispatch_line` is always called from within `_repl_loop`'s loop (line 224), the check in `_repl_loop` is sufficient. Note that the removed check had a different error message ("Command registry not initialized") than `_repl_loop`'s check ("_repl_loop called before _init_components()"), suggesting it may have been intended as a more specific guard for the slash-command path — but redundancy is still redundancy regardless of intent.

#### Step 3: Verify the class docstring's claim remains accurate

After removal, verify the class docstring's claim at lines 38-41 ("Checked in _repl_loop as the single authoritative precondition") accurately describes the resulting code state — exactly one `_cmds is None` check should remain in the file (`_repl_loop`).

```bash
rg -n "_cmds is None" scripts/agent/repl_input_loop.py
```

Expected result: Exactly one match at line 202 (_repl_loop). If multiple matches remain, report `Needs confirmation` — the docstring claim would be inaccurate.

## Compatibility considerations

- Error message text preserved for backward compatibility with any external consumers
- Runtime behavior unchanged for valid inputs
- Invalid inputs (calling methods before init) now fail at `_repl_loop` level instead of `_dispatch_line` level

## Security considerations

- No security impact: defensive check relocation does not affect authentication, authorization, or data access

## Rollback considerations

- Revert requires restoring the removed check in `_dispatch_line` and removing the added docstring content
- No database schema changes, no config changes

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/agent/repl_input_loop.py | Verify command dispatch after init | `rg -l "ReplInputLoop\|repl_input_loop" tests/` then run found tests | No behavioral regression |

## Completion criteria

- `_dispatch_line` no longer contains an independent `_cmds is None` check
- Exactly one `_cmds is None` check remains in the file (`_repl_loop`)
- The class docstring's "single authoritative precondition" claim is accurate against the resulting code
- No regression in existing REPL command-dispatch tests

## Out of scope

- Changing the `_GRACEFUL_TIMEOUT_S` value or making it configurable
- Modifying StartupOrchestrator internals
- Adding new diagnostic metrics or changing the session diagnostics schema
- Changing the WAL checkpoint strategy (PASSIVE → TRUNCATE fallback)
- Adding new signal types beyond SIGTERM/SIGINT
- Modifying CLIView or other display-layer components
- Changing the command dispatch mechanism (CommandRegistry)

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Verify no bypass caller exists | Completed | — | — | Only call site is _repl_loop at line 224 |
| 2 | Remove duplicate _cmds check from _dispatch_line | Completed | — | — | Single authoritative check remains in _repl_loop; used typing.cast for type narrowing instead of removing entirely (mypy requires it) |
| 3 | Verify the class docstring's claim remains accurate | Completed | — | — | Exactly one _cmds is None check remains at _repl_loop line 199 |
| 4 | Test the feature | Completed | — | — | 16 passed, 2 pre-existing failures (unrelated DB path); key REPL dispatch tests pass |

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
- **Requirement ID**: REQ-RIL002B-1, REQ-RIL002B-2, REQ-RIL002B-4
- **Source issue**: issues/20260907-131805_ril002b_dispatch_line_cmds_check_not_removed.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260907-213856_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260907-213856
- **Related target files**: scripts/agent/repl_input_loop.py
