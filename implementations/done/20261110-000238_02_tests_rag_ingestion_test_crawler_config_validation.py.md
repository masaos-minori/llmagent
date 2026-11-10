## Goal

- New test module asserting the missing-required-key outcomes of `WebCrawler.__init__` (single key, several keys, none) and guarding that the shipped `config/crawler.toml` defines every required key (`REQ-003`, `REQ-004`: validation tests + drift guard).

## Scope
**Release unit**: N/A: not part of a release unit

- Create `tests/rag/ingestion/test_crawler_config_validation.py` (new file); no other file is touched.

## Assumptions

- The module does not exist today (verified: `tests/rag/ingestion/` holds no module of this name).
- Tests-first (Plan Phase 1): the module is red on HEAD until the seq-01 document lands; because the tests import `_REQUIRED_KEYS` (created by seq-01), HEAD fails at collection with an `ImportError` rather than the bare `KeyError` the Plan text anticipated.
- The required-key names come from `crawler.py`'s `_REQUIRED_KEYS` tuple (defined by the seq-01 document); the tests import it instead of restating the list, so the parametrization and the drift guard both track the single declaration.

## Design decisions

- One complete-config builder (dict covering the six required keys, `rag_src_dir` from `tmp_path`, `target_urls` = `[]` — the shape proven to construct today by the `_config` helper in `test_crawl_persister_lang.py`) shared by all four test groups.

## Alternatives considered
N/A: test-only row.

## Implementation
### Target file
- `tests/rag/ingestion/test_crawler_config_validation.py`

### Procedure
- Create the module with four tests: parametrized single-key removal, multi-key removal, complete-config construction, and the shipped-file drift guard.

### Method
- `_complete_config(tmp_path: Path) -> dict` (new helper): `{"rag_src_dir": str(tmp_path / "rag-src"), "crawl_delay": 0, "max_depth": 1, "min_chunk": 0, "fetch_retry": 1, "target_urls": []}`.
- `test_each_required_key_missing` (new): `@pytest.mark.parametrize("key", _REQUIRED_KEYS)`; copy the complete config, `del cfg[key]`, `pytest.raises(ValueError, match=key)` around `WebCrawler(config=cfg)`.
- `test_several_missing_keys_named_in_declared_order` (new): remove `rag_src_dir` and `min_chunk`; assert one `ValueError` whose message contains both names and `msg.index("rag_src_dir") < msg.index("min_chunk")` (declared order).
- `test_complete_config_constructs` (new): `WebCrawler(config=_complete_config(tmp_path))` succeeds and `crawler._target_urls == []` (parsing behavior unchanged).
- `test_shipped_crawler_toml_covers_required_keys` (new): `tomllib.load` on `Path(__file__).resolve().parents[3] / "config" / "crawler.toml"`; assert `set(_REQUIRED_KEYS) <= set(data.keys())`.

### Details
- Imports: `from rag.ingestion.crawler import WebCrawler, _REQUIRED_KEYS` (the repo's `tests/rag/ingestion` modules import the `rag.*` surface, matching `test_crawl_persister_lang.py`).
- No HTTP mocking, no fixtures beyond `tmp_path`; the tests only construct (the constructor wires components but starts no I/O — same as existing constructor-site tests).

## Compatibility considerations

- The drift-guard test depends on the shipped `config/crawler.toml` staying as-is (Plan Out-of-Scope: the file is not modified); it reads, never writes.
- The existing constructor-site modules (`test_robots.py`, `test_ingestion_freshness.py`, `test_crawler_retry_boundary.py`, `test_crawler_integration.py`, `test_crawl_persister_lang.py`, `test_crawler_targets_file.py`, `test_crawler_redirects.py` — added 20261109 by ragrev012; re-verified at execution, the earlier name `test_crawl_persister_targets_file.py` does not exist) are untouched and must stay green.

## Security considerations
N/A: test-only.

## Rollback considerations
N/A: delete the new file / revert the commit.

## Validation plan

- `uv run pytest tests/rag/ingestion/test_crawler_config_validation.py -v` — red on HEAD before the seq-01 code change lands (collection fails on the `_REQUIRED_KEYS` import); after seq-01 lands, all four tests are green, the missing-key cases raising `ValueError`.
- `uv run pytest tests/rag/ingestion -q` — whole directory green unmodified (AC-2).

## Completion criteria

- AC-3: six single-key cases, a multi-key case, and a complete-config case are green. AC-4: the drift guard passes against the shipped `config/crawler.toml`.

## Out of Scope

- `crawler.py` itself (seq-01 document), type/value validation of present keys, `config/crawler.toml` changes.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Create the test module per Implementation > Procedure/Method/Details | Completed | 20261110-125634 | 20261110-125710 | Land before the seq-01 code change (red-first, Plan Phase 1) Red-first on HEAD confirmed: collection fails with ImportError on _REQUIRED_KEYS (created by seq-01); expected per corrected Validation plan |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261110-125940 | 20261110-131853 | Full green requires the seq-01 document landed 9 tests pass after the seq-01 change landed. tests/rag/ingestion unchanged suite: 354 passed. Drift guard green post-implementation as corrected in the Validation plan. ruff and mypy clean on the new module, mock-patch-targets and check_docstrings pass. Coverage note: crawler.py is in the pyproject coverage omit list, so this module adds unit coverage that diff-cover does not measure. |

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
- **Requirement ID**: `REQ-003`, `REQ-004` (missing-key tests; shipped-file drift guard)
- **Source issue**: issues/20261108-195932_ragrev019_webcrawler-config-key-access-mixes-required-and-optional-lookups.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261109-103252_ragrev019_webcrawler-config-key-access-mixes-required-and-optional-lookups.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261110-000238
- **Related target files**: `tests/rag/ingestion/test_crawler_config_validation.py`