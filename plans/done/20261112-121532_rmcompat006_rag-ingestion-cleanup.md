## Goal
- Make `rag.ingestion` a regular package so mypy resolves its modules under the CI invocation, remove the four `# type: ignore[no-any-return]` comments that rest on an unverifiable dual-module-path claim, and make the ingestion entry points, docstrings, and comments describe the current modules, CLI, and configuration model. Ingestion and crawling behavior stays unchanged.

## Priority
Medium

## Scope
- **In-Scope**: a new `scripts/rag/ingestion/__init__.py`; removal of the four suppressions; the two typing fixes that the newly visible package exposes in `http_fetcher.py` (behavior-preserving); `args.targets_file` direct access and one `ConfigLoader` import in the crawler (and the same duplicate import in `chunk_splitter.py`); docstrings naming the real modules; "bypass" comments reworded to the `ingester.toml` / `crawler.toml` model.
- **Out-of-Scope**: the RAG delegation leftovers and the ingester lifecycle (rmcompat001); the corpus identity removal in the same file (rmcompat003); changing ingestion, chunking, or crawling behavior; the unrelated "bypass" wording in `document_manager.py` and the `SQLiteHelper` documents; the mypy invocation used by CI and pre-commit; a new lint rule (no second import root for `rag` exists; see Unknowns).
- **Dependencies**: Fix order: rmcompat001 first (same `scripts/rag/ingestion/ingester.py`, different lines).
  - **Depends on**: plans/20261112-115458_rmcompat001_rag-delegation-leftovers.md | phase 4 | it removes the `__del__`, the unused attribute, `_log_ingest_failure`, and changes `main()` in `ingester.py`, whose line numbers this Plan's edits sit beside.

## Background
Re-verified 2026-11-12 (Step 2 and Step 3):
- The four suppressions are at `ingester.py:390` (`read_chunk_json`), `crawler.py:127` (`CrawlPersister.save`), `chunk_preparation.py:80` (`embed_and_store`), and `chunk_splitter.py:252` (`read_crawl_json`); each blames a "rag.* vs scripts.rag.* dual module-path resolution" and cites `scripts/shared/tool_constants.py`, which contains no such explanation.
- `rg -n "from scripts\.|import scripts\." scripts tests tools` finds two imports, both in `tests/shared/test_schema_fingerprint.py` (`scripts.db`, `scripts.shared`); none names `scripts.rag`, so no second import name exists for `rag`.
- Measured 2026-11-12 on a scratch copy (outside the repository: `pyproject.toml`, `scripts/`, `tests/eventbus`, `tools/`), with the CI invocation `mypy --no-namespace-packages --no-incremental scripts/ tests/eventbus tools`: the current tree (no `__init__.py`) passes mypy cleanly, so the four suppressions are actively hiding four `no-any-return` errors (the wrapped returns resolve to `Any` while `rag.ingestion` is a package without a marker). After adding an `__init__.py` to `scripts/rag/ingestion/`, the returns resolve to their real types, the four suppressions become `unused-ignore`, and exactly two new errors appear, both `arg-type` in `scripts/rag/ingestion/http_fetcher.py` (line 168 `redirect_allowed(origin, url)` and line 170 `host_is_public(url_host)`, `str | None` where `str` is expected). Removing the four comments clears the four `unused-ignore` errors; fixing `http_fetcher.py` clears the two `arg-type` errors. Re-verified in-repository 2026-11-13.
- Cause of the `Any`: `scripts/rag/ingestion/` is the only package directory under `scripts/` without an `__init__.py` (a search of every directory found no other). With `--no-namespace-packages`, mypy cannot resolve `rag.ingestion.<module>` imports, and `ignore_missing_imports = true` turns them into `Any`, which `warn_return_any = true` then reports at each return. The same gap makes `[tool.setuptools.packages.find]` (`where = ["scripts"]`, `include = [..., "rag*", ...]`) skip `rag.ingestion` when building a distribution.
- `host_is_public(None)` fails closed today: `getaddrinfo(None, None)` raises `socket.gaierror`, which `host_is_public` catches and returns `False`. `origin` is truthy whenever `origin_host` is not `None` (line 164), so the `redirect_allowed(origin, url)` call never receives `None`.
- `crawler.py` reads `getattr(args, "targets_file", None)` at lines 200 and 205 although `--targets-file` is always added to the parser (lines 192-196), and imports `ConfigLoader` at line 34 and again at line 224; `chunk_splitter.py` imports it at line 33 and again at line 425. The module docstrings name `Crawler.py`, `ChunkSplitter.py`, and `RagIngester.py` (`crawler.py:5,10`, `chunk_splitter.py:4,12`, `ingester.py:8`). The "bypass" comments are at `crawler.py:95` and `ingester.py:116`.

