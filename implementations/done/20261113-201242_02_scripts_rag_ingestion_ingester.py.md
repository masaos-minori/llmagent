## Goal

`REQ-001`, `REQ-004`, `REQ-005`: in `scripts/rag/ingestion/ingester.py` remove the `no-any-return` suppression, rename the non-existent modules in the docstring, and reword the "bypass" comment to the `ingester.toml` model. Ingestion behavior is unchanged.

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- `rmcompat001` (depends-on) already edited `ingester.py`, so the plan-cited line numbers shifted. Locate each target by content, not by the plan's line 390 / 116.
- The wrapped returns (`read_chunk_json`) are correctly typed once `rag.ingestion` is a regular package, so the suppressions suppress nothing and can be removed safely.

## Design decisions
- Delete the trailing `# type: ignore[no-any-return]  # — …` comment wholesale; the dangling cross-reference to `tool_constants.py` goes with it (no explanation exists there).
- Docstring and comment use the real module base names and the `ingester.toml` config model already used by `ConfigLoader.restrict_to("ingester.toml")` (line 482).

## Alternatives considered
- N/A: the edits are line-local with no public-contract, persistence, or security impact.

## Implementation
### Target file
`scripts/rag/ingestion/ingester.py`

### Procedure
1. Remove the suppression and its comment on the `_read_chunk_json` return.
2. Rename the modules in the module docstring pipeline line.
3. Reword the DB-settings comment.

### Method
1. In `_read_chunk_json`, change
   `        return read_chunk_json(path)  # type: ignore[no-any-return]  # — read_chunk_json() is correctly typed -> ChunkDocument; mypy loses this across the rag.* vs scripts.rag.* dual module-path resolution (see scripts/shared/tool_constants.py's confirmed duplicate-module-name issue)`
   to
   `        return read_chunk_json(path)`
   (current line 373; the plan cited 390).
2. In the module docstring, change
   `Pipeline position: Crawler.py -> ChunkSplitter.py -> RagIngester.py`
   to
   `Pipeline position: crawler -> chunk_splitter -> ingester`
   (current line 8).
3. In `RagIngester.__init__`, reword
   `        # DB settings stored explicitly to bypass build_db_config() / agent.toml`
   to
   `        # DB settings loaded from ingester.toml`
   (current line 115; the plan cited 116).

### Details
- Keep every other line, indentation, and the surrounding logic identical.
- Do not touch the `RagIngester` class body beyond line 115.

## Compatibility considerations
N/A: behavior-preserving; the pipeline order and DB settings are unchanged.

## Security considerations
N/A: no request handling or permission change.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`: the four `unused-ignore` from this and docs 03–05 are gone; only the two `http_fetcher.py` `arg-type` errors remain until doc 06 runs.
- `uv run pytest tests/rag/ingestion`: passes.
- `rg -n "Crawler\.py|ChunkSplitter\.py|RagIngester\.py" scripts/rag/ingestion/` (AC-4): no match from this file.
- `rg -n "bypass(es)? build_db_config" scripts/rag/ingestion/` (AC-5): no match from this file.
- `tools/check_docstrings.py`: `rag/ingestion/ingester.py` stays grandfathered ("missing separator"); no new finding, no stale entry (no em-dash is added).

## Completion criteria
- The `# type: ignore[no-any-return]` and its comment are gone from `_read_chunk_json`.
- The docstring names `crawler`, `chunk_splitter`, `ingester`; the DB comment references `ingester.toml`.
- No `bypass build_db_config` wording remains in this file.

## Out of Scope
The suppression removals in docs 03–05, the `http_fetcher.py` typing fixes (doc 06), the `args.targets_file` / import fixes in doc 03.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261113-201242 | 20261113-204236 | suppression removed; docstring/comment reworded per Method |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261113-201242 | 20261113-204236 | mypy 0 errors (561 files); pytest 353 passed; AC-4/AC-5 clear; docstrings grandfathered |

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
- **Requirement ID**: `REQ-001`, `REQ-004`, `REQ-005`
- **Source issue**: issues/20261110-171004_rmcompat006_rag-ingestion-cleanup.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261112-121532_rmcompat006_rag-ingestion-cleanup.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261113-201242
- **Related target files**: `scripts/rag/ingestion/ingester.py`
