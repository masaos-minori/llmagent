## Goal
- Remove the unreachable `CrawlOrchestrator.crawl` method so no dead code with a prohibited broad `except Exception` remains in the crawl module.

## Priority
Medium

## Scope
- **In-Scope**:
  - Delete `CrawlOrchestrator.crawl` (`scripts/rag/ingestion/orchestrator.py`, lines 76-88).
  - Confirm no remaining references to `CrawlOrchestrator.crawl` remain in `scripts/` and `tests/`.
  - Confirm the module still imports cleanly and existing tests pass.
- **Out-of-Scope**:
  - Changing `WebCrawler.crawl` behavior or its exception handling.
  - Changing `CrawlOrchestrator.crawl_site` or any live method.
  - Any other dead-code cleanup beyond this method.
- **Dependencies**: `N/A: none`

## Background
`CrawlOrchestrator` owns the per-site BFS loop via `crawl_site`. It also defines an async `crawl(targets)` method that iterates targets and calls `crawl_site` per target. `WebCrawler.crawl` in `scripts/rag/ingestion/crawler.py` performs that same iteration but calls `self.orchestrator.crawl_site` directly, and `main()` invokes `WebCrawler.crawl`.

## Problem
`CrawlOrchestrator.crawl` is never called anywhere in `scripts/` or `tests/`. It is dead code that duplicates `WebCrawler.crawl` while using a broader `except Exception as _crawl_err` than the live path (which narrows to `(httpx.RequestError, httpx.HTTPStatusError, OSError)`). If someone later wires `WebCrawler.crawl` to `orchestrator.crawl`, the broad except would silently swallow crawler failures.

## Reason for Change
Dead code with a prohibited broad-except pattern violates the project's coding conventions. Removing it eliminates a latent footgun where future wiring could hide real fetch/HTTP/OSError failures behind a generic handler.

## Implementation Intent
Delete the method body and its docstring from `CrawlOrchestrator`. Do not touch any other method. After deletion, run a zero-caller `rg` re-check to prove the method was unreachable, then confirm the module imports and existing tests pass. Note the repository deprecation policy: deprecated symbols are normally removed on the next unrelated touch of their file; this method carries no deprecation marker, and this plan is the first (and only) touch of the file, so direct removal is appropriate.

## Requirements
- `REQ-001`: `CrawlOrchestrator.crawl` MUST be removed from `scripts/rag/ingestion/orchestrator.py`.
- `REQ-002`: no reference to `CrawlOrchestrator.crawl` (or `.crawl(` bound to the orchestrator) remains in `scripts/` or `tests/`.
- `REQ-003`: `CrawlOrchestrator` still instantiates and its live methods (`crawl_site`, `_drain_queue_to_tasks`, `_process_crawl_url_async`) are unchanged.

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/rag/ingestion/orchestrator.py` | Modify | Delete the unused `CrawlOrchestrator.crawl` method (lines 76-88), including its docstring and the trailing blank line, leaving all other members intact (REQ-001, REQ-003) | REQ-001 | `crawl` at lines 76-88 has no caller in `scripts/` or `tests/`; `WebCrawler.crawl` calls `orchestrator.crawl_site` directly (verified with `rg`) | Existing orchestrator/crawler tests | Verified |

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same
one-file-per-row discipline as `Implementation Target Files` above — no directories,
glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/rag/ingestion/crawler.py` | Owns the live `WebCrawler.crawl` that duplicates `orchestrator.crawl`'s logic and calls `orchestrator.crawl_site`; read to confirm the live path is unaffected by removing the dead method (REQ-002, REQ-003) | `scripts/rag/ingestion/orchestrator.py` |

## Acceptance Criteria
- `REQ-001`: `CrawlOrchestrator.crawl` no longer exists in the source.
- `REQ-002`: A zero-caller `rg` re-check for `orchestrator.crawl(` returns no matches.
- `REQ-003`: `CrawlOrchestrator` still exposes `crawl_site` and its private helpers; the class instantiates.

## Tests
- Run the existing crawler/orchestrator test suite; confirm no regressions from removing dead code (REQ-003).
- `ruff` / `mypy` clean on the touched file (REQ-001).

