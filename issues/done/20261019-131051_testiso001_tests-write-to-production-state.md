# Running the test suite writes to production state under /opt/llm (session DB and logs)

## Priority
High

## Summary
Isolate the test suite from production state: point every test at a temporary configuration and log directory so no test can read or write `/opt/llm`, fix the tests that currently write test data into the production session database, and add a guard that fails a test which resolves a production path.

## Background
- Found on 2026-10-19 while investigating a startup error. This host is both the development checkout and the production install, so the repository `config/agent.toml` (with `/opt/llm/...` paths) is what tests resolve by default.
- A production-state read was permitted by the owner during the investigation; all inspection of the session database used a copy.

## Problem
- Production session database (Explicit evidence, from a copy of `/opt/llm/db/session.sqlite`): all 1172 rows in `memories` are test artifacts, three repeated contents (586, 293, 293 rows), added four rows per test run since 2026-07-10; the newest four rows are dated 2026-10-19T03:40:27Z, matching the file's modification time `12:40:27 JST` and a full test run. `messages` also holds 65 user rows whose content is `content` (writer not identified).
- Cause, confirmed by running `tests/agent/memory` with a plugin that redirects `db.helper.build_db_config` to a temporary database (production file unchanged during that run): four tests in `tests/agent/memory/test_memory_layer.py` each write one `memories` row because they call the real `write_ops.upsert` (through `MemoryIngestionService`) without patching `agent.memory.ingestion.write_upsert`: `test_no_entry_when_embed_fails`, `test_increment_on_embed_failure_in_persist_entry_with_dedup`, `test_increment_on_embed_failure_in_persist_entry`, and `test_summary_log_contains_count`. `SQLiteHelper("session")` resolves `session_db_path` from `config/agent.toml`, which is `/opt/llm/db/session.sqlite`. One more test in the same file, `test_on_session_stop_delegates`, is also unpatched but did not write a row.
- No isolation exists: the autouse fixtures in `tests/conftest.py` reset the tool registry, web-search metrics, and `ConfigLoader` state only.
- Production logs (Explicit evidence): about 36 modules under `scripts/` call `Logger(__name__, "/opt/llm/logs/<name>.log")` with a literal path at import time, and `shared/logger.py` opens a `FileHandler` on that path with no test-mode branch. `agent.log`, `ingest.log` (entries such as `file:///tmp/pytest-of-masaos/...`), `chunk.log`, `crawl.log`, `search.log`, `mdq-mcp.log`, the file MCP logs, and `web-search-mcp.log` all contain test output; in `agent.log` the minutes with at least 50 lines (test bursts) account for 3189 of 4067 lines.
- Effects: real startup errors are buried in test `FATAL pipeline outcomes` lines; real agent sessions can recall the test memories (not yet confirmed); and any unpatched test that reaches `db.recovery`, `db.rotation`, or `db.maintenance` (all call `build_db_config()`) could act on production database files (not yet checked).

## Reason for Change
- Data integrity and operations: tests silently modify the production session database and fill the production logs on every run, and the owner had to interrupt a full test run during an incident because of it.
- Until fixed, running the full suite on this host is unsafe; the earlier advice to run `/memory reindex --vec` on the "1160 memories" was wrong because those rows are test data.

## Implementation Intent
- Prefer one mechanism over per-test patches: `shared.runtime_paths.resolve_config_dir` already honors `LLMAGENT_CONFIG_DIR`, so `tests/conftest.py` can create a temporary config directory at import time (before any `scripts/` module is imported), copy `config/*.toml` into it with the `/opt/llm/` prefix rewritten to a temporary root, and set `LLMAGENT_CONFIG_DIR`. This redirects every `ConfigLoader()` default load, including `build_db_config()` in `helper`, `recovery`, `rotation`, and `maintenance`, and the memory JSONL, Event Bus, and storage paths.
- For logs, add an environment override in `scripts/shared/logger.py` (for example a log-directory variable that replaces the `/opt/llm/logs` prefix of the requested file) so the 36 literal call sites stay untouched; `tests/conftest.py` sets it at import time. Set both variables at module import, not in a fixture, because the `Logger` instances are created when `scripts/` modules are imported during collection.
- Add a guard (an autouse fixture or a session check) that fails a test whose resolved config directory, DB path, or log path is under `/opt/llm`, with an explicit opt-out marker for any test that must read the real path.
- Also patch the five unpatched tests so they no longer depend on the global isolation for correctness.
- Remove the temporary directory at session end.

## Target Files or Areas
- `tests/conftest.py` (temporary config directory, environment variables, guard)
- `scripts/shared/logger.py` (log-directory override)
- `tests/agent/memory/test_memory_layer.py` (patch the five unpatched tests)
- A new test module for the isolation itself, for example `tests/test_production_isolation.py` (name Unknown)
- `tests/shared/test_logger.py` (existing logger test module; add the override tests here)
- Documentation: Unknown (a testing or development document may need a note; confirm through `docs/00_index.md`)

