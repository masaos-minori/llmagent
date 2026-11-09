## Goal
- `CrawlPersister.save_http` returns `None` on every branch where it writes no file, and `CrawlOrchestrator._process_crawl_url_async` treats `None` as "nothing persisted", so a skipped save can never be read as a written artifact.

## Priority
Low

## Scope
- **In-Scope**:
  - Change the `save_http` return annotation to `Path | None` and return `None` on the unsupported-`lang`, non-list-`code_blocks`, and empty-content skip branches; state the contract in the docstring.
  - Make `_process_crawl_url_async` capture the `save_http` result and, on `None`, skip the persisted-budget increment and link enqueueing.
  - Unit tests for each skip branch and for the normal path, and one caller-side test that a `None` result is not counted against the persisted budget.
- **Out-of-Scope**:
  - The `save` (local-file) method and its `int` return contract.
  - Relaxing or removing the orchestrator's existing pre-validation before `save_http`.
  - Any other persistence method, and the `save_http` write path (payload, filename format, `Path` return).
  - Raising a dedicated error instead of returning `None` (see UNK-01).
- **Dependencies**: N/A: none (the Issue declares none). Same-file note: `scripts/rag/ingestion/orchestrator.py` is also a target of the ragrev011, ragrev012, ragrev013, and ragrev014 plans, which edit other parts of `_process_crawl_url_async` and `crawl_site`; no required order, the overlap judgment is recorded under Assumptions.

## Background
`CrawlPersister.save_http` was extracted from `WebCrawler` to separate persistence from BFS orchestration. It builds the crawl JSON payload and writes it under `rag-src/`. Its return type is `Path`, which callers read as "the file that was just written". The sole production caller is `CrawlOrchestrator._process_crawl_url_async`; the only other callers are two direct calls in `tests/rag/ingestion/test_crawl_persister_lang.py` (checked in Step 3).

## Problem
`save_http` has three early-return skip branches that return `self.make_crawl_filepath(url)` without writing a file: unsupported `lang`, `code_blocks` not a list, and empty content without code blocks. Each returns a `Path` to a file that does not exist. Verified against current source (checked in Step 2): the orchestrator pre-validates two of the three conditions before calling (empty text and code blocks; language outside `en`/`ja`), and `ContentExtractor.extract_content` is annotated to return `tuple[str, str, list[str]]`, so `code_blocks` is always a list. The branches are therefore unreachable today and the defect is a contract smell, not a live bug. The caller also ignores the return value, so a phantom path is not consumed anywhere today.

## Reason for Change
A `Path` return implies a file exists. If the orchestrator pre-checks are relaxed, a second caller is added, or `extract_content` changes its return, a caller could receive a phantom path and treat it as a written artifact, for example by counting it against the persisted budget. Making the skip contract explicit now is cheap because the call site is single and known.

## Implementation Intent
Make the skip outcome part of the type: `save_http` returns `Path | None`, `None` meaning "nothing was written". The orchestrator captures the result and returns early on `None`, the same way its existing pre-validation returns early, so a skipped page is neither counted nor used for link discovery. The write path and its return value stay unchanged.

