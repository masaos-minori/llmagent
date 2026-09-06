## Goal
Add module-level `resolve_rag_config(cfg, *, module_cfg=None, config_loader=None) ->
RagConfigImpl` to `scripts/rag/pipeline.py` (REQ-001), delegate `RagPipeline.__init__`
to it, remove the `_ModuleConfig` class (REQ-002), and remove the redundant
`cast(RagConfig, self._cfg)` (REQ-003) — with no change to the constructor's public
signature or runtime config-resolution behavior.

## Scope
- In scope: `resolve_rag_config()` addition; `__init__`'s config-resolution block
  replaced with a delegated call; `_ModuleConfig` class removal; the redundant cast
  removal.
- Out of scope: `RagConfigValidator`/`RagConfigImpl` internals; any other
  `RagPipeline` method (`search_queries`, `rerank_candidates`, `run`, `augment`,
  `get_diagnostics`, `invalidate_cache`); `AugmentRefiner`/`SemanticCache`
  initialization logic; the comment update in `rag_pipeline_service.py` (tracked in
  seq 02); the 4 test file updates (tracked in seq 03-06).

## Assumptions
- **Line-citation drift found this cycle (2026-09-06)** — confirmed by direct read of
  `scripts/rag/pipeline.py` (lines 1-220): every line number the Plan cites for this
  file is consistently off by approximately one line versus the current file:
  - `_ModuleConfig` actually spans lines 63-77 (Plan states 64-78).
  - `RagPipeline.__init__` actually spans lines 91-211, 121 lines (Plan states
    92-217, 126 lines).
  - The config-resolution block actually spans lines 117-178 (Plan states 118-179).
  - `self._cfg: RagConfig`'s declaration is actually at line 118 (Plan states line
    119).
  - The fallback-branch cast (`cast(RagConfig, RagConfigImpl(**_raw_cfg))`) is
    actually at line 178 (Plan's Problem section states line 179).
  - **The redundant cast REQ-003 targets is actually at line 182**
    (`cfg=cast(RagConfig, self._cfg)`, inside the `RagLLM(...)` call) — **not line 188**
    as stated in the Plan's Problem section, Requirements (REQ-003), Implementation
    Target Files row, Acceptance criteria (AC-4), and Requirement Traceability. This is
    a one-line-consistent citation drift, not a scope or logic error: the described
    code (an isolated, unnecessary `cast(RagConfig, self._cfg)` passed into
    `RagLLM(...)`, redundant because `self._cfg`'s declared type is already
    `RagConfig` by that point) matches the actual line 182 content exactly. Non-blocking
    per `rules/ai-execution.md` Step 3c: proceeding with the corrected line number
    rather than stopping.
  - This document uses the verified current line numbers throughout, not the Plan's
    stated ones. The Plan document itself (`plans/20260906-115512_plan.md`) is not
    edited by this row — a parallel row-processing pass is active on the same Plan
    file this cycle; the discrepancy is reported here for central reconciliation
    rather than risking a concurrent edit conflict.
- `resolve_rag_config`'s `config_loader` parameter is a zero-argument callable
  returning a `dict`, matching `ConfigLoader().load_all()`'s current return shape (Plan
  Assumptions, inferred from the Implementation Intent's behavior-preservation
  requirement).
- Config-validation warning/error logging and the `RagConfigValidator` call move into
  `resolve_rag_config` alongside the resolution logic (Plan Assumptions).
- `resolve_rag_config` returns `RagConfigImpl` directly, not a dict (Plan Assumptions).

## Design decisions
- Extract lines 117-178 (config-resolution: 3 input-type handling, 14-field
  defaulting, `RagConfigValidator` call, warning/error logging, `ValueError` raise) into
  a new module-level function `resolve_rag_config(cfg, *, module_cfg=None,
  config_loader=None) -> RagConfigImpl`, preserving priority order `cfg` (already
  `RagConfigImpl`) > `cfg` (`dict`) > `cfg` (object with `__dict__`) > `module_cfg` >
  `config_loader()` (defaults to `ConfigLoader().load_all()` when `config_loader` is
  `None`).
- `_ModuleConfig.get()`'s `except (FileNotFoundError, ValueError): cls._cache = {}`
  catch (lines 74-76) moves into `resolve_rag_config`'s default `config_loader` branch
  unchanged.
- `RagPipeline.__init__` reduces its config-resolution portion to
  `self._cfg = resolve_rag_config(cfg, module_cfg=module_cfg)`; all other constructor
  responsibilities (HTTP client, callbacks, per-run state fields, `RagLLM`/
  `AugmentRefiner` instantiation, startup logging) are unchanged.
- `_ModuleConfig` (lines 63-77) is deleted entirely; its role is replaced by
  `resolve_rag_config`'s injectable `config_loader` parameter.
- The redundant cast at (actual) line 182 is removed — `self._cfg`'s declared type
  (`RagConfig`, line 118) is already satisfied by either branch's assignment, so no
  cast is needed at the `RagLLM(...)` call site.

## Alternatives considered
- Keep `_ModuleConfig` as a thin wrapper calling `resolve_rag_config` internally,
  for backward compatibility: rejected — the Plan's REQ-002 explicitly requires full
  removal, and no external caller of `_ModuleConfig` exists outside this file and the
  4 target test files (all in scope of this same Plan).
- Leave the line-182 cast in place since it is harmless: rejected — Plan REQ-003 and
  AC-4 explicitly require its removal as part of this same Plan; leaving it would
  fail AC-4.

## Implementation
### Target file
`scripts/rag/pipeline.py`

