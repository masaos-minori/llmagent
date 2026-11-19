## Goal

Validate the chunk-size group in `ChunkSplitter.__init__` and reject wrong-typed size values, so a contradictory or mistyped config fails fast as a `PipelineValidationError` instead of being silently coerced.

## Scope
**Release unit**: chunk-size validation + regression tests (Plan `### Release units`; Phases 1–2).

## Assumptions
- The chunk-size keys are read from the injected `config` dict or `ConfigLoader().load("chunk_splitter.toml")`; missing keys fall back to the current `.get()` defaults.
- TOML integers arrive as Python `int`; the typed getter should accept plain `int` and reject `bool`, `float`, and `str` (a `bool` is a subclass of `int` and must be excluded explicitly).
- Validation runs before the Sudachi dictionary is constructed (line ~89 of `chunk_splitter.py`), so a bad config never loads the dictionary.
- The mixins (`chunk_english.py`, `chunk_japanese.py`) and `chunk_utils.merge_text_items` receive already-bounded values and gain no guards (Issue AI Implementation Instruction).
- Two existing tests rely on configs the new validation rejects and must be reworked (see the companion test-row procedure): `TestForceRechunkPrune.test_zero_chunk_forced_run_removes_old_series` (`min_chunk=100000 > max_chunk=600`) and `TestFetchedAtPropagation.test_md_heading_splits_have_matching_fetched_at` (`md_index_enable=True` with `md_snippet_max_chars=600 > max_chunk=500`).

## Design decisions
- **Typed getter over bare coercion.** Add a module-level helper `_require_int(cfg, key, *, default=...)` that returns the value when it is a plain `int` and raises `PipelineValidationError(f"{key} must be an integer, got {value!r}")` otherwise. This rejects `bool`/`float`/`str` instead of coercing, matching the Issue AC and the `rules/coding.md` type-coercion intent. `get_typed` itself is not mandated here (its policy scopes `*_models.py` only); this local helper is a deliberate, narrower choice.
- **Group validation before Sudachi construction.** Read and validate `min_chunk`, `max_chunk`, `chunk_overlap` (and, when enabled, `md_snippet_max_chars`) up front, then assign `self._*` attributes. The existing `max_chunk <= 0` guard is subsumed by `min_chunk >= 0` plus `min_chunk <= max_chunk` with `max_chunk` required positive.

## Alternatives considered
- **Reuse `rules/coding.md` `get_typed`.** Rejected: that helper's policy gates `*_models.py` loaders only; `chunk_splitter.py` is outside that scope, and a tiny local getter keeps the change self-contained and reviewable.
- **Validate after Sudachi construction.** Rejected: a bad config would still load the dictionary; fail-fast requires validation ahead of it.

## Compatibility considerations
- The default `config/chunk_splitter.toml` (`min=40, max=500, overlap=50, md_snippet=600, md_index=false`) satisfies every relation, so the production default is unaffected.
- `md_snippet_max_chars` is range-checked only when `md_index_enable` is truthy; when disabled the attribute is still read (via the typed getter with its default) so downstream usage is unchanged.

## Security considerations
N/A: configuration validation only; no input sanitization, privilege, or data-handling impact.

## Rollback considerations
N/A: revert the commit.

## Validation plan

## Implementation
### Target file
`scripts/rag/ingestion/chunk_splitter.py`

### Procedure
1. Insert a module-level helper `_require_int` above `class ChunkSplitter` (after the imports / constants, before the class).
2. In `ChunkSplitter.__init__`, replace the current size reads (lines 75–86) with typed reads and group validation, placed before the `sudachi_dict.Dictionary(...)` construction (line 89).
3. Keep `_en_stopwords`, `_ja_stop_pos`, and the Sudachi wiring exactly as they are.

### Method
Rewrite the top of `__init__` so it reads like:

