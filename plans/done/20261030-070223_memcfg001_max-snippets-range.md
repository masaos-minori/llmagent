## Goal
Add a strict-positive lower-bound constraint to `AgentConfig.agent_memory_max_startup_snippets` so values ≤ 0 are rejected at construction, and add a unit test covering the rejection and acceptance cases. Keep the default at 10.

## Priority
Low

## Scope
- **In-Scope**:
  - Add a positive-bound validation to `AgentConfig` in `scripts/agent/config_dataclasses.py` that raises a `ValueError` when `agent_memory_max_startup_snippets <= 0`, invoked from `__post_init__`. Keep the default at 10.
  - Add tests to `TestAgentConfigValidation` in `tests/agent/test_config_dataclasses.py` asserting rejection of 0 and negative values and acceptance of 1 and 5.
- **Out-of-Scope**:
  - Changing the slice semantics for valid positive values in `startup_prompt_setup.py`.
  - Clamping the value defensively at the call site in `startup_prompt_setup.py` — enforce at construction only.
  - Changing the default value (keep 10).
  - Changing any other `AgentConfig` field.
- **Dependencies**: N/A: none.

## Background
`AgentConfig` (a stdlib `@dataclass` in `scripts/agent/config_dataclasses.py`) owns the field `agent_memory_max_startup_snippets: int = 10`. It has no constraint today. `AgentConfig.__post_init__` calls `_validate_cross_field()`, which currently validates two cross-field dependencies (`_validate_memory_jsonl_dir`, `_validate_memory_embed_url`) by raising `ValueError` with a message naming the offending field.

The field is wired end-to-end: `config_builders.py`'s `build_agent_config()` supplies it via `_get_int_or_default(cfg, "agent_memory_max_startup_snippets", _get_int, 10)`, so a value from the toml reaches `AgentConfig` construction. `startup_prompt_setup.py`'s `setup_prompt()` reads it as `max_snippets = ctx.cfg.agent_memory_max_startup_snippets` and bounds the loaded snippets with `memory_snippets[:max_snippets]` inside `if len(memory_snippets) > max_snippets`.

## Problem
Because the field is unvalidated:
- `0` silently yields an empty prompt (no startup context loaded).
- A negative integer produces a backwards slice (`[:-1]`, `[:-2]`, ...) that returns most of the history rather than a small startup set — a confusing, likely-unintended result.
- No error is raised at config construction or load time, so bad values reach the slice silently.

## Reason for Change
A count-like configuration should reject non-positive values at the boundary (construction) rather than producing surprising slice semantics deep in prompt building. This is defensive hardening, not a current observed failure.

## Implementation Intent
Add a `ValueError` guard for `<= 0` to `AgentConfig`'s construction-time validation (the same mechanism `_validate_cross_field` already uses), keeping the default at 10. Then add a test in the existing `TestAgentConfigValidation` class following its `pytest.raises(ValueError, match="<field>")` convention.

## Requirements
- `REQ-001`: `AgentConfig` rejects `agent_memory_max_startup_snippets <= 0` at construction (raises `ValueError`), accepts values ≥ 1, and keeps the default at 10.
- `REQ-002`: A unit test in `tests/agent/test_config_dataclasses.py` asserts rejection of 0 and negatives and acceptance of 1 and 5; the config and prompt-setup suites pass.

