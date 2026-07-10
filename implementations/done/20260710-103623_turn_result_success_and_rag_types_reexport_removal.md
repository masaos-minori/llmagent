# Implementation: Remove `TurnResult.success` and the `rag/types.py` backward-compat re-export (Phase 2)

## Goal

Remove two backward-compatibility layers that are actively depended on by production code, by rewriting their call sites first: the `TurnResult.success` property (used at exactly one production call site) and the `shared.types` re-export inside `scripts/rag/types.py` (used across the RAG subsystem and its tests).

## Scope

**In:**
- `scripts/agent/turn_result.py`: delete the `success` property
- `scripts/agent/orchestrator.py`: rewrite the single call site (`orchestrator.py:432`) from `if not result.success:` to `if result.action != "continue":`
- `scripts/rag/types.py`: remove the re-export of `RagHit`, `MergedHit`, `RankedHit`, `RawHit` from `shared.types` (keep `RagQuery`, `PipelineRunResult`, `SearchDiagnostics`, which are genuinely defined in this module, not re-exported)
- Rewrite `from rag.types import (...)` in 9 production files to import `RagHit`/`MergedHit`/`RankedHit`/`RawHit` from `shared.types` instead, splitting the import statement where a file also imports names that remain in `rag.types`:
  - `scripts/rag/llm_client.py`
  - `scripts/rag/pipeline.py`
  - `scripts/rag/pipeline_refiner.py`
  - `scripts/rag/stages/search.py`
  - `scripts/rag/repository.py`
  - `scripts/rag/llm_prompts.py`
  - `scripts/rag/stage.py`
  - `scripts/mcp/rag_pipeline/document_manager.py`
  - `scripts/mcp/rag_pipeline/service.py`
- Rewrite the equivalent imports in 11 test files:
  - `tests/test_agent_rag.py`
  - `tests/test_rag_http_mode.py`
  - `tests/test_rag_pipeline_stage.py` (8 import sites, several inline inside test functions)
  - `tests/test_rag_repository.py`
  - `tests/test_rag_pipeline.py`
  - `tests/test_rag_pipeline_mcp_service.py`
  - `tests/test_rag_refiner.py`
  - `tests/test_rag_get_cfg.py`
  - `tests/test_pipeline_http_result_kind.py`
  - `tests/test_rag_quality_regression.py`
  - `tests/test_rag_stages.py`

**Out:**
- No change to `TurnResult`'s other fields (`action`, `answer`, `error_kind`, `reason`, `exception`, `persist_as_assistant`)
- No change to `RagQuery`, `PipelineRunResult`, `SearchDiagnostics` definitions in `scripts/rag/types.py` — these stay where they are, they are not re-exports
- No change to the `agent → shared` / `rag → shared` import-layer contract in `.importlinter` (both directions already permitted)

## Assumptions

1. `orchestrator.py:432` is the only production call site of `TurnResult.success` — confirmed by grepping `\.success\b` across `scripts/agent` and manually verifying every other hit (`factory.py`, `context_view.py`, `rag_maintenance_service.py`, `db_maintenance_service.py`, `embedding_client.py`, `memory/injection.py`, `memory/ingestion.py`) resolves to an unrelated `RepoResult`/`EmbedResult`-style dataclass, not `TurnResult`.
2. No test constructs a `TurnResult` and then asserts on `.success` — confirmed via `grep -n "\.success\|TurnResult(" tests/test_orchestrator.py tests/test_llm_turn_runner.py`; all `TurnResult(...)` constructions in tests already use `action=...` directly.
3. `shared.types` already defines `RagHit`, `MergedHit`, `RankedHit`, `RawHit` as the canonical source; `scripts/rag/types.py` currently re-exports them purely for backward compatibility (per its own docstring and `docs/90_shared_02_types_and_protocols.md`).
4. `rag → shared` is an already-permitted import direction per the layer contract in `AGENTS.md` (`rag → db, shared`), so switching these imports to `shared.types` introduces no new architecture violation.

## Implementation

### Target file

