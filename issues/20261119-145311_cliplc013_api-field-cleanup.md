# Remove or implement unused and misleading configuration and lifecycle APIs

## Priority
Low

## Summary
Remove dead parameters and duplicate helpers, or connect public fields to real runtime behavior, after the configuration and lifecycle contracts stabilize.

## Background
Source: consolidated CLI REPL and MCP lifecycle backlog (`memo-issue.md`, Issue 13). `McpServerConfig.fields` exists (`scripts/shared/mcp_config.py:77`, `Explicit in code`); the unused health timeout helpers, stderr rotation settings not reaching the manager, unused lifecycle constructor arguments, duplicate classification helpers, and stale docstrings are backlog claims and `Needs confirmation`.

## Problem
Public fields and parameters imply capabilities that do not exist or are duplicated, increasing ambiguity and test burden.

## Reason for Change
Cleanup only; it follows stabilization of the configuration and lifecycle APIs. Not time-sensitive.

## Implementation Intent
Every public field and parameter has one documented effect; duplicate helpers are removed; signatures and docstrings match the final runtime model.

## Target Files or Areas
- `scripts/shared/mcp_config.py`, `scripts/agent/http_lifecycle*.py`, reload classification helpers, `scripts/shared/runtime_tool_registry.py`, `scripts/agent/session_persister.py`

## Required Changes
- Remove or fully implement `McpServerConfig.fields`; use `health_timeout` consistently or remove obsolete helpers; wire stderr rotation settings to the logging manager; remove unused lifecycle and terminator parameters; consolidate duplicate reload classification helpers; correct stale docstrings; separate storage and display constants where appropriate.

## Constraints
- No behavior change beyond removing dead surface; final choices follow the earlier issues of this backlog.

## Acceptance Criteria
- [ ] Static analysis finds no known unused public parameters.
- [ ] Every public configuration field changes documented runtime behavior.
- [ ] Signatures, docstrings, and tests agree.

## Testing Expectations
- vulture, ruff, mypy, and the full test suite; docs checks for changed docstrings.

## Documentation Impact
Yes. Corrected docstrings and field descriptions.

## Out of Scope
- New features and the behavior changes of the earlier issues.

## Dependencies
- Depends on `issues/20261119-145303_cliplc005_staged-reload-transaction.md`, `issues/20261119-145304_cliplc006_mcp-launch-spec-credentials.md`, `issues/20261119-145305_cliplc007_mcp-process-ownership.md`, `issues/20261119-145306_cliplc008_mcp-health-capability.md`, and `issues/20261119-145307_cliplc009_redaction-stderr-diagnostics.md`.

## Unresolved Questions
- `不明`: which of the listed unused items still exist after the earlier issues land.

## AI Implementation Instruction
Re-derive the list of unused surface by static analysis at implementation time. Remove only what is confirmed unused. Stop and report any field that still has an external consumer.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261119-145311
- **Related target files**: `scripts/shared/mcp_config.py`, `scripts/shared/runtime_tool_registry.py`, `scripts/agent/session_persister.py`