## Requirements
- `REQ-001`: `CrawlPersister.save_http` is annotated `Path | None`, returns `None` on the unsupported-`lang`, non-list-`code_blocks`, and empty-content branches without computing or returning a file path, and its docstring states that it returns `None` when it skips.
- `REQ-002`: The reachable write path of `save_http` is unchanged: same payload, same filename format, same `Path` return of an existing file.
- `REQ-003`: `_process_crawl_url_async` captures the `save_http` result; when it is `None` the persisted-budget increment and link enqueueing are skipped, and when it is a `Path` the behavior is unchanged.
- `REQ-004`: Unit tests assert, per skip branch, that `save_http` returns `None` and creates no file, and that the normal path returns a `Path` whose file exists.
- `REQ-005`: A caller-side test asserts that a `None` result from `save_http` is not counted against the persisted budget.

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/rag/ingestion/crawl_persister.py` | Modify | `save_http` return annotation to `Path` or `None`; `None` on the three skip branches; docstring states the skip contract | `REQ-001`, `REQ-002` / AC-1, AC-2 | `CrawlPersister.save_http` is annotated `-> Path` and its three skip branches each `return self.make_crawl_filepath(url)` (checked in Step 2) | `tests/rag/ingestion/test_crawl_persister_lang.py` | Verified |
| `scripts/rag/ingestion/orchestrator.py` | Modify | `_process_crawl_url_async` captures the `save_http` result and returns before `budget.persisted += 1` and `enqueue_links` on `None` | `REQ-003` / AC-3 | `_process_crawl_url_async` calls `self._persister.save_http(...)` discarding the result, then runs `budget.persisted += 1` and `self._link_discovery.enqueue_links(...)` (checked in Step 2) | `tests/rag/ingestion/test_crawler_integration.py` | Verified |
| `tests/rag/ingestion/test_crawl_persister_lang.py` | Modify | Add per-branch skip tests (`None` returned, no file created) and a normal-path return test | `REQ-004` / AC-4 | `TestMakeCrawlFilePathUniqueness` already builds `CrawlPersister` directly and calls `save_http`; no test asserts a skip-branch result (checked in Step 3) | `tests/rag/ingestion/test_crawl_persister_lang.py` | Verified |
| `tests/rag/ingestion/test_crawler_integration.py` | Modify | Add a caller-side test that a `None` `save_http` result is not counted against the persisted budget | `REQ-005` / AC-5 | `TestMaxPagesBoundaryCondition` drives `WebCrawler.crawl_site` with `respx` and a `tmp_path` `rag_src_dir` and asserts the persisted-budget stop (checked in Step 3) | `tests/rag/ingestion/test_crawler_integration.py` | Verified |

Rules (see `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan
Freeze) for the full validation procedure):
- One row per file. A directory, glob pattern (`*`, `**`), component/module name, file
  group, or a vague phrase (e.g. "related files", "as necessary", "etc.") MUST NOT
  appear as a row — list each file individually by its exact repository-relative path.
- Record a test, configuration, schema, migration, deployment, or documentation file as
  its own row when it requires modification — do not fold it into the row for the
  source file it accompanies.
- `Validation Status` is `Verified` or `Needs confirmation` per row; every row must be
  `Verified` before this section may be marked `Frozen`.

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same
one-file-per-row discipline as `Implementation Target Files` above — no directories,
glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/rag/ingestion/content_extractor.py` | `extract_content` return annotation proves `code_blocks` is always a list at the call site | `REQ-003` |
| `scripts/rag/ingestion/crawler.py` | `WebCrawler` constructs `CrawlPersister` as `crawl_persister` and passes it to the orchestrator; the caller-side test patches it | `REQ-005` |
| `docs/21_rag/rag_02_06_ingestion_pipeline-supporting-components.md` | Documentation Impact check: confirms no description of `save_http`'s return | `REQ-001` |
| `docs/21_rag/rag_02_02_ingestion_pipeline-crawler.md` | Documentation Impact check: states the persisted-budget behavior the caller change must keep | `REQ-003` |
| `plans/20261108-165922_ragrev011_recrawl-304-drops-subtree.md` | Sibling Plan that records the early returns before `enqueue_links` as its UNK-02; the `None` early return is aligned with it | `REQ-003` |

## Acceptance Criteria
- AC-1 (`REQ-001`): `save_http` returns `None` when `lang` is unsupported, when `code_blocks` is not a list, and when content and code blocks are both empty; its annotation is `Path | None` and its docstring states the skip contract; `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools` passes.
- AC-2 (`REQ-002`): on the normal path `save_http` returns a `Path` whose file exists, with the same payload and filename format as before; the existing `test_simulated_save_writes_one_file_per_url` stays green unmodified.
- AC-3 (`REQ-003`): when `save_http` returns `None`, `_process_crawl_url_async` neither increments `budget.persisted` nor enqueues links; when it returns a `Path`, the persisted count and enqueueing are unchanged (existing budget tests green).
- AC-4 (`REQ-004`): one unit test per skip branch asserts `None` and no file under `rag_src_dir`; one test asserts the normal-path `Path` exists.
- AC-5 (`REQ-005`): a crawl whose `save_http` is patched to return `None` does not reach the persisted-budget stop that a counted page would reach, and does not fetch the page's links.

## Tests
- `REQ-001`/`REQ-004`: parametrized unit test in `tests/rag/ingestion/test_crawl_persister_lang.py` calling `CrawlPersister.save_http` with an unsupported language, a non-list `code_blocks`, and empty content with empty code blocks; asserts `None`, and that `rag_src_dir` holds no `*.json` file.
- `REQ-002`/`REQ-004`: unit test in the same file asserting the normal-path result is an existing `Path` under `rag_src_dir`.
- `REQ-003`/`REQ-005`: async test in `tests/rag/ingestion/test_crawler_integration.py` using the `TestMaxPagesBoundaryCondition` setup with `max_pages` of 1 and `patch.object(crawler.crawl_persister, "save_http", return_value=None)`; asserts the `persisted budget reached` warning is absent and the linked page is not requested. The counted-page variant (unpatched) is already covered by `test_stops_at_max_pages`.
- Static: `uv run ruff check`, `uv run ruff format --check`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`; `uv run pytest tests/rag/ingestion -q`.