1. `scripts/agent/turn_result.py`
2. `scripts/agent/orchestrator.py`
3. `scripts/rag/types.py`
4. The 9 production files and 11 test files listed in Scope

### Procedure

1. In `scripts/agent/orchestrator.py`, change line 432 from `if not result.success:` to `if result.action != "continue":`.
2. In `scripts/agent/turn_result.py`, delete the `success` property (lines 30-33).
3. In `scripts/rag/types.py`, remove `RagHit`, `MergedHit`, `RankedHit`, `RawHit` from `from shared.types import MergedHit, RagHit, RankedHit, RawHit` and from `__all__`; keep the import line only if any of the remaining names still need it (they don't — remove the import entirely once all four names are gone), and update its docstring to drop the "re-exported here for backward compatibility" sentence.
4. For each of the 9 production files: locate `from rag.types import (...)`, split into two import statements — one `from shared.types import <re-exported names used>` and one `from rag.types import <names still defined there, if any>` — preserving `ruff` import-order (`I` rules, isort-compatible) by running `ruff check --fix` afterward.
5. Repeat step 4 for the 11 test files, including the inline (function-local) `from rag.types import ...` statements inside `tests/test_rag_pipeline_stage.py`.
6. Run `uv run ruff format scripts/ tests/` then `uv run ruff check scripts/ tests/ --fix` to normalize import ordering.
7. Run `PYTHONPATH=scripts uv run lint-imports` — expect 0 violations.
8. Run `grep -rn "from rag.types import" scripts tests --include="*.py"` — expect matches only for `RagQuery`, `PipelineRunResult`, `SearchDiagnostics` (never `RagHit`, `MergedHit`, `RankedHit`, `RawHit`).

### Method

Caller rewrite before shim removal: first change the one production call site of `TurnResult.success`, then delete the property; first change all 20 import sites of the `rag.types` re-export, then delete the re-export. This ordering keeps the codebase importable/runnable at every intermediate step if work is interrupted.

### Details

- `TurnResult.success` is a one-line boolean derived from `action`; `result.action != "continue"` is the exact negation of the current `not result.success` check, so behavior is unchanged.
- The `rag.types` split must be done per-file because some files import a mix of re-exported names (`RawHit`, `MergedHit`, `RankedHit`, `RagHit`) and genuinely local names (`RagQuery`, `PipelineRunResult`, `SearchDiagnostics`) in a single multi-line `from rag.types import (...)` statement — these need two separate import lines after the change.
- `tests/test_rag_pipeline_stage.py` has 8 separate `from rag.types import ...` statements scattered across individual test functions (not one module-level import) — each needs to be checked and updated independently.
- After this change, `scripts/rag/types.py` keeps only `RagQuery`, `PipelineRunResult`, `SearchDiagnostics` and drops its dependency on `shared.types` entirely (unless `SearchDiagnostics` or another local type internally references one of the removed names — verify this at implementation time and keep a `shared.types` import for that internal use only if needed).

## Validation plan

```bash
uv run ruff format scripts/ tests/
uv run ruff check scripts/ tests/
uv run mypy scripts/
PYTHONPATH=scripts uv run lint-imports
uv run pytest tests/test_orchestrator.py tests/test_rag_pipeline.py tests/test_rag_pipeline_stage.py \
  tests/test_rag_repository.py tests/test_rag_pipeline_mcp_service.py tests/test_rag_refiner.py \
  tests/test_rag_stages.py tests/test_rag_quality_regression.py tests/test_agent_rag.py \
  tests/test_rag_http_mode.py tests/test_pipeline_http_result_kind.py tests/test_rag_get_cfg.py -v
grep -rn "\.success\b" scripts/agent/orchestrator.py   # expect no output (was TurnResult.success usage)
grep -rn "from rag.types import" scripts tests --include="*.py" | grep -E "RagHit|MergedHit|RankedHit|RawHit"   # expect no output
```

Expected outcome: all listed tests pass, `lint-imports` reports 0 violations, and no remaining import references `RagHit`/`MergedHit`/`RankedHit`/`RawHit` via `rag.types`.
