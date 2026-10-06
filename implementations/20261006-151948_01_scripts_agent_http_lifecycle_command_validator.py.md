## Goal

Add `"uv"` to `_DEFAULT_ALLOWED_COMMANDS` in `scripts/agent/http_lifecycle_command_validator.py` so the default `CommandValidator` accepts `uv` subprocesses (REQ-001, REQ-004).

## Scope

- **In-Scope**: `scripts/agent/http_lifecycle_command_validator.py` — add `"uv"` to the `_DEFAULT_ALLOWED_COMMANDS` frozenset literal, preserving the `frozenset[str]` annotation and the other seven entries.
- **Out-of-Scope**: `_ALLOWED_COMMANDS` in `scripts/agent/http_lifecycle.py` (handled by its own procedure document); `CommandValidator.validate()` logic; any command other than `uv`; config-driven allowlists; the protected env vars list.

## Assumptions

- `uv` is installed on the host and resolvable via PATH (`shutil.which("uv")` returns a path), so Check 1 of `validate()` passes once the allowlist admits it.
- The resolved `uv` basename is exactly `uv` (not a symlink whose basename differs), so Check 4 matches the added entry.

## Design decisions

- Data-only change: add one string to the existing frozenset literal. Keep the `frozenset[str]` annotation and the surrounding literal untouched apart from the added entry.
- Both allowlists feed the same single allowlist check in `validate()` (Check 4). The manager always injects its own copy over the validator's default, so the manager-side list is updated by its own document; here only the default is changed.

## Alternatives considered

- Making the manager fall back to the validator's default (single source of truth) — rejected: interface/constructor change, outside this document's scope.
- Adding `uv` via configuration — rejected: the plan adds a hardcoded allowlist entry (REQ-001, REQ-002), not a config change.
- Adding more than `uv` — rejected: REQ-003 admits only `uv`.

## Implementation

### Target file

`scripts/agent/http_lifecycle_command_validator.py`

### Procedure

1. **Add `"uv"` to `_DEFAULT_ALLOWED_COMMANDS`.** Insert `"uv"` into the frozenset literal at lines 24-26, alongside the existing seven entries, without touching the `frozenset[str]` annotation or the closing paren.

### Method

- Read lines 24-26 to confirm the current literal is `{"node", "npm", "npx", "uvx", "python", "pipx", "uvicorn"}` and that `uv` is absent.
- Edit line 25 to add `"uv"` to the set.
- Confirm the annotation on line 24 is unchanged.

### Details

Current:
```python
_DEFAULT_ALLOWED_COMMANDS: frozenset[str] = frozenset(
    {"node", "npm", "npx", "uvx", "python", "pipx", "uvicorn"}
)
```
After:
```python
_DEFAULT_ALLOWED_COMMANDS: frozenset[str] = frozenset(
    {"node", "npm", "npx", "uvx", "python", "pipx", "uvicorn", "uv"}
)
```
Note: `uvx` is already admitted but the `uv` runner itself was not; only `uv` is added (REQ-003).

## Compatibility considerations

- Callers: `HttpServerLifecycleManager` injects `CommandValidator(allowed_commands=...)`; when no explicit list is passed the validator falls back to `_DEFAULT_ALLOWED_COMMANDS`. No module import, constructor, or caller signature changes.
- Existing validator tests pass an explicit `allowed_commands`, so they are independent of this default and will not regress.

## Security considerations

- Widening the allowlist by one entry marginally increases the command set an MCP subprocess may invoke. The four-check pipeline (PATH resolve → realpath → regular-file → basename allowlist) still gates every command, and no other command is admitted (REQ-003).

## Rollback considerations

- Remove the `"uv"` entry added to line 25 to restore the pre-change allowlist. The change is a single literal addition with no other side effects.

## Validation plan

| Target | Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `_DEFAULT_ALLOWED_COMMANDS` | Unit — default now contains `uv` | `uv run pytest tests/agent/test_http_lifecycle_command_validator.py` | Pass, no new failures |
| Changed file | Static analysis | `uv run ruff check scripts/agent/http_lifecycle_command_validator.py` | Clean |

## Completion criteria

- `_DEFAULT_ALLOWED_COMMANDS` contains `"uv"`.
- The `frozenset[str]` annotation and the other seven entries are unchanged.
- No command other than `uv` was added (REQ-003).

## Out of scope

- `_ALLOWED_COMMANDS` in `scripts/agent/http_lifecycle.py` (its own procedure document).
- `CommandValidator.validate()` logic, other commands, config-driven allowlists, protected env vars.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261006-223323 | 20261006-223323 | REQ-001, REQ-004 |
| 2 | Add or update tests per Validation plan | N/A | — | — | doc-only change, no test edit required |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261006-223323 | 20261006-223323 | ruff + pytest |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — |  |

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
- **Requirement ID**: `REQ-001` — the default validator accepts `uv` subprocesses; `REQ-004` — the `frozenset[str]` annotation is preserved
- **Source issue**: `issues/20261005-181500_add_uv_to_allowed_commands.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261006-093924_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261006-151948
- **Related target files**: `scripts/agent/http_lifecycle_command_validator.py`