## Required Changes
- Build the temporary config directory and set `LLMAGENT_CONFIG_DIR` and the log-directory variable at `tests/conftest.py` import time; clean up at session end.
- Implement the log-directory override in `shared/logger.py` without changing behavior when the variable is unset (production binaries keep `/opt/llm/logs`).
- Add the guard and an opt-out marker, and document the marker next to its definition.
- Patch `agent.memory.ingestion.write_upsert` (or inject a temporary DB) in the five unpatched tests.
- Add tests: under pytest, `ConfigLoader().load("agent.toml")` returns no `/opt/llm` path for the DB and storage keys; `SQLiteHelper("session")` resolves under the temporary root; a `Logger` created with a `/opt/llm/logs/...` path writes under the temporary log directory; the override is inactive when the variable is unset.
- Fix any test that fails because it relied on the real `/opt/llm` values in the loaded config, using the opt-out marker or a local patch, and record each such test.
- Identify which tests write the 65 `content` rows in `messages` (candidates under `tests/agent/` that use `AgentSession` or the message repository) and confirm they are covered by the isolation.

## Constraints
- Never write to or read `/opt/llm` during implementation or tests; validate with temporary directories. The final acceptance run of the full suite must be preceded by a snapshot of `/opt/llm/db/*.sqlite` and `/opt/llm/logs/*` (size and modification time) and followed by a comparison.
- Do not run the full suite on this host before the isolation exists; use targeted tests, or a throwaway redirect plugin, until then.
- Production binaries must behave unchanged when the new environment variable is unset.
- Cleaning the existing test rows and log noise in production is a separate, approved operation and is not performed by this issue.

## Acceptance Criteria
- After the change, a full test run leaves `/opt/llm/db/*.sqlite` and `/opt/llm/logs/*` unchanged (identical size and modification time before and after).
- No test resolves a path under `/opt/llm` without the explicit opt-out marker; the guard fails such a test.
- The five unpatched tests no longer write through the real `write_ops.upsert`.
- `shared/logger.py` redirects only when the override variable is set, and its tests pass.
- The new isolation tests and the existing suite pass (any test adjusted for the new config source is listed in the pull request or commit message).

## Testing Expectations
- New tests for the isolation, the guard, and the logger override.
- The memory tests rerun with isolation active; the previously writing tests assert on their own mocks or a temporary DB.
- The `rules/toolchain.md` sequence, plus the documentation checkers if a document is edited.
- Acceptance: a full-suite run with before/after snapshots of `/opt/llm`, performed only after the isolation is in place.

## Documentation Impact
Possibly: a short note on test isolation (the two environment variables and the opt-out marker) in the development or testing documentation, named through `docs/00_index.md` during planning. Use `N/A` if no testing document exists.

## Out of Scope
- Deleting the existing test rows from the production session database (`memories`, `memories_fts`, the 65 `messages` rows) and trimming the production logs; this needs a backup and explicit approval.
- The unreachable LLM servers found in the same investigation, and unrelated pre-existing test failures.
- Changing production logging, configuration, or the binaries' behavior with the override unset.
- Moving to a different test framework or changing test collection.

## Dependencies
- N/A: none. No open issue under `issues/` overlaps; sibling check recorded 2026-10-19.
- Follow-up that depends on this issue: the approved cleanup of production test data (otherwise the next test run re-pollutes it).

## Unresolved Questions
- Which tests wrote the 65 `messages` rows with content `content` (candidates only; not attributed).
- Whether other tests reach `db.recovery`, `db.rotation`, or `db.maintenance` with the default config and could act on production database files.
- Whether any tests assert values read from the real `config/*.toml` through `ConfigLoader` that the redirected config would change (assumption: few; they are found by running the suite once the isolation exists).
- Whether real agent sessions have already recalled the test memories (not checked).
- The exact name of the new isolation test module, and whether a testing document exists to update.

## AI Implementation Instruction
- Keep the diff minimal and limited to the target files; do not change production behavior when the override variable is unset.
- Set the environment variables at `tests/conftest.py` import time; a fixture is too late for module-level `Logger` instances.
- Do not run the full suite before the isolation is in place; verify each step with targeted tests, and use temporary directories only.
- Do not touch `/opt/llm` (read or write) except for the before/after snapshot in the final acceptance run, and do not delete any production data in this issue.
- Stop and report if a test genuinely needs a real production path, instead of weakening the guard.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261019-131051
- **Related target files**: `tests/conftest.py`, `scripts/shared/logger.py`, `tests/agent/memory/test_memory_layer.py`, `tests/shared/test_logger.py`
