## Goal

`REQ-001`, `REQ-003`, `REQ-004`: in `scripts/rag/ingestion/chunk_splitter.py` remove the `no-any-return` suppression, keep one `ConfigLoader` import, and rename the non-existent modules in the docstring. Chunking behavior is unchanged.

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The duplicate `ConfigLoader` import is the one inside `if __name__ == "__main__":` (line 425); the top-level import (line 33) is kept.
- The wrapped return (`read_crawl_json`) is correctly typed once `rag.ingestion` is a regular package.

## Design decisions
- A single top-level import satisfies both `ChunkSplitter.__init__` (line 71) and `main()` (line 427 `restrict_to`).

## Alternatives considered
- N/A: line-local edits with no public-contract, persistence, or security impact.

## Implementation
### Target file
`scripts/rag/ingestion/chunk_splitter.py`

### Procedure
1. Remove the suppression and its comment on the `read_crawl_json` return.
2. Remove the duplicate `ConfigLoader` import in `__main__`.
3. Rename the modules in the docstring.

### Method
1. In the method returning `read_crawl_json`, change
   `            return read_crawl_json(src_path)  # type: ignore[no-any-return]  # — read_crawl_json() is correctly typed -> ChunkDocument; mypy loses this across the rag.* vs scripts.rag.* dual module-path resolution (see scripts/shared/tool_constants.py's confirmed duplicate-module-name issue)`
   to
   `            return read_crawl_json(src_path)`
   (current line 252).
2. Delete line 425 (`    from shared.config_loader import ConfigLoader`) inside
   ```python
   if __name__ == "__main__":
       from shared.config_loader import ConfigLoader

       ConfigLoader.restrict_to("chunk_splitter.toml")
       main()
   ```
   leaving
   ```python
   if __name__ == "__main__":
       ConfigLoader.restrict_to("chunk_splitter.toml")
       main()
   ```
   (keep the top-level import at line 33).
3. Module docstring: change every `Crawler.py` / `ChunkSplitter.py` / `RagIngester.py` to the real base names. Concretely, the pipeline line
   `Pipeline position: Crawler.py → ChunkSplitter.py → RagIngester.py`
   becomes
   `Pipeline position: crawler → chunk_splitter → ingester`
   (line 12), and any `Crawler.py` reference in the opening line (line 4) becomes `crawler`.

### Details
- Preserve the `→` arrow already used in this file's docstring.
- Do not change chunking logic, the markdown-source detection, or `process_all`.

## Compatibility considerations
N/A: behavior-preserving; chunking and config loading are unchanged.

## Security considerations
N/A: no request handling or permission change.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`: the four `unused-ignore` from docs 04–05 are gone after this runs; only the two `http_fetcher.py` `arg-type` errors remain until doc 06.
- `uv run pytest tests/rag/ingestion`: passes.
- `rg -n "Crawler\.py|ChunkSplitter\.py|RagIngester\.py" scripts/rag/ingestion/` (AC-4): no match.
- `rg -n "bypass(es)? build_db_config" scripts/rag/ingestion/` (AC-5): no match (this file had none).
- `tools/check_docstrings.py`: `rag/ingestion/chunk_splitter.py` stays grandfathered ("missing separator"); no new finding, no stale entry (no em-dash added).
- `lint-imports`: one `from shared.config_loader import ConfigLoader` remains (line 33).

## Completion criteria
- No `# type: ignore[no-any-return]`, no second `ConfigLoader` import, and no `Crawler.py`/`ChunkSplitter.py`/`RagIngester.py` remain in this file.
- `chunk_splitter.py` has exactly one `from shared.config_loader import ConfigLoader`.

## Out of Scope
The suppression removal in doc 05, the `http_fetcher.py` typing fixes (doc 06), the `crawler.py` edits (doc 03).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261113-201242 | 20261113-204236 | suppression removed; duplicate import gone; docstring reworded |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261113-201242 | 20261113-204236 | mypy 0 errors (561 files); pytest 353 passed; AC-4 clear; docstrings grandfathered |

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
- **Requirement ID**: `REQ-001`, `REQ-003`, `REQ-004`
- **Source issue**: issues/20261110-171004_rmcompat006_rag-ingestion-cleanup.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261112-121532_rmcompat006_rag-ingestion-cleanup.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261113-201242
- **Related target files**: `scripts/rag/ingestion/chunk_splitter.py`
