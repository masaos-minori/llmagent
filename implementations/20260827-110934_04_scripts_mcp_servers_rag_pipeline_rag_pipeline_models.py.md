## Goal

Align `RagPipelineConfig`'s five divergent dataclass field defaults (and their
matching `from_dict` fallback literals) with `config/rag_pipeline_mcp_server.toml`'s
operational values (REQ-002, M-7), per `plans/20260826-115018_plan.md`.

## Scope

- In scope: the dataclass defaults and `from_dict` fallback literals for
  `top_k_search`, `top_k_rerank`, `rag_min_score`, `semantic_cache_max_size`, and
  `refiner_max_chars_per_chunk` in this one file.
- Out of scope: `RagPipelineConfig.from_dict`'s pre-existing bare `int()`/`float()`
  coercions (a real but unrelated `rules/coding.md` Type-coercion policy violation —
  explicitly out of scope per this Plan; do not fix incidentally while touching
  adjacent lines); any other `RagPipelineConfig` field (all others already verified
  to match the TOML, per this Plan's Problem section); any file-read-mcp change
  (REQ-001, separate target files).

## Assumptions

- `config/rag_pipeline_mcp_server.toml`'s current values for the five fields are
  `top_k_search=20`, `top_k_rerank=15`, `rag_min_score=2.0`,
  `semantic_cache_max_size=100`, `refiner_max_chars_per_chunk=300` — re-verified
  2026-08-27 at lines 42, 45, 51, 57, 62.
- The only production constructors of `RagPipelineConfig` are `from_dict`/`load`
  (via `rag_pipeline_server.py`/`rag_pipeline_service.py`) — re-verified 2026-08-27;
  no production code constructs `RagPipelineConfig()` directly.
- **Correction found during this procedure's own adversarial verification
  (2026-08-27)**: this Plan's Risk-mitigation claim that "every test file ...
  passes explicit values for these five fields" is **false** for
  `tests/mcp_servers/rag_pipeline/test_rag_pipeline_mcp_service.py`'s
  `test_defaults_when_cfg_empty`, which hardcodes assertions against the current
  (pre-this-change) defaults. That test is a separate target file in this same pass
  (seq 07) and MUST be updated together with this file, or it will fail.

## Design decisions

- Align defaults directly in `RagPipelineConfig` itself (not a new "centralized
  canonical config values" abstraction) — per this Plan's Design > "M-7 decision",
  this keeps `RagPipelineConfig()` the single source of truth with zero extra
  indirection.
- Change both the dataclass field default AND the matching `from_dict` fallback
  literal for each of the five fields, so `RagPipelineConfig()` and
  `RagPipelineConfig.from_dict({})` agree (mirrors the file-read-mcp fix's same
  dual-default consistency requirement).

## Alternatives considered

- Annotating each divergence with a comment and centralizing canonical values in a
  new location was considered and rejected (per this Plan's Design > "M-7
  decision") — no existing pattern to extend, would be an unrequested architectural
  change for no additional safety over a direct default alignment plus a guard test.

## Implementation
### Target file
`scripts/mcp_servers/rag_pipeline/rag_pipeline_models.py`

### Procedure
1. Change the five dataclass field defaults (verified 2026-08-27 at lines 54, 55,
   57, 59, 63): `top_k_search: int = 5` → `20`; `top_k_rerank: int = 10` → `15`;
   `rag_min_score: float = 0.0` → `2.0`; `semantic_cache_max_size: int = 128` →
   `100`; `refiner_max_chars_per_chunk: int = 800` → `300`.
2. Change the matching `from_dict` fallback literals (verified 2026-08-27 at lines
   85, 86, 88, 90, 94): `d.get("top_k_search", 5)` → `20`; `d.get("top_k_rerank",
   10)` → `15`; `d.get("rag_min_score", 0.0)` → `2.0`; `d.get(
   "semantic_cache_max_size", 128)` → `100`; `d.get("refiner_max_chars_per_chunk",
   800)` → `300`.
3. Do not touch the bare `int()`/`float()` wrapper calls themselves (lines 85-94) —
   only their fallback literal arguments; the coercion-style violation itself is out
   of scope.
4. Run `uv run pytest tests/mcp_servers/rag_pipeline/ -v` (will fail on
   `test_defaults_when_cfg_empty` until the seq 07 test-file item in this pass is
   also applied).

### Method
Direct code edits (Edit tool) — five dataclass default values, five `from_dict`
fallback literals.

### Details
Current code (verified 2026-08-27):
```python
    top_k_search: int = 5           # line 54
    top_k_rerank: int = 10          # line 55
    rag_min_score: float = 0.0      # line 57
    semantic_cache_max_size: int = 128   # line 59
    refiner_max_chars_per_chunk: int = 800  # line 63
    ...
    top_k_search=int(d.get("top_k_search", 5)),                       # line 85
    top_k_rerank=int(d.get("top_k_rerank", 10)),                      # line 86
    rag_min_score=float(d.get("rag_min_score", 0.0)),                 # line 88
    semantic_cache_max_size=int(d.get("semantic_cache_max_size", 128)), # line 90
    refiner_max_chars_per_chunk=int(d.get("refiner_max_chars_per_chunk", 800)), # line 94
```
Change the literal defaults only (keep field names, types, and the `int()`/`float()`
wrapper calls unchanged):
```python
    top_k_search: int = 20
    top_k_rerank: int = 15
    rag_min_score: float = 2.0
    semantic_cache_max_size: int = 100
    refiner_max_chars_per_chunk: int = 300
    ...
    top_k_search=int(d.get("top_k_search", 20)),
    top_k_rerank=int(d.get("top_k_rerank", 15)),
    rag_min_score=float(d.get("rag_min_score", 2.0)),
    semantic_cache_max_size=int(d.get("semantic_cache_max_size", 100)),
    refiner_max_chars_per_chunk=int(d.get("refiner_max_chars_per_chunk", 300)),
```
Note: `build_rag_cfg_adapter` (lines 124-133) reads these same five attributes off an
already-constructed `RagPipelineConfig` instance (`cfg.top_k_search`, etc.) — it
requires no change since it reflects whatever value the instance already holds.

## Compatibility considerations

- Changes the effective default behavior for any caller that constructs
  `RagPipelineConfig()` directly (bypassing `from_dict`/`load`) — per Assumptions,
  no production caller does this, but `tests/mcp_servers/rag_pipeline/
  test_rag_pipeline_mcp_service.py::test_defaults_when_cfg_empty` does, and MUST be
  updated in the same change (seq 07, this same pass).
- No live production effect today since `config/rag_pipeline_mcp_server.toml`
  always supplies these five values (per this Plan's Background) — this change only
  affects the fallback path.

## Security considerations

- N/A: no security-relevant behavior; `rag_min_score`/`top_k_*` affect retrieval
  ranking/filtering quality, not an access-control or trust boundary.

## Rollback considerations

- Ten-literal revert via `git diff`/`git checkout -- scripts/mcp_servers/rag_pipeline/rag_pipeline_models.py`;
  must be reverted together with the seq 06/07 test files in this same pass, since
  `test_defaults_when_cfg_empty` (seq 07) will otherwise assert against defaults
  that no longer exist.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `scripts/mcp_servers/rag_pipeline/rag_pipeline_models.py` | Unit | `uv run pytest tests/mcp_servers/rag_pipeline/test_rag_pipeline_models.py -v` | `RagPipelineConfig()`'s 5 fields equal the operational TOML values; passes once seq 06 test-file item is also applied |
| `scripts/mcp_servers/rag_pipeline/rag_pipeline_models.py` | Regression | `uv run pytest tests/mcp_servers/rag_pipeline/test_rag_pipeline_mcp_service.py -v` | `test_defaults_when_cfg_empty` passes once seq 07 test-file item is also applied |

## Completion criteria

- `RagPipelineConfig()`'s five named fields equal `20`, `15`, `2.0`, `100`, `300`
  respectively.
- `RagPipelineConfig.from_dict({})`'s five named fields equal the same values.

## Out of scope

- `RagPipelineConfig.from_dict`'s bare-coercion pattern (`int()`/`float()` wrapper
  calls themselves).
- Any other `RagPipelineConfig` field.
- Any file-read-mcp change.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Change 5 dataclass field defaults | Pending | — | — | |
| 2 | Change 5 matching `from_dict` fallback literals | Pending | — | — | |
| 3 | Run `uv run pytest tests/mcp_servers/rag_pipeline/ -v` | Pending | — | — | Requires seq 06 and seq 07 test-file items applied first |

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
- **Requirement ID**: REQ-002
- **Source issue**: `issues/20260821_05_issue.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260826-115018_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260827-110934
- **Related target files**: `scripts/mcp_servers/rag_pipeline/rag_pipeline_models.py`
