## Goal
- Make every crawl artifact name unique per canonical URL so two distinct pages can never resolve to the same JSON file and silently overwrite each other.

## Priority
High

## Scope
- **In-Scope**:
  - Make `CrawlPersister.make_crawl_filepath` return a collision-free path per canonical URL.
  - Preserve the `.json` extension and the human-readable `{timestamp}-<label>` shape.
  - Add a regression test for the 80-character-prefix collision case.
- **Out-of-Scope**:
  - Changing the JSON payload schema or fields.
  - Changing where `rag-src/` is located.
  - Changing `url_to_slug` semantics for any other caller.
  - Robots.txt, crawl rate, or link-filtering policy.
- **Dependencies**: `N/A: none`

## Background
The crawler persists each crawled page as a JSON payload under `rag-src/`. The output name is produced by `CrawlPersister.make_crawl_filepath`, which formats `{ts}-{slug}.json`, where `{ts}` is a second-granularity timestamp and `{slug}` comes from `url_to_slug`, which truncates the URL-derived slug to 80 characters. `save_http` and `save` write with `orjson.dumps(...)` via `Path.write_bytes` and never check whether the target already exists.

## Problem
The output name is not a unique key. Two different URLs that share an 80-character-or-longer common prefix, saved within the same wall-clock second, map to the identical path. The later `write_bytes` replaces the earlier file with no error, warning, or trace. Under concurrent BFS (`crawl_concurrency`) same-second saves across distinct pages are plausible, so documents can be silently lost during a multi-page crawl.

## Reason for Change
The corpus is the sole input to downstream embedding and retrieval; a silently overwritten document degrades the index with no error log and no easy recovery. The current scheme provides no uniqueness guarantee, and no test exercises the collision case.

## Implementation Intent
Give every crawl artifact a unique, filesystem-safe name by combining the existing human-readable truncated slug with a short hash of the full canonical URL, appended to the timestamp prefix. Keep the naming inside `CrawlPersister`; do not move it to the orchestrator or change the payload. Preserve the `.json` extension and the `{timestamp}-<label>` visual shape so existing manual workflows and `rag-src/` browsing are unaffected.

## Requirements
- `REQ-001`: `make_crawl_filepath` MUST return a distinct `Path` for every pair of distinct canonical URLs, including two URLs that share an 80-character-or-longer common prefix and would otherwise be saved in the same second.
- `REQ-002`: the returned path MUST remain filesystem-safe, end in `.json`, and preserve the `{timestamp}-<label>` visual convention.
- `REQ-003`: a regression test MUST assert that two distinct long-prefix URLs never collide and that both output files exist after a simulated save.

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/rag/ingestion/crawl_persister.py` | Modify | Append a short hash of the full canonical URL to `make_crawl_filepath`'s output so the path is unique per URL (REQ-001, REQ-002) | REQ-001, REQ-002 | `make_crawl_filepath` builds `{ts}-{slug}.json` from a second-granularity timestamp and an 80-char-truncated `url_to_slug`; `save_http`/`save` call it and `write_bytes` without an existence check (checked in Step 2/3) | Regression test below | Verified |
| `tests/rag/ingestion/test_crawl_persister_lang.py` | Modify | Add a regression test asserting two distinct long-prefix URLs produce distinct output files that both exist after save (REQ-003) | REQ-003 | Existing persister tests live here and use `glob("*.json")` counts rather than exact filenames, so the format change does not break them (checked in Step 2/3) | Same file | Verified |

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same
one-file-per-row discipline as `Implementation Target Files` above — no directories,
glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/rag/ingestion/crawler_utils.py` | Owns `url_to_slug`, whose 80-char truncation is the collision source; read to preserve its label output unchanged | `scripts/rag/ingestion/crawl_persister.py` |
| `scripts/rag/ingestion/pipeline_utils.py` | Owns `read_crawl_json`, which reads the JSON payload by path; confirm the filename change does not affect the read schema (REQ-002) | `scripts/rag/ingestion/crawl_persister.py` |

## Acceptance Criteria
- `REQ-001`: Two distinct URLs sharing an 80-character-or-longer common prefix produce two distinct output paths.
- `REQ-001`: A simulated concurrent save of many distinct URLs writes one file per URL with no overwrite.
- `REQ-002`: The new naming stays filesystem-safe and ends in `.json`.
- `REQ-003`: The regression test for the collision case passes.

## Tests
- Unit test for the uniqueness function with colliding 80-char-prefix pairs (REQ-001, REQ-003).
- Integration-style test saving several distinct URLs and asserting all files exist and are distinct (REQ-001, REQ-003).
- `ruff` / `mypy` clean on touched files (REQ-002).

