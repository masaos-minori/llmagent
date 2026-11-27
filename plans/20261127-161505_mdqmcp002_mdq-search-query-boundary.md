# Move MDQ search authorization, filtering, error classification, and cancellation into one query boundary

## Goal
- Make MDQ search answer every question — authorization, counting, limiting, path and tag filtering, error classification, and cancellation — from one query boundary before any response text is built, so an unauthorized row can never affect a visible count or suppress an authorized result, and a timed-out query releases its connection and worker inside a bounded interval.

## Priority
High

## Scope
- **In-Scope**:
  - Canonicalizing and authorizing `path_prefix` and `heading_prefix` before query construction, and matching them by exact prefix comparison instead of `LIKE`.
  - Exact tag matching through `json_each()` instead of substring matching on `tags_json`.
  - Applying the authorized-source constraint in SQL before `COUNT`, ranking, and `LIMIT`, so `matched_count` is an authorized count.
  - Classifying SQLite failures by cause: malformed FTS syntax, interruption, busy or locked, missing table, corruption, and a genuine completed zero-result query.
  - A dedicated cancellable connection per search, progress-handler cancellation, a stop event on async timeout, a bounded wait for the worker before the connection is released, and a bounded active-search concurrency limit.
  - Non-sensitive timeout and cancellation metrics, and no raw query text or raw SQLite detail in persistent logs or responses.
  - Documentation of the resulting query-boundary contract.
- **Out-of-Scope**:
  - The server error contract, audit emission, and audit redaction, owned by `plans/20261127-160114_mdqmcp001_mdq-server-boundary.md` (this Plan consumes its codes and its hashed-identifier contract).
  - FTS5 schema identity and readiness, owned by `issues/20261119-142128_mdqmcp006_mdq-fts5-schema-identity.md`.
  - File-processing outcome semantics, owned by `plans/` for the file-processing-outcomes issue.
  - Any change to `scripts/db/helper.py`; the shared helper is consumed as it stands.
  - Indexing write paths and the write gate.
- **Dependencies**:
  - Depends on `plans/20261127-160114_mdqmcp001_mdq-server-boundary.md` — phase all — the closed domain error-code vocabulary and the single audit-emission boundary this Plan's classification and metrics must match are defined there.
  - Can run in parallel with the file-processing-outcomes plan once that error contract exists.
  - The MDQ server contract is documented in the MCP domain docs named by `docs/00_index.md` "Document References by Task".
  - **Depends on**: issues/20261119-142123_mdqmcp001_mdq-server-boundary.md — phase all — error codes, transport policy, and the audit redaction contract.

## Background
Source: consolidated MDQ MCP backlog (`memo-issue.md`, Issue 2), filed as `issues/20261119-142124_mdqmcp002_mdq-search-query-boundary.md`.

The issue marked two points as backlog claims needing confirmation: whether authorization is applied in SQL or in Python after `LIMIT`, and what the generic `OperationalError` branch returns. Both are now confirmed against current source, so the Problem section below states them as facts rather than claims.

The shared cancellation helper named by the issue was also checked: `scripts/db/helper.py` `SQLiteHelper.interrupt_when()` installs the connection progress handler and can be reused as it stands, because `SQLiteHelper` accepts a caller-supplied `db_path` and applies only `busy_timeout` on a read-only open. No change to the shared helper is planned, so the issue's stop-and-report condition does not trigger.

## Problem
Verified against current source:

- `_build_search_where()` in `scripts/mcp_servers/mdq/search.py` builds path, heading-path, and tag predicates with `LIKE ?` and binds `f"{req.path_prefix}%"`, `f"{req.heading_prefix}%"`, `f"%{tag}%"`. A `path_prefix` containing `%` or `_` broadens the filter beyond the intended prefix, and a `path_prefix` outside `allowed_dirs` is accepted as a filter value — authorization is not applied to it before query construction.
- Authorization is applied in Python after `LIMIT`: `COUNT(*)` runs with no authorized-source predicate and no `LIMIT`, then `authorize_path()` filters the already-limited row set. An unauthorized row can therefore inflate the reported count and occupy a `LIMIT` slot, hiding an authorized result.
- Tag filtering is substring-based on `tags_json`, so a tag that is a substring of another tag matches.
- The generic `sqlite3.OperationalError` branch returns `results = []` and `matched_count = 0`, so malformed FTS syntax, an interruption, and a busy or locked database are all reported as a successful zero-result query. Only the "no such table" and "corrupt" substrings are classified.
- `asyncio.wait_for(asyncio.to_thread(...))` stops the caller but not the SQLite statement: the worker keeps running on a connection that is closed while the statement is still executing, and the connection is not dedicated to the search.
- Raw query text reaches persistent output through `logger.info("MDQ search query: %s", req.query)`, and raw query text reaches the response through `f"No results found for: {req.query!r}"`, the result header, and the timeout message.
- `SearchDocsMetadata.query_preview` carries the first 80 characters of the raw query.

