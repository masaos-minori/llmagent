## Goal
- Make `tools/check_docs_structure.py` fail when any supplied glob matches zero files (`REQ-001`: refuse unmatched patterns), while leaving every other behavior unchanged (`REQ-002`, `REQ-003`).

## Scope
- Modify only `main()` in `tools/check_docs_structure.py`: the glob-resolution loop and the exit path.
- No check function, `MAX_SIZE`, or `SIZE_EXCEPTIONS` entry changes.

## Assumptions
- The new tests (`seq` 02 row of this Plan) are written first per Plan Phase 1 and are expected to fail until this change lands; `code-implementation` MAY execute row 02 before row 01.
- `main()` at the time of writing resolves globs at `tools/check_docs_structure.py` (`for pattern in patterns:` loop) and ends with the `total_issues` / `All checks passed` block (read 2026-10-24).
- Sibling Plan overlaps: none name this Plan (`tools/check_plan_target_overlaps.py`, 2026-10-24).

## Design decisions
- Fail on any unmatched pattern, partial or total (Plan Design; owner-revisable, UNK-01).
- Keep the unmatched report additive: per-file findings print first, then the unmatched message.

## Alternatives considered
- Warn instead of fail on a partial match: rejected, a typo in one of several globs would still hide a skipped check.
- Normalize `docs/`-relative patterns automatically: rejected (Plan Out-of-Scope, silent rewrite of a pattern).

## Implementation
### Target file
`tools/check_docs_structure.py`

### Procedure
1. In the glob loop, collect each pattern's matches in a local set; append the pattern to an `unmatched: list[str]` when the set is empty; then `files.update` the matches.
2. After the ADR-ID check and before the final return block, if `unmatched` is non-empty print `no files matched the given glob(s): {patterns}` (comma-separated) to stderr.
3. Return 1 when `total_issues` or `unmatched` is non-empty; print `All checks passed` and return 0 only when both are empty.

### Method
- Keep the `{total_issues} issue(s) found` stderr line for the findings case unchanged.
- The early `return 1` on a duplicate basename stays before the glob report (existing behavior).

### Details
- Message text is exactly `no files matched the given glob(s): {patterns}`, patterns joined with `, `.
- The implicit `docs/**/*.md` default is untouched (`patterns = args.globs or [...]`).

## Compatibility considerations
- Runs whose patterns all match keep exit codes and output; CI passes `docs/**/*.md` (172 files, Plan evidence), so it is unaffected.
- `tools/run_validation_gates.py` carries a placeholder `[glob ...]` command and never auto-invokes this gate (Plan Reference Files).

## Security considerations
N/A: local CLI exit-path change; no input parsing, secrets, or trust boundary involved.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/tools/test_check_docs_structure.py -q` passes, new cases included.
- `uv run python tools/check_docs_structure.py "23_agent/agent_13_*.md"` exits non-zero naming the pattern; `uv run python tools/check_docs_structure.py "docs/**/*.md"` still exits 0.
- `uv run ruff format tools/check_docs_structure.py`, `uv run ruff check tools/check_docs_structure.py`, `uv run mypy tools/check_docs_structure.py`, `uv run bandit tools/check_docs_structure.py`.

## Completion criteria
- A zero-match or partially matching glob set exits 1 with the unmatched message on stderr.
- A fully matching run is byte-identical in output and exit code to HEAD.

## Out of Scope
- CI workflow invocations, `MAX_SIZE`, `SIZE_EXCEPTIONS`, new checks, pattern normalization.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the unmatched-glob tracking and exit path in `main()` | Pending | — | — | |
| 2 | Confirm the row 02 tests now pass | Pending | — | — | |
| 3 | Run ruff, mypy, bandit on the file and the AC-1/AC-2 invocations | Pending | — | — | |

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
- **Requirement ID**: `REQ-001` (refuse unmatched globs), `REQ-002` (additive report), `REQ-003` (unchanged non-empty runs)
- **Source issue**: `issues/20261024-124138_docs010_check_docs_structure-glob-matching-no-files-passes-silently.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261024-214856_check_docs_structure-glob-matching-no-files-passes-silently.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261024-234854
- **Related target files**: `tools/check_docs_structure.py`
