## Goal

Lock down the new chunk-size validation with regression tests: each rejected relation, each wrong-type rejection, the `md_index_enable` range check, and accepted-boundary parity; plus rework the two existing tests that relied on configs the new validation now rejects.

## Scope
**Release unit**: chunk-size validation + regression tests (Plan `### Release units`; Phases 1–2).

## Assumptions
- Tests construct through the public constructor `ChunkSplitter(config=cfg)` so validation runs (unlike `_make_splitter`/`_make_ja_mixin`, which use `object.__new__` and bypass `__init__`).
- `_CRAWL_CONFIG` (`min_chunk=40, max_chunk=500, chunk_overlap=50, md_snippet_max_chars=600, md_index_enable absent`) is the base valid config; tests copy it and mutate one key at a time.
- Wrong-typed values must raise `PipelineValidationError` (not the raw `ValueError` that `int("abc")` would raise) — the typed getter converts it.
- `PipelineValidationError` is already imported at the top of the file (line 16).

## Design decisions
- **One mutation per test.** Each test copies `_CRAWL_CONFIG` and changes exactly one key, so the failing relation is unambiguous and the error message can be asserted against that key.
- **Assert the message names the offending key(s)** where the Plan AC requires it (REQ-001 names both keys; REQ-003 names the key and value). Use `pytest.raises(PipelineValidationError, match=...)` with a plain-key substring.
- **Keep the existing `test_non_positive_max_chunk_raises_at_construction`** unchanged — it remains valid (`max_chunk=0` still raises, now via the `chunk_overlap >= max_chunk` relation).

## Alternatives considered
- **Parametrize the rejection cases.** Rejected: explicit named tests read better as documentation of each relation and let each assert its own message.
- **Build a fresh config dict per test.** Rejected: `dict(_CRAWL_CONFIG)` with a single-key mutation is less noisy and keeps the valid baseline explicit.

## Compatibility considerations
- Two existing tests must be reworked because they construct configs the new validation rejects (see Procedure > Details). All other existing tests use valid configs and are untouched.
- `_make_io_splitter` and `_make_prune_splitter` helpers keep their signatures; only call sites change.

## Security considerations
N/A: test additions only.

## Rollback considerations
N/A: revert the commit.

## Validation plan

## Implementation
### Target file
`tests/rag/ingestion/test_chunk_splitter.py`

### Procedure
1. Extend `class TestMaxChunkValidation` with the rejection tests below.
2. Add the `md_index_enable` range test (REQ-004) — either inside `TestMaxChunkValidation` or a small new class.
3. Add one accepted-boundary parity test (REQ-005).
4. Rework `TestForceRechunkPrune.test_zero_chunk_forced_run_removes_old_series` (line ~1171).
5. Rework `TestFetchedAtPropagation.test_md_heading_splits_have_matching_fetched_at` (line ~720).
6. Run the whole `tests/rag/ingestion/test_chunk_splitter.py` suite; it must stay green.

### Method
Add these methods to `TestMaxChunkValidation`:

```python
def test_min_chunk_greater_than_max_chunk_raises_at_construction(self) -> None:
    cfg = dict(_CRAWL_CONFIG)
    cfg["min_chunk"] = 600  # > max_chunk (500)
    with pytest.raises(PipelineValidationError, match="min_chunk"):
        ChunkSplitter(config=cfg)
    with pytest.raises(PipelineValidationError, match="max_chunk"):
        ChunkSplitter(config=cfg)


def test_negative_min_chunk_raises_at_construction(self) -> None:
    cfg = dict(_CRAWL_CONFIG)
    cfg["min_chunk"] = -1
    with pytest.raises(PipelineValidationError, match="min_chunk"):
        ChunkSplitter(config=cfg)


def test_chunk_overlap_at_max_chunk_raises_at_construction(self) -> None:
    cfg = dict(_CRAWL_CONFIG)
    cfg["chunk_overlap"] = 500  # == max_chunk
    with pytest.raises(PipelineValidationError, match="chunk_overlap"):
        ChunkSplitter(config=cfg)


def test_negative_chunk_overlap_raises_at_construction(self) -> None:
    cfg = dict(_CRAWL_CONFIG)
    cfg["chunk_overlap"] = -10
    with pytest.raises(PipelineValidationError, match="chunk_overlap"):
        ChunkSplitter(config=cfg)


def test_wrong_type_max_chunk_raises_pipeline_error(self) -> None:
    cfg = dict(_CRAWL_CONFIG)
    cfg["max_chunk"] = "abc"  # str, not int
    with pytest.raises(PipelineValidationError, match="max_chunk"):
        ChunkSplitter(config=cfg)


def test_wrong_type_float_min_chunk_raises_pipeline_error(self) -> None:
    cfg = dict(_CRAWL_CONFIG)
    cfg["min_chunk"] = 40.5  # float, not int
    with pytest.raises(PipelineValidationError, match="min_chunk"):
        ChunkSplitter(config=cfg)


def test_valid_tight_boundary_config_constructs(self) -> None:
    cfg = dict(_CRAWL_CONFIG)
    cfg["chunk_overlap"] = 499  # < max_chunk (500); tightest valid overlap
    splitter = ChunkSplitter(config=cfg)  # must not raise
    assert splitter._min_chunk == 40
    assert splitter._max_chunk == 500
    assert splitter._chunk_overlap == 499
```