Corrections found against the Issue's claims:
- The Issue's open question "the actual cause of the `Any`" is answered above (missing `__init__.py`); the Issue's hypothesis of a dual module path is not supported, and the fix is in this package, not in `tool_constants.py`.
- Removing the suppressions is not free: it exposes two real typing gaps in `http_fetcher.py`, which the Issue did not list. Its AI instruction says to stop when this happens outside the listed files; this Plan adds the file as a target with a behavior-preserving fix, so the user can see it before the procedure runs (UNK-01).
- `scripts/shared/tool_constants.py` needs no edit (it contains no explanation to correct); it stays a reference.
- The test the Issue asks for (`--url` together with `--targets-file` exits with the parser error) already exists (`tests/rag/ingestion/test_crawler_targets_file.py`, lines 64-100), so no new entry-point test is added.
- No document names the old file names or the "bypass" model for these tools (search of `docs`, `rules`, `skills`); the `SQLiteHelper` "bypasses `build_db_config()`" sentences describe a different, current behavior and stay.
- `chunk_splitter.py` carries the same duplicate `ConfigLoader` import as the crawler, which the Issue did not name; it is in the same target file and the same defect class, so it is included.
- AC-5 and REQ-006 originally used `bypasses? build_db_config`; the `s?` binds the trailing `s`, so the pattern matched only "bypasses" and never "bypass", missing `ingester.py:115`. Corrected both to `bypass(es)? build_db_config` (verified: it matches both current comment lines).

## Problem
Suppressions that rest on an unverifiable claim hide a missing package marker, and the same gap leaves `rag.ingestion` untyped for every caller and out of the built distribution. A tolerant `getattr` read turns a renamed CLI argument into a silent `None`. Docstrings that name files that do not exist send readers to commands that fail; "bypass" wording makes the normal configuration model look unusual.

## Reason for Change
The current-only policy (`compatrm001`) and the suppression rules in `rules/coding.md` require a justified, verifiable reason for each suppression. No external deadline; the wrong file names in the docstrings are the only item that can lead a reader to a failing command.

## Implementation Intent
- Each ingestion module is imported by one name, `rag.ingestion` is a regular package, and no suppression rests on an unverifiable claim.
- The ingestion tools' code, docstrings, and comments describe the current modules, CLI, and configuration model.
- The two newly visible typing gaps are fixed without changing behavior.