```python
def __init__(self, config: dict | None = None) -> None:
    """Initialize the chunk splitter with configuration from TOML file or provided dict."""
    cfg: dict = config or ConfigLoader().load("chunk_splitter.toml")
    rag_src_dir = Path(cfg["rag_src_dir"])
    self._chunk_dir: Path = rag_src_dir / "chunk"

    # Chunk-size group validation + typed getters, before Sudachi construction.
    min_chunk = _require_int(cfg, "min_chunk")
    max_chunk = _require_int(cfg, "max_chunk")
    chunk_overlap = _require_int(cfg, "chunk_overlap", default=50)

    if min_chunk < 0:
        raise PipelineValidationError(
            f"min_chunk must be >= 0, got {min_chunk}"
        )
    if min_chunk > max_chunk:
        raise PipelineValidationError(
            f"min_chunk ({min_chunk}) must be <= max_chunk ({max_chunk})"
        )
    if chunk_overlap < 0:
        raise PipelineValidationError(
            f"chunk_overlap must be >= 0, got {chunk_overlap}"
        )
    if chunk_overlap >= max_chunk:
        raise PipelineValidationError(
            f"chunk_overlap ({chunk_overlap}) must be < max_chunk ({max_chunk})"
        )

    self._min_chunk = min_chunk
    self._max_chunk = max_chunk
    self._chunk_overlap = chunk_overlap

    self._en_stopwords: frozenset[str] = frozenset(cfg["en_stopwords"])
    self._ja_stop_pos: frozenset[str] = frozenset(cfg["ja_stop_pos"])

    md_index_enable = cfg.get("md_index_enable", False)
    if not isinstance(md_index_enable, bool):
        raise PipelineValidationError(
            f"md_index_enable must be a boolean, got {md_index_enable!r}"
        )
    self._md_index_enable: bool = md_index_enable
    # Read once; range-check only when the feature is enabled (REQ-004).
    md_snippet_max_chars = _require_int(
        cfg, "md_snippet_max_chars", default=600
    )
    if md_index_enable and not (
        min_chunk <= md_snippet_max_chars <= max_chunk
    ):
        raise PipelineValidationError(
            f"md_snippet_max_chars ({md_snippet_max_chars}) must be within "
            f"[min_chunk={min_chunk}, max_chunk={max_chunk}]"
        )
    self._md_snippet_max_chars: int = md_snippet_max_chars

    # SplitMode.C: longest compound unit; optimal for NLP downstream tasks
    sd_dict = sudachi_dict.Dictionary(dict=resolve_sudachi_dict_path())
    ...
```

Notes:
- The upper bound uses `<=` (UNK-01 default): `min_chunk <= md_snippet_max_chars <= max_chunk`. Document this choice in `config/chunk_splitter.toml` and the reference.
- The boolean guard for `md_index_enable` is defensive; the Issue does not require it, but it prevents a later `if md_index_enable:` from silently treating a non-bool as truthy. Keep it minimal.

### Details
- `_require_int` signature: `def _require_int(cfg: dict, key: str, *, default: int | None = None) -> int:`. Resolve the value as `raw = cfg[key] if key in cfg else default`. If `default` is used and is not a plain `int`, that is a code error, not a config error — assume the literal default is an int. Then: `if isinstance(raw, bool) or not isinstance(raw, int): raise PipelineValidationError(f"{key} must be an integer, got {raw!r}")`. Else return `raw`.
- Error messages name the key, the value read, and (for relations) the failed comparison — per REQ-001..REQ-003.
- The existing "max_chunk must be positive" contract is preserved transitively: `chunk_overlap >= 0` (validated) plus `chunk_overlap < max_chunk` forces `max_chunk > 0`. The current `test_non_positive_max_chunk_raises_at_construction` (`max_chunk=0`, `_CRAWL_CONFIG` overlap=50) still raises via the `chunk_overlap >= max_chunk` relation, so no separate positive guard is needed.

## Completion criteria
- `ChunkSplitter(config={...})` raises `PipelineValidationError` for each of: `min_chunk < 0`, `min_chunk > max_chunk`, `chunk_overlap < 0`, `chunk_overlap >= max_chunk`, wrong-typed size value, and (when `md_index_enable`) `md_snippet_max_chars` outside `[min_chunk, max_chunk]`.
- A valid config (current TOML defaults and `_CRAWL_CONFIG`) constructs without error and produces identical chunk output to before.
- The Sudachi dictionary is constructed only after validation passes.

## Out of Scope
- Per-chunker guards in `chunk_english.py` / `chunk_japanese.py` / `chunk_utils.py`.
- Re-tuning the chunk-size constants (NC-034).
- Config hot-reload or per-source overrides.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement chunk-size group validation + typed getters in `ChunkSplitter.__init__` | Completed | — | 20261119-160924 | REQ-001..REQ-004; fail-fast before Sudachi |
| 2 | Add/update tests per Validation plan | Completed | — | 20261119-160924 | companion row covers test changes |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261119-160924 | ruff + pytest |
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
- **Requirement ID**: `REQ-001`, `REQ-002`, `REQ-003`, `REQ-004` — reject contradictory/mistyped chunk-size config at construction
- **Source issue**: `issues/20261119-112015_ragcrv003_chunk-config-validation.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261119-144007_ragcrv003_chunk-config-validation.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261119-151106
- **Related target files**: `scripts/rag/ingestion/chunk_splitter.py`