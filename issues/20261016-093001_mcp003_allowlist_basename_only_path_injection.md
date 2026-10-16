# HTTP subprocess command allowlist is basename-only and does not confine binaries to a trusted directory

## Priority
Medium

## Summary
The command-validation path for HTTP subprocess MCP servers allows any executable whose basename matches the allowlist, regardless of the directory it lives in, as long as it is reachable via `PATH` and is a regular file. The directory-confinement branch (`/opt/llm/bin`) is additive, not mandatory. Confining allowlisted binaries to a trusted directory removes PATH-injection surface.

## Background
`scripts/agent/http_lifecycle_command_validator.py::CommandValidator.validate` performs: (1) `shutil.which(cmd_name)` PATH lookup, (2) `os.path.realpath` symlink resolution, (3) regular-file check, and (4) allow if `base_name in _allowed_commands` OR the resolved path is inside `/opt/llm/bin` (a regular file, exact parent match, non-writable dir). The docstring states the directory branch "is additive and never weakens the existing basename allowlist." `subprocess.Popen(cfg.cmd, ...)` then launches the command (`scripts/agent/http_lifecycle.py::_create_and_validate_proc`).

## Problem
Verified against the code on 2026-10-16:
- `validate` line 95-97: `in_allowlist = base_name in self._allowed_commands or bool(_INTERPRETER_BASENAME_RE.fullmatch(base_name))`. This is a pure basename match; no directory constraint. A binary named `node`, `python3`, `npx`, `uvx`, etc. anywhere on `PATH` passes.
- The `/opt/llm/bin` branch (`_inside_allowed_binary_dir`) is behind an `or`, so it can only ADD an allowed path; it cannot reject a basename-allowlisted binary in another directory.
- `filter_env` (`http_lifecycle_command_validator.py` lines 143-151) copies `dict(os.environ)` and blocks only `PATH`/`PYTHONPATH`/`LD_LIBRARY_PATH`/`HOME`/`USER` overrides plus the `LD_*` denylist; the inherited `PATH` is otherwise the parent agent's `PATH`. Any directory writable by the attacker that appears in that `PATH` becomes an injection point for a malicious `node`/`python3`/`npx`.
- `shutil.which` resolves through `PATH` before the realpath/allowlist checks, so the allowlist is applied to whatever `PATH` resolves first, not to a pinned location.
- Impact depends on the threat model: if `PATH` is strictly admin-controlled, risk is low; if any untrusted user can write to a `PATH` directory, they can execute an allowlisted-named binary as the agent.

## Reason for Change
A basename-only allowlist is a soft control that silently degrades to "run whatever is first on PATH with an allowed name." Confining to a trusted directory hardens the control without changing the allowlist contents.

## Implementation Intent
Make the directory-confinement branch mandatory (or add an option to require it): after resolving the real path, require it to live under a trusted binary directory in addition to matching the allowlist basename. Preserve backward compatibility only if explicitly enabled. Document the resulting `PATH` requirements.

## Target Files or Areas
- `scripts/agent/http_lifecycle_command_validator.py` (Phase 4 primary)
- `scripts/shared/mcp_config.py` (allowlist/denylist constants)
- `scripts/agent/http_lifecycle.py` (launch path)
- `tests/agent/test_http_lifecycle_command_validator.py`

## Required Changes
- Add a mode that requires the resolved real path to be inside a trusted directory (e.g. `/opt/llm/bin`) in addition to the basename allowlist.
- Keep the current permissive behavior only behind an explicit opt-in flag, and default to the stricter mode.
- Document the required `PATH`/directory model in the validator docstring and config docs.
- Add tests: a basename-allowlisted binary outside the trusted directory is rejected in strict mode; accepted in opted-in permissive mode.

## Constraints
- Do not break existing deployments that rely on allowlisted binaries outside the trusted directory unless the stricter default is adopted intentionally; treat the default as a breaking change requiring config migration.
- Preserve symlink resolution and regular-file checks.
- No change to the env-filtering logic in this issue.

## Acceptance Criteria
- In strict mode, an allowlisted-named binary located outside the trusted directory is rejected with a descriptive failure.
- In opted-in permissive mode, the current behavior is preserved and covered by a test.
- The trusted-directory check rejects a symlink that escapes the directory.

## Testing Expectations
- Unit tests for the strict vs permissive modes using temp directories and symlinks.
- `ruff`, `mypy --no-namespace-packages scripts/`, bandit, full `pytest` with sandbox config.

## Documentation Impact
Document the trusted-directory model and the opt-in flag in the MCP server config docs and the validator docstring.

## Out of Scope
- Changes to which commands are on the allowlist.
- Changes to env filtering or health polling.

## Dependencies
- `N/A: none`

## Unresolved Questions
- Whether production requires allowlisted binaries from directories other than `/opt/llm/bin` (inspect `config/*_mcp_server.toml` and the runtime `PATH`). This decides whether the stricter mode should be the default or remain opt-in.
- Whether `LLMAGENT_BINARY_DIR` override should remain available and how it interacts with the strict default.

## AI Implementation Instruction
Fix only the allowlist directory confinement. Determine default-vs-opt-in from production config inspection first. Do not touch env filtering, launch, or health polling. Add strict/permissive tests. Flag any required config migration in the issue comments.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261016-093001
- **Related target files**: scripts/agent/http_lifecycle_command_validator.py, scripts/shared/mcp_config.py, scripts/agent/http_lifecycle.py
