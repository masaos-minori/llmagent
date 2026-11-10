## Goal

- Make `WebCrawler.__init__` validate its six required config keys in one up-front pass and raise a single `ValueError` naming every missing key, while every present key keeps its current value (`REQ-001`, `REQ-002`: loud startup rejection, unchanged reads).

## Scope
**Release unit**: N/A: not part of a release unit

- `WebCrawler.__init__` and a new module-level constant in `scripts/rag/ingestion/crawler.py`.

## Assumptions

- Overlap check (Step 2 tool): no findings; no other open Plan targets `crawler.py` (re-verified at execution: the open Plans are adrrev003-006 and none target `crawler.py` in `Implementation Target Files`; `plan_dependency_order.py` overlap notes name no `crawler.py`).
- The six subscripted keys verified this cycle at L60-68: `rag_src_dir`, `crawl_delay`, `max_depth`, `min_chunk`, `fetch_retry`, `target_urls`; all other keys already use `.get()` defaults.
- The mixed access is not triggered today: `config/crawler.toml` defines all six keys (verified: L3/L14/L17/L18/L19/L33), so no shipped behavior changes.
- `ValueError` (not `ConfigMissingError`, not a new class) per the Plan's chosen alternative; no `except KeyError` exists in `scripts/rag/` and `main()` (L182) is the only production constructor site (verified this cycle).

## Design decisions

- Module-level `_REQUIRED_KEYS: tuple[str, ...]` declared just above `WebCrawler` and referenced by the seq-02 test module (REQ-004 needs the tuple reachable); a class attribute would widen the public surface for no benefit.
- The check runs after `cfg` is bound and before the first `cfg[...]` read or any component construction: `missing = [key for key in _REQUIRED_KEYS if key not in cfg]`; on non-empty `missing`, one `ValueError` joining the names in declared order (Plan Design).
- Presence-only validation: coercions, `parse_target_urls`, and the `.get()` defaults stay byte-for-byte unchanged (REQ-002).

## Alternatives considered

- Option 1 (`.get()` with a `WebCrawler` default), reusing `ConfigMissingError`, a new `ConfigKeyMissingError`, validating in `ConfigLoader.load` — all rejected per the Plan Design Alternatives.

## Implementation
### Target file
- `scripts/rag/ingestion/crawler.py`

### Procedure
- Add `_REQUIRED_KEYS` and the single presence check at the top of `__init__`; touch nothing else.

### Method
- Module level, above `class WebCrawler`: `_REQUIRED_KEYS: tuple[str, ...] = ("rag_src_dir", "crawl_delay", "max_depth", "min_chunk", "fetch_retry", "target_urls")`.
- In `__init__` (L56), immediately after `cfg: dict = self.config` (L59): compute the missing list in `_REQUIRED_KEYS` order; `if missing: raise ValueError(f"crawler config is missing required keys: {', '.join(missing)}")`.
- Append a `Raises:` line to the `__init__` docstring stating the `ValueError` for missing required keys.

### Details
- No change to any existing read, coercion, `.get()` default, the component wiring block, `main()`, or `config/crawler.toml`.
- Comments and the error message in English.
- `_rag_src_dir`, `_crawl_delay`, `_fetch_retry` stay assigned-though-unread (UNK-02 out of scope).

## Compatibility considerations

- All test constructor sites pass configs that already contain the six keys (they would fail today's subscripts otherwise), so no fixture changes are expected (Plan Risks mitigation); re-verified at execution: 38 `WebCrawler(` sites across 7 modules in `tests/rag/ingestion` — the Plan's 27/6 count predates `test_crawler_redirects.py` (added 20261109 by ragrev012), whose 5 sites use a `crawl_config` fixture carrying all six keys; `tests/rag/ingestion` must pass unmodified (AC-2).
- `ConfigLoader().load("crawler.toml")` path: the shipped file satisfies the tuple, guaranteed by the seq-02 drift-guard test.

## Security considerations
N/A: validation-only change; the error message names config key names, not values.

## Rollback considerations
N/A: revert the single commit.

## Validation plan

- `uv run pytest tests/rag/ingestion/test_crawler_config_validation.py -v` — new tests (seq-02 document) red on HEAD for missing-key cases, green after this change.
- `uv run pytest tests/rag/ingestion -q` — all existing constructor-site modules green unmodified (AC-2).
- `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`, `uv run bandit -r scripts/ -c pyproject.toml -ll`, `PYTHONPATH=scripts uv run lint-imports`.
- `uv run python tools/check_docstrings.py`, `uv run python tools/check_module_size.py` — no new findings versus baselines.

## Completion criteria

- AC-1: one `ValueError` names every missing key in declared order before any component is constructed. AC-2: no unvalidated subscript remains reachable before the pass, present keys keep their values, all existing tests green.

## Out of Scope

- The new test module (seq-02 document), defaults for optional keys, type/value validation of present keys, removing unread attributes (UNK-02), other components' config access.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261110-125710 | 20261110-125830 | Tests-first order: land the seq-02 test module (red on HEAD) before this step per the Plan's Phase 1 Changed files: scripts/rag/ingestion/crawler.py |
| 2 | Confirm the tests added by the seq-02 document pass | Completed | 20261110-125830 | 20261110-125940 | Tests live in `tests/rag/ingestion/test_crawler_config_validation.py` (own procedure document) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261110-125940 | 20261110-131853 | Gates: ruff format+check clean (crawler.py reformatted only), mypy 1 pre-existing finding scripts/rag/ingestion/ingester.py:462 no-any-return (identical on a HEAD baseline worktree, not introduced here), bandit -ll identical to HEAD baseline (Medium 8 High 39, exit 0), lint-imports 6 contracts kept, check_docstrings OK, check_module_size OK, run_validation_gates fast mode Pass, Not run: ast-grep unavailable (binary not installed). Tests: targeted testmon run 885 passed 574 deselected, full suite 12157 passed 9 skipped. Coverage gate: scripts/rag/ingestion/crawler.py is listed in pyproject [tool.coverage.run] omit, so diff-cover reports no measurable lines in this diff and the gate passes without coverage signal for this file. Docs gate applied via docs/00_index.md row 'crawler.py changes': docs/21_rag/rag_05_04-error-handling-reference.md Crawler section corrected (the claim that all Crawler-level failures are non-fatal at URL granularity no longer covers construction-time config errors), docs/21_rag/rag_02_02_ingestion_pipeline-crawler.md gained section 2.1.2 Configuration Validation At Construction (old 2.1.2 renumbered to 2.1.3, no cross-document section-number references to it). Docs checkers pass: check_docs_quality, check_docs_structure (scoped), check_docs_content_policy, check_docs_japanese, check_metadata_field_policy, check_docs_consistency --domain rag. |

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
- **Requirement ID**: `REQ-001`, `REQ-002` (single required-key validation pass; present-key behavior unchanged)
- **Source issue**: issues/20261108-195932_ragrev019_webcrawler-config-key-access-mixes-required-and-optional-lookups.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261109-103252_ragrev019_webcrawler-config-key-access-mixes-required-and-optional-lookups.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261110-000238
- **Related target files**: `scripts/rag/ingestion/crawler.py`