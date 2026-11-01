# Detect production database changes caused by a test-suite run

## Priority
High

## Summary
Add a session-level check that fails a test run when files under `/opt/llm/db/` changed during the run, and cover the subprocess path that the existing per-test guard cannot see. The goal is that a test which reaches production state is reported by the suite itself, not discovered by a person comparing timestamps.

## Background
- `Operationally observed` (2026-10-30): the full test suite modified the production `workflow.sqlite`. Test `tests/deploy/test_init_db_eventbus_schema.py` runs the real `deploy/init_db.sh`, which starts `create_schema.py` in a subprocess; the production file gained a `schema_migrations` table and a baseline row during suite runs. No test failed and no guard fired; the change was found by inspecting the file's modification time.
- `Explicit in code`: `tests/conftest.py` `_forbid_production_paths` patches `sqlite3.connect` and `logging.FileHandler.__init__` inside the test process. A subprocess is outside both patches, and the helper `_run` in the test above builds its environment from only `PATH` and `HOME`, so the isolation variables set by `conftest.py` (`LLMAGENT_CONFIG_DIR` and the others) are not inherited.
- `Explicit in code`: in that test the sandbox config was meant to pin `workflow_db_path`, but the key was appended after the last table of `config/agent.toml`, so it was not a top-level key and the subprocess fell back to the production default. The cause was fixed in the test on 2026-10-30; the missing detection is the subject here.
- `Explicit in code`: commit `1574a44bc` ("test: isolate the test suite from production state under /opt/llm") introduced the existing isolation; the gap above is the part it does not cover. `tests/conftest.py` already defines `pytest_sessionfinish`.
- `Operationally observed`: after the fix, the modification time of the production file stayed unchanged across a full-suite run; the same check can be made automatic.

## Problem
Isolation depends on every test setting up its own environment correctly. A test that spawns a subprocess with a custom environment can bypass all in-process guards, and the only symptom is a changed production file.

## Reason for Change
The affected data is the live workflow database (and, in principle, the other three). A silent write by a test run is a data-integrity risk, and schema work now being deployed makes the production file's state meaningful to the migration procedure.

## Implementation Intent
Add a detection that does not depend on test authors. At session start, record a cheap fingerprint of the production database files (existence, size, modification time, and a content hash where affordable, including the `-wal` and `-shm` sidecars); at session finish, compare and fail the run when a file changed, naming the file. Skip silently when `/opt/llm/db` does not exist (CI, other hosts). Keep the per-test guard as it is. Separately, evaluate a small shared helper that builds an isolated subprocess environment, so tests that spawn processes do not rebuild the environment by hand.

## Target Files or Areas
- `tests/conftest.py` (session-level fingerprint and comparison)
- `tools/check_conftest_integrity.py` and its tests (the integrity check that guards required `conftest.py` fixtures must know the new hook)
- A shared test helper for subprocess environments (location to be decided; `tests/` helper module)
- `tests/deploy/test_init_db_eventbus_schema.py` (use the helper, if adopted)
- `rules/toolchain.md` or the relevant test skill note (one sentence on the guarantee)

## Required Changes
- Implement the session fingerprint and comparison, with an explicit opt-out marker for tests that legitimately use production state (the existing marker `production_paths_allowed`).
- Make `check_conftest_integrity.py` require the new hook so it cannot be removed silently.
- Evaluate and, if adopted, add the isolated-subprocess-environment helper and use it in the deploy test.
- Add a regression test that a write to a temporary stand-in "production" directory is detected.

## Constraints
- The check is read-only and must not open production databases with a writing connection (use file metadata and a byte-level read).
- No effect on hosts without `/opt/llm/db`.
- The run-time overhead must be negligible against the suite's minutes-long runtime.
- Do not change any production file, including removing the rows that earlier runs added.

## Acceptance Criteria
- A test that writes to a configured stand-in production directory causes the session to fail with a message naming the file.
- A suite run that changes nothing passes, and the check is skipped when the directory is absent.
- `check_conftest_integrity.py` fails when the new hook is removed from `conftest.py`.
- The full suite passes on this host with the check enabled, and the production `workflow.sqlite` modification time is unchanged by it.

## Testing Expectations
- Unit or pytester-style tests for the detection, using a temporary directory as the stand-in.
- One full-suite run on this host, with the production files' metadata compared before and after by hand as an independent check (this is a read-only comparison).
- Tests for `check_conftest_integrity.py` covering the new requirement.

## Documentation Impact
Yes, small: one note in the test guidance stating that a session which changes production database files fails. Intent and failure behavior only.

## Out of Scope
- Cleaning the rows earlier runs left in the production database (a separate owner decision).
- Isolating non-database production paths other than what the existing guard already covers.
- Changing the migration or deploy procedure.

## Dependencies
N/A: none. No open issue or Plan targets these files (checked with `rg` over `issues/*.md` and `plans/*.md`, 2026-10-30).

## Unresolved Questions
- `不明`: whether a content hash of the production files is affordable on every run or modification time and size are sufficient; the databases are small (tens of kilobytes) on this host.
- `不明`: whether the same check should also run in CI, where `/opt/llm/db` is absent (the assumption is that it is skipped).
- Assumption: a changed `-wal` or `-shm` sidecar alone, without a main-file change, still counts as a production touch.

## AI Implementation Instruction
Implement the detection and its tests only. Never write to or delete any production file, and never open a production database with a writing connection. Keep the opt-out explicit through the existing marker. Stop and report if the fingerprint cannot be read without side effects.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261030-191351
- **Related target files**: `tests/conftest.py`, `tools/check_conftest_integrity.py`, `tests/deploy/test_init_db_eventbus_schema.py`, `rules/toolchain.md`
