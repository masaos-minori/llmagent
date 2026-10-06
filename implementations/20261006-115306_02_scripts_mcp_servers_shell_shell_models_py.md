## Goal

Change the `ShellConfig` default for `shell_sandbox_backend` from `"none"` to `"firejail"` in both the dataclass field and the `from_dict` fallback, making the code default consistent with the audit policy. (REQ-003 / AC-3)

## Scope

- Change the dataclass field default from `"none"` to `"firejail"` (line 59)
- Change the `from_dict` null/fallback from `"none"` to `"firejail"` (line 84)

## Assumptions

- Importers (`security_audit_config`, `shell_server`, `shell_service`) pass explicit values — changing the default does not affect them
- `mcp_06_04` already documents the default as `"firejail"`, confirming the intended direction
- No test asserts the old `"none"` default during implementation

## Design decisions

- Lean to `"firejail"` to match `mcp_06_04`'s documented default, rather than fail-fast on an absent key
- This aligns the code default with the audit policy (never `none`)

## Alternatives considered

- Fail-fast on an absent key (require explicit configuration) — rejected because `mcp_06_04` already documents `"firejail"` as the default, and changing to fail-fast would be a behavioral break

## Implementation

### Target file

`scripts/mcp_servers/shell/shell_models.py`

### Procedure

1. Change the dataclass field default from `"none"` to `"firejail"` (line 59)
2. Change the `from_dict` null/fallback from `"none"` to `"firejail"` (line 84)

### Method

- Edit the two string literals directly
- Verify no test asserts the old `"none"` default before merging

### Details

**Before (line 59):**
```python
shell_sandbox_backend: str = "none"
```

**After:**
```python
shell_sandbox_backend: str = "firejail"
```

**Before (line 84):**
```python
shell_sandbox_backend=_or_default(d.get("shell_sandbox_backend"), "none"),
```

**After:**
```python
shell_sandbox_backend=_or_default(d.get("shell_sandbox_backend"), "firejail"),
```

## Compatibility considerations

- Only `shell_models.py` changes; importers (`security_audit_config`, `shell_server`, `shell_service`) pass explicit values
- `none` remains a valid protocol value in `tests/shared/protocols/test_shell_policy.py` — this test stays valid
- Changing the default could affect other code paths that rely on the `"none"` default — verify no test asserts the old default before merging

## Security considerations

- This change makes the code default consistent with the audit policy — no code path defaults to `none` anymore
- The audit's raise-for-`none` remains unchanged (see Reference Files: `security_audit.py`)

## Rollback considerations

- Reverting to `"none"` would restore the contradiction with the audit
- If the default was intentionally `"none"` for backward compatibility, this change would break that — confirm with the team before reverting

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/mcp_servers/shell/shell_models.py` | Unit: default value resolves to `firejail` | `uv run pytest tests/mcp_servers/shell tests/shared/protocols/test_shell_policy.py` | Default is `firejail`; `none` still a valid protocol value |

## Completion criteria

- Dataclass field default is `"firejail"` (line 59)
- `from_dict` fallback is `"firejail"` (line 84)
- No test asserts the old `"none"` default

## Out of scope

- Changes to firejail arguments or the sandbox implementation
- Other security-audit checks (auth_token, allowlists)
- Enforcement behavior when shell-mcp is started outside the agent startup path

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Change `ShellConfig` default to `firejail` | Completed | 20261006-184747 | 20261006-184747 |  |
| 2 | Add or update tests per Validation plan | Completed | 20261006-184747 | 20261006-184747 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261006-184747 | 20261006-184747 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261006-184747 | 20261006-184747 |  |

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
- **Requirement ID**: REQ-003
- **Source issue**: issues/20261005-102246_mcp001_shell-sandbox-none-config-contradicts-startup-audit.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261005-222431_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261006-115306
- **Related target files**: scripts/mcp_servers/shell/shell_models.py