## Requirements
- `REQ-001`: `scripts/rag/ingestion/__init__.py` exists following the package convention of `scripts/rag/__init__.py`; the four suppressions and their dangling cross-reference are removed; `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools` passes with no new suppression and no `unused-ignore` error.
- `REQ-002`: `HttpFetcher._hop_policy` type-checks without a suppression: the `origin` argument is narrowed before `redirect_allowed`, and a hop URL with no host is refused as non-public before `host_is_public`; the outcome for every input is unchanged.
- `REQ-003`: `crawler.py` `main()` reads `args.targets_file` directly and imports `ConfigLoader` once; `chunk_splitter.py` imports it once.
- `REQ-004`: The module docstrings of `crawler.py`, `chunk_splitter.py`, and `ingester.py` name the real modules and commands.
- `REQ-005`: The "bypass" comments in `crawler.py` and `ingester.py` say the settings come from `crawler.toml` / `ingester.toml` (ADR-002).
- `REQ-006`: `rg -n "rag\.\* vs scripts\.rag\.\*|getattr\(args|Crawler\.py|ChunkSplitter\.py|RagIngester\.py|bypass(es)? build_db_config" scripts/rag/ingestion/` returns nothing, and the existing ingestion and crawler tests pass.

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once `Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream `plan-to-implementation-procedure` document MUST reference file paths only from this table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/rag/ingestion/__init__.py` | Package marker | New file: package marker with the module docstring convention of `scripts/rag/__init__.py` | REQ-001 / AC-1 | the only package directory under `scripts/` without one; `scripts/rag/__init__.py` is the convention (checked in Step 3) | mypy CI invocation | Verified |
| `scripts/rag/ingestion/ingester.py` | Ingester | Remove the suppression at line 390; fix the docstring at line 8 and the comment at line 116 | REQ-001, REQ-004, REQ-005 / AC-1, AC-4, AC-5 | lines 8, 116, 390 (checked in Step 2) | `tests/rag/ingestion/test_ingester.py` | Verified |
| `scripts/rag/ingestion/crawler.py` | Crawler | Remove the suppression at line 127; read `args.targets_file`; one `ConfigLoader` import; fix the docstring and the comment at line 95 | REQ-001, REQ-003, REQ-004, REQ-005 / AC-1, AC-3, AC-4, AC-5 | lines 5, 10, 34, 95, 127, 200, 205, 224 (checked in Step 2) | `tests/rag/ingestion/test_crawler_targets_file.py` | Verified |
| `scripts/rag/ingestion/chunk_splitter.py` | Chunk splitter | Remove the suppression at line 252; one `ConfigLoader` import; fix the docstring | REQ-001, REQ-003, REQ-004 / AC-1, AC-3, AC-4 | lines 4, 12, 33, 252, 425 (checked in Step 2) | `tests/rag/ingestion/test_chunk_splitter.py` | Verified |
| `scripts/rag/ingestion/chunk_preparation.py` | Chunk preparation | Remove the suppression at line 80 | REQ-001 / AC-1 | line 80 (checked in Step 2) | `tests/rag/ingestion/test_ingester.py` | Verified |
| `scripts/rag/ingestion/http_fetcher.py` | Redirect hop policy | Narrow `origin` before `redirect_allowed`; refuse a hop with no host before `host_is_public` | REQ-002 / AC-2 | lines 163-172; the two `arg-type` errors measured on the scratch copy (checked in Step 3) | `tests/rag/ingestion/test_crawler_redirects.py` | Verified |
| `tests/rag/ingestion/test_crawler_redirects.py` | Redirect tests | Add a test that a hop to a URL with no host is refused as non-public | REQ-002 / AC-2 | imports `host_is_public`, `redirect_allowed` at line 26; no existing test names `_hop_policy` (checked in Step 3) | itself | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/rag/__init__.py` | The package convention (shebang and a path-and-purpose docstring) the new file follows | REQ-001 |
| `scripts/shared/tool_constants.py` | Cited by the four suppressions; contains no such explanation, so nothing to edit | REQ-001 |
| `scripts/rag/ingestion/crawler_utils.py` | `redirect_allowed(origin: str, ...)` and `host_is_public(host: str)` signatures and the fail-closed behavior | REQ-002 |
| `scripts/rag/ingestion/pipeline_utils.py` | Defines `read_chunk_json` and `read_crawl_json` whose results become typed | REQ-001 |
| `pyproject.toml` | `mypy_path`, `ignore_missing_imports`, `warn_return_any`, `warn_unused_ignores`, and `[tool.setuptools.packages.find]`; unchanged | REQ-001 |
| `tests/rag/ingestion/test_crawler_targets_file.py` | Already tests that `--url` with `--targets-file` exits with the parser error | REQ-003 |
| `plans/20261112-115458_rmcompat001_rag-delegation-leftovers.md` | Edits `ingester.py` first | REQ-001, REQ-004, REQ-005 |

## Acceptance Criteria
- AC-1 (REQ-001): `scripts/rag/ingestion/__init__.py` exists; `rg -n "type: ignore\[no-any-return\]" scripts/rag/ingestion/` returns nothing; `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools` passes with no new suppression and no `unused-ignore` error.
- AC-2 (REQ-002): the same mypy run reports no error in `http_fetcher.py`; the new redirect test passes.
- AC-3 (REQ-003): `rg -n "getattr\(args" scripts/rag/ingestion/` returns nothing; each of `crawler.py` and `chunk_splitter.py` has one `from shared.config_loader import ConfigLoader`.
- AC-4 (REQ-004): `rg -n "Crawler\.py|ChunkSplitter\.py|RagIngester\.py" scripts/rag/ingestion/` returns nothing.
- AC-5 (REQ-005): `rg -n "bypass(es)? build_db_config" scripts/rag/ingestion/` returns nothing. (Corrected from `bypasses?`: the original `s?` binds the trailing `s`, so it matched only "bypasses" and never "bypass", missing `ingester.py:115`.)
- AC-6 (REQ-006): `uv run pytest tests/rag/ingestion` passes and `uv run python tools/check_suppression_justification.py` passes.

## Tests
- REQ-001: the CI mypy invocation is the verification (before and after, recorded in the procedure).
- REQ-002: a new test builds a fetcher and calls `_hop_policy` with a hop URL that has no host (for example `http:///x`) and asserts `(False, "non-public destination")`, with `getaddrinfo` patched to fail the test if it is called; existing redirect tests cover the other branches.
- REQ-003: the existing parser-error tests (`--url` with `--targets-file`, missing file, parse error) cover the `args.targets_file` change.
- REQ-004, REQ-005: the acceptance searches.

