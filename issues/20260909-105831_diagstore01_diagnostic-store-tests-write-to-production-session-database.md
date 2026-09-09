# `test_diagnostic_store.py` mocks the wrong import site and writes real rows into the production `session.sqlite` database

## Priority
High

## Summary
`tests/agent/test_diagnostic_store.py` fails 22-25 tests (count grows across repeated
runs) because assertions like `assert len(rows) == 1` observe hundreds of pre-existing
rows instead. Root cause confirmed by direct read-only query: `DiagnosticStore`'s tests
patch the wrong import site, so every test run in this file inserts real rows into and
reads real rows from the actual production `session.sqlite` database configured in
`config/agent.toml` — not an isolated test database. A direct read-only query during
this investigation showed the row count in the real `session_diagnostics` table
growing in step with the test run that produced it.

## Background
`scripts/agent/diagnostic_store.py` does `from db.helper import SQLiteHelper`, binding
the name into `agent.diagnostic_store`'s own module namespace. Every test in
`tests/agent/test_diagnostic_store.py` patches `"db.helper.SQLiteHelper"` — the
*origin* module where `SQLiteHelper` is defined — instead of
`"agent.diagnostic_store.SQLiteHelper"`, the name as it is actually looked up at call
time inside `DiagnosticStore`. This is the standard wrong-mock-target bug: patching
where a symbol is defined does not affect a module that already did
`from X import Y` — the local binding in `agent.diagnostic_store` is untouched by a
patch applied to `db.helper`.

## Problem
Because the patch never takes effect, `DiagnosticStore.save()`/`fetch()` fall through
to the real `SQLiteHelper("session")` construction path:
`scripts/db/config.py::build_db_config()` reads `config/agent.toml`, which sets
`session_db_path = "/opt/llm/db/session.sqlite"` — a real file that exists and is used
by the running agent. `DiagnosticStore.__init__` takes only `session_id`, with no
path-override parameter, so there is no supported way to redirect it to a test path
other than mocking the correct import site — which this test file fails to do. The
test file's own `_FakeSQLiteHelper` + `fake_db` fixture is the only isolation attempt
present, and it never engages because of the wrong patch target above. No
`tests/agent/conftest.py` exists, and `tests/conftest.py` has no diagnostics/session-DB
autouse fixture that would otherwise catch this.

**Direct, definitive production-data-impact confirmation** (read-only query, no data
modified to investigate this): `sqlite3 -readonly /opt/llm/db/session.sqlite "select
count(*) from session_diagnostics"` returned 922 rows during this investigation, up
from 846 measured moments earlier before a single additional isolated test run — the
846→922 growth exactly matches what that one test run would insert. The `kind` column's
value distribution includes `k`, `k1`, `k2`, `new_kind`, `test`, and `event` — labels
that never occur in any production code path — confirming these rows are test-inserted
pollution accumulated across repeated test runs directly into the real production file,
commingled with any genuine diagnostic rows the running agent itself has written, with
no way to distinguish or clean up one from the other after the fact.

## Reason for Change
This is a data-integrity defect, not merely a broken test: every local or CI run of
`tests/agent/test_diagnostic_store.py` silently grows a real production database file,
pollutes it with non-production data, and makes the recorded diagnostics history
unreliable for its actual operational purpose. It also makes 22-25 tests in this file
permanently fail regardless of the code under test, since they assert on row counts
that can never be exactly 1 in a table that already has hundreds of unrelated rows.

## Implementation Intent
Fix the mock-patch target in `tests/agent/test_diagnostic_store.py` from
`"db.helper.SQLiteHelper"` to `"agent.diagnostic_store.SQLiteHelper"` (the import-site
convention, matching how other test files in this repository correctly patch
import-site rather than definition-site) so the existing `_FakeSQLiteHelper`/`fake_db`
fixture actually engages and tests run against an isolated fake, not the real database.
Additionally, consider whether `DiagnosticStore` should gain an explicit path-injection
seam (e.g. an optional constructor parameter) as defense-in-depth against a future
wrong-target patch silently falling through to production config again — this is a
secondary hardening recommendation, not required to close this issue's primary defect.

## Target Files or Areas
- `tests/agent/test_diagnostic_store.py` (fix the mock-patch target on every affected
  test)
