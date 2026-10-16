# filter_env inherits the full parent environment and logs raw env values, exposing secrets

## Priority
Medium

## Summary
`CommandValidator.filter_env` builds the subprocess environment by copying the entire parent `os.environ` and removing only a small denylist/protected set, then logs the raw value of any blocked protected env var. Both behaviors can expose secrets to the MCP subprocess and to the log file. Restrict the inherited environment to an explicit allowlist and never log raw values.

## Background
`filter_env` (`scripts/agent/http_lifecycle_command_validator.py` lines 134-152) is called from `_create_and_validate_proc` (`scripts/agent/http_lifecycle.py` line 275) to prepare the environment for `subprocess.Popen`. It starts from `result = dict(os.environ)`, deletes keys matching `_ENV_KEY_DENYLIST` (`LD_PRELOAD`, `LD_LIBRARY_PATH`, `PYTHONPATH`), then merges the server's configured `env`, logging a warning for each blocked protected-var override.

## Problem
Verified against the code on 2026-10-16:
- Line 143: `result = dict(os.environ)` copies every variable in the parent environment (e.g. cloud credentials, API tokens, session cookies, `AWS_*`, `GITHUB_TOKEN`) into the child. Only `LD_PRELOAD`, `LD_LIBRARY_PATH`, `PYTHONPATH`, `PATH`, `PYTHONPATH`, `HOME`, `USER` are stripped. There is no positive allowlist of what the subprocess may receive.
- Lines 148-150: `logger.warning("Blocked protected env var override: %s=%s", key, value)` writes the full secret value of the blocked override to the log. If an admin places a secret in a protected var (or an attacker injects one), it is persisted in plaintext in the agent log.
- Impact: MCP subprocesses are semi-trusted admin-configured processes; passing the parent's full environment and logging protected-var values widens the secret exposure surface beyond the intended denylist.

## Reason for Change
The default-allow approach (inherit everything except a short denylist) leaks broadly and logs secrets. A default-deny allowlist plus no-secret-in-logs is materially safer.

## Implementation Intent
- Replace the copy-`os.environ`-then-strip model with an explicit allowlist of safe variables (e.g. `PATH`, `TEMP`, `TMP`, `SYSTEMROOT`, locale vars) plus the server's configured `env`. Remove anything not on the allowlist.
- Never log raw env values; log only the key name when blocking an override.
- Keep the existing denylist and protected-var semantics as an additional filter layer.

## Target Files or Areas
- `scripts/agent/http_lifecycle_command_validator.py` (Phase 4 primary)
- `scripts/shared/mcp_config.py` (`_ENV_KEY_DENYLIST`)
- `tests/agent/test_http_lifecycle_command_validator.py`

## Required Changes
- Introduce an explicit allowlist of inherited environment variables; drop all others from the copied parent environment.
- Change the protected-var override warning to log only the key name, never the value.
- Preserve blocking of `LD_PRELOAD`, `LD_LIBRARY_PATH`, `PYTHONPATH`, and protected-var overrides.
- Add tests: a parent var not on the allowlist (e.g. `GITHUB_TOKEN`) is not passed to the child; a blocked protected var logs the key but not the value.

## Constraints
- The launched binary still needs a usable `PATH` (and possibly `TEMP`/`TMP`) to run; include the minimum required for subprocess execution.
- Preserve `filter_env(None)` returning `None`.
- Changing the inherited environment may affect servers that currently rely on inheriting variables; treat as a behavior change requiring config verification.

## Acceptance Criteria
- Secrets present only in the parent environment (not on the allowlist, not in the server's `env`) are not passed to the subprocess.
- Blocking a protected-var override logs the key without its value.
- A subprocess still receives the variables it needs to start.

## Testing Expectations
- Unit tests for the allowlist behavior and the redacted warning using a parent env containing a fake secret.
- `ruff`, `mypy --no-namespace-packages scripts/`, bandit, full `pytest` with sandbox config.

## Documentation Impact
Document the default-deny environment model and the allowed-variable list in the MCP server config docs and the validator docstring.

## Out of Scope
- Changes to command validation, subprocess launch, health polling, or process termination.
- Changes to the `_ENV_KEY_DENYLIST` contents (handled together with the allowlist decision).

## Dependencies
- `N/A: none`

## Unresolved Questions
- Which exact variables launched MCP subprocesses require at runtime (verify against running configs) to avoid breaking startup when switching to default-deny.
- Whether the allowlist should be per-server configurable or a fixed global set.

## AI Implementation Instruction
Fix only `filter_env`: adopt default-deny allowlist inheritance and redact env values in logs. Do not touch command validation, launch, or termination. Determine the minimal required variable set from production config before finalizing the allowlist. Add tests. No compatibility shims without flagging.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261016-093044
- **Related target files**: scripts/agent/http_lifecycle_command_validator.py, scripts/shared/mcp_config.py
