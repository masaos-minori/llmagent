# Harden MCP subprocess configuration, credentials, executable validation, and server identifiers

## Priority
High

## Summary
Build a typed immutable MCP launch specification that launches the validated executable, allows only safe process options, validates server identifiers, and supplies only server-specific credentials in a minimal environment.

## Background
Source: consolidated CLI REPL and MCP lifecycle backlog (`memo-issue.md`, Issue 7). Related archived work: `issues/done/20261004-065422_mcp002_filter_env-inherits-dangerous-loader-env-vars-from-parent-process-into-mcp-subprocess.md`, `issues/done/20261016-093001_mcp003_allowlist_basename_only_path_injection.md` (re-verify against current source).

Evidence (`Explicit in code`, by reading and `rg`): `scripts/agent/http_lifecycle_subprocess_launcher.py:69` builds the environment with `filter_env(cfg.env)`; lines 100-103 set `start_new_session: True` and then `popen_kwargs.update(cfg.fields)`, so a public `fields` dictionary (`scripts/shared/mcp_config.py:77`) can override it; the validator `http_lifecycle_command_validator.py` documents a permissive mode that accepts a resolved basename on an allowlist (lines 78-81) and returns a resolved absolute path (line 118). Whether the launcher executes the resolved path or the original command, how `filter_env(None)` behaves, and the `MCP_*_AUTH_TOKEN` and `GITHUB_TOKEN` inheritance claims are from the backlog and `Needs confirmation`.

## Problem
Validation may resolve one binary while another is executed (PATH and symlink TOCTOU); security-sensitive `Popen` options can be overridden; permissive basename validation can accept names outside approved directories; server keys are unvalidated yet used in registry keys, status text, and path components; environment filtering may pass global tokens to every server.

## Reason for Change
Process-launch security and credential isolation; MCP process ownership (`issues/20261119-145305_cliplc007_mcp-process-ownership.md`) must build on a safe launch.

## Implementation Intent
Launch the exact validated binary with a fixed process-group configuration and a minimal environment holding only the credentials the server needs; server identifiers cannot influence paths or terminal output.

## Target Files or Areas
- `scripts/shared/mcp_config.py`, `scripts/agent/config_builders.py`
- `scripts/agent/http_lifecycle_command_validator.py`, `http_lifecycle_subprocess_launcher.py`
- Production configuration validation; tests under `tests/agent/` and `tests/shared/`

## Required Changes
- An immutable launch-spec object using the validated absolute executable as `argv[0]`; string-only arguments; remove `fields` or replace it with typed safe options; reject overrides of `shell`, `env`, `stdout`, `stderr`, `start_new_session`, and `preexec_fn`; validate an approved `cwd` if supported; confirm process-group creation.
- Strict trusted-directory confinement in production, permissive mode only in test and development; validate executable and parent-directory ownership and mode; prevent PATH changes from altering the launched binary after validation.
- A constrained server identifier pattern (for example lowercase ASCII, digits, underscore, hyphen) rejecting dots, separators, whitespace, control characters, and excessive length, with case and collision rules and a safe slug or hash for directories.
- Per-server required environment keys; resolve only the current server's `${ENV:...}` references; remove wildcard token inheritance; pass `GITHUB_TOKEN` only to designated servers; always build a minimal environment including for `None`; audit key names only.

## Constraints
- Tokens are secrets: no values in logs, audit, or errors.
- Production strict confinement may reject currently configured binaries (`不明`).

## Acceptance Criteria
- [ ] Validation and execution use the same executable.
- [ ] Security-critical process options cannot be overridden; production rejects binaries outside trusted directories.
- [ ] Server A cannot read server B's credentials; the parent environment is never inherited implicitly.
- [ ] Invalid server keys cannot create paths or corrupt output.

## Testing Expectations
- PATH and symlink change after validation; direct dataclass construction with unsafe options; server-key path traversal and control characters.
- Cross-server credential isolation; minimal-environment startup for every shipped MCP server.
- Run ruff, mypy, and the full test suite.

## Documentation Impact
Yes. Launch-spec contract, trusted-directory policy, identifier rules, and per-server credential model.

## Out of Scope
- Process ownership and restart (`issues/20261119-145305_cliplc007_mcp-process-ownership.md`); health authentication (`issues/20261119-145306_cliplc008_mcp-health-capability.md`).

## Dependencies
- Depends on `issues/20261119-145303_cliplc005_staged-reload-transaction.md` (strict configuration model). Blocks `issues/20261119-145305_cliplc007_mcp-process-ownership.md`, `issues/20261119-145306_cliplc008_mcp-health-capability.md`, and `issues/20261119-145311_cliplc013_api-field-cleanup.md`.

## Unresolved Questions
- `不明`: which server needs which credential environment keys.
- `不明`: whether any shipped server relies on `fields` or on inherited variables today.

## AI Implementation Instruction
Add the unsafe-option and cross-server credential tests first. Do not keep `fields` as an escape hatch. Stop and report any shipped server that cannot start under a minimal environment.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261119-145304
- **Related target files**: `scripts/shared/mcp_config.py`, `scripts/agent/config_builders.py`, `scripts/agent/http_lifecycle_command_validator.py`, `scripts/agent/http_lifecycle_subprocess_launcher.py`
