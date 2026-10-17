# Implementation Procedure — `scripts/mcp_servers/shell/shell_service.py`

## Goal

Add audit before/after state and approval correlation to the shell server's audit record
where missing (`REQ-004`).

## Scope

Modify only `scripts/mcp_servers/shell/shell_service.py`. Extend `_write_audit_log` and
its call site to include before/after state and approval correlation.

## Assumptions

- `_write_audit_log` exists at line 170 and is called at line 287; writing errors are
  logged, never propagated.
- Shell command execution is a server-checked gate, so approval correlation applies.

## Design decisions

- Extend the existing append-only record with before/after fields (command identity,
  working directory, environment scope, and post-execution result indicator) rather than
  rewriting the format.
- Reuse the same logged-never-raised contract as the file servers for consistency.

## Alternatives considered

- Emitting audit from `subprocess_runner.py` (a Reference File): rejected — that file is
  read-only here; the audit record belongs in the service that owns the operation context
  and before/after state.

## Implementation

### Target file

`scripts/mcp_servers/shell/shell_service.py`

### Procedure

1. Inspect `_write_audit_log` (170–194) and its caller (287) to learn the current record
   shape and available context (argv, cwd, env, result).
2. Extend the record to include before/after state (pre/post execution indicators, working
   directory) and an approval-correlation field.
3. Preserve the never-raise contract.

### Method

- Read lines 170–196 and the call site around 256–290.
- Modify the record string; do not change the subprocess execution path.

### Details

- Before/after: command identity + whether execution completed; avoid capturing full
  stdout/stderr (may contain sensitive data).
- Align field names with `docs/22_mcp/mcp_02_03_audit-logging-and-errors.md` (separate row).

## Compatibility considerations

Trailing fields added to the audit line; leading prefix preserved. Confirm no consumer
requires exact-line equality.

## Security considerations

Do not log command arguments that carry secrets, nor process output. Audit failure stays
non-fatal.

## Rollback considerations

Revert the commit to `shell_service.py`.

## Validation plan

- Assert the shell audit record contains before/after + correlation fields.
- Regression: legitimate shell calls still succeed.
- Command: `uv run pytest tests/mcp_servers/shell/ -q`.

## Completion criteria

Shell audit records carry before/after state and approval correlation; legitimate-call
semantics unchanged.

## Out of scope

`subprocess_runner.py`, other servers, the audit schema doc.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Extend the shell audit record | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: tool doc is a separate row |

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
- **Requirement ID**: `REQ-004` (audit before/after + correlation)
- **Source issue**: `issues/20261017-115004_mcp006_implement-missing-guard-layers-for-high-risk-tool-categories.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261017-133731_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261017-155408
- **Related target files**: `scripts/mcp_servers/shell/shell_service.py`