## Documentation Impact
N/A: no `docs/*.md` change is required (`REQ-001`). Neither `docs/21_rag/rag_02_06_ingestion_pipeline-supporting-components.md` nor `docs/21_rag/rag_02_02_ingestion_pipeline-crawler.md` describes the return value of `save_http` (`rg` for `save_http`, `CrawlPersister`, and `persisted` in the first returned no match; the second only describes the persisted-page budget, which does not change for written pages) (checked in Step 3). The only documentation change is the `save_http` docstring, which belongs to the code target row.

## Assumptions
- Returning `None` rather than raising is preferred because it matches the current swallow-and-log behavior of the skip branches; the Issue states the same preference and leaves fail-closed to a reviewer (UNK-01).
- On `None` the orchestrator returns before `enqueue_links`, matching its existing pre-validation returns (empty content, unsupported language), which also return before link enqueueing; the skip branches are unreachable today, so no shipped behavior changes (derived from confirmed evidence, see UNK-02).
- `save_http` already logs a warning on each skip branch, so the orchestrator adds no log of its own.
- Existing direct callers in `test_crawl_persister_lang.py` ignore the return value, so the annotation change does not affect them (checked in Step 3).
- Overlap judgment (Step 8b, `tools/check_plan_target_overlaps.py`): `scripts/rag/ingestion/orchestrator.py` is also a target of the ragrev011, ragrev012, ragrev013, and ragrev014 plans, and `tests/rag/ingestion/test_crawler_integration.py` of the ragrev011 and ragrev013 plans; judged compatible with no required order. Each plan edits a different part: ragrev014 the per-URL robots guard at the start of `_process_crawl_url_async`, ragrev011 the fetch-result handling, ragrev012 the arguments of the `save_http` call, ragrev013 the loop exit in `crawl_site`; this plan edits only the code after the `save_http` call. In the shared test file, ragrev011 updates the `fetch_html` tests and ragrev013 adds an in-flight budget test, while this plan adds an independent test that patches `save_http`. If ragrev012 lands first, the capture-and-return is applied to the call as it then stands.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether a skip should return `None` or raise a dedicated error (fail-closed) | Reviewer preference; the Issue prefers `None` | Default is `None`; a raising contract would be a separate Plan because it changes the public contract | False |
| UNK-02 | Whether a page whose save is skipped should still have its links enqueued | Intended behavior of early returns before `enqueue_links` is not decided; ragrev011 records the same question for the existing pre-validation returns as its UNK-02 | Default is parity with the existing returns (no enqueue); revisit together with ragrev011's UNK-02 once the owner decides | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/rag/ingestion/crawl_persister.py` | Modify | Medium (public method return contract; one production caller, two test calls) | 0 | N/A (git-fame not run) | not applicable (rsynced) |
| `scripts/rag/ingestion/orchestrator.py` | Modify | Medium (crawl traversal; `radon`: `_process_crawl_url_async` A (5), `crawl_site` C (11) untouched) | 4 | N/A (git-fame not run) | not applicable (rsynced) |
| `tests/rag/ingestion/test_crawl_persister_lang.py` | Modify | Low | 0 | N/A (git-fame not run) | not applicable (rsynced) |
| `tests/rag/ingestion/test_crawler_integration.py` | Modify | Low | 3 | N/A (git-fame not run) | not applicable (rsynced) |

## Design
Path B (more than 3 target files; the return contract of a public method changes). The Issue named only `test_crawler_integration.py` for tests; verification found that unit tests of `CrawlPersister` live in `tests/rag/ingestion/test_crawl_persister_lang.py`, so skip-branch tests go there and the caller-side test goes to the integration file (corrected from the Issue).

