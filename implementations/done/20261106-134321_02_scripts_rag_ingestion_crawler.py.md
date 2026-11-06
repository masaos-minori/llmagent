## Goal

Add a one-shot pre-BFS startup validation that raises a clear `RuntimeError` naming
`rag_db_path` when an HTTP target exists but the path is unconfigured, invoked once at
the top of `WebCrawler.crawl()` (`REQ-001`, `REQ-004`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Verification (20261106): stale detection passed. `crawl()` calls
  `_ensure_rag_db_for_http(targets)` at line 110; the guard (lines 122-139) raises the
  exact `RuntimeError` message documented in Details; `file://` exemption present.
  Existing tests: `test_crawl_raises_on_empty_rag_db_for_http` (REQ-001),
  `test_crawl_empty_path_ok_for_file_targets_only` (REQ-004) in
  `TestConditionalHeadersMisconfiguration`. No code or test changes needed.
- The change described here is **already present in the current source**
  (`scripts/rag/ingestion/crawler.py`): `_ensure_rag_db_for_http(targets)` is called at
  the top of `crawl()` (line 110) and raises `RuntimeError` for HTTP targets with an
  empty `rag_db_path`, exempting `file://` targets. Committed in
  `03a307158`. `code-implementation` is a verification pass.
- `crawl()` is the real startup entry point; `__init__` must NOT raise (many unit tests
  construct the crawler with a blank path, `REQ-004`).

## Design decisions
- Place the guard in a dedicated method `_ensure_rag_db_for_http` invoked at the BFS
  boundary (`crawl()`), not in `__init__`, to keep the constructor contract stable.
- Scope the check to HTTP(S) targets only; `file://` targets never touch the
  conditional-header cache and stay exempt.

## Alternatives considered
- Raising in `__init__` for true fail-fast — rejected: breaks many existing tests that
  construct the crawler with a blank path (`REQ-004`).
- Validating inside `main()` instead of `crawl()` — rejected: `crawl()` is the tested
  entry and the guard belongs at the BFS boundary.

## Implementation
### Target file
`scripts/rag/ingestion/crawler.py`

### Procedure
Ensure `crawl()` calls `self._ensure_rag_db_for_http(targets)` before the target loop,
and that `_ensure_rag_db_for_http` raises a single `RuntimeError` naming `rag_db_path`
when any HTTP(S) target is present and `self._rag_db_path` is empty.

### Method
Edit `WebCrawler.crawl()` / `_ensure_rag_db_for_http` (lines 108-139):
- At the top of `crawl()`, call `self._ensure_rag_db_for_http(targets)`.
- `_ensure_rag_db_for_http` collects target URLs, checks `any(url.startswith(("http://",
  "https://")))`, and if so raises `RuntimeError` when `not self._rag_db_path`.

### Details
- The error message names the config key and action: "rag_db_path is not configured in
  crawler.toml; set rag_db_path before crawling HTTP URLs".
- `file://` targets are filtered out before the HTTP check, so file crawls are unaffected.

## Compatibility considerations
Backward compatible: the guard only fires when an HTTP target exists AND `rag_db_path`
is unconfigured — the exact broken case. Valid configurations are unaffected.

## Security considerations
N/A.

## Rollback considerations
N/A: revert the commit that introduced this procedure.

## Validation plan
- Static: `uv run ruff format` / `uv run ruff check` on
  `scripts/rag/ingestion/crawler.py`; `uv run mypy --no-namespace-packages scripts/`.
- Behavioral: `uv run pytest tests/rag/ingestion/ -v` — an HTTP target with a blank
  `rag_db_path` raises the startup `RuntimeError` before BFS; file crawls and valid
  configs pass (`REQ-001`, `REQ-004`).

## Completion criteria
- Starting a crawl with an HTTP target and empty `rag_db_path` emits exactly one clear
  startup error naming the misconfiguration before BFS.
- `__init__` still accepts a blank path; valid configurations crawl normally.

## Out of Scope
Changing where `rag_db_path` is read from config, or the SQLite schema.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add pre-BFS startup validation for empty `rag_db_path` (`scripts/rag/ingestion/crawler.py`) | Completed | — | 20261106 | Code already present in HEAD 03a307158; verify against tests Verification pass: source and tests already match (03a307158); no edits needed |
| 2 | Add or update tests per Validation plan | Completed | — | 20261106 | Startup-error test in `test_crawler_integration.py` Verification pass: source and tests already match (03a307158); no edits needed |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261106 | Verification pass: source and tests already match (03a307158); no edits needed |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20261106 | N/A N/A |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | N/A: no blocker | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-001`, `REQ-004`
- **Source issue**: `issues/20261106-073205_crawl003_rag-db-path-misconfiguration-handling.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261106-094153_crawl003_rag-db-path-misconfiguration-handling.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261106-134321
- **Related target files**: `scripts/rag/ingestion/crawler.py`