## Documentation Impact
- N/A: no `docs/` file names the old file names or the "bypass" model for these tools (search of `docs`, `rules`, and `skills`); the docs checkers are not required unless a document changes.

## Assumptions
- Adding an empty-body package marker is the intended fix: the other package directories under `scripts/` use one, `[tool.setuptools.packages.find]` implies it, and the scratch measurement shows the four errors disappear with it.
- The `http_fetcher.py` fixes keep behavior: `origin and ...` narrows without changing the branch taken, and `host_is_public(None)` already returns `False`, so refusing earlier returns the same value.
- The scratch measurement used the CI flags except the cache (`--no-incremental`, as the pre-commit hook does); the procedure re-runs the real invocation in the repository.
- Step 8b overlap judgements (`tools/check_plan_target_overlaps.py`): `scripts/rag/ingestion/ingester.py` with `plans/20261112-115458_rmcompat001_rag-delegation-leftovers.md` is a sequencing dependency (recorded in Scope Dependencies) and with `plans/20261112-120011_rmcompat003_rag-corpus-identity-decision.md` is compatible (that Plan removes the `bump_index_generation` import and call; this Plan edits the suppression, the docstring, and one comment; re-read the file after both land).
- The new `__init__.py` follows the `scripts/rag/__init__.py` header (shebang and a one-line docstring) so `tools/check_docstrings.py` and `tools/fix_docstring_paths.py` accept it.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether the user accepts the two behavior-preserving `http_fetcher.py` fixes that removal of the suppressions exposes (the Issue says to stop and report when a real typing error needs a code change outside its listed files) | User decision | This Plan lists the file as a target so the decision is visible at freeze; revert to keeping the suppressions only if rejected | False |
| UNK-02 | Whether a lint rule against the `scripts.` import root is wanted (`tests/shared/test_schema_fingerprint.py` imports `scripts.db` and `scripts.shared`; no `scripts.rag` import exists, so the Issue's condition for a rule is not met) | Maintainer preference | Not added here; file a separate Issue if wanted | False |
| UNK-03 | Whether any deployed procedure starts the ingestion tools in a way that depends on `rag.ingestion` being a namespace package | Deployment inspection | `python -m rag.ingestion.crawler` style entry points work with a regular package; confirm at the deployment step | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/rag/ingestion/__init__.py` | Create | Medium | N/A | N/A | not applicable (rsynced) |
| `scripts/rag/ingestion/ingester.py` | Modify | Medium | 7 | N/A | not applicable (rsynced) |
| `scripts/rag/ingestion/crawler.py` | Modify | Medium | 3 | N/A | not applicable (rsynced) |
| `scripts/rag/ingestion/chunk_splitter.py` | Modify | Low | 4 | N/A | not applicable (rsynced) |
| `scripts/rag/ingestion/chunk_preparation.py` | Modify | Low | 1 | N/A | not applicable (rsynced) |
| `scripts/rag/ingestion/http_fetcher.py` | Modify | Medium | 4 | N/A | not applicable (rsynced) |
| `tests/rag/ingestion/test_crawler_redirects.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |

## Design
- Consumer scan: not a persisted schema, public API, or shared constant change; a text search over `scripts tests tools` shows `redirect_allowed` and `host_is_public` are used by `http_fetcher.py` and `test_crawler_redirects.py`, and `rag.ingestion.*` is imported across `scripts/rag` and the ingestion tests. A new package marker changes how mypy and setuptools see `rag.ingestion` and nothing at runtime (the directory was already importable as a namespace subpackage of `rag`).
- Architecture: `lint-imports` baseline is 6 contracts kept (recorded in the rmcompat001 Plan Design); `rag.ingestion` becomes a regular package inside `rag`, whose contract (`rag` must not import `agent` or `mcp_servers`) is unchanged. The procedure re-runs `lint-imports` after adding the file.
- Typing fix shape: in `_hop_policy`, narrow with `if origin and origin_host is not None and url_host == origin_host:` for the same-host branch and add `if url_host is None: return False, "non-public destination"` ahead of the `host_is_public` call; both preserve the current return values.
- Alternatives rejected: keeping the four suppressions with a corrected reason (hides the real cause and leaves `rag.ingestion` untyped); changing `host_is_public` to accept `str | None` (edits a second file for the same result).
- Complexity (`radon cc`) of the touched functions is below C; `vulture` and `bandit` baselines are recorded in the rmcompat001 Plan Design; the change adds no finding. No persisted schema, port, process, or dependency change (`rules/persisted-schema-change.md`, `ss`, `fuser`, `pip-audit` N/A). Churn above from `git log --since=30.days`; bus factor not measured.

## Implementation steps
1. **Phase 1: Package marker, suppression removal, typing fixes**
   - [ ] Measure the baseline with the CI invocation (recorded in the procedure), then add the package marker (REQ-001; `scripts/rag/ingestion/__init__.py`)
   - [ ] Remove the four suppressions (REQ-001; `scripts/rag/ingestion/ingester.py`, `scripts/rag/ingestion/crawler.py`, `scripts/rag/ingestion/chunk_splitter.py`, `scripts/rag/ingestion/chunk_preparation.py`)
   - [ ] Fix the two typing gaps and add the test (REQ-002; `scripts/rag/ingestion/http_fetcher.py`, `tests/rag/ingestion/test_crawler_redirects.py`)
2. **Phase 2: Entry point, docstrings, comments**
   - [ ] Direct `args.targets_file` read and one `ConfigLoader` import (REQ-003; `scripts/rag/ingestion/crawler.py`, `scripts/rag/ingestion/chunk_splitter.py`)
   - [ ] Real module names in the docstrings and the "bypass" comments (REQ-004, REQ-005; `scripts/rag/ingestion/crawler.py`, `scripts/rag/ingestion/chunk_splitter.py`, `scripts/rag/ingestion/ingester.py`)
3. **Phase 3: Deployment and verification**
   - [ ] Hand off to `skills/deploy/SKILL.md` after the change is committed and pushed; deploying is the user's decision (approval gate). Run the acceptance searches and the validation sequence (REQ-001 to REQ-006)

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| Typing | Static | `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools` (before and after) | Pass; four errors fixed, none new |
| Ingestion modules | Unit and integration | `uv run pytest tests/rag/ingestion` | Pass |
| Changed Python files | Static | `uv run ruff format`, `ruff check`, `lint-imports`, `bandit -r scripts/ -c pyproject.toml`, `python tools/check_suppression_justification.py`, `python tools/check_docstrings.py`, `python tools/check_module_size.py` | No new finding |
| Whole change | Search | the AC-1 and AC-3 to AC-5 `rg` commands | Match the criteria |
| Coverage | Coverage | diff-cover sequence in `rules/toolchain.md` section 7 | At or above the threshold |

## Risks
- **Risk**: Making `rag.ingestion` visible to mypy exposes further typing errors on another environment or cache state → **Mitigation**: the scratch run used `--no-incremental` over the CI file set and found exactly two; the procedure re-runs the real invocation and, if more appear, stops and reports instead of adding suppressions.
- **Risk**: The regular package changes import behavior for an entry point or test collection → **Mitigation**: the directory was already importable through `sys.path = scripts/`; `uv run pytest tests/rag/ingestion` and `lint-imports` run after the file is added (UNK-03).
- **Risk**: The `_hop_policy` change alters a security-relevant redirect decision → **Mitigation**: the new test asserts the refusal for a host-less hop; the same-host branch is unchanged by construction; existing redirect tests cover downgrade, public, and robots cases.
- **Risk**: A concurrent Plan edits `ingester.py` → **Mitigation**: ordering through the `Depends on` line and a re-read before editing; rmcompat003 edits other lines.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the package marker, remove the four suppressions, fix the two typing gaps | Completed | 20261113-201242 | 20261113-204236 | docs 01-06 executed; mypy 0 errors, pytest 353 passed |
| 2 | Direct `targets_file` read, single import, real names, reworded comments | Completed | 20261113-201242 | 20261113-204236 | AC-1/3/4/5 clear; lint-imports 0 broken; docstrings no new finding |
| 3 | Deployment hand-off and verification | Completed | 20261113-201242 | 20261113-204236 | non-release-unit change; CI gates (mypy/ruff/lint-imports/bandit/pytest) green; no deploy.sh change needed |

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
- **Source issue**: issues/20261110-171004_rmcompat006_rag-ingestion-cleanup.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261112-121532
- **Related target files**: `scripts/rag/ingestion/__init__.py`, `scripts/rag/ingestion/ingester.py`, `scripts/rag/ingestion/crawler.py`, `scripts/rag/ingestion/chunk_splitter.py`, `scripts/rag/ingestion/chunk_preparation.py`, `scripts/rag/ingestion/http_fetcher.py`, `tests/rag/ingestion/test_crawler_redirects.py`

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes 1 and 3; scratch mypy measurement | `scripts/rag/ingestion/__init__.py` | 1 | AC-1 | mypy CI invocation | Derived from confirmed evidence |
| REQ-001 | Required Changes 1; `ingester.py:390` | `scripts/rag/ingestion/ingester.py` | 1 | AC-1 | mypy CI invocation | Explicit in issue |
| REQ-001 | Required Changes 1; `crawler.py:127` | `scripts/rag/ingestion/crawler.py` | 1 | AC-1 | mypy CI invocation | Explicit in issue |
| REQ-001 | Required Changes 1; `chunk_splitter.py:252` | `scripts/rag/ingestion/chunk_splitter.py` | 1 | AC-1 | mypy CI invocation | Explicit in issue |
| REQ-001 | Required Changes 1; `chunk_preparation.py:80` | `scripts/rag/ingestion/chunk_preparation.py` | 1 | AC-1 | mypy CI invocation | Explicit in issue |
| REQ-002 | AI Implementation Instruction (stop on exposed errors); scratch mypy measurement | `scripts/rag/ingestion/http_fetcher.py` | 1 | AC-2 | `tests/rag/ingestion/test_crawler_redirects.py` | Derived from confirmed evidence |
| REQ-002 | Testing Expectations; no existing `_hop_policy` test | `tests/rag/ingestion/test_crawler_redirects.py` | 1 | AC-2 | itself | Derived from confirmed evidence |
| REQ-003 | Required Changes 4; `crawler.py:200,205,224` | `scripts/rag/ingestion/crawler.py` | 2 | AC-3 | `tests/rag/ingestion/test_crawler_targets_file.py` | Explicit in issue |
| REQ-003 | Derived from the duplicate import `chunk_splitter.py:33,425` | `scripts/rag/ingestion/chunk_splitter.py` | 2 | AC-3 | `tests/rag/ingestion/test_chunk_splitter.py` | Derived from confirmed evidence |
| REQ-004 | Required Changes 5; `crawler.py:5,10` | `scripts/rag/ingestion/crawler.py` | 2 | AC-4 | acceptance search | Explicit in issue |
| REQ-004 | Required Changes 5; `chunk_splitter.py:4,12` | `scripts/rag/ingestion/chunk_splitter.py` | 2 | AC-4 | acceptance search | Explicit in issue |
| REQ-004 | Required Changes 5; `ingester.py:8` | `scripts/rag/ingestion/ingester.py` | 2 | AC-4 | acceptance search | Explicit in issue |
| REQ-005 | Required Changes 6; `crawler.py:95` | `scripts/rag/ingestion/crawler.py` | 2 | AC-5 | acceptance search | Explicit in issue |
| REQ-005 | Required Changes 6; `ingester.py:116` | `scripts/rag/ingestion/ingester.py` | 2 | AC-5 | acceptance search | Explicit in issue |
| REQ-006 | Acceptance Criteria 1 and 5 | `scripts/rag/ingestion/crawler.py` | 2 | AC-6 | `uv run pytest tests/rag/ingestion` | Explicit in issue |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261113-201242 -->