## Reason for Change
Authorization and information-disclosure risk plus a resource leak on timeouts. The query boundary is also the place where the error codes defined by the server-boundary plan are first applied to a tool path, so the classification must be settled before the later indexing and schema work reuse it.

## Implementation Intent
One query boundary owns every decision about a search: the canonicalized, authorized source predicate is part of the SQL before `COUNT`, ranking, and `LIMIT`; filters use exact prefix and exact tag semantics; every SQLite failure is classified by cause against the closed domain code vocabulary; and each search runs on its own cancellable connection with a stop event, a bounded drain, and a bounded concurrency limit. Response text, metadata, and persistent logs carry only the hashed query identifier defined by the server-boundary plan's audit contract, never raw query text or raw SQLite detail. `scripts/db/helper.py` is used as it stands.

## Requirements
- `REQ-001`: Canonicalize and authorize `path_prefix` and `heading_prefix` before query construction; match them by exact prefix comparison rather than `LIKE`, so wildcard characters cannot broaden scope; match tags against exact JSON values with `json_each()`.
- `REQ-002`: Apply the authorized-source constraint in SQL before `COUNT`, ranking, and `LIMIT`; `matched_count` is an authorized count; an unauthorized row cannot occupy a result slot or change a visible count.
- `REQ-003`: Classify SQLite failures by cause — malformed FTS syntax is a validation error, an interruption is a timeout, busy or locked is a retryable consistency error, missing table, corruption, or schema mismatch is a non-retryable consistency error; success is reported only for a completed zero-result query; no raw SQLite detail or raw query text in a response.
- `REQ-004`: One dedicated cancellable connection per search; progress-handler cancellation; a stop event set on async timeout with a bounded wait for the worker before the connection is released; an interrupted connection is never reused; a bounded active-search concurrency limit; non-sensitive timeout and cancellation metrics.
- `REQ-005`: Persistent logs and response text carry the hashed query identifier from the server-boundary plan's audit contract, not raw query text.
- `REQ-006`: Document the query-boundary contract: authorized count, exact path and tag filter semantics, the cause-to-code classification, and cancellation behavior.

