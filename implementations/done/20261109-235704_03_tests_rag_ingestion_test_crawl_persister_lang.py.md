## Goal

- Unit-test the `save_http` skip contract: each skip branch returns `None` and creates no file, and the normal path returns an existing `Path` (`REQ-004`: per-branch skip tests).

## Scope
**Release unit**: N/A: not part of a release unit

- New tests in `tests/rag/ingestion/test_crawl_persister_lang.py` only.

## Assumptions

- The skip branches are unreachable from the orchestrator today but reachable through direct `CrawlPersister` construction — `TestMakeCrawlFilePathUniqueness._persister` (L126-127) already builds one directly and is the pattern to reuse (verified this cycle).
- Tests-first (Plan Phase 1): the skip tests are expected to fail against the current `-> Path` return until the seq-01 document lands.

## Design decisions

- One parametrized test for the three skip branches (unsupported `lang`, non-list `code_blocks`, empty content + empty code blocks) plus one normal-path test; assert `None` (or `Path`) and the `rag_src_dir` `*.json` count in the same test to prove "writes nothing".

## Alternatives considered
N/A: test-only row.

## Implementation
### Target file
- `tests/rag/ingestion/test_crawl_persister_lang.py`

### Procedure
- Add a new test class `TestSaveHttpSkipContract` (new) with a parametrized skip test and a normal-path test.

### Method
- Skip test (`test_skip_branches_return_none_and_write_nothing` (new), `@pytest.mark.parametrize` over three argument sets: `lang="de"` with content and `code_blocks=[]`; `lang="en"` with `code_blocks="not-a-list"`; `lang="en"` with `content=""` and `code_blocks=[]`): build the persister with the existing `self._persister(tmp_path)`-style construction, call `save_http`, assert the result is `None`, and assert `rag_src_dir.glob("*.json")` is empty.
- Normal path (`test_normal_path_returns_existing_path` (new)): `save_http(url, title="t", lang="en", content="x", code_blocks=[])` returns a `Path` whose `exists()` is true under `rag_src_dir`.

### Details
- Do not modify the existing `test_simulated_save_writes_one_file_per_url` (it is the AC-2 regression).
- No fixtures beyond `tmp_path`; the Japanese/English text fixtures are irrelevant to these branches.

## Compatibility considerations

- The file's existing classes and helpers are untouched; new class sits alongside `TestMakeCrawlFilePathUniqueness`.

## Security considerations
N/A: test-only.

## Rollback considerations
N/A: revert the commit.

## Validation plan

- `uv run pytest tests/rag/ingestion/test_crawl_persister_lang.py -v` — new tests red on HEAD (skip branches return a `Path`), green after the seq-01 document lands.

## Completion criteria

- AC-4: three parametrized skip cases assert `None` and an empty `rag_src_dir`; the normal-path case asserts an existing `Path`; all pre-existing tests in the file stay green.

## Out of Scope

- `save_http` itself (seq-01 document), the caller-side test (seq-04 document).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the tests per Implementation > Procedure/Method/Details | Completed | 20261110-131239 | 20261110-131239 | Executed and validated: ruff/mypy/lint-imports/bandit clean, targeted + full suite green, diff-cover 100% on changed lines |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261110-131239 | 20261110-131239 | Executed and validated: ruff/mypy/lint-imports/bandit clean, targeted + full suite green, diff-cover 100% on changed lines |

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
- **Requirement ID**: `REQ-004` (per-branch skip unit tests)
- **Source issue**: issues/20261108-195932_ragrev018_save_http-returns-a-path-to-a-file-it-never-wrote-when-it-skips.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261109-102846_ragrev018_save_http-returns-a-path-to-a-file-it-never-wrote-when-it-skips.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261109-235704
- **Related target files**: `tests/rag/ingestion/test_crawl_persister_lang.py`
