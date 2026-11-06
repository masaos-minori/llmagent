# Match _invoke_callback's exception scope to its never-re-raise contract

## Goal
- `DocumentManager._invoke_callback` catches `Exception` (as its docstring already promises),
  so a raising `on_ingest_complete` callback is logged and never breaks `ingest_all`.

## Priority
Low

## Scope
- **In-Scope**: one handler-scope change in `_invoke_callback`; one failure-class regression
  test.
- **Out-of-Scope**: consistency report contents; `check_consistency`'s own try/except scope;
  adding a callback to the CLI path (`ingester.py:409` passes none — unchanged).
- **Dependencies**: none (issue Dependencies N/A). Coordination with
  `plans/20261106-094942_raging002_etag-updated-before-reingestion.md` (co-targets
  `document_manager.py` in a disjoint region — see Design).

## Background
`_invoke_callback` catches only `(TypeError, ValueError)` (`document_manager.py:159`) while its
docstring says "logging any exception without re-raising" (`:155`). It is invoked at
`check_consistency` `:140`, outside that method's try/except (`:134-138`), and
`check_consistency` is called unguarded inside `RagIngester.ingest_all` (`ingester.py:171-175`)
— so any other exception type (e.g. `sqlite3.Error` from a DB-reporting callback) escapes
`ingest_all` after all ingestion already succeeded, and also skips the
`bump_index_generation` step at `ingester.py:181-182`. Verified against HEAD `bdb9bed66` in
Step 2 of this cycle. Latent today: the CLI caller (`ingester.py:409`) passes no callback.

## Problem
A successful ingestion run can crash and misreport its exit status purely because its
completion-notification callback failed — contradicting the never-re-raise contract that the
surrounding reporting code (`check_consistency` DB-error handling, `bump_index_generation`)
already follows.

## Reason for Change
Consistency with the established "ingestion completion must not be broken by reporting
failures" contract and with the method's own docstring (issue Reason for Change).

## Implementation Intent
Change `except (TypeError, ValueError)` to `except Exception` in `_invoke_callback`, keeping the
existing `logger.exception("on_ingest_complete callback failed")` call and message unchanged.

## Requirements
- `REQ-001`: `_invoke_callback` catches `Exception` instead of `(TypeError, ValueError)`
  (`document_manager.py:159`); the `logger.exception` call and its message are unchanged
  (issue Constraints); the broadened catch wraps only the `callback()` invocation (`:158`) —
  `check_consistency` and the ingestion path are untouched. `TypeError` catch coverage is a
  strict superset today, so no existing behavior narrows.
- `REQ-002`: Regression test in `tests/rag/ingestion/test_rag_ingester_callback.py`: callback
  raising `sqlite3.Error` — `ingest_all(force=False, on_ingest_complete=raising_callback)`
  returns its consistency report normally (no exception propagates) and the failure is logged
  (caplog or `logger.exception` patch). Harness reuse: existing fixture pattern
  (`test_rag_ingester_callback.py:57-79` — patched `_process_url_groups` returning `[]`,
  mocked `check_rag_consistency` returning a MagicMock report).
- `REQ-003`: The existing happy-path test (`:81`) stays unchanged and green; `except Exception`
  must pass ruff `BLE001` (selected at `pyproject.toml:106`) — verified empirically in Step 2
  (probe file clean; precedent `orchestrator.py:86`), no suppression comment needed.

## Implementation Target Files
**Freeze status**: Frozen (Step 8b validation passed 20261106-104959 — every row `Verified`).

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/rag/ingestion/document_manager.py` | Modify | Broaden `_invoke_callback` except tuple to `Exception` | REQ-001, REQ-003; AC-1, AC-2 | Narrow catch at `:159` vs docstring `:155`; unguarded call sites at `:140` and `ingester.py:171-175`; pre-bump escape position at `ingester.py:181-182` (checked in Step 2) | `tests/rag/ingestion/test_rag_ingester_callback.py` | Verified |
| `tests/rag/ingestion/test_rag_ingester_callback.py` | Modify | Add the `sqlite3.Error`-callback regression test | REQ-002; AC-1, AC-3 | Single happy-path test at `:81`; reusable fixture harness at `:49-79` (checked in Step 2) | itself | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/rag/ingestion/ingester.py` | `check_consistency` call site (`:171-175`) and the bump consequence (`:181-182`); unchanged by this plan | REQ-001 scope confirmation |
| `scripts/rag/ingestion/orchestrator.py` | `except Exception` + `logger.exception` precedent (`:86`) confirming lint feasibility | REQ-003 |
| `pyproject.toml` | ruff select list incl. `BLE001` (`:106`) — no per-file ignores affect this file | REQ-003 |
| `plans/20261106-094942_raging002_etag-updated-before-reingestion.md` | Co-targets `document_manager.py` (`handle_existing_document` region); ordering in Design | Dependencies |

