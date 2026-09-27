## Goal

Add `structured_log=True` to `scripts/rag/ingestion/ingester.py`'s `Logger` construction, if the owner rules JSON-lines output was intended (REQ-002, conditional).

## Scope

In scope: this one-line conditional change. Out of scope: `shared/logger.py` itself; the other two scripts (rows 2-3).

## Assumptions

- The owner has ruled "enable" (row 1's decision) before this row executes.
- No existing consumer of this script's current text-format log output would break from the format change (REQ-003).

## Design decisions

Add the flag at the existing `Logger()` construction call site — no other structural change.

## Alternatives considered

N/A: a single config-flag addition has no meaningful alternative.

## Implementation

### Target file

`scripts/rag/ingestion/ingester.py`

### Procedure

1. Confirm the owner's ruling from row 1 is "enable" before proceeding.
2. Check for any existing consumer of `ingest.log`'s current text-format output (REQ-003) before proceeding.
3. Re-confirm the current `Logger` construction line (confirmed at line 32 as of this cycle) immediately before editing.
4. Add `structured_log=True` as a keyword argument to the `Logger(...)` call.

### Method

Single keyword-argument addition to an existing constructor call.

### Details

- Confirmed current line (re-verified this cycle, line 32): `logger = Logger(__name__, "/opt/llm/logs/ingest.log")`.
- After: `logger = Logger(__name__, "/opt/llm/logs/ingest.log", structured_log=True)`.

## Compatibility considerations

Changes this script's log output format from text to JSON-lines — REQ-003's consumer check is the safeguard.

## Security considerations

N/A: logging-format change only, same fields either way.

## Rollback considerations

`git revert` the commit, or remove the added keyword argument.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `scripts/rag/ingestion/ingester.py` | Manual | Run the script and inspect `/opt/llm/logs/ingest.log` | Output parses as valid JSON-lines, including the expected context fields when present |
| `scripts/rag/ingestion/ingester.py` | Static | `uv run ruff check scripts/rag/ingestion/ingester.py && uv run mypy scripts/rag/ingestion/ingester.py` | Pass |
| Full suite | Regression | `uv run pytest -q` | No new failures |

## Completion criteria

- `ingest.log`'s output is valid JSON-lines including the previously-dropped context fields (AC-2).

## Out of scope

- `shared/logger.py` itself.
- `crawler.py`/`chunk_splitter.py` (rows 2-3).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260927-164500 | 20260927-164500 | Owner ruled "enable" (via AskUserQuestion). REQ-003 consumer check: `ingest.log` is shared with 6 other writers (`chunk_grouping.py`, `document_manager.py`, `etag_manager.py`, `transaction_commit.py`, `embedding.py`, `file_routing.py`, out of scope for this row) — no `tools/` reader found; owner accepted the resulting mixed-format consequence for this shared log file |
| 2 | Add or update tests per Validation plan | Completed | 20260927-164500 | 20260927-164500 | Manual smoke-test of `Logger(structured_log=True)` end-to-end confirms valid JSON-lines output with all 5 context fields present; targeted suite `tests/rag/ingestion/` (165 tests) passes |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260927-164500 | 20260927-164500 | ruff/bandit clean. mypy: 1 pre-existing unused-`type:ignore` finding at line 340, confirmed present before this edit too (git stash check) — unrelated. lint-imports: pre-existing unrelated `shared`→`agent` violation. Full suite: 14 failed (all eventbus/orchestrator/docs_quality, unrelated to this change), 7990 passed, 24 skipped |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260927-164500 | 20260927-164500 | Covered by row 1's `docs/21_rag/rag_05_3-logging.md` update |

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
- **Requirement ID**: REQ-002, REQ-003
- **Source issue**: issues/done/20260927-120057_nc039_decide-whether-rag-ingestion-scripts-should-adopt-structured-logging.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260927-121739_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260927-124916
- **Related target files**: scripts/rag/ingestion/ingester.py
