## Goal
Replace the bare `int()` / `float()` / `list()` coercions in the MCP server `*_models.py` config loaders with `get_typed`-style validation so a wrong-typed TOML value raises `ValueError` instead of being silently coerced. Covers `CicdConfig.from_dict`, `GitHubConfig.from_dict`, `RagPipelineConfig.from_dict`, and the re-coercing `build_rag_cfg_adapter`.

## Priority
Medium

## Scope
- **In-Scope**:
  - Replace every bare `int()` / `float()` coercion in `CicdConfig.from_dict`, `GitHubConfig.from_dict`, and `RagPipelineConfig.from_dict` with `get_typed(...)` carrying an explicit `default=` matching the dataclass default.
  - Replace the bare `list()` coercions for the allowlist/denylist fields with `list(get_typed(...))` using the project's sanctioned pattern (`list(get_typed(d, key, list, "a list", default=[]))`).
  - Replace the bare `int()` / `float()` re-coercions in `build_rag_cfg_adapter` with pass-through of the already-typed `RagPipelineConfig` fields (no dict/key exists there, so `get_typed` does not apply; passing the validated value through removes the bare coercion).
  - Update the two RAG characterization tests that assert the old coercion behavior (see Tests).
  - Add one wrong-typed-value test per loader asserting `ValueError`.
- **Out-of-Scope**:
  - Any change to `workflow_loader.py` (already covered by `issues/done/20261103-134147_wfreview003_...`).
  - Changing Pydantic request/response models or their `Field` constraints.
  - Changing dataclass field definitions, defaults, or public `load()` behavior beyond raising `ValueError` on wrong types.
  - Replacing the scalar `str(...)` / retained `bool(...)` coercions (see Assumptions).
- **Dependencies**:
  - **Depends on**: `issues/done/20261103-134147_wfreview003_workflow-loader-bare-int-coercion.md` | phase all | prior fix of the same defect class in `workflow_loader.py`; already archived, no sequencing constraint.

## Background
`rules/coding.md` "Type-coercion policy" prohibits bare `int()`, `float()`, and `list()` coercions in config loading because they silently accept wrong types (`1048576.0` → `1048576`, `True` → `1`) and mandates `get_typed(d, "field_name", int, "an integer", default=DEFAULT)`. The policy states every `*_models.py` config loader MUST use `get_typed`-style validation for typed fields. `shared.config_utils.get_str` already covers string fields, and other MCP servers (`git`, `file`, `web_search`) already route int/float/bool/list through `get_typed`. The MCP config loaders named here still use bare coercions, and `get_typed`'s `default=` parameter is mandatory (omitting it means "reject missing keys").

## Problem
The three MCP `*_models.py` loaders construct their dataclasses with bare coercions of raw TOML values:
- `CicdConfig.from_dict`: `max_log_size_kb` via `int(...)`, `repo_allowlist`/`workflow_allowlist` via `list(...)`.
- `GitHubConfig.from_dict`: several int fields via `int(...)`, lists via `list(...)`.
- `RagPipelineConfig.from_dict`: many int fields via `int(...)`, float fields via `float(...)`.
- `build_rag_cfg_adapter`: re-coerces the same numeric fields with bare `int()` / `float()` when bridging to the RAG runtime contract.

`get_typed` raises `ValueError` with a clear message on a wrong type, whereas `int(1048576.0)` truncates, `int(True)` yields `1`, and `int("30")` succeeds. A malformed TOML value therefore produces a silently wrong configuration value instead of a fail-fast load error at the config boundary.

## Reason for Change
The config loader is the boundary that must reject bad configuration before any process starts. Bare coercions defeat that boundary for every numeric/boolean/list field, and the silent-truncation failure mode is exactly what `rules/coding.md` prohibits. The fix is mechanical and removes an untested assumption that TOML values already have the expected type.

