# Session sqlite-vec is not loaded at runtime, so Memory vector writes and KNN always fail

## Priority
High

## Summary
Adopt Session Vector: amend ADR-008 (and the documents that restate its scope) so sqlite-vec is a sanctioned extension for `session.sqlite` as well as `rag.sqlite`, make `SQLiteHelper("session")` load it by default, and add real-DB tests so Memory vector CRUD and KNN are verified on the session connection.

## Background
- Origin: review memo1.md V26-05, investigated and reproduced in the same session (2026-10-19). Decision by the user: adopt option 1 (amend ADR-008) with connection fix (b) (change the helper default for session), and file it as an issue.
- ADR-008, the overview, and the shared overview state that sqlite-vec is loaded only into `rag.sqlite` and not applied to `session`. Yet the Memory schema (`memories_vec`, a vec0 virtual table) lives in `session.sqlite`, and Memory code reads and writes it through `SQLiteHelper("session")`.
- `tools/check_db_separation.py` already registers `memories_vec` as a session-owned vec table, and permits explicit `load_vec=True` only in `scripts/db/create_schema.py`. It also pins the helper default to `resolved == "rag"`.
- The logical separation of Session and Memory responsibilities is not a physical DB split; this issue does not change DB ownership.

## Problem
- Confirmed by reproduction on a temporary session DB, via the real `SQLiteHelper("session")` path:
  - With `load_vec` unset (the way every `scripts/agent/memory/*.py` call site opens the connection), `INSERT`, `COUNT`, and KNN `MATCH` against `memories_vec` all raise `sqlite3.OperationalError: no such module: vec0`.
  - With `load_vec=True`, `COUNT` and KNN succeed.
- Cause: the helper default is `_default_load_vec = (resolved == "rag")`, and `load_vec=True` is passed only at schema creation.
- Effects on runtime:
  - Retrieval catches the `OperationalError`, logs a WARNING, and degrades to FTS-only on every call, so the failure is silent and Memory retrieval is never hybrid. (Confirmed in code)
  - Writes with an embedding call `_write_vec`, which raises on failure. Whether the whole write transaction fails or the error is swallowed by callers is unknown.
- Tests do not catch it: the integration conftest swallows the exception, and the retriever unit test uses an in-memory DB without vec.

## Reason for Change
- Correctness: a documented feature (hybrid Memory retrieval, vector index maintenance, `/memory reindex --vec`, `rebuild`) cannot work on the real connection, and the degradation is silent.
- Documentation conflict: the normative scope rule ("RAG only") contradicts the implemented and checked schema ownership (`memories_vec` in session).
- The check tool currently locks in the defect (it fails if the helper default stops being `resolved == "rag"`).

## Implementation Intent
- Treat this as one coordinated change across the ADR, the helper default, the check tool, and tests, so the design is stated once.
- ADR-008 amendment: sqlite-vec is loaded for the databases that own a vec0 table (`rag.sqlite`: `chunks_vec`, `session.sqlite`: `memories_vec`); it is still not applied to `workflow.sqlite` or `eventbus.sqlite`. Keep the explicit `load_vec` override.
- Connection fix (b): change the session default in the helper so that Session connections load the extension, instead of passing `load_vec=True` at each Memory call site. This keeps one place to reason about and avoids new sanctioned call sites.
- Keep the check tool as the enforcement point: update its helper-default rule and sanctioned-site rule to describe the new design rather than deleting the check.
- Fail visibly rather than silently where the extension is required but cannot load (see Unresolved Questions for the exact startup behavior).

## Target Files or Areas
- `docs/10_adr/adr_02_008_sqlite-4db-separation.md` (Constraints / Decision scope for sqlite-vec; approval text per ADR rules)
- `docs/01_overview/overview_01_03-arch-features.md`
- `docs/40_shared/shared_01_overview.md`
- `docs/41_db/db_01_architecture_and_schema-overview-and-config.md` (helper default and `open(load_vec=...)` description) and `docs/41_db/db_05_api_and_operations-protocol-and-backend.md` (Memory DB description)
- `scripts/db/helper.py` (default for the session target; also the constructor path that derives the default from `sqlite_vec_so`)
- `tools/check_db_separation.py` (vec-scope check, `LOAD_VEC_SANCTIONED`)
- `scripts/agent/memory/` (verify no call site needs a change; `write_ops.py`, `retriever.py`, `count_ops.py`, `rebuild_ops.py`, `import_ops.py`, `store.py`)
- `tests/` for the DB helper, the memory package, and `tests/integration/conftest.py` (swallowed exception)

