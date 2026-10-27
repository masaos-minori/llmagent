#!/usr/bin/env python3
"""Fill the 20261027-165951 rag004 implementation-procedure skeletons with plan-derived content.

One-shot generator used by the plan-to-implementation-procedure workflow for
plans/20261027-111107_rag004_ingester-sqlite3-error-aborts-batch.md. Content is
derived from the Plan rows plus live line-number evidence verified on 2026-10-27.
"""

from pathlib import Path

PREFIX = "implementations/20261027-165951"
PLAN = "plans/done/20261027-111107_rag004_ingester-sqlite3-error-aborts-batch.md"
ISSUE = "issues/20261027-074526_rag004_ingester-sqlite3-error-aborts-batch.md"
GEN_AT = "20261027-165951"

OVERLAP = (
    "- Overlap: `docs/21_rag/rag_05_04-error-handling-reference.md` is also targeted by the "
    "rag003 Plan procedures (implementations/20261027-154425_26_*), which rename the "
    "`rag_service_url` occurrence in the RagPipeline table; this procedure adds a row to the "
    "RagIngester table. Disjoint tables; whichever implements second rebases (Plan "
    "Dependencies)."
)

STATIC = (
    "- `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/`, "
    "`uv run bandit -r scripts/ -c pyproject.toml -ll`, `PYTHONPATH=scripts uv run "
    "lint-imports` — clean; no blind-except findings (AC-1).\n"
    "- `uv run pytest tests/` — full suite green (AC-5)."
)

OOS = (
    "- Broadening the catch to bare `Exception`/`BaseException` (Issue Constraint).\n"
    "- Changing transaction boundaries or rollback behavior (`SQLiteHelper.begin_immediate` "
    "stays as-is).\n"
    "- Changing `ingest_url_group`'s own exception semantics for direct callers.\n"
    "- The `int(cfg[...])` coercion style in `crawler.py`, `chunk_splitter.py`, "
    "`db/config.py`, `db/maintenance.py`.\n"
    "- httpx/transport error handling — verified contained inside `ChunkFactory.prepare` and "
    "converted to `failed_paths` (Issue Unresolved Question, answered: no change)."
)

ROLLBACK = (
    "- Single commit adding the import, the widened tuple, tests, and the doc row; rollback is "
    "`git revert`. No config, schema, or deployed-state change."
)

SECURITY = (
    "- The widened catch stays bounded to the `sqlite3.Error` hierarchy — narrower than "
    "`Exception` — so non-DB programming errors (`TypeError`, `AttributeError`) still fail "
    "fast (Plan Risks). `logger.exception` preserves the full traceback; failures are recorded "
    "as results, never silent."
)


def doc(
    title,
    target,
    reqs,
    goal,
    scope,
    assumptions,
    decisions,
    alternatives,
    procedure,
    method,
    details,
    compat,
    security,
    rollback,
    validation,
    completion,
    oos,
):
    return (
        "\n".join(
            [
                f"# Implementation Procedure: {title}",
                "",
                "## Goal",
                goal,
                "",
                "## Scope",
                scope,
                "",
                "## Assumptions",
                assumptions,
                "",
                "## Design decisions",
                decisions,
                "",
                "## Alternatives considered",
                alternatives,
                "",
                "## Implementation",
                "### Target file",
                f"`{target}`",
                "### Procedure",
                procedure,
                "### Method",
                method,
                "### Details",
                details,
                "",
                "## Compatibility considerations",
                compat,
                "",
                "## Security considerations",
                security,
                "",
                "## Rollback considerations",
                rollback,
                "",
                "## Validation plan",
                validation,
                "",
                "## Completion criteria",
                completion,
                "",
                "## Out of Scope",
                oos,
                "",
                "## Execution Status\n\n"
                "### Execution Status\n"
                "| Step | Description | Status | Started | Completed | Notes |\n"
                "|------|-------------|--------|---------|-----------|-------|\n"
                "| 1 | Implement the change described in Implementation > Procedure/Method/Details | "
                "Pending | — | — | |\n"
                "| 2 | Add or update tests per Validation plan | Pending | — | — | |\n"
                "| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |\n"
                "| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | "
                "— | — | |\n\n"
                "### Blocker Log\n"
                "| Step | Blocker Description | Resolved | Resolution Date |\n"
                "|------|---------------------|----------|-----------------|\n"
                "| — | — | — | — |\n\n"
                "### Work Items Created\n"
                "| Item ID | Related Step | Type | Status | Owner | Due Date |\n"
                "|---------|--------------|------|--------|-------|----------|\n"
                "| — | — | — | — | — | — |\n",
                "## Traceability\n"
                "- **Workflow phase**: plan-to-implementation-procedure\n"
                f"- **Requirement ID**: {reqs}\n"
                f"- **Source issue**: {ISSUE}\n"
                "- **Source requirement**: N/A: no standalone requirement document is generated\n"
                f"- **Source plan**: {PLAN}\n"
                "- **Source implementation procedure**: N/A: this document is the generated "
                "implementation procedure\n"
                f"- **Generated at**: {GEN_AT}\n"
                f"- **Related target files**: {target}",
            ]
        )
        + "\n"
    )


