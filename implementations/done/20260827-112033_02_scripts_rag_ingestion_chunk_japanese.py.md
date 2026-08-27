## Goal

Refactor `ChunkJapaneseMixin._emit_and_start_new()` to reuse the shared
`start_next_buf()` helper instead of duplicating overlap-slicing logic inline
(REQ-001), per `plans/20260826-120822_plan.md`.

## Scope

- In scope: `_emit_and_start_new()`'s two duplicated overlap-slicing branches
  (verified at lines 107-119 as of 2026-08-27) and one new import.
- Out of scope: `_append_to_buffer()`, `_reset_buffer()` (no overlap logic, no
  equivalent in `chunk_utils.py`); `chunk_english.py`, `chunk_splitter.py`,
  `chunk_utils.py` itself (all already correct or unaffected); the L-1 dead-code
  item (already resolved by an unrelated prior commit, per this Plan's Background).

## Assumptions

- `tests/rag/ingestion/test_chunk_splitter.py`'s new characterization test (seq 01
  in this same pass) has been authored and confirmed passing against the CURRENT
  (pre-refactor) implementation before this item is applied — this item's success
  criterion is that the same test continues to pass afterward.
- No caller outside `ChunkSplitter` constructs `ChunkJapaneseMixin` directly or
  depends on `_emit_and_start_new()`'s internal implementation — re-verified
  2026-08-27 via `rg -n "ChunkJapaneseMixin" scripts/ tests/`, finding only
  `chunk_utils.py`'s docstring mention and `chunk_splitter.py`'s import/class
  declaration/comment — no other references.
- **Edge-case caveat (plan-to-implementation-procedure adversarial verification,
  2026-08-27)**: `start_next_buf()` (`chunk_utils.py:12-17`) skips `.strip()` when
  `prev`'s trailing overlap slice is itself empty, while the current inline code
  always applies `.strip()`. If seq 01's edge-case investigation found this
  reachable and produces a real output difference, this item must add an explicit
  `.strip()` on `orig`/`norm` before calling `start_next_buf()` (or another fix
  confirmed against seq 01's test) rather than proceeding with the direct
  substitution shown in this Plan's Design section.

## Design decisions

- Mirror `ChunkEnglishMixin`'s existing pattern exactly (`chunk_english.py`,
  `from rag.ingestion.chunk_utils import start_next_buf`, one call per buffer) —
  per this Plan's Design section, this is a direct, minimal substitution, not a
  redesign.
- Call `start_next_buf()` twice — once for `_orig_buf`, once for `_norm_buf` —
  since the Japanese mixin's two-buffer accumulation is structurally different from
  `merge_text_items()`'s single-list loop (out of scope to generalize, per this
  Plan's Scope).
- Use `" "` as the separator (matching the mixin's existing inline `+ " " +`
  convention), not `"\n"` (which `chunk_english.py` uses for paragraph joins).

## Alternatives considered

- Generalizing `chunk_utils.merge_text_items()` to accept the Japanese mixin's
  `(original, normalized)` pair shape was considered and rejected (per this Plan's
  Scope) — it would touch `chunk_utils.py`'s public signature and require changes
  beyond this 2-file scope, for no additional benefit over reusing the already-generic
  `start_next_buf()` twice.

## Implementation
### Target file
`scripts/rag/ingestion/chunk_japanese.py`

### Procedure
1. Add `from rag.ingestion.chunk_utils import start_next_buf` to this file's
   imports.
2. Replace `_emit_and_start_new()`'s duplicated inline slicing branches (lines
   107-119) with two `start_next_buf()` calls.
3. Run `uv run pytest tests/rag/ingestion/test_chunk_splitter.py
   tests/rag/ingestion/test_chunk_utils.py -v` and confirm all pre-existing tests
   plus the seq 01 new test pass unchanged.
4. Run `uv run mypy scripts/rag/ingestion/chunk_japanese.py` — confirm no new
   errors (attribute types must remain unchanged).

### Method
Direct code edit (Edit tool) — one import addition, one method body replacement.