Architecture: `crawl_persister` imports only `rag.ingestion.crawler_utils` and standard/third-party modules; `orchestrator` imports `CrawlPersister`. No new import edge; `lint-imports` reports 6 contracts kept at plan time.

Dependency graph: `save_http` has one production caller (`CrawlOrchestrator._process_crawl_url_async`) and two direct test calls. Consumer scan (`tools/scan_change_consumers.py --seed save_http`): `crawl_persister.py` and `orchestrator.py` are target rows; `tests/rag/ingestion/test_crawl_persister_lang.py` is a target row (its existing calls ignore the result, so they are not affected by the annotation change; the import line is `not affected: import only`). The scan is text-only and its testmon state was stale, so absence of other consumers is not evidence; a mock-based consumer would not be detected, and none was found by reading the test directory.

Historical: `orchestrator.py` had 4 commits in 30 days and four other open Frozen Plans edit it; the change here is confined to the two lines around the `save_http` call.

Change: in `save_http`, the three skip branches return `None` and no longer call `make_crawl_filepath`. In `_process_crawl_url_async`, the result is captured and `if saved is None: return` precedes `budget.persisted += 1` and `enqueue_links`; mypy narrows the `Path | None` through that check. Alternatives: (a) raise a dedicated error on skip, rejected here (changes the public contract; UNK-01); (b) keep returning a `Path` and add a separate `was_written` flag, rejected (a second signal to keep in sync, and the phantom path stays); (c) delete the unreachable guards, rejected (the Issue puts relaxing or removing pre-validation out of scope and the guards defend the public method).

Persisted schema check: not applicable (no DDL, no schema version, no migration).

Validation baseline (checked in Step 5): `radon cc` on the two source targets: `save_http` B (6), `save` B (8), `_process_crawl_url_async` A (5); `vulture --min-confidence 80` on the two source targets: no findings (the repository-wide run reports only findings in other files); `bandit` on the two source targets: no issues; module size `orchestrator.py` 10234 bytes and `crawl_persister.py` 5426 bytes, both under the 24576 byte gate; `diff-cover`: no changed source lines at plan time (clean tree), 90 percent required at implementation per `rules/toolchain.md`.

## Implementation steps
1. **Phase 1: Persister contract and unit tests**
   - [ ] Add the per-branch skip tests and the normal-path test first, and confirm the skip tests fail against the current `Path` return (`REQ-004`; `tests/rag/ingestion/test_crawl_persister_lang.py`).
   - [ ] Change the `save_http` annotation to `Path | None`, return `None` on the three skip branches, and update the docstring; do not touch `save` or the write path; comments and logs in English (`REQ-001`, `REQ-002`; `scripts/rag/ingestion/crawl_persister.py`).
2. **Phase 2: Caller handling and caller-side test**
   - [ ] Add the caller-side test with `save_http` patched to return `None` and confirm it fails against the current unconditional `budget.persisted += 1` (`REQ-005`; `tests/rag/ingestion/test_crawler_integration.py`).
   - [ ] Capture the `save_http` result in `_process_crawl_url_async` and return before the budget increment and `enqueue_links` when it is `None`; keep ruff and mypy clean (`REQ-003`; `scripts/rag/ingestion/orchestrator.py`).