## Implementation Target Files
**Freeze status**: Frozen — `issue-to-plan` Step 8's Implementation Target Files
Validation passed for every row on 20261127; see `rules/workflow-lifecycle.md`
Implementation Target Files Validation (Plan Freeze).

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/mcp_servers/mdq/search.py` | Modify | Build the query from one boundary: canonicalized authorized source predicate before `COUNT`, ranking, and `LIMIT`; exact prefix comparison instead of `LIKE`; exact tag match with `json_each()`; cause-based error classification; dedicated cancellable connection with stop event and bounded drain; bounded active-search concurrency; hashed query identifier in logs and response text | REQ-001, REQ-002, REQ-003, REQ-004, REQ-005, AC-1, AC-2, AC-3, AC-4 | `_build_search_where()` binds `f"{req.path_prefix}%"` and `f"%{tag}%"` with `LIKE ?`; `COUNT(*)` runs without an authorized-source predicate; `authorize_path()` runs after `LIMIT`; the generic `sqlite3.OperationalError` branch sets `results = []`; `asyncio.wait_for(asyncio.to_thread(...))` with `timeout=service.search_timeout_sec`; `logger.info("MDQ search query: %s", req.query)` | `tests/mcp_servers/mdq/test_search.py`, `tests/mcp_servers/mdq/test_mdq_search_counts.py`, `tests/mcp_servers/mdq/test_mdq_search_cancellation.py` | Verified |
| `scripts/mcp_servers/mdq/auth.py` | Modify | Expose the canonicalized roots used by the SQL source predicate, so authorization stays in one place and the query boundary does not re-implement it | REQ-001, REQ-002, AC-1, AC-2 | `authorize_path()` resolves the path and each root before `_is_within_root()`; nothing exposes the canonicalized root set to a SQL predicate | `tests/mcp_servers/mdq/test_mdq_path_jail.py`, `tests/mcp_servers/mdq/test_auth.py` | Verified |
| `scripts/mcp_servers/mdq/mdq_models.py` | Modify | `SearchDocsMetadata.query_preview` carries the hashed query identifier instead of the first 80 raw characters; the request model keeps `path_prefix`, `heading_prefix`, and `tag_filter` as the filter contract | REQ-005, AC-3 | `query_preview: str` is populated from `req.query[:80]` in `search.py` | `tests/mcp_servers/test_mdq_audit.py` | Verified |
| `tests/mcp_servers/mdq/test_search.py` | Modify | Replace the swallowed-`OperationalError` characterization with cause-based classification; add wildcard and exact-tag tests; add the no-raw-query-text assertion on the log line | REQ-001, REQ-003, REQ-005, AC-2, AC-3 | `test_non_corruption_operational_error_returns_empty_results_without_raising` asserts that a malformed FTS query is swallowed as an empty result, which is the behavior being replaced | itself | Verified |
| `tests/mcp_servers/mdq/test_mdq_search_counts.py` | Modify | Assert `matched_count` is the authorized count and that an unauthorized row cannot change a visible count | REQ-002, AC-1 | `test_matched_count_is_exact_regardless_of_limit` runs with every row inside the authorized root, so it cannot currently show count leakage | itself | Verified |
| `tests/mcp_servers/mdq/test_mdq_search_limits.py` | Modify | Assert the `LIMIT` slots are filled only by authorized rows, so an unauthorized row cannot suppress an authorized result | REQ-002, AC-1 | `test_explicit_limit_above_cap_is_bounded_at_sql_layer` pins the SQL-layer cap but not the authorization order | itself | Verified |
| `tests/mcp_servers/mdq/test_mdq_search_modes.py` | Modify | Keep the mode and cap characterization passing under the new boundary and add the genuine zero-result case | REQ-003, AC-3 | `test_unsupported_mode_rejected` and `test_request_override_above_cap_is_bounded` pin the request contract that must stay unchanged | itself | Verified |
| `tests/mcp_servers/mdq/test_mdq_read_authorization.py` | Modify | Add the mixed-root cases: unauthorized rows ranked above authorized rows, and the shrink-allowlist behavior measured through the query boundary | REQ-002, AC-1 | `test_narrowed_allowed_dirs_hides_indexed_content` and `test_deny_all_returns_no_matches_not_unfiltered_scan` cover the Python post-`LIMIT` filter, not the SQL predicate | itself | Verified |
| `tests/mcp_servers/mdq/test_mdq_path_jail.py` | Modify | Add the canonicalized-prefix cases for the SQL source predicate, including a symlinked root and a prefix outside `allowed_dirs` | REQ-001, AC-2 | `test_symlink_escape_denied` tests `authorize_path()` directly; no test covers a `path_prefix` that is outside `allowed_dirs` or that contains wildcard characters | itself | Verified |
| `tests/mcp_servers/mdq/test_mdq_search_cancellation.py` | Create | New file: dedicated connection per search, stop event on timeout, bounded drain, no reuse of an interrupted connection, bounded concurrency, and the repeated-timeout resource-leak test | REQ-004, AC-4 | Does not exist; `tests/mcp_servers/mdq/` holds 35 test files and none covers cancellation or worker leakage (checked in Step 3) | itself | Verified |
| `docs/22_mcp/mcp_04_04_mdq.md` | Modify | Document the query-boundary contract: `matched_count` as the authorized count, exact path and tag filter semantics, the cause-to-code classification, and cancellation behavior | REQ-006, AC-3, AC-4 | The doc states `search_docs` chunks outside `allowed_dirs` are "silently excluded from results (not counted)" and that on timeout "the background thread is not forcibly interrupted" | `uv run python tools/check_docs_content_policy.py` | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/db/helper.py` | `SQLiteHelper.interrupt_when()` and `set_progress_handler` are the cancellation mechanism reused as-is; `SQLiteHelper` accepts a caller-supplied `db_path` and applies only `busy_timeout` on a read-only open, so no shared-helper change is needed | REQ-004 |
| `scripts/mcp_servers/mdq/mdq_service.py` | `_get_db_connection()` is the connection source the dedicated per-search connection replaces; `search_timeout_sec` and `allowed_dirs` are the boundary inputs | REQ-004, REQ-002 |
| `scripts/mcp_servers/mdq/mdq_error_codes.py` | The closed domain codes this Plan's classification maps to; defined by the server-boundary plan | REQ-003 |
| `scripts/mcp_servers/mdq/mdq_server.py` | The single audit boundary and the transport rendering that consume this Plan's classification; owned by the server-boundary plan | REQ-003, REQ-005 |
| `scripts/mcp_servers/mdq/audit_target.py` | The hashed query identifier contract this Plan's logs and metadata must match; owned by the server-boundary plan | REQ-005 |
| `scripts/mcp_servers/mdq/index_write.py` | `normalized_path = path.resolve().as_posix()` is why stored `source_path` values are already canonical, so the SQL prefix predicate compares canonical values | REQ-001, REQ-002 |
| `scripts/mcp_servers/mdq/db_schema.py` | `chunks.tags_json` is the column `json_each()` reads; the column is `TEXT` and can be `NULL`, which `json_each()` resolves to no rows | REQ-001 |
| `scripts/mcp_servers/mdq/parser.py` | Frontmatter tags are stored as a JSON array, so exact matching is defined against that array | REQ-001 |
| `scripts/shared/tool_transport_invoker.py` | `DEFAULT_PER_SERVER_CONCURRENCY = 8` is the existing concurrency convention the bounded active-search limit follows | REQ-004 |
| `config/agent.toml` | `tool_concurrency_limits` deliberately omits `mdq`, so the default ceiling is the value in force today | REQ-004 |
| `tests/mcp_servers/_auth_headers.py` | The HTTP-level fixture reused by the boundary tests | REQ-002, REQ-004 |
| `docs/22_mcp/mcp_02_03_audit-logging-and-errors.md` | The audit and logging rule that forbids raw query text in persistent output; owned by the server-boundary plan | REQ-005 |
| `docs/22_mcp/mcp_03_03_transport-and-health.md` | The retry classification the per-code guidance in the classification table must match | REQ-003 |