## Acceptance Criteria
- AC-1 (REQ-001, REQ-002): `ingest_all` with a callback raising `sqlite3.Error` returns its
  consistency report and logs the callback failure; nothing propagates (covered by the new
  test).
- AC-2 (REQ-001, REQ-003): the only code change is the except clause; the `logger.exception`
  message string is byte-identical; ruff reports no BLE001 finding on the file.
- AC-3 (REQ-002, REQ-003): `uv run pytest tests/rag/ingestion/test_rag_ingester_callback.py`
  (old + new tests) and `uv run pytest tests/rag/ingestion` pass; changed lines reach the
  `rules/toolchain.md` diff-cover threshold (≥ 90%).

## Tests
- REQ-002 new: `test_callback_failure_does_not_break_ingest_all` (or equivalent name) —
  `on_ingest_complete` raising `sqlite3.Error("boom")` → `ingest_all` returns the mocked
  report, no exception, one ERROR log record with the existing message.
- Characterization: `test_ingest_all_calls_on_ingest_complete` unchanged and green (pins the
  happy path and the exactly-once call).

## Documentation Impact
N/A: behavior is already documented in the method docstring, which the change makes true
(issue statement confirmed in Step 3 — no `docs/` file describes the callback's catch scope).

## Assumptions
- Catching `Exception` (not `BaseException`) is the intended ceiling: `KeyboardInterrupt` /
  `SystemExit` must still propagate (standard convention, matches `orchestrator.py:86`
  precedent).
- No current production caller depends on callback exceptions propagating (verified in Step 2:
  CLI passes no callback; no other production caller found).

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| — | N/A: no unknowns remain | — | — | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/rag/ingestion/document_manager.py` | Modify | Low | 0 | High (single maintainer) | not applicable (rsynced) |
| `tests/rag/ingestion/test_rag_ingester_callback.py` | Modify | Low | 0 | High (single maintainer) | not applicable (rsynced) |

## Design
- Path A classification: one except-clause widening in one method plus one test; no contract,
  schema, or cross-module change.
- Catch-shape decision: plain `except Exception:` keeping the binding-free
  `logger.exception("on_ingest_complete callback failed")` exactly as today (issue Constraint
  "Keep the `logger.exception` call and its message"). Empirically BLE001-clean under this
  repo's ruff config (Step 2 probe); the bound-variable form (`except Exception as exc`) is not
  needed since `logger.exception` renders the traceback and message itself.
- Why not move the try/except into `check_consistency` or `ingest_all`: the contract lives with
  the callback wrapper (issue AI Instruction "single handler-scope change"); widening at the
  narrowest existing boundary keeps the catch adjacent to the invocation and cannot accidentally
  swallow ingestion errors (issue Constraint 1).
- Interaction with the 002 Plan: 002 edits `DocumentManager.handle_existing_document` (removes
  the pre-commit `_update_etag` call); this plan edits only `_invoke_callback` (`:153-160`).
  Disjoint regions of the same file — implement 002 first to keep same-file edits serialized;
  otherwise a clean rebase either order. Dependency path:
  `plans/20261106-094942_raging002_etag-updated-before-reingestion.md`.
- Consequence note (not a requirement): with the catch widened, the `bump_index_generation`
  step (`ingester.py:181-182`) can no longer be skipped by a callback crash — verified escape
  order in Step 2; no `ingester.py` change is needed for that.
- `scan_change_consumers.py` not run: no persisted schema, public API, or shared-constant
  change; `_invoke_callback` is private with one caller (`check_consistency`, verified in
  Step 2). Historical analysis (Step 3): churn (30d) 0 on both files; single maintainer
  throughout. Operational check: inherited from this batch's `fuser /opt/llm/db/rag.sqlite`
  (no holders). Persisted schema check: N/A — no DDL.
- Validation quality baseline (Step 5): `radon cc` — file has no C-or-worse grade (small
  methods; measured in this batch's ingestion-package scans); `bandit`/`vulture` clean on the
  ingestion package in this batch's scans; re-run at implementation. `pip-audit` N/A: no
  dependency change. Diff-cover current number not measured; ≥ 90% on changed lines required
  at implementation per `rules/toolchain.md`.

## Implementation steps
1. **Phase 1: Failing regression test (RED)**
   - [x] Add the `sqlite3.Error`-callback test to
     `tests/rag/ingestion/test_rag_ingester_callback.py` (REQ-002; must fail against current
     code before Phase 2)
2. **Phase 2: Catch widening (GREEN)**
   - [x] Change `except (TypeError, ValueError)` to `except Exception` in
     `scripts/rag/ingestion/document_manager.py` (`:159`) (REQ-001, REQ-003)
3. **Phase 3: Verification & deploy hand-off**
   - [x] Run the `rules/toolchain.md` gate sequence on the touched files (pytest targeted +
     `tests/rag/ingestion`, ruff — incl. BLE001, mypy, lint-imports, bandit, diff-cover ≥ 90%)
   - [ ] Deploy hand-off: after the change is committed and pushed, `scripts/` sync via
     `skills/deploy/SKILL.md` is the user's decision (approval gate) (REQ-001)

### Release units
**Unit**: callback-catch-widening | **Phases**: 1, 2 | **Reason**: Phase 1 adds a test that fails against the current narrow catch; the suite is green only after Phase 2 widens the catch, so neither phase validates alone.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/rag/ingestion/document_manager.py` | Unit + new regression | `uv run pytest tests/rag/ingestion/test_rag_ingester_callback.py -v` | Raising callback is logged; `ingest_all` returns its report; happy-path test unchanged |
| whole `tests/rag/ingestion` | Regression | `uv run pytest tests/rag/ingestion` | All ingestion tests green |
| `scripts/` touched files | Static gates | `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`, `PYTHONPATH=scripts uv run lint-imports`, `uv run bandit -r scripts/ -c pyproject.toml -ll` | Clean, no BLE001 or other new findings |
| changed lines | Coverage | `uv run coverage run -m pytest tests/` then `uv run coverage xml` and `uv run diff-cover coverage.xml --compare-branch=master` | ≥ 90% on changed lines |

## Risks
- **Risk**: `except Exception` masks a genuine caller bug in the callback (e.g. a wrong
  signature) → **Mitigation**: `logger.exception` records the full traceback at ERROR level
  (unchanged message), so masked failures remain observable; AC-1 test asserts the log record.
- **Risk**: BLE001 finding blocks the gate → **Mitigation**: empirically clean in this repo's
  config (Step 2 probe + `orchestrator.py:86` precedent); if a future ruff version flags the
  binding-free form, bind the exception and pass it through without changing the message.
- **Risk**: same-file conflict with the 002 Plan → **Mitigation**: disjoint methods
  (`_invoke_callback` vs `handle_existing_document`); implement 002 first.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `sqlite3.Error`-callback regression test | Completed | 2026-11-06 | 2026-11-06 | REQ-002 |
| 2 | Widen except clause in `scripts/rag/ingestion/document_manager.py` | Completed | 2026-11-06 | 2026-11-06 | REQ-001, REQ-003 |
| 3 | Gate sequence + deploy hand-off | Completed | 2026-11-06 | 2026-11-06 | REQ-001..003; deploy hand-off pending push |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | N/A: no blocker recorded at plan creation | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| `implementations/20261106-155620_01_scripts_rag_ingestion_document_manager.py.md` | 2 | Procedure | Completed | — | — |
| `implementations/20261106-155620_02_tests_rag_ingestion_test_rag_ingester_callback.py.md` | 1 | Procedure | Completed | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: `issues/20261106-073538_raging012_ingest-callback-narrow-catch.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261106-104959
- **Related target files**: `scripts/rag/ingestion/document_manager.py`,
  `tests/rag/ingestion/test_rag_ingester_callback.py`

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Issue Required Changes bullet 1 + Constraints bullets 1-2; narrow catch verified at `document_manager.py:159`, escape path at `:140` / `ingester.py:171-175` (checked in Step 2) | `scripts/rag/ingestion/document_manager.py` | Phase 2 | AC-1, AC-2 | New regression test | Confirmed by repository evidence |
| REQ-002 | Issue Required Changes bullet 2 + Testing Expectations; single-test coverage verified at `test_rag_ingester_callback.py:81` (checked in Step 2) | `tests/rag/ingestion/test_rag_ingester_callback.py` | Phase 1 | AC-1, AC-3 | New failure-class test | Explicit in issue |
| REQ-003 | Issue Constraints bullet 2; BLE001 feasibility verified via probe and `orchestrator.py:86` precedent (checked in Step 2) | `scripts/rag/ingestion/document_manager.py` | Phase 2 | AC-2 | ruff gate run unchanged-message review | Confirmed by repository evidence |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261106-155620 -->
