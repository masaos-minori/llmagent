## Goal
- `WebCrawler.__init__` validates its required config keys in one up-front pass and raises a single error that names every missing key, instead of an opaque `KeyError` from the first missing subscript, while every present key keeps its current value.

## Priority
Low

## Scope
- **In-Scope**:
  - One validation pass at the start of `WebCrawler.__init__` over the required keys (`rag_src_dir`, `crawl_delay`, `max_depth`, `min_chunk`, `fetch_retry`, `target_urls`), raising one `ValueError` that lists all missing keys.
  - A new unit-test module for the missing-key outcomes and for the shipped `config/crawler.toml` still defining every required key.
- **Out-of-Scope**:
  - Config access in any other component (`HttpFetcher`, `CrawlOrchestrator`, `CrawlPersister`, `LinkDiscovery`).
  - Changing default values of the optional keys, adding or removing config keys, and `config/crawler.toml`.
  - Type or value validation of present keys (a key that is present with a wrong value keeps today's behavior).
  - Removing `WebCrawler` attributes that are assigned but never read (see UNK-02).
- **Dependencies**: N/A: none (the Issue declares none). No other open Plan targets `scripts/rag/ingestion/crawler.py` (checked in Step 8b).

## Background
`WebCrawler.__init__` reads its settings from a config dict. The component classes it wires (`HttpFetcher`, `CrawlOrchestrator`, `CrawlPersister`) read config with `config.get(key, default)`. `WebCrawler.__init__` mixes subscript access for six keys with `.get()` for the rest. The shipped `config/crawler.toml` defines all six subscripted keys, so the mixed access is not triggered today (checked in Step 2).

## Problem
A config dict missing one of `rag_src_dir`, `crawl_delay`, `max_depth`, `min_chunk`, `fetch_retry`, or `target_urls` raises a bare `KeyError` naming only the first missing key, at startup, with no indication that it is a configuration error. Facts found while verifying (checked in Step 2) that the Issue does not state: (1) the component classes already carry their own defaults for the same keys and those defaults differ from the shipped values and from each other: `CrawlOrchestrator` defaults `crawl_delay` and `max_depth` to 0 (the shipped file sets 1.5 and 3), and `CrawlPersister` defaults `rag_src_dir` to `rag-src` (the shipped file sets an absolute path); (2) `WebCrawler` passes its own `max_depth` to `LinkDiscovery` while the orchestrator reads `max_depth` again from the same dict, so a second default in `WebCrawler` could make the two disagree; (3) `WebCrawler` assigns `_rag_src_dir`, `_crawl_delay`, and `_fetch_retry` but nothing in `crawler.py` reads them, so for those keys the requirement is enforced only by this subscript.

## Reason for Change
A missing required key is a startup configuration error and should say so, naming every missing key at once. Normalizing now is cheap before more keys are added, and the project's fail-fast rule (`skills/DESIGN.md` Pythonic safety constraints, "Use fail-fast for unknown tool names, tiers, or metadata — never fail-open") and its config-loader convention (`rules/coding.md` Type-coercion policy: a missing key without a declared default is rejected) both point to rejecting rather than defaulting.

## Implementation Intent
Choose the Issue's option 2: keep the six keys required and check them once, up front, before anything is read or constructed. Option 1 (all `.get()` with defaults) is rejected here because the keys have no single correct default: giving `WebCrawler` a default would add a third, possibly different value beside the orchestrator's and the persister's, and a missing `max_depth` would then be applied inconsistently between `LinkDiscovery` and the orchestrator. After the validation pass, the existing reads and coercions stay as they are, so present keys keep exactly their current values.

## Requirements
- `REQ-001`: `WebCrawler.__init__` runs one validation pass over a declared tuple of required keys before reading any key or constructing any component, and raises a single `ValueError` whose message names every missing key in declared order.
- `REQ-002`: Behavior for present keys is unchanged: same coercions, same `parse_target_urls` handling of `target_urls`, same `.get()` defaults for the optional keys, no change to `config/crawler.toml`.
- `REQ-003`: Unit tests assert the outcome for a config missing each required key individually, for a config missing several keys (all named in the message), and for a complete config (constructs normally).
- `REQ-004`: A unit test asserts that the shipped `config/crawler.toml` defines every key in the required tuple, so the tuple and the shipped file cannot drift apart unnoticed.

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/rag/ingestion/crawler.py` | Modify | Declare the required-key tuple and add the single validation pass at the top of `WebCrawler.__init__`; existing reads and coercions unchanged | `REQ-001`, `REQ-002` / AC-1, AC-2 | `WebCrawler.__init__` subscripts `rag_src_dir`, `crawl_delay`, `max_depth`, `min_chunk`, `fetch_retry`, and `target_urls` and uses `.get()` for the other keys (checked in Step 2) | `tests/rag/ingestion/test_crawler_config_validation.py` | Verified |
| `tests/rag/ingestion/test_crawler_config_validation.py` | Create | New file: missing-key outcomes (single, several, none) and the shipped-`config/crawler.toml` drift guard | `REQ-003`, `REQ-004` / AC-3, AC-4 | New file; the containing directory `tests/rag/ingestion/` exists and holds no module of this name (checked in Step 3); `config/crawler.toml` defines all six required keys (checked in Step 2) | `tests/rag/ingestion/test_crawler_config_validation.py` | Verified |

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
| `config/crawler.toml` | Shipped values for every required key; the drift-guard test reads it | `REQ-002`, `REQ-004` |
| `scripts/rag/ingestion/orchestrator.py` | Its own `config.get` defaults for `crawl_delay` and `max_depth` differ from the shipped values; it re-reads `max_depth` from the same dict | `REQ-001`, `REQ-002` |
| `scripts/rag/ingestion/crawl_persister.py` | Its own `config.get` default for `rag_src_dir` | `REQ-001`, `REQ-002` |
| `scripts/rag/ingestion/crawler_utils.py` | `parse_target_urls` semantics must stay identical | `REQ-002` |
| `tests/rag/ingestion/test_crawler_integration.py` | Holds the `mock_config` fixture shape and the `max_pages` fallback test that must stay green | `REQ-002`, `REQ-003` |
| `docs/21_rag/rag_02_02_ingestion_pipeline-crawler.md` | Documentation Impact check: confirms no per-key defaults are documented | `REQ-002` |
| `docs/21_rag/rag_05_01-configuration-reference.md` | Documentation Impact check: lists crawler keys without defaults | `REQ-002` |

## Acceptance Criteria
- AC-1 (`REQ-001`): constructing `WebCrawler` with a config missing one required key raises `ValueError` whose message names that key; with several missing, one error names all of them in declared order; no component is constructed before the check.
- AC-2 (`REQ-002`): `WebCrawler.__init__` has no unvalidated subscript access (every `cfg[...]` follows the single validation pass), present keys keep their values, and all existing tests under `tests/rag/ingestion` pass unmodified.
- AC-3 (`REQ-003`): the new tests cover each of the six keys missing individually, a multi-key omission, and a complete config.
- AC-4 (`REQ-004`): the shipped `config/crawler.toml` contains every key in the required tuple.

## Tests
- `REQ-001`/`REQ-003`: parametrized test over the six required keys; each case removes one key from a complete config and asserts `ValueError` naming it (`pytest.raises` with `match`).
- `REQ-001`/`REQ-003`: one test removing several keys, asserting every name appears in the message in declared order.
- `REQ-003`: one test with a complete config asserting construction succeeds and `_target_urls` is parsed as before.
- `REQ-004`: one test loading `config/crawler.toml` with `tomllib` and asserting the required tuple is a subset of its keys.
- `REQ-002`: the existing constructor sites in `test_robots.py`, `test_ingestion_freshness.py`, `test_crawler_retry_boundary.py`, `test_crawler_integration.py`, `test_crawl_persister_lang.py`, and `test_crawler_targets_file.py` run unmodified.
- Static: `uv run ruff check`, `uv run ruff format --check`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`; `uv run pytest tests/rag/ingestion -q`.

## Documentation Impact
N/A: no `docs/*.md` change is required (`REQ-002`). No default is introduced, and neither `docs/21_rag/rag_02_02_ingestion_pipeline-crawler.md` (it describes `max_depth` only as the traversal bound) nor `docs/21_rag/rag_05_01-configuration-reference.md` (it lists the crawler keys without defaults and its crawler key table is generated from `config/crawler.toml` by `tools/generate_reference_table.py`, not from code defaults) documents per-key defaults that could drift (checked in Step 2). The new error is documented by the `__init__` docstring, which belongs to the code target row.

## Assumptions
- Option 2 is chosen as the Plan's design from the evidence in Problem and Implementation Intent; the Issue leaves the preference open (UNK-01) and permits either option.
- The required set stays exactly the six keys the Issue lists, because adding or removing config keys is out of scope; `rag_src_dir`, `crawl_delay`, and `fetch_retry` stay required even though `crawler.py` does not read their stored attributes (UNK-02).
- `ValueError` is the error type: the config loaders already signal configuration problems with `ValueError` (the `Config*Error` classes in `scripts/shared/config_errors.py` subclass it), and `parse_target_urls` raises it for a bad `target_urls`. `ConfigMissingError` is not reused because its contract is a missing config file. No new exception class is added.
- Validation checks key presence only; a key present with `None` or a wrong type behaves as today (out of scope).
- No code in `scripts/rag/` catches `KeyError` around the constructor, and `main()` is the only production constructor site and does not handle either exception, so changing the exception type affects no handler (checked in Step 3).
- Overlap judgment (Step 8b, `tools/check_plan_target_overlaps.py`): no finding names `scripts/rag/ingestion/crawler.py` or the new test module; the other Frozen Plans that mention `crawler.py` do so only as a reference file.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether the owner prefers silent defaults (option 1) or loud rejection (option 2) for genuinely required keys such as `rag_src_dir` and `target_urls` | Owner preference; the Issue marks it `Needs confirmation` | Default is option 2, backed by the conflicting component defaults and the fail-fast and config-loader conventions; choosing option 1 would first require one agreed default per key shared by `WebCrawler`, `CrawlOrchestrator`, and `CrawlPersister`, which is a separate Plan | False |
| UNK-02 | Whether the `WebCrawler` attributes `_rag_src_dir`, `_crawl_delay`, and `_fetch_retry`, which nothing in `crawler.py` reads, should be removed and their keys left to the components that consume them | Intended ownership of these keys is not recorded | Out of scope here (`AGENTS.md` Global Rule 5); raise as a separate Issue if the owner wants the cleanup | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/rag/ingestion/crawler.py` | Modify | Medium (public constructor failure type; one production constructor site, 27 test constructor sites in 6 test modules; `radon`: `WebCrawler.__init__` A (3)) | 1 | High (39 of 40 commits in the last year carry name variants of one author; merging the variants is an assumption) | not applicable (rsynced) |
| `tests/rag/ingestion/test_crawler_config_validation.py` | Create | Low | N/A | N/A | not applicable (rsynced) |

## Design
Path B (the failure type of the public `WebCrawler` constructor changes, observable at startup; classified Path B when unsure per `skills/issue-to-plan/SKILL.md` Routing). Two target files.

Architecture: `crawler.py` imports the `rag.ingestion` components, `shared.config_loader`, and `shared.logger`; the change adds no import. `lint-imports` reports 6 contracts kept at plan time (run in the ragrev018 cycle on the same unchanged `scripts/` tree).

Dependency graph: `WebCrawler` has one production constructor site (`main()` in `crawler.py`) and 27 constructor sites in 6 test modules (`rg -c "WebCrawler\("`, per `rules/toolchain.md` Impact-radius check: 7 files and 28 references in total, above the 20-reference rule of thumb, recorded here and under Risks). Every one of those sites passes a config that already contains the six required keys, because the current subscripts would fail otherwise, so none is expected to change. Consumer scan (`tools/scan_change_consumers.py --seed WebCrawler`): scripts candidates are the component modules' docstrings and `crawler.py` itself, doc candidates are descriptive mentions, and the test candidates are the 6 modules above; the scan is text-only and its testmon state was stale.

Historical: `crawler.py` had 1 commit in 30 days; no other open Plan targets it.

Change: add a module-level or class-level tuple of the six required key names, and at the top of `__init__`, after `cfg` is bound, collect the keys absent from `cfg` in declared order and raise one `ValueError` naming them all. The remaining reads stay as they are; the `cfg[...]` subscripts that follow are covered by the validation pass, which the Issue's second option and acceptance criterion permit. The tuple is reachable by the tests so that REQ-004 can compare it with the shipped file.

Alternatives: (a) option 1, `.get()` with defaults for all keys, rejected (no single correct default; a third default beside the orchestrator's and persister's, and `LinkDiscovery` and the orchestrator could then disagree on `max_depth`; it also hides misconfiguration); (b) reuse `ConfigMissingError`, rejected (its contract is a missing config file); (c) a new `ConfigKeyMissingError` class in `shared`, rejected (a new shared symbol for one caller, beyond the Issue's scope); (d) validate in `ConfigLoader.load`, rejected (changes every config consumer; Issue puts other components out of scope). Chosen: one presence check with `ValueError`.

Persisted schema check: not applicable (no DDL, no schema version, no migration).

Validation baseline (checked in Step 5): `radon cc` on `crawler.py`: `WebCrawler.__init__` A (3), `main` C (11) untouched; `vulture --min-confidence 80` on `crawler.py`: no findings; `bandit` on `crawler.py`: no issues; module size `crawler.py` 9622 bytes, under the 24576 byte gate; `diff-cover`: no changed source lines at plan time, 90 percent required at implementation per `rules/toolchain.md`.

## Implementation steps
1. **Phase 1: Validation pass and tests**
   - [ ] Write the new test module first (missing-key parametrized, multi-key, complete config, shipped-file drift guard) and confirm the missing-key tests fail against the current bare `KeyError` (`REQ-003`, `REQ-004`; `tests/rag/ingestion/test_crawler_config_validation.py`).
   - [ ] Add the required-key tuple and the single validation pass at the top of `WebCrawler.__init__`; leave every existing read, coercion, and the `parse_target_urls` call untouched; comments and messages in English; ruff and mypy clean (`REQ-001`, `REQ-002`; `scripts/rag/ingestion/crawler.py`).
2. **Phase 2: Deployment & Verification**
   - [ ] Hand off to `skills/deploy/SKILL.md` for the `scripts/` change: prerequisite is that the change is committed and pushed first, and deploying is the user's decision (approval gate); then run the validation sequence of `rules/toolchain.md`, run the six existing constructor-site test modules, and confirm `uv run python -m rag.ingestion.crawler --help` still starts with the shipped `crawler.toml` (`REQ-001`, `REQ-002`; `scripts/rag/ingestion/crawler.py`).

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tests/rag/ingestion/test_crawler_config_validation.py` | Unit: each required key missing, several missing, complete config, shipped-file drift guard | `uv run pytest tests/rag/ingestion/test_crawler_config_validation.py -v` | New tests fail on HEAD for the missing-key cases and pass after the change |
| `scripts/rag/ingestion/crawler.py` | Regression across all constructor sites | `uv run pytest tests/rag/ingestion -q` | All pass unmodified, including `test_max_pages_fallback_default` |
| `scripts/rag/ingestion/crawler.py` | Static | `uv run ruff format scripts/ tests/rag/ingestion`, `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`, `uv run bandit -r scripts/ -c pyproject.toml -ll`, `PYTHONPATH=scripts uv run lint-imports` | No new findings |
| `scripts/rag/ingestion/crawler.py` | Docstring and size gates | `uv run python tools/check_docstrings.py`, `uv run python tools/check_module_size.py` | No new finding versus the baselines; size far below the gate |
| `scripts/rag/ingestion/crawler.py` | Changed-line coverage | `uv run coverage run -m pytest tests/`, `uv run coverage xml`, `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90` | At least 90 percent on changed lines |

## Risks
- **Risk**: A test or caller constructs `WebCrawler` with a config missing a required key and relied on the `KeyError` type → **Mitigation**: such a site already fails today because of the subscript; `rg` found no `except KeyError` in `scripts/rag/` and no test asserting `KeyError` on the crawler (checked in Step 3); the full `tests/rag/ingestion` run confirms.
- **Risk**: Blast radius of the constructor change is 6 test modules and 27 test references, 28 with the production site (above the rule-of-thumb threshold in `rules/toolchain.md`) → **Mitigation**: the change only adds a pre-check that every existing site already satisfies, so none is expected to change; the implementation runs the six modules by name before the full suite, and the budget for a surprise is one fixture fix per module.
- **Risk**: The required tuple drifts from `config/crawler.toml` when a key is added or renamed → **Mitigation**: REQ-004's drift-guard test fails when the shipped file lacks a tuple key.
- **Risk**: The pre-check and the later subscripts could disagree if a key is added to one and not the other → **Mitigation**: the tuple is the single declaration and the subscripts for those keys follow it; the acceptance criterion forbids unvalidated subscripts, and the parametrized test covers every tuple key.
- **Risk**: A present key with `None` or a wrong type still fails opaquely → **Mitigation**: explicitly out of scope and recorded under Assumptions; type validation would be a separate Plan.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Required-key validation pass in `WebCrawler.__init__` with the new test module (tests first) | In Progress | — | — |  |
| 2 | Deployment hand-off and verification | Pending | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261110-000238_01_scripts_rag_ingestion_crawler.py.md | 1 | Procedure | Pending | — | — |
| implementations/20261110-000238_02_tests_rag_ingestion_test_crawler_config_validation.py.md | 1 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261108-195932_ragrev019_webcrawler-config-key-access-mixes-required-and-optional-lookups.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261109-103252
- **Related target files**: `scripts/rag/ingestion/crawler.py`, `tests/rag/ingestion/test_crawler_config_validation.py`

### Requirement Traceability
See `templates/requirement-traceability.md` for the canonical column format.

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Issue Implementation Intent (option 2), Problem; component default conflicts (Step 2) | `scripts/rag/ingestion/crawler.py` | Phase 1 | AC-1 | Parametrized and multi-key tests in `tests/rag/ingestion/test_crawler_config_validation.py` | Derived from confirmed evidence |
| REQ-002 | Issue Constraints, Acceptance Criteria (values unchanged) | `scripts/rag/ingestion/crawler.py` | Phase 1 | AC-2 | `uv run pytest tests/rag/ingestion -q` | Explicit in issue |
| REQ-003 | Issue Testing Expectations | `tests/rag/ingestion/test_crawler_config_validation.py` | Phase 1 | AC-3 | `uv run pytest tests/rag/ingestion/test_crawler_config_validation.py -v` | Explicit in issue |
| REQ-004 | Issue Constraints and Acceptance Criteria (shipped values unchanged); `config/crawler.toml` defines all six keys (Step 2) | `tests/rag/ingestion/test_crawler_config_validation.py` | Phase 1 | AC-4 | Shipped-file drift-guard test | Confirmed by repository evidence |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261110-000238 -->