## Goal

Add `structured_log=True` to `scripts/rag/ingestion/crawler.py`'s `Logger` construction, if the owner rules JSON-lines output was intended (REQ-002, conditional).

## Scope

In scope: this one-line conditional change. Out of scope: `shared/logger.py`'s `structured_log` mechanism itself; the other two scripts (rows 3-4, separate documents).

## Assumptions

- The owner has ruled "enable" (row 1's decision) before this row executes — if the owner rules "intentional" (no change), this row does not apply; skip it.
- No existing consumer of this script's current text-format log output would break from the format change (REQ-003 — to be confirmed before applying, see Details).

## Design decisions

Add the flag at the existing `Logger()` construction call site — no other structural change to this script's logging.

## Alternatives considered

N/A: a single config-flag addition has no meaningful alternative implementation.

## Implementation

### Target file

`scripts/rag/ingestion/crawler.py`

### Procedure

1. Confirm the owner's ruling from row 1 is "enable" before proceeding — do not apply this change speculatively.
2. Check for any existing consumer (dashboard, log parser, other `tools/` script) of `crawl.log`'s current text-format output (REQ-003) — if one exists, confirm it can handle the JSON-lines format change, or coordinate the change with it, before proceeding.
3. Re-confirm the current `Logger` construction line (confirmed at line 36 as of this cycle) immediately before editing.
4. Add `structured_log=True` as a keyword argument to the `Logger(...)` call.

### Method

Single keyword-argument addition to an existing constructor call.

### Details

- Confirmed current line (re-verified this cycle, line 36): `logger = Logger(__name__, "/opt/llm/logs/crawl.log")`.
- After: `logger = Logger(__name__, "/opt/llm/logs/crawl.log", structured_log=True)`.

## Compatibility considerations

Changes this script's log output format from text to JSON-lines — REQ-003's consumer check (Procedure step 2) is the safeguard against breaking an existing downstream consumer.

## Security considerations

N/A: a logging-format change, no new data exposure (the same fields are logged either way; JSON-lines exposes previously-dropped context fields like `session_id`/`rag_query_id`, which were already being computed/passed, not newly collected).

## Rollback considerations

`git revert` the commit, or remove the added keyword argument.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `scripts/rag/ingestion/crawler.py` | Manual | Run the script and inspect `/opt/llm/logs/crawl.log` | Output parses as valid JSON-lines, including `turn_id`/`session_id`/`rag_query_id`/`workflow_id`/`task_id` when present |
| `scripts/rag/ingestion/crawler.py` | Static | `uv run ruff check scripts/rag/ingestion/crawler.py && uv run mypy scripts/rag/ingestion/crawler.py` | Pass |
| Full suite | Regression | `uv run pytest -q` | No new failures |

## Completion criteria

- `crawl.log`'s output is valid JSON-lines including the previously-dropped context fields (AC-2).

## Out of scope

- `shared/logger.py` itself.
- `chunk_splitter.py`/`ingester.py` (rows 3-4).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Conditional on the owner's row-1 ruling being "enable" |
| 2 | Add or update tests per Validation plan | Pending | — | — | Manual JSON-lines output check per Validation plan |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | Covered by row 1's `docs/21_rag/rag_05_3-logging.md` update |

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
- **Related target files**: scripts/rag/ingestion/crawler.py