## Acceptance Criteria
- `AC-1` (REQ-002): Unauthorized rows never affect visible counts or limits and cannot suppress authorized results.
- `AC-2` (REQ-001): Path wildcard characters do not broaden scope; tags match exact values; a `path_prefix` outside `allowed_dirs` is refused before query construction.
- `AC-3` (REQ-003, REQ-005): Malformed FTS syntax is not reported as zero results; every failure resolves to a code from the closed vocabulary; no raw SQLite detail or raw query text appears in a response, metadata, or persistent log.
- `AC-4` (REQ-004): Timed-out queries stop within a bounded interval; repeated timeouts do not leak threads or connections; an interrupted connection is never reused.

## Tests
- `REQ-001`: `tests/mcp_servers/mdq/test_search.py` — `%`, `_`, and escape characters in path and heading prefixes; exact and similar tags; `tests/mcp_servers/mdq/test_mdq_path_jail.py` — a prefix outside `allowed_dirs` and a symlinked root.
- `REQ-002`: `tests/mcp_servers/mdq/test_mdq_read_authorization.py` — mixed authorized and unauthorized roots with unauthorized rows ranked above authorized rows; `tests/mcp_servers/mdq/test_mdq_search_counts.py` — authorized count; `tests/mcp_servers/mdq/test_mdq_search_limits.py` — limit slots filled only by authorized rows.
- `REQ-003`: `tests/mcp_servers/mdq/test_search.py` — malformed FTS syntax, interruption, busy or locked, missing table, corruption, and the genuine zero-result case; `tests/mcp_servers/mdq/test_mdq_search_modes.py` — the unchanged request contract.
- `REQ-004`: `tests/mcp_servers/mdq/test_mdq_search_cancellation.py` — dedicated connection, stop event, bounded drain, no reuse of an interrupted connection, bounded concurrency, and the repeated-timeout resource-leak test.
- `REQ-005`: `tests/mcp_servers/mdq/test_search.py` — no raw query text in the captured log or in the response text; `tests/mcp_servers/test_mdq_audit.py` — the metadata field carries the hashed identifier.
- Full-suite validation: `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`, `uv run bandit -r scripts/ -c pyproject.toml -ll`, `PYTHONPATH=scripts uv run lint-imports`, `uv run pytest`, `uv run diff-cover coverage.xml --compare-branch=master` at or above 90% on changed lines, `uv run pre-commit run --all-files`.

Baseline before any change: `uv run pytest tests/mcp_servers/mdq/test_search.py tests/mcp_servers/mdq/test_mdq_search_counts.py tests/mcp_servers/mdq/test_mdq_search_limits.py tests/mcp_servers/mdq/test_mdq_search_modes.py tests/mcp_servers/mdq/test_mdq_read_authorization.py tests/mcp_servers/mdq/test_mdq_path_jail.py tests/mcp_servers/test_audit_redaction.py -q` → 69 passed; the whole `tests/mcp_servers/mdq/` suite is 460 passed, 1 skipped.

## Documentation Impact
Yes. Per `docs/00_index.md` "Document References by Task" (MCP server spec row):
- `REQ-006` drives the MDQ server contract doc: `matched_count` as the authorized count, exact path and tag filter semantics, the cause-to-code classification, and cancellation behavior. Two statements must be removed: that unauthorized chunks are "silently excluded from results (not counted)", and that on timeout "the background thread is not forcibly interrupted".
- `REQ-005` is already documented by the audit-logging and errors doc, which is owned by the server-boundary plan; this Plan adds no row to that doc.
Doc content policy applies: the cause-to-code classification table is a closed vocabulary (retain); no per-exception handling table or implementation-location statement is added (`skills/DESIGN.md` Docs content policy). Run `uv run python tools/check_docs_content_policy.py` per `rules/tool-gates.md`.

