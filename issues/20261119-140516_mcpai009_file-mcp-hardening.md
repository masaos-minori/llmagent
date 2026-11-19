# Consolidate File MCP schema, traversal, deletion, and audit hardening

## Priority
Medium

## Summary
Harden File MCP in one update covering strict schema generation, recursive traversal authorization and limits, delete dry-run authorization, destructive-operation audit behavior, and the unenforced `supported_extensions` setting.

## Background
Source: consolidated review backlog (`memo-issue.md`, Issue 9).

Evidence (`Explicit in code`, by `rg`): in `scripts/mcp_servers/file/delete_service.py`, `delete_directory` returns the dry-run response at line 219-220 before `_check_not_deleting_allowed_root` at line 224; `scripts/mcp_servers/file/read_business.py` traverses with `rglob("*")` (lines 219, 239) and no symlink handling appears in `read_business.py` or `read_static_helpers.py`; `supported_extensions` is parsed in `write_models.py:30` and reported `not_applicable` by posture (`write_security_validation.py:93-96`, "parsed but not enforced"). Audit-failure and schema-generation claims are from the review and `Needs confirmation`.

## Problem
Delete dry-run and real execution can disagree on the allowed-root guard; recursive tree, search, and grep authorize the base path but may expose data outside allowed roots through symlinks and lack node, file, byte, and time limits; runtime audit failure behavior is weaker than the startup posture for destructive operations; and a configured extension control is not enforced.

## Reason for Change
Security-sensitive: file access outside allowed roots and unaudited destructive operations. Configuration must not claim a control the runtime does not enforce.

## Implementation Intent
Fail closed with one schema and one authorization model: share validation between dry-run and real deletion, authorize every discovered candidate or exclude symlinks, bound traversal, audit intent before destruction, and either enforce or remove `supported_extensions` completely.

## Target Files or Areas
- File request models (`read_models.py`, `write_models.py`, `delete_models.py`), `common.py`
- `scripts/mcp_servers/file/read_business.py`, `read_static_helpers.py`, `delete_service.py`, `delete_server.py`
- `read_tools.py`, `write_tools.py`, `delete_tools.py`; `config/file_write_mcp_server.toml`; posture code in `write_security_validation.py`
- Tests under `tests/mcp_servers/file/`

## Required Changes
- Generate read, write, and delete tool schemas from strict Pydantic models, preserving constraints.
- Exclude symlinks by default during recursion or resolve and re-authorize every candidate; block escapes through directory symlinks; handle loops and broken links.
- Add limits for tree nodes, scanned files, cumulative bytes, per-file bytes, and a deadline; return a structured truncation reason.
- Move the allowed-root guard before the dry-run branch and share validation and authorization between dry-run and real deletion.
- Write intent audit before destructive operations (fail closed); report completion-audit failure distinctly when deletion was applied; add session, request, and logical call identifiers to audit records.
- Enforce `supported_extensions` for write, edit, and move destination, or remove it from code, configuration, posture, tests, and documentation.
- Reject empty edit lists and empty `old_text` unless an explicit insertion operation is designed.

## Constraints
- Dry-run and real execution return the same authorization decision.
- Removing `supported_extensions` changes configuration and posture contracts and their tests.

## Acceptance Criteria
- [ ] Runtime and discovery schemas match for all file tools.
- [ ] Recursive operations cannot read or enumerate data outside allowed roots through symlinks; traversal stops at every configured limit.
- [ ] Dry-run and real deletion give the same authorization decision; the allowed root cannot be deleted in any mode.
- [ ] Intent-audit failure prevents deletion; applied deletion plus completion-audit failure is reported accurately.
- [ ] `supported_extensions` is either enforced everywhere required or completely removed.

## Testing Expectations
- External file and directory symlink tests; symlink chain, loop, and broken-link tests.
- Large flat directory, many-small-files, and cumulative-byte-limit tests.
- Allowed-root delete dry-run tests; audit permission, read-only filesystem, and disk-full fault injection.
- Schema and model consistency tests for all file tools.
- Run ruff, mypy, and the full test suite.

## Documentation Impact
Yes. File write and delete design statements (atomic write, size limits, root protection, postconditions) and the extension decision (final sweep in `issues/20261119-140519_mcpai012_mcp-design-docs-update.md`).

## Out of Scope
- GitHub and Git servers; the dedup state machine.

## Dependencies
- Depends on `issues/20261119-140511_mcpai004_logical-idempotency-key-replay.md` (logical-call ids in audit records) and `issues/20261119-140512_mcpai005_structured-execution-context.md` (structured dry-run semantics). Schema and traversal work may start in parallel; deletion audit and dry-run acceptance require both.
- Sibling check: archived `issues/done/20260816-160000_file_delete_models_validation_hardening.md` touched the delete models; re-verify against it.

## Unresolved Questions
- `不明`: enforce or remove `supported_extensions` (owner decision needed).
- `不明`: default symlink policy (exclude versus resolve and re-authorize).
- `不明`: limit values and the insertion-operation design for edits.

## AI Implementation Instruction
Split the work into tested steps in the order schema, traversal, delete, audit, extension. Keep the three file servers' behavior otherwise unchanged. Stop and report the owner decision on `supported_extensions` instead of choosing silently.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261119-140516
- **Related target files**: `scripts/mcp_servers/file/common.py`, `scripts/mcp_servers/file/read_business.py`, `scripts/mcp_servers/file/read_static_helpers.py`, `scripts/mcp_servers/file/delete_service.py`, `scripts/mcp_servers/file/delete_server.py`, `scripts/mcp_servers/file/write_models.py`, `scripts/mcp_servers/file/write_security_validation.py`, `config/file_write_mcp_server.toml`