## Documentation Impact
`N/A: the removed method is not documented in `docs/*.md``.

## Assumptions
- No external entry point, plugin, or config references `CrawlOrchestrator.crawl` outside `scripts/` and `tests/`.
- The deprecation policy does not require a separate deprecation cycle because the method is not currently marked deprecated and this is the first touch of the file.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether to leave a deprecation marker before removal per the coding.md deprecation policy. | The method has no existing deprecation comment; policy applies to already-deprecated symbols. | Direct removal is accepted; if a reviewer prefers a deprecation-first approach, keep the method for one release with a deprecation warning. Non-blocking. | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/rag/ingestion/orchestrator.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |

## Design
`CrawlOrchestrator.crawl` (lines 76-88) iterates `targets` and calls
`self.crawl_site(url, lang)` per target, wrapping each in a try/except that catches
`Exception`. `WebCrawler.crawl` (in `scripts/rag/ingestion/crawler.py`) performs the
identical iteration but narrows the except to `(httpx.RequestError, httpx.HTTPStatusError,
OSError)`. Because `main()` calls `WebCrawler.crawl` and nothing calls
`CrawlOrchestrator.crawl`, the orchestrator method is unreachable dead code. Its broad
`except Exception` is both a convention violation and a latent footgun. The fix is a pure
deletion of the method; no caller, import, or interface changes are required.

## Implementation steps
1. **Phase 1: Delete the dead method** (`scripts/rag/ingestion/orchestrator.py`, REQ-001)
   - [ ] Remove lines 76-88 (`async def crawl(...)` through the final `logger.info("=== done: ...")` line) and the intervening blank line, preserving surrounding members.
   - [ ] Confirm `__init__` and `crawl_site` are byte-for-byte unchanged.
2. **Phase 2: Zero-caller re-check** (REQ-002)
   - [ ] Run `rg -n "orchestrator.crawl\("` under `scripts/` and `tests/`; expect no matches.
3. **Phase 3: Verification & commit** (REQ-003)
   - [ ] Run `uv run ruff format` and `uv run ruff check` on `scripts/rag/ingestion/orchestrator.py`; confirm clean.
   - [ ] Run `uv run mypy --no-namespace-packages scripts/`; confirm no new errors.
   - [ ] Run the existing crawler/orchestrator test suite; confirm pass.
   - [ ] Commit, rebase onto `origin/master`, and push via `git-commit-and-sync`.

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/rag/ingestion/orchestrator.py` | Static: format, lint, type | `uv run ruff format` / `uv run ruff check` / `uv run mypy --no-namespace-packages scripts/` | Clean, no new errors |
| `scripts/rag/ingestion/orchestrator.py` | Behavioral: live crawl methods still work | existing crawler/orchestrator tests | No regressions |

## Risks
- **Risk**: Removing a method that some undiscovered caller relies on. → **Mitigation**: zero-caller `rg` re-check across `scripts/` and `tests/` before and after deletion.
- **Risk**: Accidentally altering a live method during deletion. → **Mitigation**: diff review confirms only lines 76-88 changed.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Delete `CrawlOrchestrator.crawl` (`scripts/rag/ingestion/orchestrator.py`) | Pending | — | — | |
| 2 | Zero-caller `rg` re-check | Pending | — | — | |
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
- **Source issue**: `issues/20261106-073205_crawl002_remove-dead-orchestrator-crawl-method.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261106-093856
- **Related target files**: `scripts/rag/ingestion/orchestrator.py`

### Requirement Traceability
See `templates/requirement-traceability.md` for the canonical column format.

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Reason for Change / Required Changes | `scripts/rag/ingestion/orchestrator.py` | Step 1 | REQ-001 acceptance criteria | rg zero-caller check | Confirmed by repository evidence |
| REQ-002 | Problem / Required Changes | `scripts/rag/ingestion/orchestrator.py` | Step 2 | REQ-002 acceptance criteria | rg zero-caller check | Confirmed by repository evidence |
| REQ-003 | Background / Required Changes | `scripts/rag/ingestion/orchestrator.py` | Step 3 | REQ-003 acceptance criteria | existing tests pass | Confirmed by repository evidence |