3. **Phase 3: Deployment & Verification**
   - [ ] Hand off to `skills/deploy/SKILL.md` for the `scripts/` change: prerequisite is that the change is committed and pushed first, and deploying is the user's decision (approval gate); then run the validation sequence of `rules/toolchain.md` and confirm the crawl still persists pages (`REQ-002`, `REQ-003`; `scripts/rag/ingestion/crawl_persister.py`, `scripts/rag/ingestion/orchestrator.py`).

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/rag/ingestion/crawl_persister.py` | Unit: skip branches return `None` and write nothing; normal path returns an existing `Path` | `uv run pytest tests/rag/ingestion/test_crawl_persister_lang.py -v` | All pass, including the unmodified `test_simulated_save_writes_one_file_per_url` |
| `scripts/rag/ingestion/orchestrator.py` | Integration: a `None` result is not counted and enqueues nothing; written pages keep the budget behavior | `uv run pytest tests/rag/ingestion/test_crawler_integration.py -v` | New test passes; `TestMaxPagesBoundaryCondition` tests stay green |
| `scripts/rag/ingestion/crawl_persister.py`, `scripts/rag/ingestion/orchestrator.py` | Static | `uv run ruff format scripts/ tests/rag/ingestion`, `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`, `uv run bandit -r scripts/ -c pyproject.toml -ll`, `PYTHONPATH=scripts uv run lint-imports` | No new findings; the optional `Path` result flows through the caller |
| `scripts/rag/ingestion/crawl_persister.py` | Docstring format | `uv run python tools/check_docstrings.py` | No new finding versus the baseline |
| `scripts/rag/ingestion/orchestrator.py` | Module size gate | `uv run python tools/check_module_size.py` | Passes (far below the byte gate) |
| `tests/rag/ingestion/test_crawler_integration.py` | Patch target check | `uv run python tools/check_mock_patch_targets.py` | Passes (`patch.object` on the instance) |
| Changed lines | Coverage | `uv run coverage run -m pytest tests/`, `uv run coverage xml`, `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90` | At least 90 percent on changed lines |

## Risks
- **Risk**: A future caller ignores the `None` result, which is the same as today's ignored result → **Mitigation**: the `Path | None` annotation makes mypy reject use of the result as a `Path` without a check; the caller-side test pins the current caller's handling.
- **Risk**: Four open Frozen Plans (ragrev011, ragrev012, ragrev013, ragrev014) edit `scripts/rag/ingestion/orchestrator.py`, and ragrev012 changes the arguments of the same `save_http` call, so a textual merge conflict is possible → **Mitigation**: the change here is a two-line capture-and-return around that call and does not touch its arguments; `plan-to-implementation-procedure` re-runs the overlap check, and the implementation re-reads the function before editing.
- **Risk**: Returning before `enqueue_links` on `None` could hide a subtree if the branch ever becomes reachable → **Mitigation**: parity with the existing pre-validation returns; the question is recorded as UNK-02 and revisited with ragrev011's UNK-02.
- **Risk**: Blast radius of the contract change is small (one production caller, one test file with two calls, fewer than 10 files and 20 references per `rules/toolchain.md`), so no budget increase is needed → **Mitigation**: re-run `uv run python tools/scan_change_consumers.py --seed save_http` before implementation, because its testmon state was stale.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Persister contract change (optional `Path` return, `None` on skips, docstring) with per-branch unit tests | Pending | — | — | |
| 2 | Orchestrator handles `None` (no budget increment, no enqueue) with caller-side test | Pending | — | — | |
| 3 | Deployment hand-off and verification | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261108-195932_ragrev018_save_http-returns-a-path-to-a-file-it-never-wrote-when-it-skips.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261109-102846
- **Related target files**: `scripts/rag/ingestion/crawl_persister.py`, `scripts/rag/ingestion/orchestrator.py`, `tests/rag/ingestion/test_crawl_persister_lang.py`, `tests/rag/ingestion/test_crawler_integration.py`

### Requirement Traceability
See `templates/requirement-traceability.md` for the canonical column format.

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Issue Problem, Required Changes; `save_http` skip branches and annotation (Step 2) | `scripts/rag/ingestion/crawl_persister.py` | Phase 1 | AC-1 | Per-branch unit test in `tests/rag/ingestion/test_crawl_persister_lang.py`; mypy | Confirmed by repository evidence |
| REQ-002 | Issue Constraints | `scripts/rag/ingestion/crawl_persister.py` | Phase 1 | AC-2 | Normal-path unit test; existing `test_simulated_save_writes_one_file_per_url` | Explicit in issue |
| REQ-003 | Issue Required Changes (caller handling); orchestrator pre-validation returns (Step 2) | `scripts/rag/ingestion/orchestrator.py` | Phase 2 | AC-3 | Caller-side test; existing `TestMaxPagesBoundaryCondition` tests | Derived from confirmed evidence |
| REQ-004 | Issue Testing Expectations; test location corrected by Step 3 | `tests/rag/ingestion/test_crawl_persister_lang.py` | Phase 1 | AC-4 | `uv run pytest tests/rag/ingestion/test_crawl_persister_lang.py -v` | Confirmed by repository evidence |
| REQ-005 | Issue Acceptance Criteria (no caller counts `None`); `TestMaxPagesBoundaryCondition` setup (Step 3) | `tests/rag/ingestion/test_crawler_integration.py` | Phase 2 | AC-5 | `uv run pytest tests/rag/ingestion/test_crawler_integration.py -v` | Derived from confirmed evidence |