## Documentation Impact
`N/A: the output layout is not documented in `docs/*.md``; if a crawler config note describes the filename shape, update only the uniqueness policy, not the implementation.

## Assumptions
- The `url` argument passed to `make_crawl_filepath` is already the canonical/normalized URL used elsewhere in the crawl, so hashing it yields a stable per-page key.
- `hashlib` is already imported in `crawl_persister.py` (used by `save` for SHA-256), so no new import is needed.
- Downstream consumers match artifacts by `rag-src/**/*.json` glob, not by an exact filename pattern.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Hash-suffix versus untruncated-slug placement for the uniqueness component. The issue defers this to implementation and states both satisfy uniqueness. | None required; both approaches verified feasible against `make_crawl_filepath`. | Decided in Design: append an 8-hex-char SHA-256 of the full URL. Accepted alternative: use the untruncated slug. Non-blocking. | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/rag/ingestion/crawl_persister.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |

## Design
`make_crawl_filepath` currently returns `self._rag_src_dir / f"{ts}-{slug}.json"`, where
`slug` is `url_to_slug(url)` truncated to 80 characters. Two distinct URLs with an
80-character-or-longer common prefix collapse to the same `slug`; within the same second
they also share the same `ts`, so the full path collides.

**Decision: append a short hash of the full canonical URL.** Compute
`hash8 = hashlib.sha256(url.encode("utf-8")).hexdigest()[:8]` and return
`{ts}-{slug}-{hash8}.json`. This keeps the leading human-readable `{timestamp}-<label>`
shape (the truncated slug is still the visible label) while the trailing 8-hex-char hash
guarantees per-URL uniqueness. SHA-256 gives a 32-hex-char digest; the first 8 chars offer a
2^32 collision space, which is negligible for a local corpus. `hashlib` is already imported
in the module (used by `save`), so no new import is introduced.

The alternative endorsed by the issue — using the untruncated slug — is accepted but
rejected in favor of the hash because it bounds filename length for very long URLs and keeps
the label readable. This is a Path A implementation detail; the issue explicitly leaves the
choice to the implementer (UNK-01).

## Implementation steps
1. **Phase 1: Uniqueness in `make_crawl_filepath`** (`scripts/rag/ingestion/crawl_persister.py`, REQ-001, REQ-002)
   - [ ] Compute `hash8 = hashlib.sha256(url.encode("utf-8")).hexdigest()[:8]` from the full canonical `url`.
   - [ ] Return `self._rag_src_dir / f"{ts}-{slug}-{hash8}.json"` so the path is unique per URL while preserving the `{timestamp}-<label>` shape and `.json` extension.
   - [ ] Confirm `url_to_slug` and its callers are unchanged.
2. **Phase 2: Regression test** (`tests/rag/ingestion/test_crawl_persister_lang.py`, REQ-003)
   - [ ] Add a test that two distinct URLs sharing an 80-character-or-longer common prefix produce distinct `make_crawl_filepath` results.
   - [ ] Add a test that a simulated save of several distinct URLs writes one file per URL with no overwrite.
3. **Phase 3: Deployment & Verification**
   - [ ] Run `uv run ruff format` and `uv run ruff check` on `scripts/rag/ingestion/crawl_persister.py` and the test file; confirm clean.
   - [ ] Run `uv run mypy --no-namespace-packages scripts/` on the changed files; confirm no new errors.
   - [ ] Run `uv run pytest tests/rag/ingestion/test_crawl_persister_lang.py -v`; confirm the new and existing tests pass.
   - [ ] Commit, rebase onto `origin/master`, and push via `git-commit-and-sync`.

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/rag/ingestion/crawl_persister.py` | Static: format, lint, type | `uv run ruff format` / `uv run ruff check` / `uv run mypy --no-namespace-packages scripts/` | Clean, no new errors |
| `tests/rag/ingestion/test_crawl_persister_lang.py` | Unit/integration: collision uniqueness and no-overwrite | `uv run pytest tests/rag/ingestion/test_crawl_persister_lang.py -v` | New and existing tests pass |

## Risks
- **Risk**: Changing the filename shape could break a downstream consumer that matches an exact filename pattern instead of the `rag-src/**/*.json` glob. → **Mitigation**: keep the `.json` extension and the `{timestamp}-<label>-<hash>.json` shape; the existing glob still matches every artifact.
- **Risk**: A truncated SHA-256 could theoretically collide between two unrelated URLs. → **Mitigation**: 8 hex chars give a 2^32 space; collision probability is negligible for a local corpus, and the corpus is regenerated on re-crawl.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add hash-suffix uniqueness to `make_crawl_filepath` (`scripts/rag/ingestion/crawl_persister.py`) | Pending | — | — | |
| 2 | Add collision regression test (`tests/rag/ingestion/test_crawl_persister_lang.py`) | Pending | — | — | |
| 3 | Format/lint/type/test verification and commit | Pending | — | — | |

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
- **Source issue**: `issues/20261106-073205_crawl001_crawler-output-filename-uniqueness.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261106-093306
- **Related target files**: `scripts/rag/ingestion/crawl_persister.py`, `tests/rag/ingestion/test_crawl_persister_lang.py`

### Requirement Traceability
See `templates/requirement-traceability.md` for the canonical column format.

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Implementation Intent / Required Changes | `scripts/rag/ingestion/crawl_persister.py` | Step 1 | REQ-001 acceptance criteria | Unit + integration uniqueness tests | Confirmed by repository evidence |
| REQ-002 | Constraints / Implementation Intent | `scripts/rag/ingestion/crawl_persister.py` | Step 1 | REQ-002 acceptance criteria | ruff/mypy clean | Confirmed by repository evidence |
| REQ-003 | Required Changes / Testing Expectations | `tests/rag/ingestion/test_crawl_persister_lang.py` | Step 2 | REQ-003 acceptance criteria | Collision regression test | Confirmed by repository evidence |
