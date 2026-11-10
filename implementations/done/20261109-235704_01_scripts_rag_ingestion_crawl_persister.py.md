## Goal

- Make `CrawlPersister.save_http` return `None` on every branch that writes no file — unsupported `lang`, non-list `code_blocks`, empty content — with the annotation and docstring stating the contract (`REQ-001`, `REQ-002`: explicit skip return).

## Scope
**Release unit**: N/A: not part of a release unit

- `save_http` in `scripts/rag/ingestion/crawl_persister.py`; return contract only.

## Assumptions

- Overlap check (Step 2 tool): `check_plan_target_overlaps.py` reports no findings; the ragrev011-014 plans that also touched `orchestrator.py` are no longer open, so the Plan's same-file note carries no live sequencing dependency.
- The three skip branches are unreachable from the production caller today (orchestrator pre-validates empty content and language; `extract_content` returns `list[str]`), so this is a contract fix with no shipped behavior change (Plan Problem fact, verified this cycle: branches at L120/L123/L126).
- Returning `None` rather than raising is the Plan default (UNK-01, non-blocking, False).

## Design decisions

- Keep the existing per-branch `logger.warning` lines untouched; only the return value and annotation change (Plan Assumptions: the caller adds no log of its own).
- The skip branches stop calling `make_crawl_filepath` (REQ-001 "without computing or returning a file path"); the reachable write path (L128 onward) is byte-for-byte unchanged.

## Alternatives considered

- Raise a dedicated error on skip; a separate `was_written` flag; deleting the unreachable guards — all rejected per the Plan Design Alternatives.

## Implementation
### Target file
- `scripts/rag/ingestion/crawl_persister.py`

### Procedure
- Change the `save_http` return annotation to `Path | None`; make each of the three skip branches return `None`; state the skip contract in the docstring.

### Method
- L116: `-> Path` becomes `-> Path | None`.
- L119-126: each skip branch keeps its `logger.warning` line and replaces `return self.make_crawl_filepath(url)` with `return None`.
- Docstring (L117): append a sentence — returns the written file's `Path`, or `None` when the save is skipped (unsupported `lang`, `code_blocks` not a list, or empty content without code blocks).

### Details
- `save` (L41) and `make_crawl_filepath` (L94) are untouched; payload, filename format, and the normal-path `Path` return (REQ-002) are unchanged.
- Comments and docstring in English per the Plan step wording.

## Compatibility considerations

- The two existing direct calls in `tests/rag/ingestion/test_crawl_persister_lang.py` (`TestMakeCrawlFilePathUniqueness`, L143/L146) ignore the return value and stay green; the sole production caller is updated by the seq-02 document.

## Security considerations
N/A: return-contract change; no new I/O.

## Rollback considerations
N/A: revert the single commit.

## Validation plan

- `uv run pytest tests/rag/ingestion/test_crawl_persister_lang.py -v` — new skip-branch tests (seq-03 document) green after this change; `test_simulated_save_writes_one_file_per_url` unmodified (AC-2).
- `uv run ruff check scripts/`, `uv run ruff format --check`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools` — the widened annotation type-checks at the caller.
- `uv run python tools/check_docstrings.py` — no new finding versus the baseline.

## Completion criteria

- AC-1: annotation is `Path | None`, each skip branch returns `None` with its warning log, docstring states the contract, mypy passes. AC-2: the normal path returns an existing `Path` with unchanged payload and filename format.

## Out of Scope

- Caller handling (seq-02 document), the tests (seq-03/seq-04 documents), `save`, raising instead of `None` (UNK-01).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261110-131239 | 20261110-131239 | Executed and validated: ruff/mypy/lint-imports/bandit clean, targeted + full suite green, diff-cover 100% on changed lines |
| 2 | Confirm the tests added by the seq-03 document pass | Completed | 20261110-131239 | 20261110-131239 | Executed and validated: ruff/mypy/lint-imports/bandit clean, targeted + full suite green, diff-cover 100% on changed lines |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261110-131239 | 20261110-131239 | Executed and validated: ruff/mypy/lint-imports/bandit clean, targeted + full suite green, diff-cover 100% on changed lines |

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
- **Requirement ID**: `REQ-001`, `REQ-002` (explicit `None` skip return; unchanged write path)
- **Source issue**: issues/20261108-195932_ragrev018_save_http-returns-a-path-to-a-file-it-never-wrote-when-it-skips.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261109-102846_ragrev018_save_http-returns-a-path-to-a-file-it-never-wrote-when-it-skips.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261109-235704
- **Related target files**: `scripts/rag/ingestion/crawl_persister.py`
