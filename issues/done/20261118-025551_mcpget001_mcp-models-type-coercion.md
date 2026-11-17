# MCP `*_models.py` config loaders bypass `get_typed` with bare int/float coercion

## Priority
Medium

## Summary
Replace the bare `int()` / `float()` / `list()` coercions in the MCP server `*_models.py` config loaders with `get_typed`-style validation so wrong-typed TOML values raise a clear error instead of being silently coerced. Covers `CicdConfig.from_dict`, `GitHubConfig.from_dict`, and `RagPipelineConfig.from_dict` (and the re-coercing `build_rag_cfg_adapter`).

## Background
`rules/coding.md` "Type-coercion policy" prohibits bare `int()`, `float()`, and `list()` coercions in config loading because they silently accept wrong types (for example `1048576.0` -> `1048576`, `True` -> `1`) and documents the mandated pattern: `get_typed(d, "field_name", int, "an integer", default=DEFAULT)`. The policy names `*_models.py` config loaders explicitly. `shared.config_utils.get_str` already exists for string fields, but the numeric/boolean/list fields in the MCP config loaders still use bare coercions. A prior adversarial review (`issues/done/20261103-134147_wfreview003_workflow-loader-bare-int-coercion.md`) fixed the same class of defect in `workflow_loader.py`, which lies outside the `*_models.py` naming scope, but the MCP `*_models.py` loaders were not in that scope.

## Problem
The three MCP `*_models.py` loaders construct their dataclasses with bare coercions of raw TOML values:
- `CicdConfig.from_dict` coerces `max_log_size_kb` with `int(...)` and the allowlists with `list(...)`.
- `GitHubConfig.from_dict` coerces several integer fields with `int(...)`, booleans with `bool(...)`, and lists with `list(...)`.
- `RagPipelineConfig.from_dict` coerces many integer fields with `int(...)` and float fields with `float(...)`, and scalar strings with `str(...)`.
- `build_rag_cfg_adapter` re-coerces the same numeric fields with bare `int()` / `float()` when bridging to the RAG runtime contract.

`get_typed` raises `ValueError` with a clear message when a value has the wrong type, whereas `int(1048576.0)` truncates, `int(True)` yields `1`, and `int("30")` succeeds. A malformed TOML value therefore produces a silently wrong configuration value instead of a fail-fast load error.

## Reason for Change
The config loader is the boundary that should reject bad configuration before any process starts. Bare coercions defeat that boundary for every numeric/boolean/list field, and the silent-truncation failure mode is exactly what `rules/coding.md` prohibits. The fix is mechanical (replace each coercion with `get_typed`) and low-risk, and it removes an untested assumption that TOML values already have the expected type.

## Implementation Intent
Route every typed field in the three `from_dict` methods through `get_typed` with a mandatory `default=` argument, matching the documented pattern. Preserve the existing `get_str` usage for string fields and the existing fail-fast `load()` guards (for example `GitHubConfig.load`'s empty `protected_branches` check). Apply the same change to the numeric re-coercions in `build_rag_cfg_adapter` so the bridge does not reintroduce bare coercions. Do not change the dataclass field definitions, defaults, or public `load()` behavior beyond raising `ValueError` on wrong types.

## Target Files or Areas
- `scripts/mcp_servers/cicd/cicd_models.py` (`CicdConfig.from_dict`)
- `scripts/mcp_servers/github/github_models_config.py` (`GitHubConfig.from_dict`)
- `scripts/mcp_servers/rag_pipeline/rag_pipeline_models.py` (`RagPipelineConfig.from_dict`, `build_rag_cfg_adapter`)
- `scripts/shared/config_utils.py` (`get_typed` — confirm signature/availability)
- `tests/mcp_servers/**` covering the three loaders

## Required Changes
- Replace each bare `int()` / `float()` coercion in the three `from_dict` methods with `get_typed(...)` carrying a `default=`.
- Replace the bare `list()` coercions for the allowlist/denylist fields with `get_typed(...)` for a list type (or the project's sanctioned list-validation helper) where a typed result is required.
- Apply the same replacement to the numeric coercions in `build_rag_cfg_adapter`.
- Add or update unit tests asserting that a wrong-typed value raises `ValueError` and that a missing key returns the default.

## Constraints
- Preserve existing valid-config behavior exactly: correct values and defaults must be unchanged.
- `get_typed`'s `default=` parameter is mandatory (omitting it means "reject missing keys"); do not omit it.
- Do not change the Pydantic request/response models or their `Field` constraints.
- Preserve `GitHubConfig.load`'s fail-closed empty `protected_branches` check.

## Acceptance Criteria
- No bare `int()` / `float()` / `list()` coercion remains in the three `from_dict` methods or in `build_rag_cfg_adapter`.
- A wrong-typed TOML value for a numeric/boolean/list field raises `ValueError` with a clear message.
- A missing key returns the documented default.
- Existing valid-config unit tests pass unmodified.

## Testing Expectations
- Unit: assert `get_typed`-backed coercion raises `ValueError` on a float given for an `int` field, on a string given for an `int` field that cannot parse, and on a wrong list type; assert missing-key defaults.
- Run `uv run pytest` over the affected MCP server test paths and confirm no regression.
- `uv run ruff check` and `uv run mypy` clean on the changed files.

## Documentation Impact
None expected. If `get_typed` is not yet exported from `shared.config_utils`, documenting its signature there is in scope; otherwise no doc change.

## Out of Scope
- Any change to `workflow_loader.py` (already covered by `wfreview003`).
- Adding new config fields or changing existing field types/defaults.
- Refactoring the Pydantic request/response models.

## Dependencies
N/A: none

## Unresolved Questions
- Whether the `list()` fields should go through `get_typed` with a list type or a dedicated list-validation helper in `shared.config_utils`; confirm `get_typed` supports a list type before implementing.

## AI Implementation Instruction
Read `rules/coding.md` "Type-coercion policy" and `shared.config_utils` before editing. Replace only the bare `int()` / `float()` / `list()` coercions in the three `from_dict` methods and in `build_rag_cfg_adapter` with `get_typed(...)` carrying a `default=`. Do not touch the Pydantic models, field definitions, or `load()` guards beyond what the coercion replacement requires. Add a wrong-typed-value test per loader. Stop and report if `get_typed` does not support the list type needed for the allowlist fields.

## Traceability
- **Workflow phase**: python-code-review → issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261118-025551
- **Related target files**: `scripts/mcp_servers/cicd/cicd_models.py`, `scripts/mcp_servers/github/github_models_config.py`, `scripts/mcp_servers/rag_pipeline/rag_pipeline_models.py`