### Procedure
1. Add `resolve_rag_config(cfg, *, module_cfg=None, config_loader=None) ->
   RagConfigImpl` as a new module-level function, placed after the `_ModuleConfig`
   class's current location (before it is deleted) or directly before `RagPipeline`,
   containing:
   - The 3-input-type priority resolution currently at lines 119-128.
   - The 14-field default-filling currently at lines 130-167.
   - The `RagConfigValidator().validate()` call and warning/error logging currently
     at lines 168-177.
   - The default `config_loader` fallback: when `config_loader` is `None`, call
     `ConfigLoader().load_all()` wrapped in the same
     `except (FileNotFoundError, ValueError)` catch `_ModuleConfig.get()` uses today
     (lines 74-76), returning `{}` on failure.
   - Return `RagConfigImpl(**_raw_cfg)` for the non-`RagConfigImpl`-input path, or
     `cfg` directly when `cfg` is already a `RagConfigImpl` (line 119-120's current
     behavior).
2. Replace `RagPipeline.__init__`'s lines 117-178 (the `self._cfg: RagConfig`
   declaration through the fallback-branch cast) with
   `self._cfg = resolve_rag_config(cfg, module_cfg=module_cfg)`.
3. Delete the `_ModuleConfig` class (lines 63-77).
4. Remove the cast at (actual) line 182: change
   `cfg=cast(RagConfig, self._cfg),` to `cfg=self._cfg,` inside the `RagLLM(...)` call.
5. Confirm no other reference to `_ModuleConfig` remains in this file via
   `rg -n "_ModuleConfig" scripts/rag/pipeline.py` (expect zero matches after the
   edit).

### Method
Confirmed this cycle (2026-09-06) via direct read of `scripts/rag/pipeline.py` lines
1-220: `_ModuleConfig` (lines 63-77), `RagPipeline.__init__` (lines 91-211),
config-resolution block (lines 117-178), redundant cast (line 182, inside the
`RagLLM(...)` call spanning lines 179-183). See Assumptions for the full line-citation
drift versus the Plan's stated numbers.

### Details
No change to `SemanticCache`, `RagLLM`, or `AugmentRefiner` instantiation logic beyond
the single cast removal at the `RagLLM(...)` call site — their call sites and argument
values are otherwise unchanged.

## Compatibility considerations
`RagPipeline.__init__`'s public signature (`http`, `cfg`, `module_cfg`, `on_status`,
`on_clear`) is unchanged (Plan AC-5). `resolve_rag_config` is a new public
module-level symbol; no existing caller is broken by its addition. Removing
`_ModuleConfig` is a breaking change only for the 4 test files that directly
reference it — tracked as their own rows (seq 03-06) in this same Plan.

## Security considerations
N/A: no new external input, credential, or network access is introduced;
`resolve_rag_config` wraps the same `ConfigLoader`/`RagConfigValidator` calls
`__init__` already performs.

## Rollback considerations
Revert via `git checkout scripts/rag/pipeline.py` alone if validation
(`uv run pytest tests/rag/test_rag_pipeline.py tests/agent/test_rag_get_cfg.py
tests/rag/test_stage_observability.py tests/rag/test_rag_quality_regression.py`)
fails after this row's change — the 4 test-file rows (seq 03-06) depend on this row
landing first, so a revert here also requires deferring those rows' own changes.

## Validation plan
- `uv run pytest tests/rag/test_rag_pipeline.py tests/agent/test_rag_get_cfg.py tests/rag/test_stage_observability.py tests/rag/test_rag_quality_regression.py -v` — all pass (Plan-stated baseline: 59/59 passed pre-change).
- `uv run pytest -v` — full suite, no new failures.
- `uv run mypy scripts/rag/pipeline.py` — no new errors.
- `uv run ruff check scripts/rag/pipeline.py` — clean.
- `PYTHONPATH=scripts uv run lint-imports` — pass, no new `rag → agent`/`mcp_servers` violation.
- `uv run bandit -r scripts/rag/pipeline.py -c pyproject.toml` — no new high/medium findings (Plan-stated baseline: 0 issues).
- `uv run coverage run -m pytest tests/ && uv run coverage xml && uv run diff-cover coverage.xml --compare-branch=master --fail-under=90` — ≥ 90% on changed lines.
- `rg "RagConfigImpl\(\*\*.*_raw_cfg" scripts/rag/` — no matches outside `resolve_rag_config`'s own body.

## Completion criteria
- `resolve_rag_config()` exists as a module-level function handling all 3 input types
  and returning a validated `RagConfigImpl` (AC-1).
- `RagPipeline.__init__` contains no inline config-resolution logic; it delegates via
  `self._cfg = resolve_rag_config(cfg, module_cfg=module_cfg)` (AC-2).
- `_ModuleConfig` no longer exists in this file (AC-3).
- No `cast(RagConfig, self._cfg)` remains anywhere in `__init__` (AC-4).
- `__init__`'s public signature, exceptions, and warning/error log messages are
  unchanged (AC-5).
- `uv run mypy`/`uv run ruff check` report no new errors (AC-7).
- `rg "RagConfigImpl\(\*\*.*_raw_cfg" scripts/rag/` returns no matches outside
  `resolve_rag_config`'s body (AC-8).

## Out of scope
- `scripts/mcp_servers/rag_pipeline/rag_pipeline_service.py`'s stale comment — tracked
  in seq 02.
- The 4 test files referencing `_ModuleConfig` — tracked in seq 03-06.
- `RagConfigValidator`/`RagConfigImpl` internals — read-only reference for this row.

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
- **Requirement ID**: REQ-001, REQ-002, REQ-003
- **Source issue**: issues/20260905-192946_refactor_ragpipeline_responsibility_boundaries.md
- **Source plan**: plans/20260906-115512_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260906-152050
- **Related target files**: scripts/rag/pipeline.py