FILES: list[str] = []


def emit(name, text):
    path = Path(f"{PREFIX}_{name}")
    path.write_text(text, encoding="utf-8")
    FILES.append(path.name)


emit(
    "01_scripts_rag_ingestion_ingester.py.md",
    doc(
        "Add `import sqlite3` and widen the `_process_url_groups` except tuple to include "
        "`sqlite3.Error`",
        "scripts/rag/ingestion/ingester.py",
        "REQ-001, REQ-002, REQ-003",
        'Make the ingestion batch honor its documented "log exceptions without stopping" '
        "contract for the whole SQLite error hierarchy: a `sqlite3.Error` on one URL group is "
        "logged and recorded as an unexpected failure, remaining groups still process, and "
        "`check_consistency` still runs (REQ-001, REQ-002).",
        "- One `import sqlite3` addition and one except-tuple extension in "
        "`_process_url_groups`. Logging call, result recording, loop structure, and "
        "`ingest_url_group` itself are untouched.",
        "- `sqlite3.Error` and its subclasses (`OperationalError`, `IntegrityError`, "
        "`DatabaseError`, `ProgrammingError`, `DataError`, `InternalError`, "
        "`NotSupportedError`) derive from `Exception`, not from `OSError`/`RuntimeError`/"
        "`ValueError` (stdlib hierarchy, Plan-verified).\n"
        "- `ChunkFormatError` subclasses `ValueError` (verified `scripts/rag/exceptions.py` "
        "L27), so its current catch path is unaffected by the added category (Plan Reference "
        "Files).\n"
        "- A `sqlite3.Error` reaching the loop means the group's transaction was already "
        "rolled back by `SQLiteHelper._begin_transaction` (verified rollback-on-any-exception "
        "at `scripts/db/helper.py` L219-220), so continuing introduces no partial writes "
        "(Plan Assumptions).\n" + OVERLAP,
        "- Catch the base class `sqlite3.Error` rather than enumerating subclasses as "
        "`check_consistency` does (which also catches `ValueError` for data-shape errors, a "
        "different context): the batch loop wants the whole hierarchy, and the base class is "
        "bounded and intent-revealing (Plan Design/Assumptions).\n"
        "- Widen only at the loop boundary: `ingest_url_group` keeps propagating DB errors to "
        "direct callers, preserving the TestAtomicity contract and fail-fast per-group "
        "semantics (REQ-003).",
        "- Enumerate `OperationalError`/`IntegrityError`/`DatabaseError` like "
        "`document_manager.check_consistency` (verified catch at L136) — rejected: the batch "
        "loop wants the entire hierarchy, and enumeration risks missing a subclass.\n"
        "- Catch `Exception` — forbidden by the Issue's Constraints and rejected: it would "
        "swallow programming errors (Plan Risks).",
        "1. Add `import sqlite3` to the module imports of `scripts/rag/ingestion/"
        "ingester.py` (verified: the module currently has no `sqlite3` import).\n"
        "2. Extend the except tuple `except (OSError, RuntimeError, ValueError):` (verified at "
        "L377) to `except (OSError, RuntimeError, ValueError, sqlite3.Error):`.\n"
        '3. Keep the body unchanged: `logger.exception("ingest_url_group failed: %s", url)` '
        "and `results.append(IngestUrlResult.unexpected_failure(url))` (verified at L378-379).\n"
        "4. Confirm no other catch site in the module is widened (AC-1). The loop docstring at "
        'L370 ("log exceptions without stopping") already states the now-true contract and '
        "needs no change.",
        "Two-line change: one import, one tuple extension. No new helper, no new result type.",
        "- Downstream consumers of `ingest_all` results (counts, diagnostics, the "
        "`check_consistency(embed_failed=...)` aggregation verified at L169) see DB failures "
        "as the existing `unexpected_failure` result kind — no new result type (Plan Design).\n"
        "- `ingest_all` reaches `check_consistency` because the loop no longer aborts on DB "
        "errors (REQ-002).",
        "- No config, service, or deployment change: the existing `rag_ingester` service "
        "restarts through normal deploy (Plan Implementation steps, Phase 4).",
        SECURITY,
        ROLLBACK,
        "- `uv run pytest tests/rag/ingestion/test_rag_ingester.py` — continuation and "
        "boundary tests (procedure _02) pass; all pre-existing tests pass unmodified, "
        "including `TestAtomicity::test_database_failure_during_replacement` (AC-3).\n"
        + STATIC
        + "\n- Diff coverage: `uv run coverage run -m pytest tests/ && uv run "
        "coverage xml && uv run diff-cover coverage.xml --compare-branch=master "
        "--fail-under=90` — new except branch covered.",
        "- The except tuple is `(OSError, RuntimeError, ValueError, sqlite3.Error)`; "
        "`import sqlite3` present; no other catch widened; continuation test green; "
        "TestAtomicity propagation test green unmodified.",
        OOS,
    ),
)
emit(
    "02_tests_rag_ingestion_test_rag_ingester.py.md",
    doc(
        "Add the two-group batch-continuation regression test and the sqlite3 hierarchy "
        "boundary test",
        "tests/rag/ingestion/test_rag_ingester.py",
        "REQ-002, REQ-003",
        "Pin the widened batch boundary with a regression test (first group fails with "
        "`sqlite3.OperationalError`, second group still ingests, `check_consistency` runs) and "
        "a boundary test guarding the error-hierarchy claim inside the suite (REQ-002, "
        "REQ-003, AC-2).",
        "- Two new test functions. All existing tests, including `TestAtomicity::"
        "test_database_failure_during_replacement` (verified at L245, class at L203), stay "
        "unmodified.",
        "- No existing test drives `_process_url_groups`/`ingest_all` with a sqlite3 error: "
        "the only DB-error test targets `ingest_url_group` propagation directly (verified "
        "L272-274 `pytest.raises`), so it is unaffected by the loop-level widening and must "
        "keep passing as-is (AC-3).\n"
        "- The `_make_ingester` fixture pattern (verified at L61: temp dirs plus mocked config "
        "dict) plus the existing `mock_db`/`mock_http_client`/`mock_doc_mgr` fixtures are "
        "reused.\n"
        "- Determinism via patching — no wall-clock or real lock contention (Plan Tests).",
        "- Fail the first group only by wrapping the instance's `ingest_url_group` with a "
        "first-call-raises side effect: `_process_url_groups` calls `self.ingest_url_group`, "
        "so the failure injection stays at the group boundary the test targets and the second "
        "group exercises the normal success path end to end.\n"
        "- Keep the propagation test untouched rather than adapting it: it is the contract "
        "`ingest_url_group` must preserve (REQ-003).",
        "- Patch `TransactionManager._insert_chunks_batch` with a call-count side effect "
        "(pattern precedent verified at L269-274) — viable but couples the test to internal "
        "call order across both groups; the instance-level wrapper is simpler and equally "
        "deterministic. Either satisfies the Plan; the wrapper is preferred.",
        "1. Add `test_sqlite_error_first_group_continues` (new): build an ingester with "
        "`_make_ingester` and two chunk files belonging to two distinct URL groups in "
        "`chunk_dir` (fixture pattern verified at L61 and L132-166 usage). Patch the group "
        "builder or let the two files form two groups naturally.\n"
        "2. Wrap `ingester.ingest_url_group` (new behavior in the test only) so the first call "
        'raises `sqlite3.OperationalError("database is locked")` and later calls delegate to '
        "the real method.\n"
        "3. Run `ingest_all` and assert: two results returned; group 1 is "
        "`IngestUrlResult.unexpected_failure`; group 2 succeeded (`n_success == 1`); `no "
        "exception escapes`; `check_consistency` invoked (assert on the mocked doc manager).\n"
        "4. Assert the `ERROR` log with traceback is emitted for the failed group "
        "(caplog/fixture already used in this suite).\n"
        "5. Add `test_sqlite_error_hierarchy_boundary` (new): assert "
        "`issubclass(sqlite3.OperationalError, sqlite3.Error)` and `not issubclass("
        "sqlite3.Error, (OSError, RuntimeError, ValueError))` — guards the Issue's hierarchy "
        "claim inside the suite (Plan Tests).",
        "Two new test functions in the existing file style (class-organized or module-level, "
        "matching the neighboring test's placement); reuse existing fixtures "
        "`mock_db`/`mock_http_client`/`mock_doc_mgr` where needed.",
        "- `sqlite3` is already imported in the test module (verified at L3); no import "
        "change needed.\n"
        "- The new continuation test depends on procedure _01 landing first; it belongs to "
        "Plan Phase 3 after Phase 2.",
        "- Existing tests keep passing unmodified (AC-3, AC-5); the propagation contract is "
        "not relaxed.",
        "- Test-only change; no production surface.",
        ROLLBACK,
        "- `uv run pytest tests/rag/ingestion/test_rag_ingester.py` — the two new tests pass "
        "against the widened catch (procedure _01) and the continuation test fails against "
        "pre-change code (red-before-green confirmation of the regression).\n"
        "- `uv run pytest tests/rag/ingestion/` green.\n" + STATIC,
        "- Two new tests present and passing; all pre-existing tests unmodified and passing; "
        "new except branch covered by diff-cover.",
        OOS,
    ),
)
emit(
    "03_docs_21_rag_rag_05_04-error-handling-reference.md.md",
    doc(
        "Add the DB-error row to the RagIngester error table",
        "docs/21_rag/rag_05_04-error-handling-reference.md",
        "REQ-004",
        "Record the new explicit catch in the subsystem's error contract: add one row to the "
        "RagIngester error table documenting the `sqlite3.Error` batch behavior (REQ-004, "
        "AC-4).",
        "- One added table row in the `## RagIngester` section. No other table, section, or "
        "page change.",
        '- The Issue\'s "Documentation Impact: None" is incomplete: the RagIngester table '
        "(verified rows: embedding retry, retry-limit, invalid `lang`, invalid `fetched_at`; "
        "section heading at L82, table rows through the `fetched_at` row around L88) has no "
        "database-error row, and the reference is the contract record reviewers consult "
        "(Plan Problem).\n" + OVERLAP,
        '- Docs as contract: the row prevents a future "fix" from re-narrowing the catch '
        "(Plan Design). Row wording mirrors the implemented behavior exactly, in the table's "
        "existing `Error | Action` two-column style.",
        "- Leave the table unchanged since the docstring already promises no-stop — rejected: "
        "the per-component table is the machine-checkable contract record; docstrings alone "
        "proved insufficient (the bug existed despite the docstring).",
        "1. In the `## RagIngester` table, append one row (new):\n"
        "   `| sqlite3.Error during URL group processing (caught by `_process_url_groups()`) "
        "| Skip URL group; `ERROR` (with traceback); continue with remaining groups; "
        "`check_consistency` still runs after the batch |`\n"
        "2. Keep the existing four rows byte-identical.\n"
        "3. Do not touch the `## RagPipeline` table (that is the rag003 Plan's edit region on "
        "this page).",
        "Single Markdown table row in the existing style; no reflow of neighboring rows.",
        "- The row must match implemented behavior after procedure _01 lands; sequence the doc "
        "edit with the code change in the same implementation pass (Plan Phase 4).",
        "- Page is high-churn (30d churn 8 per Plan Affected areas): rebase immediately "
        "before editing and re-verify the table region line numbers.",
        "- Documentation-only change.",
        ROLLBACK,
        "- `rules/toolchain.md` documentation consistency check for the 21_rag domain passes; "
        "the row is present and matches the implemented catch (AC-4).\n"
        "- If the rag003 procedure (implementations/20261027-154425_26_*) has already "
        "renamed the RagPipeline row on this page, rebase before editing (overlap note).",
        "- RagIngester table contains exactly one sqlite3.Error row with the wording above; "
        "RagPipeline table untouched by this procedure.",
        OOS + "\n- Rewording the existing RagIngester rows or the RagPipeline table.",
    ),
)

print(f"filled {len(FILES)} procedure documents")
