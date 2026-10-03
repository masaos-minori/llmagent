# CommandValidator allowlist bypasses via `python3` prefix match allows arbitrary command execution

## Priority
Medium

## Summary
`CommandValidator.validate()` accepts any executable whose resolved basename starts with the literal string `python3`, which weakens the command allowlist enough to permit execution of non-interpreter binaries. Tighten the allowlist check so only genuine Python interpreters pass.

## Background
HTTP subprocess MCP servers are launched by `HttpServerLifecycleManager._create_and_validate_proc()` (scripts/agent/http_lifecycle.py), which delegates command validation to `CommandValidator.validate()` in scripts/agent/http_lifecycle_command_validator.py. The intent (per the module docstring) is a four-check allowlist: PATH lookup, symlink resolution, regular-file check, and basename allowlist against `{node, npm, npx, uvx, python, pipx, uvicorn}`.

## Problem
The allowlist check at scripts/agent/http_lifecycle_command_validator.py:82-84 is:
```python
if base_name not in self._allowed_commands and not base_name.startswith("python3"):
    raise HttpStartupError(...)
```
Any basename beginning with `python3` passes without further verification. `shutil.which()` resolves the command through PATH, so an attacker who can place a file named e.g. `python3foo` (or a symlink resolving to one) in a PATH directory makes `validate()` return its absolute path. The subsequent `subprocess.Popen(cfg.cmd, ...)` then executes it as the agent process.

## Reason for Change
The `startswith("python3")` branch was clearly meant to accept versioned interpreters (`python3.11`, `python3.12`), but as written it also matches unrelated executables such as `python3-config`, `python3-distutils`, or a maliciously named binary. This defeats the purpose of the basename allowlist, which is the last control before arbitrary code execution.

## Implementation Intent
Restrict the interpreter exception to real interpreter basenames rather than an open prefix. Match against a bounded set (e.g. exact names plus an optional dotted version suffix like `python3\.?\d+`) instead of a bare `startswith`. Preserve acceptance of legitimate `python3`, `python3.11`, etc. Do not broaden the primary allowlist.

## Target Files or Areas
- scripts/agent/http_lifecycle_command_validator.py
- tests covering CommandValidator (if present)

## Required Changes
- Replace `base_name.startswith("python3")` with a bounded pattern that matches only genuine interpreter basenames (exact `python3` / `python` plus optional `.NN` version suffix).
- Ensure a crafted name like `python3evil` or `python3-config` is rejected by a new unit test.
- Keep the resolved-path basename check; do not change the allowlist's primary command set.

## Constraints
- Must still accept legitimately installed versioned interpreters used by admin config.
- Behavior for the primary allowlist (`node`, `uvx`, etc.) must not change.
- No change to the public signature of `validate()`.

## Acceptance Criteria
- A command resolving to a basename starting with `python3` but not a real interpreter (e.g. `python3evil`) raises `HttpStartupError`.
- Versioned interpreters (`python3`, `python3.11`, `python3.12`) still validate successfully.
- Existing allowlisted commands continue to validate.

## Testing Expectations
- Add/extend unit tests for `CommandValidator.validate()` covering the new rejection and accepted interpreter variants.
- Run ruff + mypy + bandit on the touched file.

## Documentation Impact
None required unless the allowlist policy is documented elsewhere; if so, note that only genuine interpreters are permitted.

## Out of Scope
- Changing the primary command allowlist contents.
- Reworking symlink-resolution or env-filtering logic in this issue.

## Dependencies
N/A: none

## Unresolved Questions
N/A: none

## AI Implementation Instruction
Only modify the allowlist comparison in scripts/agent/http_lifecycle_command_validator.py. Do not touch subprocess launch, env filtering, or the primary allowlist. Add a regression test proving a `python3*` non-interpreter basename is rejected while `python3.NN` is accepted. Keep the change minimal.

## Traceability
- **Workflow phase**: python-code-review → issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261004-065217
- **Related target files**: scripts/agent/http_lifecycle_command_validator.py