## Assumptions
- `scripts/db/helper.py` is not modified. `SQLiteHelper` is consumed as it stands with a caller-supplied `db_path`; the issue's stop-and-report condition applies only if a shared-helper change becomes necessary, which the inspection shows it does not.
- Stored `source_path` values are canonical (`path.resolve().as_posix()` at index time), so the SQL prefix predicate compares canonical values. Rows indexed before canonical storage existed are still checked by the fail-closed Python check, which remains as the last gate for symlink escapes that SQL cannot resolve.
- `json_each()` is available in both the development and production SQLite builds (3.53.4 and 3.53.1 verified), and a `NULL` `tags_json` resolves to no rows rather than an error.
- The bounded active-search limit follows the existing per-server concurrency convention (`DEFAULT_PER_SERVER_CONCURRENCY = 8`, `mdq` deliberately unlisted in `tool_concurrency_limits`); no new configuration key is introduced.
- The bounded drain interval is a named constant in the search path rather than a configuration key; its value is recorded as UNK-02.
- The response header and metadata carry the hashed query identifier defined by the server-boundary plan; no test pins the current raw-text header wording, so the change is test-compatible.
- The overlap with the server-boundary plan is limited to consuming its codes and its hashed-identifier contract; this Plan does not modify `mdq_server.py`, `audit.py`, or `audit_target.py`.
- The three shared target files with the server-boundary plan are compatible: `mdq_models.py` — that plan changes the `MdqConfig` field types, this Plan changes the `SearchDocsMetadata.query_preview` field, different sections of the same module; `docs/22_mcp/mcp_04_04_mdq.md` — that plan documents the availability, health, stats, error-code, and audit surfaces, this Plan documents the query-boundary contract and removes the two search-specific statements; `tests/mcp_servers/mdq/test_mdq_read_authorization.py` — that plan adds the stats-refusal case, this Plan adds the mixed-root search cases.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | The size of the bounded active-search limit | No owner decision recorded; the existing convention gives 8 as the process-wide default and `mdq` is deliberately unlisted in `tool_concurrency_limits` | Confirm with the concurrency-policy owner; the plan's default is the existing convention, so implementation can proceed with 8 | False |
| UNK-02 | The bounded drain interval for the worker after an async timeout | No existing repository convention for a post-timeout worker wait | Decide between a named constant in the search path and a configuration key; a new key would add a `deploy.sh` line and change the deployed config | False |
| UNK-03 | Whether the shared `scripts/db/helper.py` progress handler can be reused as is | None remaining — resolved by inspection | Resolved: `SQLiteHelper` accepts a caller-supplied `db_path` and `interrupt_when()` works on its open connection, so the helper is reused unchanged; the plan records no change to it | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/mcp_servers/mdq/search.py` | Modify | Highest for the search path: every `search_docs` call, every count, every filter, and every SQLite failure classification pass through it; no external importer outside `mcp_servers.mdq` | 0 | 3 | N/A: copied by the scripts sync |
| `scripts/mcp_servers/mdq/auth.py` | Modify | Medium: shared by `search.py`, `indexer.py`, and `mdq_service.py`; the change is additive (exposes the canonicalized roots) | 0 | 3 | N/A |
| `scripts/mcp_servers/mdq/mdq_models.py` | Modify | Medium: `SearchDocsMetadata` is consumed by the audit detail builder | 0 | 2 | N/A |
| `scripts/db/helper.py` | No change | High if touched (shared by the RAG, session, and workflow stores; 23961 B against the 24576 B module gate); this Plan consumes it as-is | 7 | 3 | N/A |
| `docs/22_mcp/mcp_04_04_mdq.md` | Modify | Low | 2 | 2 | N/A |

## Design
**One query boundary.** `_build_search_where()` becomes the single place that decides what a search may see. The authorized-source predicate is part of the SQL, built from the canonicalized roots exposed by `auth.py`, so `COUNT`, ranking, and `LIMIT` all run over the authorized row set. Prefix comparison uses `instr(source_path, ?) = 1` against the canonicalized prefix rather than `LIKE`, which removes the wildcard-broadening problem without an `ESCAPE` clause; tag matching uses `json_each(c.tags_json)` with an exact value comparison. All values stay bound as parameters; the SQL text is assembled only from static predicate fragments, so the existing bandit `B608` justification continues to hold.

**Two-layer authorization.** SQL applies the canonicalized-root predicate before counting and limiting; `authorize_path()` stays as the final fail-closed check on the returned rows because SQL cannot resolve symlinks. The two layers cannot disagree for canonical stored paths, and the Python layer is the one that catches a symlinked root.

**Cause-based classification.** The single generic `OperationalError` branch is replaced by classification on the cause: malformed FTS syntax maps to the validation code, an interruption to the timeout code, busy or locked to the retryable consistency code, missing table, corruption, or schema mismatch to the non-retryable consistency code. A completed query that legitimately matches nothing is the only case that reports zero results as success. Codes come from the closed vocabulary defined by the server-boundary plan; this Plan does not extend it.

**Cancellable connection.** Each search opens its own connection through `SQLiteHelper` with the supplied `db_path`, installs `interrupt_when(stop)`, and closes it in the worker's own `finally`. On async timeout the caller sets the stop event and waits for the worker inside the bounded drain interval before reporting the timeout; a worker that does not stop within the interval is reported as a timeout and its connection is never reused. The connection is never shared across searches, so an interrupted connection cannot leak into a later call.

**Non-sensitive metrics.** Timeout and cancellation reporting carries counts, duration, and the cancellation flag only, with the hashed query identifier; no raw query text and no raw SQLite detail.

**Consumer scan (Step 3).** `grimp` reports 18 MDQ modules with no external importers; `mcp_servers.mdq.search` is imported only by `mcp_servers.mdq.mdq_service`, and `mcp_servers.mdq.auth` only by `indexer`, `search`, and `mdq_service` inside the same package. `PYTHONPATH=scripts uv run lint-imports` passes (6 contracts kept, 552 files). No change to `scripts/db/helper.py` is required, so the shared-store blast radius stays closed.

**Predictable fallout check (Step 3).**
- Module size gate (24576 B): `search.py` 8514 B has headroom; `scripts/db/helper.py` 23961 B is 615 B below the gate, which is why this Plan does not add anything to it.
- Pinned behavior that changes: `tests/mcp_servers/mdq/test_search.py::test_non_corruption_operational_error_returns_empty_results_without_raising` asserts the swallowed-error behavior being replaced; `tests/mcp_servers/mdq/test_mdq_search_counts.py` pins the count semantics; `tests/mcp_servers/test_mdq_audit.py` asserts the audit detail is sourced from metadata, which stays compatible because the metadata field is opaque to that test.
- No test pins the response header wording (`"Search results for:"`, `"No results found for:"`), so replacing raw query text with the hashed identifier is not a pinned-output change.
- `tests/mcp_servers/mdq/test_mdq_search_modes.py::test_max_search_results_field_does_not_exist` pins the request contract; the request model is not changed.

## Implementation steps
1. **Phase 1: Characterization tests first**
   - [ ] Write the unauthorized-rows-ranked-first test and the repeated-timeout resource-leak test before any production change (REQ-002, REQ-004; `tests/mcp_servers/mdq/test_mdq_read_authorization.py`, `tests/mcp_servers/mdq/test_mdq_search_cancellation.py`)
   - [ ] Add the wildcard, exact-tag, and no-raw-query-text tests that pin the current `LIKE` and raw-log behavior (REQ-001, REQ-005; `tests/mcp_servers/mdq/test_search.py`, `tests/mcp_servers/mdq/test_mdq_path_jail.py`)
   - [ ] Add the authorized-count and authorized-limit tests (REQ-002; `tests/mcp_servers/mdq/test_mdq_search_counts.py`, `tests/mcp_servers/mdq/test_mdq_search_limits.py`)
2. **Phase 2: Query construction**
   - [ ] Expose the canonicalized roots from `auth.py` and build the authorized-source predicate in SQL before `COUNT`, ranking, and `LIMIT` (REQ-001, REQ-002; `scripts/mcp_servers/mdq/auth.py`, `scripts/mcp_servers/mdq/search.py`)
   - [ ] Replace `LIKE` prefix predicates with exact prefix comparison and tag substring matching with `json_each()` exact matching (REQ-001; `scripts/mcp_servers/mdq/search.py`)
3. **Phase 3: Error classification**
   - [ ] Replace the generic `OperationalError` fallback with cause-based classification against the closed code vocabulary (REQ-003; `scripts/mcp_servers/mdq/search.py`)
   - [ ] Remove raw query text from the response text, metadata, and the persistent log line, and use the hashed identifier (REQ-005; `scripts/mcp_servers/mdq/search.py`, `scripts/mcp_servers/mdq/mdq_models.py`)
4. **Phase 4: Cancellation and concurrency**
   - [ ] Give each search its own connection through `SQLiteHelper`, install the progress-handler stop event, and close in the worker's `finally` (REQ-004; `scripts/mcp_servers/mdq/search.py`)
   - [ ] Set the stop event on async timeout, wait for the worker inside the bounded drain interval, and refuse reuse of an interrupted connection (REQ-004; `scripts/mcp_servers/mdq/search.py`)
   - [ ] Apply the bounded active-search concurrency limit and the non-sensitive timeout and cancellation metrics (REQ-004; `scripts/mcp_servers/mdq/search.py`)
5. **Phase 5: Documentation**
   - [ ] Update the MDQ server contract doc for the authorized count, exact filter semantics, the classification table, and cancellation behavior, and remove the two contradictory statements (REQ-006; `docs/22_mcp/mcp_04_04_mdq.md`)
   - [ ] Run the full validation sequence in `rules/toolchain.md` including `uv run python tools/check_module_size.py` and `uv run python tools/check_docs_content_policy.py`

### Release units
**Unit**: query-boundary-characterization-tests | **Phases**: 1, 2, 3, 4 | **Reason**: the tests written in Phase 1 assert behavior that only lands in Phases 2 through 4, so Phase 1 cannot be validated alone.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/mcp_servers/mdq/search.py` | Unit for query construction and classification; integration for the timeout and cancellation path | `uv run pytest tests/mcp_servers/mdq/test_search.py tests/mcp_servers/mdq/test_mdq_search_counts.py tests/mcp_servers/mdq/test_mdq_search_limits.py tests/mcp_servers/mdq/test_mdq_search_modes.py tests/mcp_servers/mdq/test_mdq_search_cancellation.py` | Counts and limits are computed over the authorized row set; wildcard characters do not broaden scope; tags match exactly; each cause resolves to its code; repeated timeouts leak no thread or connection |
| `scripts/mcp_servers/mdq/auth.py` | Unit for the canonicalized roots plus the existing jail tests | `uv run pytest tests/mcp_servers/mdq/test_auth.py tests/mcp_servers/mdq/test_mdq_path_jail.py` | A prefix outside `allowed_dirs` is refused before query construction; symlink escapes stay denied |
| `scripts/mcp_servers/mdq/mdq_models.py` | Unit for the metadata field plus the audit detail test | `uv run pytest tests/mcp_servers/test_mdq_audit.py` | The metadata field carries the hashed identifier; no raw query text in the detail |
| `scripts/db/helper.py` | No change; existing suite run unchanged | `uv run pytest tests/db/test_sqlite_helper.py tests/db/test_db_maintenance.py` | Passes unchanged, confirming the helper is consumed as-is |
| Architecture boundary | Contract check | `PYTHONPATH=scripts uv run lint-imports` | Passes; no new cross-layer import introduced |
| Module size gate | Gate check | `uv run python tools/check_module_size.py` | No module crosses 24576 B; `helper.py` stays untouched near the gate |
| Static analysis | CI parity | `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`, `uv run bandit -r scripts/ -c pyproject.toml -ll` | No new errors; the `B608` justification still holds because all values are bound |
| Coverage | Diff coverage | `uv run diff-cover coverage.xml --compare-branch=master` | At or above 90% on changed lines |
| Documentation | Content policy | `uv run python tools/check_docs_content_policy.py` | No implementation-detail content introduced |

