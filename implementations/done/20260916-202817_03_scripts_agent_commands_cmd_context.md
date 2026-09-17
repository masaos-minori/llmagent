## Goal

Add a mandatory `check_preflight()` call in `_cmd_diff()` before its direct `ToolExecutor.execute("git_diff", ...)` call, denying and reporting (not executing) when policy rejects the tool. (REQ-004; "Add a mandatory `check_preflight(ctx.cfg, "git_diff", args)` call in `_cmd_diff()` (`scripts/agent/commands/cmd_context.py`) before its direct `ToolExecutor.execute()` call, denying and reporting (not executing) when policy rejects the tool.")

## Scope

- Add `check_preflight()` call before the `ctx.services.tools.execute("git_diff", {...})` call in `_cmd_diff()`.
- On `PolicyViolationError`, report a denial message instead of executing.

## Assumptions

- `check_preflight()`'s existing signature (`cfg, tool_name, args`) is sufficient for this call site without modification, since `ctx.cfg` is already in scope.
- `ctx.services.tools` is available at this point in the method (guarded by the existing `if ctx.services is None or ctx.services.tools is None:` check).
- `PolicyViolationError`'s existing message format does not echo tool arguments, so no credential/payload exposure is introduced by surfacing it in the denial output.

## Design decisions

- **Placement**: Insert the `check_preflight()` call immediately after the `ctx.services.tools` availability guard and before the `execute()` call — this ensures the preflight gate runs before any tool execution.
- **Denial handling**: Catch `PolicyViolationError` and write a denial message using the exception's own text, consistent with how `check_approval()` already surfaces denials via `emit_denied(str(preflight_exc))`.
- **Import**: Both `cmd_context.py` and `check_preflight()` reside in the `agent` layer, so no new import-layer exception is introduced.

## Alternatives considered

- **Adding the check in `ToolExecutor.execute()` itself**: Rejected — the `shared` layer must not import from `agent` (import-layer contract); the fix must live at the `agent`-layer call site.
- **Adding a wrapper method on `ToolExecutor`**: Rejected — over-engineering; the existing `check_preflight()` function is sufficient.

## Implementation

### Target file

`scripts/agent/commands/cmd_context.py`

### Procedure

1. Import `PolicyViolationError` from `agent.tool_policy`.
2. In `_cmd_diff()`, after the `ctx.services.tools` availability guard (line 204), add a `try/except` block wrapping the `execute()` call:
   ```python
   try:
       agent.tool_policy.check_preflight(ctx.cfg, "git_diff", {})
   except PolicyViolationError as e:
       self._out.write(f"[DENIED] git_diff: {e}")
       return
   ```
3. Move the existing `execute()` call inside the `try` block.

### Method

Modify the `_cmd_diff()` method body and add an import. No new dependencies.

### Details

**Step 1: Add the import**

After line 32 (`from agent.output_tags import OutputTag`), add:
```python
from agent.tool_policy import PolicyViolationError
```

**Step 2: Wrap the execute() call**

Replace lines 208-215 with:
```python
        try:
            agent.tool_policy.check_preflight(ctx.cfg, "git_diff", {})
        except PolicyViolationError as e:
            self._out.write(f"[DENIED] git_diff: {e}")
            return
        for path in outside_repo:
            self._out.write(f"{path}: not inside a git repository (skipped)")
        for repo_root, repo_paths in by_repo.items():
            result = await ctx.services.tools.execute(
                "git_diff", {"repo_path": repo_root, "commit": ""}
            )
            if result.is_error or result.output.startswith("[DENIED]"):
                self._out.write(f"[{repo_root}] git diff unavailable: {result.output}")
                continue
            self._print_repo_diffs(repo_root, repo_paths, result.output)
```

Key changes:
- Added `check_preflight()` call before the `execute()` call.
- On `PolicyViolationError`, write a denial message and return early.

## Compatibility considerations

- **No signature change**: The method signature remains unchanged; only internal control flow is modified.
- **Denial message format**: Uses `[DENIED]` prefix, consistent with the existing `[DENIED]` prefix used in `result.output.startswith("[DENIED]")` check on line 212.

## Security considerations

This change closes a confirmed security gap: a tool hidden from the LLM could still be executable through the `/diff` slash command if called by name through this bypass path.

## Rollback considerations

If the denial message format causes UX issues, revert to silently skipping (the current behavior) — but this would re-open the security gap. A better rollback would be to log the denial rather than display it to the user.

## Validation plan

- Unit test in `tests/agent/commands/test_agent_cmd_context.py`: confirm `_cmd_diff()` denies (does not execute) `git_diff` when it is absent from `cfg.tool.allowed_tools`.
- Regression: `uv run pytest tests/agent/commands/test_agent_cmd_context.py -v` — confirm all pre-existing transport/error-path tests still pass.
- Static analysis: `uv run mypy scripts/agent/commands/cmd_context.py` — confirm no type regressions.
- Architecture check: `PYTHONPATH=scripts uv run lint-imports` — confirm no new import-layer violations.

## Completion criteria

- `_cmd_diff()` calls `check_preflight()` before executing `git_diff`.
- When `git_diff` is absent from `cfg.tool.allowed_tools`, `_cmd_diff()` reports a denial and returns without executing.
- All pre-existing tests in `tests/agent/commands/test_agent_cmd_context.py` continue to pass.

## Out of scope

- Adding `check_preflight()` to `_execute_mdq()` (covered by a separate document).
- Tests for the MDQ bypass (covered by a separate document).
- Changes to `apply_policy()` (covered by a separate document).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `PolicyViolationError` import | Completed | 20260917-112629 | 20260917-112629 |  |
| 2 | Add `check_preflight()` call before `execute()` in `_cmd_diff()` | Completed | 20260917-112629 | 20260917-112629 |  |
| 3 | Add denial regression test | Completed | 20260917-113006 | 20260917-113006 |  |

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
- **Requirement ID**: REQ-004
- **Source issue**: issues/20260914-103138_mcpagent04_runtime-policy-reload-reversibility.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260916-122227_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260916-202817
- **Related target files**: scripts/agent/commands/cmd_context.py