## Implementation Intent
Route every typed field in the three `from_dict` methods through `get_typed` with a mandatory `default=` argument matching the dataclass default, mirroring the existing pattern in `scripts/mcp_servers/git/git_models.py` and `scripts/mcp_servers/file/*.py`. Preserve the existing `get_str` usage for string fields and the existing fail-fast `load()` guards (notably `GitHubConfig.load`'s empty `protected_branches` check). In `build_rag_cfg_adapter`, pass the already-validated `RagPipelineConfig` fields through directly (the input is already typed, so no coercion is needed and `get_typed` has no dict/key to operate on). Do not touch the Pydantic models, field definitions, or `load()` guards beyond what the coercion replacement requires.

## Requirements
- `REQ-001`: `CicdConfig.from_dict` routes `max_log_size_kb` through `get_typed(..., int, ..., default=256)` and `repo_allowlist`/`workflow_allowlist` through `list(get_typed(..., list, "a list", default=[]))`; a wrong-typed value raises `ValueError` and a missing key returns the default. (Target: `scripts/mcp_servers/cicd/cicd_models.py`)
- `REQ-002`: `GitHubConfig.from_dict` routes every bare `int()` field through `get_typed(..., int, ..., default=<default>)` and every bare `list()` field through `list(get_typed(..., list, "a list", default=[]))`; wrong type raises `ValueError`, missing key returns default. String fields keep `get_str`. (Target: `scripts/mcp_servers/github/github_models_config.py`)
- `REQ-003`: `RagPipelineConfig.from_dict` routes every bare `int()`/`float()` field through `get_typed(..., int|float, ..., default=<default>)`; wrong type raises `ValueError`, missing key returns default. String fields keep `str(...)`/`get_str` as present. (Target: `scripts/mcp_servers/rag_pipeline/rag_pipeline_models.py`)
- `REQ-004`: `build_rag_cfg_adapter` passes the already-validated `RagPipelineConfig` fields through without bare `int()`/`float()` re-coercion. (Target: `scripts/mcp_servers/rag_pipeline/rag_pipeline_models.py`)
- `REQ-005`: Existing RAG characterization tests that assert the old coercion behavior are updated, and one wrong-typed-value test per loader asserts `ValueError` and missing-key defaults. (Targets: the three test files below)

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/mcp_servers/cicd/cicd_models.py` | Modify | Replace `int()`/`list()` coercions in `CicdConfig.from_dict` with `get_typed(..., default=...)`. | REQ-001 | Bare `int(d.get("max_log_size_kb", 256))` and `list(d.get("repo_allowlist", []))` present in `CicdConfig.from_dict` (checked in Step 2); `get_typed` supports `int`/`list` (checked in Step 2) | `tests/mcp_servers/cicd/test_cicd_models.py` | Verified |
| `scripts/mcp_servers/github/github_models_config.py` | Modify | Replace `int()`/`list()` coercions in `GitHubConfig.from_dict` with `get_typed(..., default=...)`; preserve `get_str` and the `load()` empty-`protected_branches` guard. | REQ-002 | Bare `int()`/`list()`/`bool()` coercions present in `GitHubConfig.from_dict`; fail-closed `protected_branches` check in `load()` (checked in Step 2) | `tests/mcp_servers/github/test_github_server_auth.py` | Verified |
| `scripts/mcp_servers/rag_pipeline/rag_pipeline_models.py` | Modify | Replace `int()`/`float()` coercions in `RagPipelineConfig.from_dict` with `get_typed(..., default=...)`; replace bare `int()`/`float()` in `build_rag_cfg_adapter` with pass-through of validated fields. | REQ-003, REQ-004 | Bare `int()`/`float()` in `RagPipelineConfig.from_dict` and `build_rag_cfg_adapter`; `build_rag_cfg_adapter` called by `rag_pipeline_service.py` (checked in Step 2/3) | `tests/mcp_servers/rag_pipeline/test_rag_pipeline_models.py`, `tests/mcp_servers/rag_pipeline/test_rag_pipeline_mcp_service.py` | Verified |
| `tests/mcp_servers/cicd/test_cicd_models.py` | Modify | Add a wrong-typed-value test asserting `ValueError` and missing-key default. | REQ-005 | `test_cicd_config_from_dict_defaults`/`_populated` exercise `from_dict` with correct types (checked in Step 2) | `scripts/mcp_servers/cicd/cicd_models.py` | Verified |
| `tests/mcp_servers/github/test_github_server_auth.py` | Modify | Add a wrong-typed-value test asserting `ValueError` for a numeric/list field via `GitHubConfig.from_dict`. | REQ-005 | `GitHubConfig.from_dict` is unit-tested here (lines 103-113) (checked in Step 2) | `scripts/mcp_servers/github/github_models_config.py` | Verified |
| `tests/mcp_servers/rag_pipeline/test_rag_pipeline_models.py` | Modify | Update `test_numeric_string_values_are_coerced` (asserts old coercion) to assert `ValueError` instead; update `test_falsy_present_values_are_not_treated_as_missing`'s int-for-float case; add missing-key default assertions. | REQ-005 | `test_numeric_string_values_are_coerced` asserts string→number coercion that the fix removes; `test_falsy_present_values...` passes `rag_min_score: 0` (int) for a float field (checked in Step 2) | `scripts/mcp_servers/rag_pipeline/rag_pipeline_models.py` | Verified |

Rules (see `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan
Freeze) for the full validation procedure):
- One row per file. A directory, glob pattern (`*`, `**`), component/module name, file
  group, or a vague phrase (e.g. "related files", "as necessary", "etc.") MUST NOT
  appear as a row — list each file individually by its exact repository-relative path.