## Risks
- **Risk**: the SQL prefix predicate compares stored `source_path` values that were written before canonical storage, so a legacy row could be excluded by the SQL layer while `authorize_path()` would have accepted it. → **Mitigation**: the Python fail-closed check stays as the last gate; the mixed-root tests cover both layers, and the schema-identity plan owns any storage-format migration.
- **Risk**: changing the classification turns currently swallowed failures into raised errors, which changes the observable outcome of existing tests. → **Mitigation**: the affected assertions are listed in Implementation Target Files and are rewritten in Phase 1 before the production change, so the new behavior is pinned by tests rather than inferred.
- **Risk**: cancellation through the progress handler depends on statement length; a short statement may finish before the stop event is observed, so the bounded drain can expire. → **Mitigation**: the drain interval is bounded and the plan reports a timeout without reusing the connection; `check_every` is left at the helper's default and recorded in the design.
- **Risk**: `scripts/db/helper.py` is 615 B below the module size gate, so any addition there would breach it and affect three other stores. → **Mitigation**: this Plan makes no change to the helper; if a change becomes necessary the issue's instruction is to stop and report.
- **Risk**: the bounded active-search limit is an assumption until the concurrency-policy owner confirms it. → **Mitigation**: recorded as UNK-01; the plan uses the existing convention and introduces no new configuration key.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: characterization tests first | Pending | — | — | Unauthorized-rows-ranked-first and repeated-timeout leak tests written first per the issue's instruction |
| 2 | Phase 2: query construction | Pending | — | — | Authorized SQL predicate, exact prefix and tag semantics |
| 3 | Phase 3: error classification | Pending | — | — | Cause-based mapping to the closed code vocabulary |
| 4 | Phase 4: cancellation and concurrency | Pending | — | — | Dedicated connection, stop event, bounded drain, bounded concurrency |
| 5 | Phase 5: documentation | Pending | — | — | MDQ contract doc and doc content policy gate |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: `issues/20261119-142124_mdqmcp002_mdq-search-query-boundary.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261127-161505
- **Evidence revision**: 1ea69ed7f1415545ca2c75f531e8a9376939ddad
- **Related target files**: `scripts/mcp_servers/mdq/search.py`, `scripts/mcp_servers/mdq/auth.py`, `scripts/mcp_servers/mdq/mdq_models.py`, `tests/mcp_servers/mdq/test_search.py`, `tests/mcp_servers/mdq/test_mdq_search_counts.py`, `tests/mcp_servers/mdq/test_mdq_search_limits.py`, `tests/mcp_servers/mdq/test_mdq_search_modes.py`, `tests/mcp_servers/mdq/test_mdq_read_authorization.py`, `tests/mcp_servers/mdq/test_mdq_path_jail.py`, `tests/mcp_servers/mdq/test_mdq_search_cancellation.py`, `docs/22_mcp/mcp_04_04_mdq.md`

### Requirement Traceability
See `templates/requirement-traceability.md` for the canonical column format.

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes; authorize and canonicalize `path_prefix` before query construction | `scripts/mcp_servers/mdq/auth.py` | Phase 2 | AC-2 | `tests/mcp_servers/mdq/test_mdq_path_jail.py` | Confirmed by repository evidence |
| REQ-001 | Required Changes; escape `LIKE` metacharacters or use a non-`LIKE` comparison | `scripts/mcp_servers/mdq/search.py` | Phase 2 | AC-2 | `tests/mcp_servers/mdq/test_search.py` | Confirmed by repository evidence |
| REQ-001 | Required Changes; match tags exactly with `json_each()` | `scripts/mcp_servers/mdq/search.py` | Phase 2 | AC-2 | `tests/mcp_servers/mdq/test_search.py` | Confirmed by repository evidence |
| REQ-002 | Implementation Intent; apply authorized-source constraints in SQL before `COUNT`, ranking, and `LIMIT` | `scripts/mcp_servers/mdq/search.py` | Phase 2 | AC-1 | `tests/mcp_servers/mdq/test_mdq_search_counts.py` | Confirmed by repository evidence |
| REQ-002 | Testing Expectations; unauthorized rows ranked above authorized rows | `tests/mcp_servers/mdq/test_mdq_read_authorization.py` | Phase 1 | AC-1 | itself | Confirmed by repository evidence |
| REQ-002 | Acceptance Criteria; unauthorized rows cannot suppress authorized results | `tests/mcp_servers/mdq/test_mdq_search_limits.py` | Phase 1 | AC-1 | itself | Confirmed by repository evidence |
| REQ-003 | Required Changes; malformed FTS syntax to validation, interruption to timeout, busy or locked to retryable consistency | `scripts/mcp_servers/mdq/search.py` | Phase 3 | AC-3 | `tests/mcp_servers/mdq/test_search.py` | Confirmed by repository evidence |
| REQ-003 | Problem; the generic `OperationalError` branch returns a successful zero-result response | `tests/mcp_servers/mdq/test_search.py` | Phase 1 | AC-3 | itself | Confirmed by repository evidence |
| REQ-003 | Testing Expectations; genuine zero-result case | `tests/mcp_servers/mdq/test_mdq_search_modes.py` | Phase 1 | AC-3 | itself | Confirmed by repository evidence |
| REQ-004 | Required Changes; dedicated connection per search and progress-handler cancellation | `scripts/mcp_servers/mdq/search.py` | Phase 4 | AC-4 | `tests/mcp_servers/mdq/test_mdq_search_cancellation.py` | Confirmed by repository evidence |
| REQ-004 | Required Changes; set a stop event on async timeout and wait for the worker before closing | `scripts/mcp_servers/mdq/search.py` | Phase 4 | AC-4 | `tests/mcp_servers/mdq/test_mdq_search_cancellation.py` | Confirmed by repository evidence |
| REQ-004 | Required Changes; bounded active-search semaphore and non-sensitive metrics | `scripts/mcp_servers/mdq/search.py` | Phase 4 | AC-4 | `tests/mcp_servers/mdq/test_mdq_search_cancellation.py` | Confirmed by repository evidence |
| REQ-004 | Testing Expectations; repeated-timeout resource-leak test | `tests/mcp_servers/mdq/test_mdq_search_cancellation.py` | Phase 1 | AC-4 | itself | Confirmed by repository evidence |
| REQ-005 | Constraints; unauthorized counts never appear in text, metadata, or audit | `scripts/mcp_servers/mdq/mdq_models.py` | Phase 3 | AC-3 | `tests/mcp_servers/test_mdq_audit.py` | Confirmed by repository evidence |
| REQ-005 | Required Changes; no raw SQLite or query text in responses; raw query logged at `logger.info` in `scripts/mcp_servers/mdq/search.py` | `scripts/mcp_servers/mdq/search.py` | Phase 3 | AC-3 | `tests/mcp_servers/mdq/test_search.py` | Confirmed by repository evidence |
| REQ-006 | Documentation Impact; `matched_count` as authorized count and filter semantics | `docs/22_mcp/mcp_04_04_mdq.md` | Phase 5 | AC-3 | `uv run python tools/check_docs_content_policy.py` | Confirmed by repository evidence |
| REQ-006 | Documentation Impact; error codes and cancellation behavior | `docs/22_mcp/mcp_04_04_mdq.md` | Phase 5 | AC-4 | `uv run python tools/check_docs_content_policy.py` | Confirmed by repository evidence |