Add an `md_index_enable` range test (REQ-004):

```python
class TestMdSnippetValidation:
    def test_md_snippet_above_max_chunk_raises_when_enabled(self) -> None:
        cfg = dict(_CRAWL_CONFIG)
        cfg["md_index_enable"] = True
        cfg["md_snippet_max_chars"] = 600  # > max_chunk (500)
        with pytest.raises(PipelineValidationError, match="md_snippet_max_chars"):
            ChunkSplitter(config=cfg)

    def test_md_snippet_within_range_constructs_when_enabled(self) -> None:
        cfg = dict(_CRAWL_CONFIG)
        cfg["md_index_enable"] = True
        cfg["md_snippet_max_chars"] = 400  # within [40, 500]
        splitter = ChunkSplitter(config=cfg)  # must not raise
        assert splitter._md_index_enable is True
        assert splitter._md_snippet_max_chars == 400

    def test_md_snippet_not_checked_when_disabled(self) -> None:
        cfg = dict(_CRAWL_CONFIG)
        # md_index_enable absent -> False; the 600 vs 500 mismatch is unchecked.
        splitter = ChunkSplitter(config=cfg)  # must not raise
        assert splitter._md_index_enable is False
```

### Details
**Rework 1 — `TestForceRechunkPrune.test_zero_chunk_forced_run_removes_old_series`** (line ~1171). It currently calls `_make_prune_splitter(tmp_path, min_chunk=100000, max_chunk=600)` to force zero chunks; that `min_chunk > max_chunk` config is now rejected at construction. Replace with a valid config whose `min_chunk` exceeds the source length so `_chunk_english` discards everything:

```python
new_count = _make_prune_splitter(
    tmp_path, min_chunk=100000, max_chunk=100001
).process_file(src, force=True)
```

`min_chunk=100000 <= max_chunk=100001` and `chunk_overlap` defaults to 50 (< 100001), so it is valid; `_LONG_SINGLE` (~700 chars) is below `min_chunk` and discarded, yielding zero chunks — preserving the test's intent.

**Rework 2 — `TestFetchedAtPropagation.test_md_heading_splits_have_matching_fetched_at`** (line ~720). It calls `_make_io_splitter(tmp_path, md_index_enable=True)`, which pulls `md_snippet_max_chars=600` from `_CRAWL_CONFIG` while `max_chunk=500`; REQ-004 rejects that. Build the config directly with a valid snippet size instead of using the helper:

```python
def test_md_heading_splits_have_matching_fetched_at(self, tmp_path: Path) -> None:
    src_dir = tmp_path / "rag-src"
    src_dir.mkdir(exist_ok=True)
    cfg = dict(_CRAWL_CONFIG)
    cfg["rag_src_dir"] = str(src_dir)
    cfg["md_index_enable"] = True
    cfg["md_snippet_max_chars"] = 400  # valid: within [min_chunk=40, max_chunk=500]
    splitter = ChunkSplitter(config=cfg)
    self._write_crawl_json(tmp_path, _CRAWL_WITH_MD_HEADINGS)
    total = splitter.process_all(force=True)
    assert total >= 3
    ...  # (rest unchanged)
```

`400` is above every heading section length and below `max_chunk`, so sections are kept whole and the `>= 3` split still holds. This keeps the change localized to this one test (no change to the shared `_make_io_splitter` helper).

**Accepted-boundary parity (REQ-005).** The `test_valid_tight_boundary_config_constructs` method above confirms a tight-but-valid boundary constructs. Full output parity is covered by the regression gate: every pre-existing test uses a valid config and must pass unchanged, so no valid configuration changes its chunk output.

## Completion criteria
- Each rejected relation (`min_chunk > max_chunk`, `min_chunk < 0`, `chunk_overlap >= max_chunk`, `chunk_overlap < 0`) and each wrong-type value (`str`, `float`) raises `PipelineValidationError` naming the key.
- `md_index_enable` out-of-range `md_snippet_max_chars` raises; in-range constructs; disabled leaves the mismatch unchecked.
- The two reworked tests pass under the new validation and preserve their original intent.
- The entire `tests/rag/ingestion/test_chunk_splitter.py` suite is green.

## Out of Scope
- Restructuring the constructor-call pattern in the sibling issue `issues/20261119-112021_ragcrv009_chunk-test-construction-fragility.md` (sequences after this fix).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20261119-160924 | code row 01 owns the implementation |
| 2 | Add or update tests per Validation plan | Completed | — | 20261119-160924 | add rejection/wrong-type/md-snapshot tests; rework 2 existing tests |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261119-160924 | ruff + pytest on the rag ingestion suite |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20261119-160924 | docs handled by rows 03/04 N/A: no docs edited for this member; relations documented in rows 03/04 |

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
- **Requirement ID**: `REQ-001`, `REQ-002`, `REQ-003`, `REQ-004`, `REQ-005` — reject contradictory/mistyped chunk-size config; keep valid configs' output unchanged
- **Source issue**: `issues/20261119-112015_ragcrv003_chunk-config-validation.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261119-144007_ragcrv003_chunk-config-validation.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261119-151106
- **Related target files**: `tests/rag/ingestion/test_chunk_splitter.py`