- Record a test, configuration, schema, migration, deployment, or documentation file as
  its own row when it requires modification — do not fold it into the row for the
  source file it accompanies.
- `Validation Status` is `Verified` or `Needs confirmation` per row; every row must be
  `Verified` before this section may be marked `Frozen`.

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same
one-file-per-row discipline as `Implementation Target Files` above — no directories,
glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/shared/config_utils.py` | Source of `get_typed`; confirm signature, `default=` semantics, bool/int/float/list support, and the `isinstance(True, int)` rejection. | `scripts/mcp_servers/cicd/cicd_models.py`, `scripts/mcp_servers/github/github_models_config.py`, `scripts/mcp_servers/rag_pipeline/rag_pipeline_models.py` |
| `scripts/mcp_servers/git/git_models.py` | Canonical precedent applying `get_typed` to `int`/`bool`/`list` config fields. | all loaders |
| `scripts/mcp_servers/file/*.py` | Precedent for the `list(get_typed(d, key, list, "a list", default=[]))` allowlist pattern. | allowlist/denylist fields |
| `scripts/mcp_servers/rag_pipeline/rag_pipeline_service.py` | Consumer of `build_rag_cfg_adapter` (line 108); confirm pass-through preserves the `RagConfig` Protocol contract. | `scripts/mcp_servers/rag_pipeline/rag_pipeline_models.py` |

## Acceptance Criteria
- `AC-001` (REQ-001): No bare `int()` / `list()` remains in `CicdConfig.from_dict`; a wrong-typed `max_log_size_kb` raises `ValueError`; missing keys return defaults.
- `AC-002` (REQ-002): No bare `int()` / `list()` remains in `GitHubConfig.from_dict`; wrong types raise `ValueError`; missing keys return defaults; `GitHubConfig.load` still fails closed on empty `protected_branches`.
- `AC-003` (REQ-003): No bare `int()` / `float()` remains in `RagPipelineConfig.from_dict`; wrong types raise `ValueError`; missing keys return defaults.
- `AC-004` (REQ-004): No bare `int()` / `float()` remains in `build_rag_cfg_adapter`; output still satisfies every `RagConfig` Protocol field.
- `AC-005` (REQ-005): Existing valid-config tests pass unmodified except the two RAG characterization tests that asserted the removed coercion behavior; one wrong-typed-value test per loader is green.

## Tests
- `T-001` (REQ-001): In `tests/mcp_servers/cicd/test_cicd_models.py`, assert `CicdConfig.from_dict({"max_log_size_kb": 1.5})` raises `ValueError`, and that a missing `max_log_size_kb` returns `256`.
- `T-002` (REQ-002): In `tests/mcp_servers/github/test_github_server_auth.py`, assert `GitHubConfig.from_dict({"max_per_page": "x"})` raises `ValueError`, and a missing key returns the default.
- `T-003` (REQ-003): In `tests/mcp_servers/rag_pipeline/test_rag_pipeline_models.py`, assert a float field given a wrong type raises `ValueError`, and missing keys return defaults.
- `T-004` (REQ-005): Update `test_numeric_string_values_are_coerced` to assert `ValueError` on stringly-typed numbers; reconcile `test_falsy_present_values_are_not_treated_as_missing`'s `rag_min_score: 0` (int for a float field) case.
- `T-005`: Run `uv run pytest` over `tests/mcp_servers/cicd`, `tests/mcp_servers/github`, `tests/mcp_servers/rag_pipeline` and confirm no regression; `uv run ruff check` and `uv run mypy` clean on changed files.

## Documentation Impact
N/A: no `docs/*.md` requires updating. The change is internal to config loaders; no public protocol, config key, or operational behavior documented in `docs/` changes.

## Assumptions
- **Scope follows the issue's Acceptance Criteria (bare `int()` / `float()` / `list()` only).** The `bool(...)` coercions present in `GitHubConfig.from_dict` (`allow_force_push`, `require_pr_review`) and `RagPipelineConfig.from_dict` (`use_mqe`, `use_rrf`, `use_rerank`, `use_refiner`) and in `build_rag_cfg_adapter` are retained, because the Acceptance Criteria enumerate only `int()` / `float()` / `list()`. This is a deliberate scope boundary, not an omission: extending to `get_typed(..., bool, ...)` is recommended below but is beyond the frozen acceptance gate.
- `get_typed`'s `default=` is passed explicitly on every call (the policy makes it mandatory; omitting it means "reject missing keys").
- Passing already-typed fields through `build_rag_cfg_adapter` preserves the `RagConfig` Protocol contract, since `RagPipelineConfig` fields are validated at `from_dict`.
- Correct valid-config behavior (values and defaults) is unchanged: `get_typed` returns the same value for a correctly-typed key and the same default for a missing/None key.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether to also replace the `bool(...)` coercions with `get_typed(..., bool, ...)`. The Issue Problem text lists `bool()` among the coercions and `rules/coding.md` mandates `get_typed` for typed fields, but the Acceptance Criteria enumerate only `int()` / `float()` / `list()`. | Author intent on scope. | Confirm with issue author; if unconfirmed, implement `int()` / `float()` / `list()` only per the frozen Acceptance Criteria. | False |
| UNK-02 | Best home file for the `GitHubConfig.from_dict` wrong-typed test (no dedicated `*_models.py` test exists for github). | Implementation convention. | Use `tests/mcp_servers/github/test_github_server_auth.py` (directly exercises `from_dict`) unless a more fitting existing github test file is preferred. | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/mcp_servers/cicd/cicd_models.py` | Modify | Low | 0 | N/A (git-fame not run) | not applicable (rsynced) |
| `scripts/mcp_servers/github/github_models_config.py` | Modify | Low | 1 | N/A (git-fame not run) | not applicable (rsynced) |
| `scripts/mcp_servers/rag_pipeline/rag_pipeline_models.py` | Modify | Medium | 5 | N/A (git-fame not run) | not applicable (rsynced) |
| `tests/mcp_servers/cicd/test_cicd_models.py` | Modify | Low | 0 | N/A (git-fame not run) | not applicable (rsynced) |
| `tests/mcp_servers/github/test_github_server_auth.py` | Modify | Low | 0 | N/A (git-fame not run) | not applicable (rsynced) |
| `tests/mcp_servers/rag_pipeline/test_rag_pipeline_models.py` | Modify | Low | 1 | N/A (git-fame not run) | not applicable (rsynced) |

## Design
All three loaders share one design: route every typed field through
`shared.config_utils.get_typed(d, "<key>", <type>, "<a noun>", default=<default>)`,
where `<default>` equals the dataclass field default, and let `get_typed` raise
`ValueError` on a wrong type. This mirrors the canonical precedent in
`scripts/mcp_servers/git/git_models.py` (e.g. `get_typed(d, "max_log_entries", int,
"an integer", default=50)`, `get_typed(d, "read_only", bool, "a boolean",
default=True)`) and the allowlist pattern in `scripts/mcp_servers/file/*.py`
(`list(get_typed(d, "allowed_dirs", list, "a list", default=[]))`).

Design decisions:
- **Scalar int/float**: replace `int(d.get("k", D))` / `float(d.get("k", D))` with
  `get_typed(d, "k", int, "an integer", default=D)` / `... float, "a float", default=D`.
  `get_typed` returns the value unchanged for a correct type and raises `ValueError`
  otherwise; the mandatory `default=` preserves the missing-key default.
- **Allowlist/denylist**: replace `list(d.get("k", []))` with
  `list(get_typed(d, "k", list, "a list", default=[]))`, the exact `file/*.py` shape.
- **`build_rag_cfg_adapter`**: pass the already-validated `RagPipelineConfig` fields
  through directly. There is no dict/key there, so `get_typed` does not apply; passing
  the validated value removes the bare re-coercion while preserving the `RagConfig`
  Protocol contract (confirmed by `rag_pipeline_service.py` line 108).
- **Preserve**: `get_str`/`str(...)` for string fields, the retained `bool(...)`
  coercions (scope boundary, see Assumptions/UNK-01), and the fail-fast `load()`
  guards (notably `GitHubConfig.load`'s empty-`protected_branches` check).
- **Scope boundary**: only `int()` / `float()` / `list()` are replaced, per the frozen
  Acceptance Criteria. `bool(...)` is intentionally retained; extending to
  `get_typed(..., bool, ...)` is a follow-up (UNK-01, non-blocking).
- **No release unit**: each loader is independently testable, so every phase validates
  on its own (see Release units).

## Implementation steps
Each step description MUST cite the exact file path(s) it touches by referencing rows
of `Implementation Target Files` above — do not restate file-level detail
independently of that frozen table. A step is a top-level numbered item (a Phase); its
checklist items are sub-tasks, and the Execution Status table has one row per step.
Declare a release unit (see `### Release units` below) when a phase breaks existing callers or
tests until another phase lands (for example a `NOT NULL` column added before its write path):
one line per unit, `**Unit**: {name} | **Phases**: {N, N} | **Reason**: {why the members cannot be
validated alone}`. Phases that land together in one commit cannot be validated alone: declare them
as a unit; `N/A` is only for a Plan whose every phase passes validation alone.

1. **Phase 1: Core Logic — `CicdConfig.from_dict`**
   - [ ] Replace `int(d.get("max_log_size_kb", 256))` with `get_typed(d, "max_log_size_kb", int, "an integer", default=256)` (REQ-001; `scripts/mcp_servers/cicd/cicd_models.py`)
   - [ ] Replace `list(d.get("repo_allowlist", []))` and `list(d.get("workflow_allowlist", []))` with `list(get_typed(d, "repo_allowlist", list, "a list", default=[]))` / `list(get_typed(d, "workflow_allowlist", list, "a list", default=[]))` (REQ-001; `scripts/mcp_servers/cicd/cicd_models.py`)
2. **Phase 2: Core Logic — `GitHubConfig.from_dict`**
   - [ ] Replace every bare `int()` field with `get_typed(..., int, ..., default=<dataclass default>)` (REQ-002; `scripts/mcp_servers/github/github_models_config.py`)
   - [ ] Replace every bare `list()` field with `list(get_typed(..., list, "a list", default=[]))`; leave `get_str` and `bool(...)` untouched (REQ-002; `scripts/mcp_servers/github/github_models_config.py`)
   - [ ] Confirm `GitHubConfig.load`'s empty-`protected_branches` fail-closed guard is unchanged (REQ-002; `scripts/mcp_servers/github/github_models_config.py`)
3. **Phase 3: Core Logic — `RagPipelineConfig.from_dict` + `build_rag_cfg_adapter`**
   - [ ] Replace every bare `int()` / `float()` field with `get_typed(..., int|float, ..., default=<dataclass default>)`; leave `str(...)`/`get_str` and `bool(...)` untouched (REQ-003; `scripts/mcp_servers/rag_pipeline/rag_pipeline_models.py`)
   - [ ] Replace the bare `int()` / `float()` re-coercions in `build_rag_cfg_adapter` with pass-through of the validated `RagPipelineConfig` fields (REQ-004; `scripts/mcp_servers/rag_pipeline/rag_pipeline_models.py`)
4. **Phase 4: Tests**
   - [ ] Add wrong-typed-value + missing-key-default test in `tests/mcp_servers/cicd/test_cicd_models.py` (T-001; REQ-005)
   - [ ] Add wrong-typed-value + missing-key-default test in `tests/mcp_servers/github/test_github_server_auth.py` (T-002; REQ-005)
   - [ ] Add wrong-typed-value + missing-key-default test in `tests/mcp_servers/rag_pipeline/test_rag_pipeline_models.py` (T-003; REQ-003)
   - [ ] Update `test_numeric_string_values_are_coerced` to assert `ValueError`; reconcile `test_falsy_present_values_are_not_treated_as_missing`'s `rag_min_score: 0` int-for-float case (T-004; REQ-005)
5. **Phase 5: Deployment & Verification**
   - [ ] Run `uv run pytest` over `tests/mcp_servers/cicd`, `tests/mcp_servers/github`, `tests/mcp_servers/rag_pipeline`; confirm no regression across the full suite (`uv run pytest`) (T-005)
   - [ ] Run `uv run ruff check` and `uv run mypy` on changed files; fix any findings (T-005)

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/mcp_servers/cicd/cicd_models.py` + `tests/mcp_servers/cicd/test_cicd_models.py` | Unit | `uv run pytest tests/mcp_servers/cicd` | green; new wrong-typed test asserts `ValueError`, missing-key returns default |
| `scripts/mcp_servers/github/github_models_config.py` + `tests/mcp_servers/github/test_github_server_auth.py` | Unit | `uv run pytest tests/mcp_servers/github` | green; new wrong-typed test asserts `ValueError`; empty-`protected_branches` guard still fails closed |
| `scripts/mcp_servers/rag_pipeline/rag_pipeline_models.py` + `tests/mcp_servers/rag_pipeline/test_rag_pipeline_models.py` | Unit | `uv run pytest tests/mcp_servers/rag_pipeline` | green; `test_numeric_string_values_are_coerced` asserts `ValueError`; `test_falsy_present_values...` reconciled; no regression in `test_rag_pipeline_mcp_service.py` |
| Full suite | Integration | `uv run pytest` | no regression anywhere |
| Changed files | Lint / type | `uv run ruff check` and `uv run mypy` on `scripts/mcp_servers/cicd/cicd_models.py`, `scripts/mcp_servers/github/github_models_config.py`, `scripts/mcp_servers/rag_pipeline/rag_pipeline_models.py` | clean (no new findings) |

## Risks
- **Risk**: Updating `test_numeric_string_values_are_coerced` changes its intent from "coerce strings to numbers" to "reject wrong types"; a careless edit could mask a real behavior change. → **Mitigation**: the new assertion still exercises the same `from_dict` code path with stringly-typed numeric values, now asserting the corrected fail-fast `ValueError`; the valid-config path is covered by the unchanged populated-config tests.
- **Risk**: `get_typed` rejects `bool` where `int` is expected (`isinstance(True, int)` is `True` in Python, so `get_typed`'s explicit bool guard matters); an existing valid config passing `True` for an int field would now raise. → **Mitigation**: scope excludes `bool(...)` fields; valid-config tests confirm correct-type behavior is unchanged, and no valid config passes a bool for an int/float field.
- **Risk**: A `default=` value that does not match the dataclass field default silently changes the loaded default. → **Mitigation**: copy each `default=` verbatim from the dataclass field definition; verified against the current field defaults during Step 2.
- **Risk**: Passing already-typed fields through `build_rag_cfg_adapter` could drop type safety if a `RagPipelineConfig` field is `None`. → **Mitigation**: `from_dict` guarantees non-None defaults via `default=`, so validated fields are never `None`; `test_rag_pipeline_mcp_service.py` confirms the `RagConfig` Protocol contract is preserved.
- **Risk**: The `GitHubConfig.from_dict` wrong-typed test lives in `test_github_server_auth.py` (not a dedicated models test), which is unconventional. → **Mitigation**: this file directly exercises `GitHubConfig.from_dict` (lines 103-113) and is the closest existing home; documented as UNK-02, non-blocking.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Core Logic — `CicdConfig.from_dict` (`scripts/mcp_servers/cicd/cicd_models.py`) | In Progress | — | — | REQ-001 |
| 2 | Core Logic — `GitHubConfig.from_dict` (`scripts/mcp_servers/github/github_models_config.py`) | In Progress | — | — | REQ-002 |
| 3 | Core Logic — `RagPipelineConfig.from_dict` + `build_rag_cfg_adapter` (`scripts/mcp_servers/rag_pipeline/rag_pipeline_models.py`) | In Progress | — | — | REQ-003, REQ-004 |
| 4 | Tests (companion test files) | In Progress | — | — | REQ-005 |
| 5 | Deployment & Verification | Pending | — | — | REQ-005 |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261118-070059_01_scripts_mcp_servers_cicd_cicd_models.py.md | 1 | Procedure | Pending | — | — |
| implementations/20261118-070059_02_scripts_mcp_servers_github_github_models_config.py.md | 2 | Procedure | Pending | — | — |
| implementations/20261118-070059_03_scripts_mcp_servers_rag_pipeline_rag_pipeline_models.py.md | 3, 4 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: `issues/20261118-025551_mcpget001_mcp-models-type-coercion.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 2026-11-18T04:18:31
- **Related target files**: `scripts/mcp_servers/cicd/cicd_models.py`, `scripts/mcp_servers/github/github_models_config.py`, `scripts/mcp_servers/rag_pipeline/rag_pipeline_models.py`, `tests/mcp_servers/cicd/test_cicd_models.py`, `tests/mcp_servers/github/test_github_server_auth.py`, `tests/mcp_servers/rag_pipeline/test_rag_pipeline_models.py` — the full list of `File Path` values from
  `Implementation Target Files` above, once `Frozen`

### Requirement Traceability
See `templates/requirement-traceability.md` for the canonical column format.

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261118-070059 -->
