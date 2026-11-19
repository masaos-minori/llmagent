# Consolidate MDQ file processing, indexing outcomes, grep correctness, and parser warnings

## Priority
High

## Summary
Introduce a structured per-file processing result for indexing and refresh, correct file-size semantics, fix grep locations and context, and surface non-fatal parser warnings.

## Background
Source: consolidated MDQ MCP backlog (`memo-issue.md`, Issue 3).

Evidence (`Explicit in code`, by `rg`): `indexer.py:80-85` compares the file size in bytes with `service.max_file_chars` and logs a skip. The remaining claims (callers count skipped files as success and update `index_state` after failure, directory counts mixing paths and files, grep context computed but not returned, chunk-relative line numbers, one match per chunk, zero context replaced by defaults, invalid frontmatter silently ignored) are backlog claims and `Needs confirmation`.

## Problem
There is no reliable file-level outcome, so counts and `index_state` can misreport success; limits use ambiguous units; grep locations and context are wrong; metadata loss from invalid frontmatter is invisible.

## Reason for Change
Result accuracy and state integrity; the transaction (`issues/20261119-142127_mdqmcp005_mdq-transaction-atomicity.md`), fingerprint (`issues/20261119-142126_mdqmcp004_mdq-file-identity-stale.md`), and approval (`issues/20261119-142129_mdqmcp007_mdq-approval-dry-run.md`) work depend on these outcomes.

## Implementation Intent
One shared per-file result DTO feeds indexing, refresh, and aggregation; `index_state` advances only after a successful commit; limits have explicit units; grep reports original-file line numbers.

## Target Files or Areas
- `scripts/mcp_servers/mdq/indexer.py`, `index_scan.py`, `parser.py`, `db_grep.py`
- MDQ index, grep, parser, and service-result models
- `tests/mcp_servers/mdq/test_db_grep.py`, `test_parser.py`, `test_mdq_incremental_refresh.py`, `test_mdq_service.py`; new `test_mdq_index_internal_failures.py` (absent)

## Required Changes
- Per-file DTO with statuses `indexed`, `skipped_unchanged`, `skipped_size_limit`, `skipped_no_content`, and failure, stable reason codes, and non-sensitive warning counts; update `index_state` only after commit; separate input-path, discovered, committed, skipped, and failed counts; continue after a file failure; `partial_success` for mixed outcomes and a tool error when all files fail.
- Replace `max_file_chars` pre-read behavior with `max_file_bytes` (plus a decoded-character limit if required); define include and exclude matching on normalized root-relative POSIX paths, symlink-directory behavior, canonical deduplication, re-authorization and re-stat between scan and read, and deterministic exclude rules with documented case sensitivity.
- Grep: return requested context before and after matches; compute line numbers from stored `start_line` with the synthetic heading offset; define multiple matches per chunk and multiline-regex semantics; only `None` selects defaults, zero is honored; apply output limits to the final context-inclusive text.
- Keep the permissive invalid-frontmatter fallback, emit structured `invalid_frontmatter` warnings and counts without absolute paths; consider an optional strict mode.

## Constraints
- Configuration key rename (`max_file_chars` to `max_file_bytes`) is a compatibility change and must be documented.
- Uses the error contract of `issues/20261119-142123_mdqmcp001_mdq-server-boundary.md`.

## Acceptance Criteria
- [ ] A skipped or failed file never advances successful state; directory counts describe files.
- [ ] Byte and character limits are unambiguous.
- [ ] Grep line numbers match source files; requested context, including zero, is honored; multiple-match behavior is documented and tested.
- [ ] Invalid frontmatter remains non-blocking but observable.

## Testing Expectations
- Production SQLite failure, size limit, file disappearance, and no-content cases; mixed-success directories and retry after failure.
- ASCII, Japanese, emoji, and BOM size-limit cases; symlink, duplicate include, nested exclude, and file-replacement scans.
- Grep context, source line, heading, multiple-match, and multiline cases; invalid-frontmatter warnings.
- Run ruff, mypy, and the full test suite.

## Documentation Impact
Yes. File-result statuses and counters; byte versus character limits; scan, symlink, grep, and parser-warning semantics.

## Out of Scope
- Content fingerprints (`issues/20261119-142126_mdqmcp004_mdq-file-identity-stale.md`); transaction atomicity (`issues/20261119-142127_mdqmcp005_mdq-transaction-atomicity.md`).

## Dependencies
- Depends on `issues/20261119-142123_mdqmcp001_mdq-server-boundary.md`. Blocks `issues/20261119-142126_mdqmcp004_mdq-file-identity-stale.md`, `issues/20261119-142127_mdqmcp005_mdq-transaction-atomicity.md`, and `issues/20261119-142129_mdqmcp007_mdq-approval-dry-run.md`. Can run in parallel with `issues/20261119-142124_mdqmcp002_mdq-search-query-boundary.md`.

## Unresolved Questions
- `不明`: the configuration migration for `max_file_chars`.
- `不明`: multiline-regex and multiple-match semantics (owner decision).

## AI Implementation Instruction
Introduce the DTO first and migrate callers with tests. Keep fingerprint and transaction work out of this change. Stop and report if `index_state` semantics cannot be preserved.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261119-142125
- **Related target files**: `scripts/mcp_servers/mdq/indexer.py`, `scripts/mcp_servers/mdq/index_scan.py`, `scripts/mcp_servers/mdq/parser.py`, `scripts/mcp_servers/mdq/db_grep.py`