## Required Changes
- Amend ADR-008 scope text and cited invariants/tests for the sqlite-vec rule; record the approval for the amendment as the ADR process requires. Do not change the four-database decision.
- Align the overview, shared overview, and DB reference documents with the amended rule (default per database, explicit override, which connections load the extension).
- Change `scripts/db/helper.py` so the session target loads sqlite-vec by default, keeping the explicit `load_vec` override and the empty-`sqlite_vec_so` behavior unchanged.
- Update `tools/check_db_separation.py` so the helper-default rule and sanctioned-site rule match the new design, and the check still fails on loading the extension for `workflow` or `eventbus`.
- Add tests that open a real `SQLiteHelper("session")` against a temporary DB with the extension loaded and exercise vec INSERT, `INSERT OR REPLACE`, DELETE, COUNT, and KNN through the Memory write, count, and retrieval code (not an in-memory DB without vec).
- Replace the swallowed exception in the integration conftest and the session recovery test with an explicit skip when the extension is unavailable, so a real failure is not hidden.
- Decide and implement what happens when the extension cannot be loaded for a session connection (startup validation versus per-call degrade), consistent with ADR-004 failure handling.

## Constraints
- ADR-008 four-database decision, table ownership, and the no-cross-DB-FK / no-`ATTACH` rules stay unchanged.
- Docs under `docs/` are written in English and must stay free of line numbers and concrete config values per `skills/DESIGN.md`.
- The Memory feature must keep working where sqlite-vec is not installed only if that is the sanctioned degraded mode; do not introduce a silent fallback that hides a missing extension (ADR-004).
- ADR edits are checked by `tools/check_adr_preservation.py`; changed Decision text needs a sentence-level mapping and invariant text changes are errors.
- Production DB, `/opt/llm/`, and deployment are not touched by this issue.

## Acceptance Criteria
- ADR-008, the overview, the shared overview, and the DB reference describe one consistent sqlite-vec scope (default per DB, explicit override, Memory vector in session).
- On a real `SQLiteHelper("session")` connection created with default arguments, vec INSERT, DELETE, COUNT, and KNN against `memories_vec` succeed, verified by tests that fail if the extension is not loaded.
- `uv run python tools/check_db_separation.py` passes, and still fails when `workflow` or `eventbus` would load the extension.
- A retrieval run with an embedding on a real session DB reports hybrid mode rather than the FTS-only fallback.
- The behavior when the extension cannot be loaded is defined, documented, and tested.
- The checkers listed in `routing.md` for the touched files pass (docs quality, structure, content policy, consistency for the agent and overview domains, ADR preservation, `generate_reference_table.py --check`, ruff, mypy, pytest).

## Testing Expectations
- Unit tests for the helper default per target (rag and session load, workflow and eventbus do not; explicit override both ways).
- Integration tests on a temporary session DB covering vec write, replace, delete, count, KNN, and `rebuild`/`reindex --vec` code paths.
- A regression test for the retriever: with a real vec table and an embedding, the result mode is hybrid.
- Regression test for `tools/check_db_separation.py` rules.
- Run the full validation sequence in `rules/toolchain.md`.

## Documentation Impact
Yes. Update intent and constraints of the sqlite-vec scope in ADR-008, the overview, the shared overview, and the DB reference; document the failure behavior when the extension cannot load. Register any Needs-Confirmation marker per governance rules and run `tools/check_needs_confirmation_inventory.py` if one is added.

## Out of Scope
- Moving Memory vector storage to `rag.sqlite` or removing the Memory vector feature (options 2 and 3 were rejected).
- Changing the four-database separation, table ownership, or the embedding dimension and schema of `memories_vec`.
- Embedding generation, RRF merging, or retrieval ranking changes.
- RAG remote and local corpus identity checks.
- Deploying the change to production.

## Dependencies
- N/A: none. No open issue under `issues/` touches the same files; sibling check recorded 2026-10-19.
- ADR amendment approval is required before the documentation and tool changes are merged.

## Unresolved Questions
- Do writes with an embedding (`write_ops.add` and `upsert`) fail the whole transaction or are errors swallowed by callers today? Not confirmed; verify before fixing and record the observed behavior.
- Startup behavior when the extension cannot be loaded for session: abort startup, disable Memory vector, or degrade per call? Needs a decision consistent with ADR-004 (assumption: no silent fallback).
- Whether loading the extension on every session connection (including non-Memory use such as conversation tables) has a measurable cost; assumed negligible, unmeasured.

## AI Implementation Instruction
- Do the ADR amendment and documents first and stop for approval before changing the check tool or helper default if approval is not yet recorded.
- Keep the diff minimal: no unrelated refactoring (AGENTS.md Global Rule 5), no change to Memory call sites unless the helper default alone cannot fix them.
- Never loosen the check tool for `workflow` or `eventbus`.
- Reproduce the failure with a test before changing the helper default, then show the test passes after.
- Stop and report if the transaction behavior on write failure reveals data loss or if the extension is unavailable in the test environment.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261019-092704
- **Related target files**: `docs/10_adr/adr_02_008_sqlite-4db-separation.md`, `scripts/db/helper.py`, `tools/check_db_separation.py`, `scripts/agent/memory/`, `tests/integration/conftest.py`
