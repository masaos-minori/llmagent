## Goal

Update the stale prefix-semantics comment above the `approval_shell_safe_prefixes` field in `scripts/agent/config_dataclasses.py`. (REQ-001; AC1)

## Scope

- Change the one-line comment from describing the pre-change prefix semantics ("shell_run command prefixes always auto-approved...") to describe the post-change exact-token-sequence matching semantics.

## Assumptions

- The field declaration and its default values remain unchanged — only the comment text changes.
- The existing comment is at line 328 of `config_dataclasses.py` (confirmed via Read).

## Design decisions

- Keep the comment concise — one sentence describing the new semantics.
- Do not add implementation details (e.g., `shlex.split()`) that would need updating again if the implementation approach changes.

## Alternatives considered

- Removing the comment entirely — not ideal since the field still needs documentation for future readers.
- Adding a multi-line explanation — unnecessary verbosity for a simple semantic clarification.

## Compatibility considerations

- Existing non-disabled servers are unaffected; the added `is_disabled` check only prevents registry publication for disabled servers.
- A disabled server excluded by this change will not appear in the registry's `_tools` dict, which is consistent with treating it as "not configured."

## Security considerations

- Preventing registry publication for disabled servers eliminates the possibility of a disabled server's tools being available for execution even if other gates are bypassed.

## Rollback considerations

- Reverting the `is_disabled` check in `publish_all()` restores the pre-fix behavior where disabled servers get their tools published to the registry.

## Implementation

### Target file

`scripts/agent/config_dataclasses.py`

### Procedure

1. **Phase 1: Comment update**
   - Replace the comment at line 328 from:
     ```
     # shell_run command prefixes always auto-approved despite "high" base level
     ```
   - To:
     ```
     # shell_run commands whose parsed leading tokens exactly match these entries
     # (after shlex.split()) receive RiskLevel.NONE when all path constraints pass
     ```

### Method

- Edit the comment at line 328 using Write/Edit.

### Details

**Step 1 — Comment update:**

```python
# Before (line 328):
# shell_run command prefixes always auto-approved despite "high" base level
approval_shell_safe_prefixes: list[str] = field(
    default_factory=lambda: [
        "ls",
        "cat",
        ...
```

```python
# After:
# shell_run commands whose parsed leading tokens exactly match these entries
# (after shlex.split()) receive RiskLevel.NONE when all path constraints pass
approval_shell_safe_prefixes: list[str] = field(
    default_factory=lambda: [
        "ls",
        "cat",
        ...
```

## Validation plan

- Static analysis: `uv run ruff check scripts/agent/config_dataclasses.py`, `uv run mypy scripts/agent/config_dataclasses.py`.
- Verify the field's type/default remains unchanged: read `tests/agent/test_config_builders.py` (read-only verification).

## Completion criteria

- [ ] Comment accurately describes the post-change semantics.
- [ ] Field's type/default remains unchanged.
- [ ] No new lint/type errors introduced.

## Out of scope

- Modifying `scripts/mcp_servers/shell/` (the shell-mcp server's own `command_allowlist` check is a separate defense layer).
- Any MCP server business logic unrelated to the startup/discovery/registry-publication path.

## execution_status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260917-104212 | 20260917-104212 |  |
| 2 | Add or update tests per Validation plan | Completed | 20260917-104222 | 20260917-104222 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260917-104232 | 20260917-104232 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260917-104243 | 20260917-104243 |  |

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
- **Requirement ID**: REQ-001
- **Source issue**: issues/20260914-103045_mcpagent02_shell-command-parsed-policy-enforcement.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260916-120003_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260916-172149
- **Related target files**: scripts/agent/config_dataclasses.py