## Implementation Target Files
**Freeze status**: Frozen (was `Draft`; set to `Frozen` once `issue-to-plan` Step 8's Implementation Target Files Validation passed — see `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan Freeze)).

This table is the canonical, frozen source of implementation scope for this Plan. Once `Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream `plan-to-implementation-procedure` document MUST reference file paths only from this table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/agent/config_dataclasses.py` | Modify | Add a positive-bound guard to `AgentConfig` construction-time validation: raise `ValueError` when `agent_memory_max_startup_snippets <= 0`, invoked from `__post_init__`; keep the default at 10 | REQ-001; AC1, AC2 | Field declared in `AgentConfig` with default 10 and no constraint; `AgentConfig.__post_init__` calls `_validate_cross_field()`, which raises `ValueError` naming the offending field for the two existing cross-field checks; module imports the stdlib `dataclass` (no pydantic) (checked in Step 2) | `TestAgentConfigValidation` (existing) | Verified |
| `tests/agent/test_config_dataclasses.py` | Modify | Add rejection/acceptance tests for `agent_memory_max_startup_snippets` to `TestAgentConfigValidation` | REQ-002; AC3 | `TestAgentConfigValidation` exists and uses `pytest.raises(ValueError, match="...")` for each field's validation; existing tests construct `AgentConfig(rag=RAGConfig(embed_url=...))` (checked in Step 2) | `TestAgentConfigValidation::test_memory_embed_without_embed_url_raises`, `test_memory_layer_without_jsonl_dir_raises` | Verified |

Rules (see `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan Freeze for the full validation procedure):
- One row per file. A directory, glob pattern (`*`, `**`), component/module name, file group, or a vague phrase (e.g. "related files", "as necessary", "etc.") MUST NOT appear as a row — list each file individually by its exact repository-relative path.
- Record a test, configuration, schema, migration, deployment, or documentation file as its own row when it requires modification — do not fold it into the row for the source file it accompanies.
- `Validation Status` is `Verified` or `Needs confirmation` per row; every row must be `Verified` before this section may be marked `Frozen`.

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same one-file-per-row discipline as `Implementation Target Files` above — no directories, glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/agent/startup_prompt_setup.py` | Confirm the call site receives a guaranteed-positive bound after the constraint and that no valid-value path depends on non-positive semantics | `scripts/agent/config_dataclasses.py`; REQ-001 |
| `scripts/agent/config_builders.py` | Confirm end-to-end wiring (`_get_int_or_default(cfg, "agent_memory_max_startup_snippets", _get_int, 10)`) so construction-time validation applies to configs built from raw dicts/toml | `scripts/agent/config_dataclasses.py`; REQ-001 |

## Acceptance Criteria
- Constructing an `AgentConfig` with `agent_memory_max_startup_snippets <= 0` raises a `ValueError` (REQ-001, AC1).
- Constructing an `AgentConfig` with `agent_memory_max_startup_snippets >= 1` succeeds, and the default remains 10 (REQ-001, AC2).
- New test(s) cover the rejection and acceptance cases (REQ-002, AC3).
- Existing config and prompt-setup suites still pass (REQ-002, AC4).

## Tests
- In `TestAgentConfigValidation` (`tests/agent/test_config_dataclasses.py`), add tests asserting:
  - `AgentConfig(agent_memory_max_startup_snippets=0)` raises `ValueError` (message references the field).
  - `AgentConfig(agent_memory_max_startup_snippets=-1)` raises `ValueError`.
  - `AgentConfig(agent_memory_max_startup_snippets=1)` and `AgentConfig(agent_memory_max_startup_snippets=5)` construct successfully.
  - The default (no argument) is 10.
- Match the existing `pytest.raises(ValueError, match="<field>")` style used by `TestAgentConfigValidation` and the other `Test*ConfigValidation` classes (REQ-002).
- Run the config and prompt-setup suites and confirm all tests pass (REQ-002).

## Documentation Impact
The field currently has no docstring on `AgentConfig`, so there is no existing docstring text to revise. Adding a concise one-line note that the value must be ≥ 1 is optional and within scope. No external `docs/*.md` update required (REQ-001).

## Assumptions
- `AgentConfig` is a stdlib `@dataclass`, so validation belongs in `__post_init__` / `_validate_cross_field`, not via a pydantic constraint.
- The constraint is enforced at construction only; the call site in `startup_prompt_setup.py` is not clamped (matches the issue's recommendation).
- All existing usages are positive: the default is 10, `config_builders.py` defaults to 10, and existing tests set 10. No config or test passes a non-positive value, so the constraint breaks nothing.
- The field is owned by `AgentConfig`, not by a memory sub-config.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Should the constraint also be defensively enforced (clamped) in `startup_prompt_setup.py`, or enforced at construction only? | None — resolved by evidence. | Enforce at construction only; do not clamp at the call site. The call site receives a guaranteed-positive bound, and clamping would hide misconfiguration. Matches the issue's own recommendation. | False |
| UNK-02 | Are there existing configs or tests that legitimately pass 0/negative today that would break under the new constraint? | None — resolved by evidence. | No. Repo-wide check shows every usage is positive (default 10; tests set 10; `config_builders.py` defaults to 10). No `config/*.toml` sets this key. The constraint cannot break an existing positive value. | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor` columns. The `File` column here MUST be a subset of `Implementation Target Files`' rows — this table analyzes change-impact risk for those same files; it is not a separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/agent/config_dataclasses.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/agent/test_config_dataclasses.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |

## Design
Path A (≤3 files, no public/runtime interface change, no schema change). Analysis limited to direct verification of the two target files and their immediate dependencies.

**Adversarial verification findings (issue vs. current source).** Several specifics in the issue are stale and were corrected against current source:
- **Field owner.** The issue names `AgentMemoryConfig.agent_memory_max_startup_snippets`. The field is actually a direct field of `AgentConfig` (the composite dataclass), not of any memory sub-config. There is no `AgentMemoryConfig`.
- **Default value.** The issue states the default is 5. Current source defaults it to **10** (via the field default and `config_builders.py`'s `_get_int_or_default(..., 10)`).
- **Usage shape.** The issue's snippet (`max_startup_snippets = self.config.agent_memory.agent_memory_max_startup_snippets; snippets = memory.conversation_snippets[:max_startup_snippets]`) does not match current code. `setup_prompt()` reads `max_snippets = ctx.cfg.agent_memory_max_startup_snippets` and bounds with `memory_snippets[:max_snippets]` inside `if len(memory_snippets) > max_snippets`.
- **Enforcement mechanism.** The issue offers `pydantic.Field(default=5, gt=0)` as one option. `AgentConfig` is a stdlib `@dataclass` (imports `from dataclasses import dataclass, field`; no pydantic), so `pydantic.Field` is not viable. The correct mechanism is a `ValueError` guard in `__post_init__`, following the existing `_validate_cross_field` pattern (which already raises `ValueError` naming the offending field). This resolves the issue's "pick one" by selecting the validator approach and adapting it to a stdlib dataclass.

**Baseline.** radon: `AgentConfig` is A(3); `_validate_cross_field` is A(1). Adding one `if ... <= 0: raise ValueError(...)` guard adds negligible complexity. vulture and bandit report no findings on either target file.

## Implementation steps
1. **Phase 1: Add the positive-bound guard to `AgentConfig`**
   - [ ] In `scripts/agent/config_dataclasses.py`, add a `ValueError` guard for `agent_memory_max_startup_snippets <= 0` in `AgentConfig`'s construction-time validation (add it to `_validate_cross_field` or a dedicated method called from `__post_init__`), with a message naming the field. Keep the default at 10 (REQ-001; AC1, AC2).
2. **Phase 2: Add the unit test**
   - [ ] In `TestAgentConfigValidation` (`tests/agent/test_config_dataclasses.py`), add tests asserting rejection of 0 and negatives and acceptance of 1 and 5, plus that the default is 10, matching the existing `pytest.raises(ValueError, match="<field>")` style (REQ-002; AC3).
3. **Phase 3: Deployment & Verification**
   - [ ] Run `uv run pytest tests/agent/test_config_dataclasses.py tests/agent/test_startup_prompt_setup.py` and confirm all tests pass, including the new tests and the existing `TestAgentConfigValidation` tests (REQ-002; AC4).

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/agent/config_dataclasses.py::AgentConfig` (construction) | Positive: `AgentConfig(agent_memory_max_startup_snippets=0)` and `-1` raise `ValueError`; `1`, `5`, and the default construct successfully | `uv run pytest tests/agent/test_config_dataclasses.py -k "AgentConfig"` | New tests pass; existing `TestAgentConfigValidation` tests still pass |
| `tests/agent/test_config_dataclasses.py` | Full-suite regression | `uv run pytest tests/agent/test_config_dataclasses.py` | All tests pass |
| `tests/agent/test_startup_prompt_setup.py` | Regression: prompt setup still works with a guaranteed-positive bound | `uv run pytest tests/agent/test_startup_prompt_setup.py` | All tests pass |

## Risks
- **Risk**: Attempting `pydantic.Field(gt=0)` on a stdlib dataclass. → **Mitigation**: Confirmed via reading the module imports (`from dataclasses import dataclass, field`); the plan mandates a `ValueError` guard in `__post_init__` following the existing `_validate_cross_field` pattern.
- **Risk**: Adding the guard to `_validate_cross_field` could reorder or interfere with the two existing cross-field validations. → **Mitigation**: The guard is additive; the existing `test_memory_embed_without_embed_url_raises` and `test_memory_layer_without_jsonl_dir_raises` tests remain valid and still pass.
- **Risk**: Rejecting non-positive values could break an existing config or test. → **Mitigation**: Repo-wide check confirms every existing usage is positive (default 10; tests set 10; `config_builders.py` defaults to 10); no `config/*.toml` sets this key, so no existing positive value is affected.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the positive-bound guard to `AgentConfig` | In Progress | — | — | Touches `scripts/agent/config_dataclasses.py` |
| 2 | Add the unit test | In Progress | — | — | Touches `tests/agent/test_config_dataclasses.py` |
| 3 | Deployment & Verification | Pending | — | — | Runs `pytest tests/agent/test_config_dataclasses.py tests/agent/test_startup_prompt_setup.py` |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261030-073807_01_scripts_agent_config_dataclasses.py.md | 1 | Procedure | Pending | — | — |
| implementations/20261030-073807_02_tests_agent_test_config_dataclasses.py.md | 2 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261029-220801_memcfg001_max-snippets-range.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261030-070223
- **Related target files**: scripts/agent/config_dataclasses.py, tests/agent/test_config_dataclasses.py

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Problem / Reason for Change / Required Changes; field unvalidated (Step 2) | `scripts/agent/config_dataclasses.py` | Step 1 | AC1, AC2 | Construction rejects ≤ 0, accepts ≥ 1, default 10 (Step 2) | Confirmed by repository evidence |
| REQ-002 | Testing Expectations / AI Implementation Instruction; `TestAgentConfigValidation` exists (Step 2) | `tests/agent/test_config_dataclasses.py` | Step 2 | AC3, AC4 | New + existing tests pass (Step 2) | Confirmed by repository evidence |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261030-073807 -->