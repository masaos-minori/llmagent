## Goal
Remove the now-invalid `patch("rag.pipeline._ModuleConfig.get", ...)` wrappers in
`_make_pipeline()` and `test_fallback_no_embed_server()` and dedent the
`RagPipeline(...)` construction calls they wrap (REQ-004), so this file keeps
passing once `_ModuleConfig` is removed from `scripts/rag/pipeline.py`
(REQ-002).

## Scope
- In scope: the 3 `patch("rag.pipeline._ModuleConfig.get", ...)` call sites in
  this file (lines 76, 78, 171 — see Assumptions for the corrected count/line
  numbers vs. the Plan's citation).
- Out of scope: any other `patch(...)` call in this file (e.g. lines 134, 188,
  214, 225, 242, 260, 301, 342, 383, 401, 418 — these patch unrelated targets
  such as `rag.stages.search._search_all_queries`, not `_ModuleConfig`); the
  test assertions themselves (unchanged); `scripts/rag/pipeline.py` (seq 01)
  and all other Plan rows.

## Assumptions
- **Plan citation discrepancy found this cycle (2026-09-06)**: the Plan
  (`plans/20260906-115512_plan.md`, Implementation Target Files row 6 and
  Requirement Traceability REQ-004 row) states "2 occurrences" at "lines
  80-82, 175". Direct read this cycle
  (`grep -n "_ModuleConfig" tests/rag/test_rag_quality_regression.py`) found
  **3** occurrences instead, at lines **76, 78, and 171**:
  - Line 76: `with patch("rag.pipeline._ModuleConfig.get", return_value={"embed_url": ""}):` inside `_make_pipeline()`'s `if embedder is not None:` branch.
  - Line 78: `with patch("rag.pipeline._ModuleConfig.get", return_value={}):` inside `_make_pipeline()`'s fallback branch (same function, no `embedder`).
  - Line 171: `with patch("rag.pipeline._ModuleConfig.get", return_value={}):` inside `test_fallback_no_embed_server()`, wrapping a direct `RagPipeline(_make_http(), cfg)` construction (not via `_make_pipeline()`).
  The Plan's line numbers (80-82, 175) do not match current content at all —
  likely stale from an earlier revision of this file. This document uses the
  confirmed-current locations (76, 78, 171) instead. Per
  `skills/plan-to-implementation-procedure/workflow.md` Step 3a, this is
  reported here rather than silently corrected in the Plan (out of this row's
  authority to edit the shared Plan document during parallel per-row
  processing) — flagged for the Plan owner to reconcile centrally.
- Confirmed this cycle: `_make_rag_cfg()` (line 21) returns `SimpleNamespace`
  (has `__dict__`), and both `_make_pipeline()` and
  `test_fallback_no_embed_server()` always pass a `SimpleNamespace` `cfg` to
  `RagPipeline(...)`. Per `scripts/rag/pipeline.py`'s current config-resolution
  priority (`cfg` if `RagConfigImpl` > `cfg` if `dict` > `cfg` if
  object-with-`__dict__` > `module_cfg` > `config_loader()`/`_ModuleConfig`),
  the object-with-`__dict__` branch always wins here — the `_ModuleConfig.get()`
  patch at all 3 sites is never actually exercised at runtime. This confirms
  the Plan's Design-section claim (the patches are defensive/inert) still
  holds despite the line-number discrepancy above.

## Design decisions
- Remove the 3 `with patch("rag.pipeline._ModuleConfig.get", ...):` context
  managers and dedent the single statement each one wraps, preserving the
  exact same `RagPipeline(...)` call and return/assignment.
- No change to `_make_rag_cfg()`, fixture bodies, or any assertion — this is a
  removal of dead patch scaffolding only, per REQ-004's stated intent
  ("without changing what each test verifies").

## Alternatives considered
- Leave the 3 patches in place, relying on their inertness: rejected — once
  `_ModuleConfig` is removed from `scripts/rag/pipeline.py` (REQ-002, seq 01),
  `patch("rag.pipeline._ModuleConfig.get", ...)` raises `AttributeError` at
  patch-application time (the attribute no longer exists on the target
  module), regardless of whether the patched behavior is ever exercised at
  runtime — so removal is mandatory, not optional.

## Implementation
### Target file
`tests/rag/test_rag_quality_regression.py`

### Procedure
1. In `_make_pipeline()` (lines 66-79): replace
   ```python
   if embedder is not None:
       # Patch the module-level config to provide embed_url
       with patch("rag.pipeline._ModuleConfig.get", return_value={"embed_url": ""}):
           return RagPipeline(http, cfg)
   with patch("rag.pipeline._ModuleConfig.get", return_value={}):
       return RagPipeline(http, cfg)
   ```
   with
   ```python
   if embedder is not None:
       return RagPipeline(http, cfg)
   return RagPipeline(http, cfg)
   ```
   (the `# Patch the module-level config to provide embed_url` comment is
   removed along with the patch it described).
2. In `test_fallback_no_embed_server()` (lines 168-172): replace
   ```python
   with patch("rag.pipeline._ModuleConfig.get", return_value={}):
       pipeline = RagPipeline(_make_http(), cfg)
   ```
   with
   ```python
   pipeline = RagPipeline(_make_http(), cfg)
   ```
3. Re-check whether `patch` (from `unittest.mock`) remains used elsewhere in
   this file after the above removals (it does — lines 134, 188, 214, 225,
   242, 260, 301, 342, 383, 401, 418 patch unrelated targets) — do not remove
   the `from unittest.mock import ...` import.

### Method
Confirmed this cycle (2026-09-06) via `grep -n "_ModuleConfig\|patch(" tests/rag/test_rag_quality_regression.py`
and direct read of lines 60-90 and 160-178.

### Details
No change to any assertion, fixture, or non-`_ModuleConfig` patch in this
file.

## Compatibility considerations
Both call sites construct `cfg` via `_make_rag_cfg()` (a `SimpleNamespace`),
so `RagPipeline.__init__`'s object-with-`__dict__` branch is always taken and
the `_ModuleConfig`/`config_loader` fallback path is never reached at
runtime — removing the inert patch wrapper changes no test behavior or
outcome.

## Security considerations
N/A: test-only change, no security-relevant logic.

## Rollback considerations
Revert via `git checkout` on this file alone if `uv run pytest
tests/rag/test_rag_quality_regression.py -v` regresses after this change.

## Validation plan
- `uv run pytest tests/rag/test_rag_quality_regression.py -v` — all pass.
- `uv run pytest -v` (full suite, per Plan's Tests section) — no new failures.
- `rg "_ModuleConfig" tests/rag/test_rag_quality_regression.py` — no matches
  remain.

## Completion criteria
- All 3 `patch("rag.pipeline._ModuleConfig.get", ...)` wrappers are removed
  from this file.
- `_make_pipeline()` and `test_fallback_no_embed_server()` construct
  `RagPipeline(...)` directly, with no behavior change to what either test
  verifies.
- `uv run pytest tests/rag/test_rag_quality_regression.py -v` passes.

## Out of scope
- `scripts/rag/pipeline.py` — seq 01, the file whose removal of
  `_ModuleConfig` this row's change accommodates.
- Any non-`_ModuleConfig` `patch(...)` call in this file.
- The Plan's stale line-number citation (80-82, 175) — flagged in Assumptions
  for the Plan owner to correct; not edited here per this row's
  parallel-processing scope.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: REQ-004
- **Source issue**: issues/20260905-192946_refactor_ragpipeline_responsibility_boundaries.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260906-115512_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260906-152050
- **Related target files**: tests/rag/test_rag_quality_regression.py
