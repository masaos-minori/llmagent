## Goal

- Make `CrawlOrchestrator._process_crawl_url_async` capture the `save_http` result and return before the persisted-budget increment and link enqueueing when it is `None` (`REQ-003`: a skipped save is never counted).

## Scope
**Release unit**: N/A: not part of a release unit

- The `save_http` call site region in `_process_crawl_url_async` in `scripts/rag/ingestion/orchestrator.py`; two-line capture-and-return only.

## Assumptions

- Overlap check (Step 2 tool): no findings this cycle; the Plan's ragrev011-012-013/014 same-file note (shared `orchestrator.py`) is historical — those plans are no longer open. This document still edits only the code after the `save_http` call (L267-278 verified), per the Plan's overlap judgment.
- The existing pre-validation returns (empty content L257-259, unsupported language L262-264) already return before `enqueue_links`; the `None` early return mirrors them (Plan Assumptions; UNK-02 default parity, non-blocking).
- `save_http` already logs a warning on each skip branch, so the orchestrator adds no log of its own.

## Design decisions

- `saved = self._persister.save_http(...)` then `if saved is None: return` (Plan Design): mypy narrows `Path | None` through the check; no other restructuring of `_process_crawl_url_async`.

## Alternatives considered

- Counting the page but skipping only enqueueing, or passing a `was_written` flag: rejected — a skip must neither consume budget nor trigger link discovery (AC-3).

## Implementation
### Target file
- `scripts/rag/ingestion/orchestrator.py`

### Procedure
- Capture the return of the `self._persister.save_http(...)` call (L267-276) and return early on `None` before `budget.persisted += 1` (L277) and `self._link_discovery.enqueue_links(...)` (L278).

### Method
- L267: `self._persister.save_http(` becomes `saved = self._persister.save_http(`.
- After the call block: `if saved is None: return` — no log, no budget change, no enqueue.
- L277-278 unchanged for the `Path` case.

### Details
- No other lines of `_process_crawl_url_async` or `crawl_site` are touched; the `save_http` arguments are not modified (the historical ragrev012 concern does not apply — that change is already landed).
- Comments in English.

## Compatibility considerations

- Existing `TestMaxPagesBoundaryCondition` tests exercise the written-page path (unpatched `save_http` returns `Path`), so their budget assertions stay green (AC-3).
- Depends on the seq-01 document landing first: the caller must not compare against a still-`Path`-only return.

## Security considerations
N/A: control-flow change around an existing call.

## Rollback considerations
N/A: revert the single commit.

## Validation plan

- `uv run pytest tests/rag/ingestion/test_crawler_integration.py -v` — new caller-side test (seq-04 document) green after this change; `TestMaxPagesBoundaryCondition` tests stay green (AC-3).
- `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`, `PYTHONPATH=scripts uv run lint-imports`.
- `uv run python tools/check_module_size.py` — passes (module far below the byte gate).

## Completion criteria

- AC-3: on `None` neither `budget.persisted` increments nor links enqueue; on `Path` behavior is byte-identical to before; static gates clean.

## Out of Scope

- The `save_http` contract itself (seq-01 document), the tests (seq-03/seq-04 documents), the pre-validation guards, UNK-02 (enqueue-on-skip policy).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | After the seq-01 document (Plan phase order); the seq-04 test lands red before this step per Plan Phase 2 |
| 2 | Confirm the tests added by the seq-04 document pass | Pending | — | — | Tests live in `tests/rag/ingestion/test_crawler_integration.py` (own procedure document) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-003` (caller treats a `None` save result as no persistence)
- **Source issue**: issues/20261108-195932_ragrev018_save_http-returns-a-path-to-a-file-it-never-wrote-when-it-skips.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261109-102846_ragrev018_save_http-returns-a-path-to-a-file-it-never-wrote-when-it-skips.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261109-235704
- **Related target files**: `scripts/rag/ingestion/orchestrator.py`
