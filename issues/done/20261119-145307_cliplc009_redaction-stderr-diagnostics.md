# Standardize redaction, stderr logging, retention, and public diagnostics

## Priority
Medium

## Summary
Apply one public-error and diagnostic redaction model across CLI output, lifecycle errors, WAL, configuration, session persistence, MCP health, stderr logs, process snapshots, and Memory display.

## Background
Source: consolidated CLI REPL and MCP lifecycle backlog (`memo-issue.md`, Issue 9). Related archived work: `issues/done/20261118-025717_agentfd001_stderr-log-fd-leak.md`.

Evidence (`Explicit in code`, by `rg`): `scripts/agent/http_lifecycle_stderr_log_manager.py:92-110` rotates by `os.rename(log_file_path, rotated_path)` and creates a new file. The remaining claims (raw exceptions, absolute paths, and URLs in errors, `/config` and `/mcp status` showing internal paths and commands, health logging full URLs, server keys as directory names, unclear retention and permissions, internal log paths in process snapshots, Memory content disclosure) are from the backlog and `Needs confirmation`.

## Problem
Sensitive operational details can reach normal CLI output and logs through several independent paths, and stderr rotation by rename can break an active writer and its tail reader.

## Reason for Change
Information-disclosure risk, to be fixed once with the final state and error models of the shutdown, configuration, and lifecycle work.

## Implementation Intent
Normal CLI output is safe for terminal capture and screen sharing; raw details stay in secret-masked internal logs; stderr files use safe paths, restrictive permissions, configured rotation and retention, and rotation compatible with the active writer.

## Target Files or Areas
- A common redaction helper; `scripts/agent/http_lifecycle_errors.py`, `http_lifecycle_health_checker.py`, `http_lifecycle_stderr_log_manager.py`, `http_lifecycle.py`
- `scripts/agent/wal_checkpoint_manager.py`, `session_persister.py`; config and MCP display commands; Memory display commands
- Tests under `tests/agent/`

## Required Changes
- Stable public error codes and safe summaries; strip URL userinfo, query, and fragment; replace paths with basenames, root-relative ids, or logical identifiers; no raw config values, SQLite errors, command paths, or token-derived details; redact before truncating; separate normal and verbose diagnostics; define PID, PGID, log path, and full Memory content display policy; use public process snapshots without internal paths.
- Stderr: safe slug or hash directories; align documented and actual log location; apply configured size and generation limits; mode `0o600`; purge expired generations; rotation compatible with the active writer or only on restart; consistent writer and tail-reader paths; mask stderr before CLI display; define disk-retention and secret-handling policy.

## Constraints
- Redaction applies before truncation and covers internal logs through the common secret masker.
- Verbose diagnostics need an explicit opt-in.

## Acceptance Criteria
- [ ] No credential, absolute path, raw SQLite error, or credential-bearing URL appears in normal CLI output.
- [ ] Internal logs pass the common secret masker.
- [ ] Stderr rotation preserves active writes and tail access; retention and permissions are enforced.
- [ ] Public process snapshots omit internal log paths.

## Testing Expectations
- Error messages containing tokens, paths, URLs, and SQLite details; `/config`, `/mcp status`, Memory, and shutdown output; active subprocess log rotation with a real subprocess; retention and file-mode tests.
- Run ruff, mypy, and the full test suite.

## Documentation Impact
Yes. Public diagnostic policy, stderr location, retention, and verbose-mode rules.

## Out of Scope
- Process ownership and health semantics (`issues/20261119-145305_cliplc007_mcp-process-ownership.md`, `issues/20261119-145306_cliplc008_mcp-health-capability.md`).

## Dependencies
- Depends on `issues/20261119-145302_cliplc004_bounded-shutdown-machine.md`, `issues/20261119-145303_cliplc005_staged-reload-transaction.md`, `issues/20261119-145304_cliplc006_mcp-launch-spec-credentials.md`, `issues/20261119-145305_cliplc007_mcp-process-ownership.md`, and `issues/20261119-145306_cliplc008_mcp-health-capability.md`.

## Unresolved Questions
- `不明`: the production call site of `rotate_log()`, the log retention cleanup implementation, and the deployment log directory configuration.
- `不明`: PID, PGID, and log path display policy.

## AI Implementation Instruction
Locate the production caller of `rotate_log()` first. Add redaction-leak tests before editing. Do not log new sensitive data while debugging. Stop and report if the redaction helper changes other components' output.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261119-145307
- **Related target files**: `scripts/agent/http_lifecycle_errors.py`, `scripts/agent/http_lifecycle_health_checker.py`, `scripts/agent/http_lifecycle_stderr_log_manager.py`, `scripts/agent/http_lifecycle.py`, `scripts/agent/wal_checkpoint_manager.py`, `scripts/agent/session_persister.py`
