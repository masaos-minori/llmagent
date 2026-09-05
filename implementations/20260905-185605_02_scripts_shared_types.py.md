## Goal
Remove `semantic_cache_max_size`, `semantic_cache_threshold`, and `use_semantic_cache`
attribute declarations from the shared `RagConfig` `Protocol` (`scripts/shared/types.py`),
so the structural contract no longer requires the three removed fields (`REQ-001`).

## Scope
- **In-Scope**: remove the three `Protocol` attribute declarations
  (`semantic_cache_max_size: int`, line 88; `semantic_cache_threshold: float`, line 89;
  `use_semantic_cache: bool`, line 106).
- **Out-of-Scope**: every other attribute in the `RagConfig` `Protocol` — confirmed
  unrelated by reading the full class; the class docstring's description of concrete
  implementations (`RagConfigImpl`, `RagPipelineConfig`'s adapter) — no change needed,
  since it names the DTOs by module path, not by field.

## Assumptions
- Same hard ordering dependency as procedure document `01`: this change must not be
  applied until `semcacherm` has landed and `scripts/rag/pipeline.py` no longer reads
  `self._cfg.semantic_cache_max_size`/`semantic_cache_threshold`/`use_semantic_cache`
  via this structural protocol.
- Because `RagConfig` is a `Protocol` (structural typing, not nominal inheritance), no
  class explicitly declares `class RagConfigImpl(RagConfig):` — removing fields here
  has no direct runtime effect on any concrete class; its effect is purely on static
  type-checking (`mypy`) of any code that type-hints a parameter as `RagConfig`.

## Design decisions
(per `skills/python-design/SKILL.md` Final Output §6, narrow bullet only)
- Remove all three attributes together, mirroring procedure document `01`'s removal
  from `RagConfigImpl` — the protocol and its concrete implementation must stay in
  sync, since `RagConfigImpl`/`RagPipelineConfig`'s adapter are both expected to
  satisfy this `Protocol` structurally.

## Alternatives considered
N/A: straightforward attribute removal from a `Protocol` with no remaining concrete
field to satisfy.

## Implementation
### Target file
`scripts/shared/types.py`

### Procedure
1. Re-verify `semcacherm` has landed (Assumptions) before proceeding.
2. Remove `semantic_cache_max_size: int` (line 88).
3. Remove `semantic_cache_threshold: float` (line 89).
4. Remove `use_semantic_cache: bool` (line 106).

### Method
Direct removal via `Edit` on a `Protocol` class body — no `__init__` or constructor
logic exists to update (`Protocol` classes declare structure only).

### Details
- Confirm after editing: `rg -n
  "semantic_cache_max_size|semantic_cache_threshold|use_semantic_cache"
  scripts/shared/types.py` returns zero matches.
- Since this is structural typing, removing an attribute from the `Protocol` does not
  by itself break any concrete class — it only means `mypy` will no longer require (or
  recognize) that attribute when checking code typed against `RagConfig`. The actual
  runtime effect comes from procedure documents `01` (`RagConfigImpl`) and the
  `RagPipelineConfig` document removing the concrete fields.

## Compatibility considerations
- Any code that currently type-hints a `RagConfig`-typed parameter and reads one of
  the three removed attributes will fail `mypy` type-checking after this change (by
  design — this surfaces any missed call site as a static-analysis failure rather than
  a runtime `AttributeError`).

## Security considerations
N/A: no security-sensitive code path is touched.

## Rollback considerations
- Revert via `git checkout` on this single file; should be reverted together with
  procedure document `01` (`RagConfigImpl`) to keep the protocol and its primary
  concrete implementation in sync.

## Validation plan
- `uv run mypy scripts/` — no new type errors; confirms no remaining code type-hints
  against `RagConfig` while still reading a removed attribute.
- `rg -n "semantic_cache_max_size|semantic_cache_threshold|use_semantic_cache"
  scripts/shared/types.py` — zero matches.

## Completion criteria
- The `RagConfig` `Protocol` no longer declares any of the three removed attributes
  (Plan `AC-2`).
- `uv run mypy scripts/` passes with no new findings attributable to this change.

## Out of scope
- `scripts/rag/models_config.py`'s `RagConfigImpl` (procedure document `01`).
- Any test file — Plan's evidence states "none directly" tests this protocol.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Blocked until `semcacherm` lands — see Assumptions |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: no direct test targets this protocol |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: documentation deferred to `semcachedocs` |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | Depends on `semcacherm`'s implementation landing first | No | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-001` (remove the three fields from the shared `RagConfig` protocol)
- **Source issue**: issues/20260902-150340_semcacheconfig_remove_semanticcache_settings_from_config_contracts.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260904-141001_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260905-185605
- **Related target files**: scripts/shared/types.py