### Details
Current code (verified 2026-08-27, lines 107-119):
```python
    def _emit_and_start_new(self, orig: str, norm: str) -> None:
        """Emit buffer as chunk and start new buffer with overlap."""
        self._result.append((self._orig_buf, self._norm_buf))
        if self._chunk_overlap:
            self._orig_buf = (
                self._orig_buf[-self._chunk_overlap :] + " " + orig
            ).strip()
            self._norm_buf = (
                self._norm_buf[-self._chunk_overlap :] + " " + norm
            ).strip()
        else:
            self._orig_buf = orig
            self._norm_buf = norm
```
Change to (per this Plan's Design section, subject to the Edge-case caveat above):
```python
    def _emit_and_start_new(self, orig: str, norm: str) -> None:
        """Emit buffer as chunk and start new buffer with overlap."""
        self._result.append((self._orig_buf, self._norm_buf))
        self._orig_buf = start_next_buf(self._orig_buf, orig, " ", self._chunk_overlap)
        self._norm_buf = start_next_buf(self._norm_buf, norm, " ", self._chunk_overlap)
```
Add the import near this file's existing imports (`from rag.exceptions import
TokenizationError`, `from rag.utils import normalize_unicode`, verified at lines
14-15):
```python
from rag.ingestion.chunk_utils import start_next_buf
```

## Compatibility considerations

- No change to `_emit_and_start_new()`'s signature, return type, or the mixin's
  declared attribute types (`_orig_buf`, `_norm_buf`, `_chunk_overlap` remain
  `str`/`str`/`int`) — `mypy` must show no new errors.
- Behavior-preserving except for the Edge-case caveat above, which seq 01's test
  must confirm is either unreachable or unaffected.

## Security considerations

- N/A: no security-relevant behavior; internal text-buffer accumulation logic.

## Rollback considerations

- Revert via `git diff`/`git checkout -- scripts/rag/ingestion/chunk_japanese.py`;
  independent of seq 01's test file (reverting this file alone leaves the new test
  failing against the old inline logic — expected, since the test was authored to
  pin down pre-refactor behavior and should still pass against it).

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `scripts/rag/ingestion/chunk_japanese.py` | Unit (existing + new) | `uv run pytest tests/rag/ingestion/test_chunk_splitter.py tests/rag/ingestion/test_chunk_utils.py -v` | All pre-existing tests plus the seq 01 new test pass unchanged |
| `scripts/rag/ingestion/chunk_japanese.py` | Type check | `uv run mypy scripts/rag/ingestion/chunk_japanese.py` | No new errors |
| `scripts/rag/ingestion/chunk_japanese.py` | Lint | `uv run ruff check scripts/rag/ingestion/chunk_japanese.py` | Clean |
| `scripts/rag/ingestion/chunk_japanese.py` | Security | `uv run bandit scripts/rag/ingestion/chunk_japanese.py` | No new findings (baseline: 0 issues) |

## Completion criteria

- `rg -n "self._orig_buf\[-self._chunk_overlap" scripts/rag/ingestion/chunk_japanese.py`
  returns no matches.
- `rg -n "start_next_buf" scripts/rag/ingestion/chunk_japanese.py` returns at least
  two matches.
- All tests in `test_chunk_splitter.py`/`test_chunk_utils.py` pass, including the
  seq 01 new characterization test.

## Out of scope

- `_append_to_buffer()`, `_reset_buffer()`.
- `chunk_english.py`, `chunk_splitter.py`, `chunk_utils.py`.
- The L-1 dead-code item (already resolved, no action needed).
- `docs/03_rag_02_07_ingestion_pipeline-utils.md` §7's update (flagged by this Plan
  as a required follow-up, not part of this document-only workflow phase's output —
  raise as a separate documentation task once this code change lands).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `start_next_buf` import | Pending | — | — | |
| 2 | Replace `_emit_and_start_new()`'s inline slicing with `start_next_buf()` calls | Pending | — | — | Subject to the Edge-case caveat — verify seq 01's test result first |
| 3 | Run `uv run pytest tests/rag/ingestion/test_chunk_splitter.py tests/rag/ingestion/test_chunk_utils.py -v` | Pending | — | — | |
| 4 | Run `uv run mypy scripts/rag/ingestion/chunk_japanese.py` | Pending | — | — | |

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
- **Requirement ID**: REQ-001
- **Source issue**: `issues/20260821_07_issue.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260826-120822_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260827-112033
- **Related target files**: `scripts/rag/ingestion/chunk_japanese.py`
