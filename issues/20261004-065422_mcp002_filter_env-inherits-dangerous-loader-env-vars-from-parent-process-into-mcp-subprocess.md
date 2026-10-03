# filter_env inherits dangerous loader env vars from the parent process into MCP subprocesses

## Priority
Medium

## Summary
`CommandValidator.filter_env()` copies the entire parent environment into every HTTP subprocess MCP server via `dict(os.environ)`. Protected keys only block *config-provided* overrides; inherited values such as `LD_PRELOAD`, `LD_LIBRARY_PATH`, and `PYTHONPATH` from the agent process still propagate to the subprocess, which runs arbitrary admin-launched node/python code. Sanitize inherited loader/interpreter variables.

## Background
Subprocesses for HTTP MCP servers are launched in `HttpServerLifecycleManager._create_and_validate_proc()` (scripts/agent/http_lifecycle.py:273) using `env = self._command_validator.filter_env(cfg.env)`. `filter_env()` is defined in scripts/agent/http_lifecycle_command_validator.py:98-113. Separately, scripts/shared/mcp_config.py:26 defines `_ENV_KEY_DENYLIST = ("LD_PRELOAD", "LD_LIBRARY_PATH", "PYTHONPATH")`, which rejects those keys when *building* config, but that denylist is only consulted for config-supplied env entries, not inherited ones.

## Problem
`filter_env()` implements:
```python
result = dict(os.environ)
for key, value in env.items():
    if key in self._protected_env_vars:
        logger.warning(...)
    else:
        result[key] = value
return result
```
Lines scripts/agent/http_lifecycle_command_validator.py:107-112. The `result` seed is the full parent environment. Protection is applied only to keys present in the incoming `env` dict. Therefore:
- If the agent process itself has `LD_PRELOAD`/`LD_LIBRARY_PATH`/`PYTHONPATH` set (via its own startup, container, or a prior injection), those values are passed unchanged to the subprocess.
- The subprocess executes arbitrary configured commands (node/python/etc.), so an inherited `LD_PRELOAD` enables shared-library hijacking of that process.

The config-build denylist gives a false sense of coverage because it never sees inherited variables.

## Reason for Change
The defense-in-depth denylist at the config layer does not cover the runtime env-passing path. Since these subprocesses are arbitrary-code-execution sinks, uncontrolled inheritance of ELF/preload and Python-path variables materially widens the attack surface.

## Implementation Intent
Make `filter_env()` drop dangerous loader/interpreter variables from the inherited environment, not just block config overrides. Reuse the same denylist semantics as `_ENV_KEY_DENYLIST` in scripts/shared/mcp_config.py so both layers agree. Preserve the existing protected-var logging for config overrides. Keep returning None for a None input and preserving benign inherited vars (PATH, HOME, etc.).

## Target Files or Areas
- scripts/agent/http_lifecycle_command_validator.py (`filter_env`)
- scripts/shared/mcp_config.py (reference for the canonical denylist)
- Tests for `filter_env`

## Required Changes
- After seeding `result = dict(os.environ)`, remove any key matching the loader/interpreter denylist (`LD_PRELOAD`, `LD_LIBRARY_PATH`, `PYTHONPATH`) before applying config overrides.
- Centralize the denylist so the config layer and runtime share one definition (avoid drift).
- Add a regression test asserting inherited dangerous keys are stripped even when absent from `cfg.env`.

## Constraints
- Must not strip benign vars needed by the subprocess (PATH, PYTHONHOME is out of scope — see Out of Scope).
- Backward compatibility: callers relying on inherited values for the denied keys should be treated as unsupported.
- Do not change `validate()` or the subprocess launch path.

## Acceptance Criteria
- With `os.environ` containing `LD_PRELOAD`/`LD_LIBRARY_PATH`/`PYTHONPATH` and `cfg.env=None`, `filter_env()` returns a dict without those keys.
- Benign inherited vars remain present.
- Config-provided non-protected vars still merge in.

## Testing Expectations
- Unit tests for `filter_env()` covering inherited-denylist stripping and preserved benign vars.
- ruff + mypy + bandit on the touched file.

## Documentation Impact
Document that loader/interpreter env vars are intentionally stripped at runtime; note the relationship to `_ENV_KEY_DENYLIST`.

## Out of Scope
- Adding other env vars (e.g. `TZ`, `PYTHONHASHSEED`) to the denylist — evaluate separately.
- Changing how `cfg.env` overrides interact with allowed inherited vars beyond the denylisted set.

## Dependencies
N/A: none

## Unresolved Questions
- Should `PYTHONHOME`/`PYTHONSTARTUP` be added to the denylist, or handled at a higher layer?

## AI Implementation Instruction
Modify only `filter_env()` in scripts/agent/http_lifecycle_command_validator.py to strip inherited loader/interpreter env vars, sharing the denylist with scripts/shared/mcp_config.py. Do not alter subprocess launch, `validate()`, or protected-var handling semantics. Add regression tests.

## Traceability
- **Workflow phase**: python-code-review → issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261004-065422
- **Related target files**: scripts/agent/http_lifecycle_command_validator.py, scripts/shared/mcp_config.py
