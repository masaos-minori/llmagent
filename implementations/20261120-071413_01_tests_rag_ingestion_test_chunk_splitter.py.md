## Goal

Replace the repeated inline splitter-`config` dictionaries in
`tests/rag/ingestion/test_chunk_splitter.py` with one shared config-builder
fixture and route the existing tests through it, without changing any assertion
(REQ-001). No test constructs a chunk/splitter object with `object.__new__`, and
the chunk suite runs without relying on Sudachi dictionary availability (REQ-003).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Only `test_chunk_splitter.py` constructs a `ChunkSplitter` in the chunk suite;
  `test_chunk_utils.py` calls `merge_text_items` directly and
  `test_chunk_grouping.py` does not construct a splitter, so neither needs the
  shared fixture. The fixture therefore lives locally in `test_chunk_splitter.py`
  rather than `tests/conftest.py` (UNK-01 resolution: keep local).
- `_make_splitter` (line 43) already seeds a real `ChunkSplitter` via a `config`
  dict; the new fixture returns the same shape of dict so the construction seam
  is unchanged in behavior.
- The chunk suite currently collects 126 tests; this refactor must keep that
  count and every assertion identical.
- **Overlap (ragcrv009 ↔ ragcrv010)**: both Plans edit
  `docs/21_rag/rag_02_03_ingestion_pipeline-chunksplitter.md`, but different
  locations in section 3.1.4 — this Plan touches only the test file (this row);
  ragcrv010 edits the doc. The two are compatible (different lines, different
  concerns, both non-production). This row's procedure does not touch the doc.

## Design decisions
- Add a module-level `@pytest.fixture` named `splitter_config` (new) that returns a
  validated splitter-`config` dict (the same keys/values `_CRAWL_CONFIG` /
  `_make_splitter` produce today), plus a second fixture that seeds
  `ChunkSplitter` through its public constructor using that config where a test
  needs the constructed splitter.
- Route the existing inline-config tests through these fixtures by replacing each
  inline `config={...}` literal / `cfg = dict(_CRAWL_CONFIG)` + mutation with a
  fixture-provided dict, leaving every assertion byte-for-byte unchanged.
- Keep `_CRAWL_CONFIG` as the single source the fixture builds from, so the
  fixture and the constant cannot drift.

## Alternatives considered
- Placing the fixture in `tests/conftest.py` for cross-file reuse: rejected —
  only `test_chunk_splitter.py` constructs a splitter today; a local fixture is
  sufficient and avoids widening the change surface. Promote to conftest only if
  a later test requires it.
- Refactoring `_make_splitter` into the fixture and deleting it: rejected —
  `_make_splitter` is the documented construction helper (ragcrv006); the
  fixture is the config-builder, `_make_splitter` stays the constructor wrapper.

## Implementation
### Target file
`tests/rag/ingestion/test_chunk_splitter.py`

### Procedure
1. Add a module-level fixture near `_make_splitter` (after line 60):
   ```python
   @pytest.fixture
   def splitter_config() -> dict[str, Any]:
       """Single builder for the splitter-`config` dict used across this suite."""
       return dict(_CRAWL_CONFIG)

   @pytest.fixture
   def splitter(splitter_config: dict[str, Any]) -> ChunkSplitter:
       """Seed a real ChunkSplitter through its public constructor."""
       return ChunkSplitter(config=splitter_config)
   ```
2. In `TestMaxChunkValidation` / `TestMdSnippetValidation`, replace each
   `cfg = dict(_CRAWL_CONFIG)` with `cfg = dict(splitter_config())` is wrong
   (fixtures inject by parameter, not call): instead add a `splitter_config` (new)
   parameter to each test method that needs a base config and drop the local
   `dict(_CRAWL_CONFIG)` line, then keep the existing mutations and
   `ChunkSplitter(config=cfg)` calls. Where a test only asserts on a constructed
   splitter, accept the `splitter` fixture directly.
3. Replace the inline `config={...}` literals in `_make_splitter`'s callers and
   the `chunker = ChunkSplitter(config={...})` blocks (lines ~965, ~1005,
   ~1038, ~1086, ~1129, ~1156, ~1176, ~1666) with the `splitter`/`splitter_config` (new)
   fixtures where they build the standard config; preserve any test-specific
   value overrides that were inside those literals.
4. Do not touch any `assert`, `pytest.raises`, or matcher string.

### Method
Edit the fixture block and each construction site; verify by diff that no
assertion line changed and by re-running the chunk suite that the count stays at
126. Confirm no inline `config` literal remains via the evidence grep.

### Details
`_make_splitter` (lines 43-60) builds an inline `config={...}` with
`min_chunk=40, max_chunk=500, chunk_overlap=50, md_snippet_max_chars=400`.
`_CRAWL_CONFIG` (line 550) is the module-level constant the validation tests
clone via `dict(_CRAWL_CONFIG)` before mutating. The fixture returns
`dict(_CRAWL_CONFIG)` so the seeded config is identical to what the inline
literals produced. `object.__new__` appears only in docstrings (lines 44, 206);
no test fabricates an instance, satisfying REQ-003. The stub-tokenizer seam
(`_StubTokenizer` via `_make_ja_mixin`) keeps Japanese unit tests independent of
the Sudachi dictionary.

## Compatibility considerations
Test-only change; no production impact. Routing through a fixture changes how a
config is obtained, not its contents, so behavior and the 126-pass count are
preserved. The isolation guard `production_paths_allowed` in `tests/conftest.py`
is unaffected because no production paths are opened.

## Security considerations
N/A: test-only refactoring.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- Unit: `uv run pytest tests/rag/ingestion/test_chunk_splitter.py
  tests/rag/ingestion/test_chunk_grouping.py tests/rag/ingestion/test_chunk_utils.py
  -q` passes with the count unchanged at 126 and no new isolation-guard failures.
- Static: `rg -n "config" tests/rag/ingestion/test_chunk_splitter.py` review
  confirms the config is built only via the fixture (no stray inline literal for
  splitter construction remains).

## Completion criteria
One shared `splitter_config` (new)/`splitter` fixture builds every splitter-`config`;
no inline `config` dictionary remains for splitter construction; all assertions
unchanged; the chunk suite still passes 126 tests.

## Out of Scope
Changing any test assertion, adding new size-rule regression tests, touching
`test_chunk_utils.py` / `test_chunk_grouping.py`, or any production chunking code.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add shared `splitter_config` (new)/`splitter` fixtures | Pending | — | — | |
| 2 | Route existing tests through the fixtures without assertion changes | Pending | — | — | |
| 3 | Run chunk suite; confirm 126 pass, no isolation-guard failures | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: test-only |

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
- **Requirement ID**: `REQ-001`, `REQ-003`
- **Source issue**: `issues/20261119-112021_ragcrv009_chunk-test-construction-fragility.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261120-050144_ragcrv009_chunk-test-construction-fragility.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261120-071413
- **Related target files**: `tests/rag/ingestion/test_chunk_splitter.py`
