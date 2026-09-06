## Goal
Remove the now-invalid `with patch("rag.pipeline._ModuleConfig.get", ...)` wrapper
around the `RagPipeline(http, cfg)` construction in `_make_pipeline()`, so this test
module keeps passing once `_ModuleConfig` is removed from `scripts/rag/pipeline.py`
(REQ-004).

## Scope
- In scope: `_make_pipeline()`'s one `with patch(...)` wrapper (lines 56-57) — remove
  the `with` statement and dedent the `return RagPipeline(http, cfg)` call.
- Out of scope: `_make_cfg()`, `TestStageObservability` test bodies, and every other
  file in this Plan (tracked in their own rows).

## Assumptions
- Confirmed by Read: `cfg` passed into `_make_pipeline()` is always a `SimpleNamespace`
  (built by `_make_cfg()`, line 15-47), which has `__dict__` — so the current
  `resolve_rag_config`/`RagPipeline.__init__` config-resolution logic takes the
  object-with-`__dict__` branch and never actually reaches
  `_ModuleConfig.get()`/`config_loader()` at runtime in this test. The `patch(...)`
  wrapper is therefore defensive/inert here, exactly as the Plan's Design section
  states — confirmed against current source, not just the Plan's claim.
- Minor citation drift (non-blocking): the Plan's `Implementation Target Files` row
  cites "line 59"; the actual `with patch(...)` line is 56 (`return` at 57) as of this
  cycle. Same statement, off-by-a-few-lines citation only — does not change the
  required edit.

## Design decisions
- Simply delete the `with patch("rag.pipeline._ModuleConfig.get", return_value={}):`
  line and dedent the `return RagPipeline(http, cfg)` line by one level — no other
  change to `_make_pipeline()`'s signature or behavior, since the patch was inert.

## Alternatives considered
- Keep the `patch(...)` wrapper but retarget it at `resolve_rag_config`'s
  `config_loader` parameter: rejected — `_make_pipeline()` never reaches that fallback
  path (its `cfg` always satisfies the object-with-`__dict__` branch), so patching
  anything there would be dead code, same as today's inert patch.

## Implementation
### Target file
`tests/rag/test_stage_observability.py`

### Procedure
1. Open `_make_pipeline()` (current lines 50-57).
2. Delete line 56 (`with patch("rag.pipeline._ModuleConfig.get", return_value={}):`).
3. Dedent line 57 (`return RagPipeline(http, cfg)`) to the function body's indentation
   level.
4. Remove the now-unused `patch` import from
   `from unittest.mock import AsyncMock, MagicMock, patch` (line 8) only if no other
   `patch(...)` call remains in this file — confirm via `rg -n "patch\(" tests/rag/test_stage_observability.py` before removing the import.

### Method
Confirmed this cycle via direct Read (lines 1-60): `_make_pipeline()` at lines 50-57;
the sole `patch("rag.pipeline._ModuleConfig.get", ...)` call at line 56; `cfg`'s type
is `SimpleNamespace` per `_make_cfg()` (lines 15-47).

### Details
No change to `_make_cfg()`, to any `TestStageObservability` test method, or to any
assertion in this file.

## Compatibility considerations
No behavioral change: the patch was inert (never reached at runtime because `cfg` is
always a `SimpleNamespace`), so removing it does not alter what any test in this file
exercises or asserts.

## Security considerations
N/A: test-only change, no security-relevant code path.

## Rollback considerations
Revert via `git checkout tests/rag/test_stage_observability.py` if the full-file
`pytest` run for this file regresses after `_ModuleConfig`'s removal lands.

## Validation plan
- `uv run pytest tests/rag/test_stage_observability.py -v` — all tests pass, no
  `AttributeError` from the removed `patch` target.
- `rg -n "_ModuleConfig" tests/rag/test_stage_observability.py` — no remaining match.

## Completion criteria
- The `with patch("rag.pipeline._ModuleConfig.get", ...)` wrapper no longer exists in
  this file.
- `RagPipeline(http, cfg)` is called at the function body's base indentation level.
- `uv run pytest tests/rag/test_stage_observability.py -v` passes.

## Out of scope
- `scripts/rag/pipeline.py`'s own `_ModuleConfig` removal — tracked in seq 01 (REQ-002).
- The other 3 test files referencing `_ModuleConfig` — tracked in their own rows
  (seq 03, 05, 06).

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
- **Related target files**: tests/rag/test_stage_observability.py
