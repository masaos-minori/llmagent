## Goal

Add `"uv"` to `HttpServerLifecycleManager._ALLOWED_COMMANDS` in `scripts/agent/http_lifecycle.py` so the manager injects an allowlist that accepts `uv` subprocesses (REQ-002, REQ-004).

## Scope

- **In-Scope**: `scripts/agent/http_lifecycle.py` — add `"uv"` to the `_ALLOWED_COMMANDS` frozenset literal, preserving the `frozenset[str]` annotation and the other seven entries.
- **Out-of-Scope**: `_DEFAULT_ALLOWED_COMMANDS` in `scripts/agent/http_lifecycle_command_validator.py` (handled by its own procedure document); `CommandValidator.validate()` logic; any command other than `uv`; config-driven allowlists; the protected env vars list.

## Assumptions

- `uv` is installed on the host and resolvable via PATH (`shutil.which("uv")` returns a path), so Check 1 of `validate()` passes once the allowlist admits it.
- The resolved `uv` basename is exactly `uv` (not a symlink whose basename differs), so Check 4 matches the added entry.

## Design decisions

- Data-only change: add one string to the existing frozenset literal. Keep the `frozenset[str]` annotation and the surrounding literal untouched apart from the added entry.
- This is the manager-injected copy of the allowlist. Both copies must stay consistent because the manager always passes its value over the validator's default; the validator's default is updated by its own document.

## Alternatives considered

- Removing `_ALLOWED_COMMANDS` and letting the manager use the validator's default — rejected: constructor/caller change, outside this document's scope.
- Adding `uv` via configuration — rejected: the plan adds a hardcoded allowlist entry (REQ-001, REQ-002), not a config change.
- Adding more than `uv` — rejected: REQ-003 admits only `uv`.

## Implementation

### Target file

`scripts/agent/http_lifecycle.py`

### Procedure

1. **Add `"uv"` to `_ALLOWED_COMMANDS`.** Insert `"uv"` into the frozenset literal at lines 67-69, alongside the existing seven entries, without touching the `frozenset[str]` annotation or the closing paren.

### Method

- Read lines 67-69 to confirm the current literal is `{"node", "npm", "npx", "uvx", "python", "pipx", "uvicorn"}` and that `uv` is absent.
- Edit line 68 to add `"uv"` to the set.
- Confirm the annotation on line 67 is unchanged.

### Details

Current:
```python
_ALLOWED_COMMANDS: frozenset[str] = frozenset(
    {"node", "npm", "npx", "uvx", "python", "pipx", "uvicorn"}
)
```
After:
```python
_ALLOWED_COMMANDS: frozenset[str] = frozenset(
    {"node", "npm", "npx", "uvx", "python", "pipx", "uvicorn", "uv"}
)
```
The literal is injected at construction via `CommandValidator(allowed_commands=type(self)._ALLOWED_COMMANDS)`; no constructor or caller change is needed.

## Compatibility considerations

- Callers: `HttpServerLifecycleManager.__init__` builds `CommandValidator(allowed_commands=type(self)._ALLOWED_COMMANDS)` (line 81-83). No import, constructor, or caller signature changes.
- `tests/agent/test_lifecycle.py::TestStartHttpSubprocess._patch_allowed_commands` derives its patched set from the original (`original | {"uvicorn"}`), so it is independent of whether `uv` is present and will not regress.

## Security considerations

- Widening the allowlist by one entry marginally increases the command set an MCP subprocess may invoke. The four-check pipeline (PATH resolve → realpath → regular-file → basename allowlist) still gates every command, and no other command is admitted (REQ-003).

## Rollback considerations

- Remove the `"uv"` entry added to line 68 to restore the pre-change allowlist. The change is a single literal addition with no other side effects.

## Validation plan

| Target | Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `_ALLOWED_COMMANDS` | Unit — injected allowlist now contains `uv` | `uv run pytest tests/agent/test_lifecycle.py` | Pass, no new failures |
| Changed file | Static analysis | `uv run ruff check scripts/agent/http_lifecycle.py` | Clean |

## Completion criteria

- `_ALLOWED_COMMANDS` contains `"uv"`.
- The `frozenset[str]` annotation and the other seven entries are unchanged.
- No command other than `uv` was added (REQ-003).

## Out of scope

- `_DEFAULT_ALLOWED_COMMANDS` in `scripts/agent/http_lifecycle_command_validator.py` (its own procedure document).
- `CommandValidator.validate()` logic, other commands, config-driven allowlists, protected env vars.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | REQ-002, REQ-004 |
| 2 | Add or update tests per Validation plan | N/A | — | — | doc-only change, no test edit required |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | ruff + pytest |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — | |

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
- **Requirement ID**: `REQ-002` — the manager injects an allowlist that accepts `uv` subprocesses; `REQ-004` — the `frozenset[str]` annotation is preserved
- **Source issue**: `issues/20261005-181500_add_uv_to_allowed_commands.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261006-093924_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261006-151948
- **Related target files**: `scripts/agent/http_lifecycle.py`