- `scripts/agent/diagnostic_store.py` (reference only — confirms the
  `from db.helper import SQLiteHelper` import-site binding; optional hardening target
  if a path-injection seam is added, see Implementation Intent)
- `scripts/db/config.py` (reference only — confirms `build_db_config()`'s
  `session_db_path` resolution from `config/agent.toml`)

## Required Changes
- Change every `patch("db.helper.SQLiteHelper", ...)` (or equivalent) in
  `tests/agent/test_diagnostic_store.py` to `patch("agent.diagnostic_store.SQLiteHelper", ...)`.
- Confirm the existing `_FakeSQLiteHelper`/`fake_db` fixture actually engages after the
  fix (no real DB file opened during a run of this test file — verify via a
  filesystem-level check, e.g. confirming `/opt/llm/db/session.sqlite`'s row count is
  unchanged before/after running this file).
- (Optional hardening, may be split into a follow-up) Add an explicit DB-path
  constructor parameter to `DiagnosticStore` so a future incorrect patch target fails
  loudly (e.g. a missing/invalid test path) rather than silently falling through to
  production config.

## Constraints
Do not attempt to clean up or delete the existing test-inserted rows already present in
the real `/opt/llm/db/session.sqlite` as part of this issue — that file may also contain
genuine production diagnostic data commingled with the test pollution, and a cleanup
strategy (if pursued) needs its own careful, separately-considered scope given the risk
of deleting real data. This issue's scope is stopping further pollution, not remediating
what has already accumulated.

## Acceptance Criteria
- [ ] Every `SQLiteHelper` patch in `tests/agent/test_diagnostic_store.py` targets
  `agent.diagnostic_store.SQLiteHelper`, not `db.helper.SQLiteHelper`
- [ ] Running `tests/agent/test_diagnostic_store.py` produces no change in
  `/opt/llm/db/session.sqlite`'s row count (verified by a before/after row-count check
  against the real file)
- [ ] `uv run pytest tests/agent/test_diagnostic_store.py -q` passes with the row-count
  assertions now observing exactly the rows each test itself inserted into the fake
  store, not hundreds of unrelated rows

## Testing Expectations
- `uv run pytest tests/agent/test_diagnostic_store.py -q` — full file must pass
- Manual/scripted verification: `sqlite3 -readonly /opt/llm/db/session.sqlite "select
  count(*) from session_diagnostics"` run immediately before and immediately after the
  test file, confirming no change — this is the definitive regression check for this
  specific defect and should be run once as part of closing this issue, not
  automated into CI unless a lightweight way to do so is found

## Documentation Impact
N/A: this is a test-isolation bug fix with no documented-behavior change to
`DiagnosticStore` itself (unless the optional path-injection hardening from
Implementation Intent is also implemented, in which case document the new constructor
parameter in `DiagnosticStore`'s own docstring — no `docs/*.md` impact identified).

## Out of Scope
- Cleaning up rows already written into the real `/opt/llm/db/session.sqlite` by past
  test runs (see Constraints).
- Any change to `scripts/db/config.py` or `config/agent.toml`'s `session_db_path`.
- Auditing other test files for the same wrong-mock-target pattern against
  `db.helper.SQLiteHelper` — if this issue's fix reveals the same bug shape elsewhere,
  file it separately.

## Dependencies
N/A: none. Related to (but does not duplicate) the now-deleted triage record
`issues/20260908-203803_regr001_full-suite-491-pre-existing-failures.md`, which first
flagged this as a data-integrity risk requiring priority investigation.

## Unresolved Questions
Whether the optional `DiagnosticStore` path-injection hardening (Implementation Intent)
should be done in this same change or split into its own follow-up — both are small
enough to combine, but the primary defect (wrong patch target) is the priority and
should not be blocked on deciding this.

## AI Implementation Instruction
Fix the patch target first and verify via the before/after row-count check against the
real `/opt/llm/db/session.sqlite` — do not consider this issue resolved on `pytest`
passing alone, since a fix that merely changes assertions to tolerate a growing row
count would still leave production data being written to. Do not attempt to delete or
modify existing rows in the real database file. Do not implement the optional
path-injection hardening without first confirming the primary patch-target fix alone
stops the pollution.

## Traceability
- **Workflow phase**: N/A: manually filed
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260909-105831
- **Related target files**: see Target Files or Areas above
