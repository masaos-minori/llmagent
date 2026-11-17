## Goal
- Make `ToolLoopGuard.check_dedup` honor the `<= 0` disables-the-guard convention that
  every sibling guard in the class follows, so a zero or negative
  `tool_dedup_max_repeats` cleanly disables dedup instead of blocking every tool call on its
  first occurrence.

## Priority
Low

## Scope
- **In-Scope**:
  - Add an early-return to `check_dedup` that mirrors the sibling guards: when
    `ctx.cfg.tool.tool_dedup_max_repeats <= 0`, return `None` before mutating `seen_calls`.
  - Add a regression test asserting `check_dedup` returns `None` and leaves `seen_calls` empty
    when `tool_dedup_max_repeats` is `0` (and/or negative), and a regression case confirming
    detection is unchanged for a positive value.
- **Out-of-Scope**:
  - Any change to `check_retry`, `check_cycle`, `check_error_limit`,
    `scan_empty_result_repeat`, `scan_unavailable_repeat`, `record_tool_result`, or
    `report_effective_state`.
  - Any change to config validation (`validate_tool_dedup_max_repeats`) or default values.
  - Any change to the DAG scheduler, `execute_all_tool_calls`, or `LLMTurnRunner.run`.
- **Dependencies**: N/A: none. Related (already resolved) issue exists; revisiting its
  documentation note is out of scope.
  - **Depends on**: `N/A: none`

## Background
The tool-loop guard in `scripts/agent/tool_loop_guard.py` guards the inner tool-call loop
against dedup, cycle, retry, consecutive-error, stagnation, and empty/unavailable repeats.
Every other guard in the class treats a `<= 0` config value as a clean disable:
`check_retry`, `check_cycle`, `check_error_limit`, `scan_empty_result_repeat`,
`scan_unavailable_repeat`, and `record_tool_result` all return early when their config is
`<= 0`. `scan_unavailable_repeat`/`check_unavailable_repeat` even document this contract in
their docstrings ("limit <= 0 disables the check entirely (default-off)").

`check_dedup` has no such guard. Config validation (`validate_tool_dedup_max_repeats`,
invoked from `ToolConfig.__post_init__`) currently enforces a minimum of `1`, so the
divergent value cannot reach the runtime guard through the normal config path.

## Problem
`check_dedup` increments `seen_calls[key]` and compares `seen_calls[key] >=
cfg.tool_dedup_max_repeats` with no `<= 0` short-circuit. When `tool_dedup_max_repeats` is
`0` or negative, the comparison is always true, so the very first occurrence of any
`(tool, args)` pair is reported as a duplicate and the turn exits with "Repeated tool call
detected." — the agent cannot execute any tool call once. This contradicts the module-wide
"`<= 0` disables" contract that all siblings implement and that a maintainer expects from
reading the class.

## Reason for Change
The divergence is a latent footgun. Right now config validation masks it, but the guard
boundary itself is wrong: if validation ever loosens, if the guard is invoked programmatically
or from a test with a `0` value, or if a future refactor bypasses `__post_init__`, dedup
silently becomes "block everything." Adding the parity guard makes the one-disable-per-class
semantics uniform across the class and removes the catastrophic-zero case. Severity is Low
because the defect is currently gated by config validation and cannot manifest through the
normal config path; the timing is maintainability/robustness, not a live runtime risk.

## Implementation Intent
Add an early-return to `check_dedup` that mirrors the sibling guards: when
`ctx.cfg.tool.tool_dedup_max_repeats <= 0`, return `None` before mutating `seen_calls`.
Preserve the existing increment-and-compare logic for the enabled case and leave all other
guards, the counting machinery, and the disabled-by-default policy untouched. Do not change
`validate_tool_dedup_max_repeats` or its `>= 1` enforcement.

## Requirements
- `REQ-001`: Add `if ctx.cfg.tool.tool_dedup_max_repeats <= 0: return None` at the top of
  `check_dedup`, before the `seen_calls` mutation loop.
- `REQ-002`: For any `tool_dedup_max_repeats >= 1`, dedup detection behaves exactly as before
  (first block on the Nth identical call); the enabled path is unchanged.
- `REQ-003`: A regression test asserts `check_dedup` returns `None` and leaves `seen_calls`
  empty when `tool_dedup_max_repeats` is `0` (and/or negative), and a regression case
  confirms detection is unchanged for a positive value.

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this table —
no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/agent/tool_loop_guard.py` | Modify | Add `if ctx.cfg.tool.tool_dedup_max_repeats <= 0: return None` at the top of `check_dedup` (before the `_iter_tool_call_keys` loop at lines 422-433). All sibling guards gate on `<= 0`: `check_retry` (line 451), `check_cycle` (line 339), `check_error_limit` (lines 502-505), `scan_empty_result_repeat` (line 227), `scan_unavailable_repeat` (line 275), `record_tool_result` (line 214), `_check_progress_stagnation` (line 375). `check_dedup` is the only guard without it. (checked in Step 2) | REQ-001, REQ-002 | `check_dedup` lines 415-434 has no `<= 0` guard; siblings gate on `<= 0` (see above). `validate_tool_dedup_max_repeats` enforces `>= 1` (`scripts/agent/services/config_validators.py` lines 118-120), so this is defensive. | `tests/agent/test_tool_loop_guard.py` | Verified |
| `tests/agent/test_tool_loop_guard.py` | Modify | Add a `TestCheckDedup` case asserting `check_dedup` returns `None` and leaves `seen_calls` empty when `tool_dedup_max_repeats` is `0`, and confirm detection is unchanged for a positive value. (checked in Step 2) | REQ-003 | Existing `TestCheckDedup` uses `_cfg(tool_dedup_max_repeats=...)` + `_make_ctx(cfg)` + `guard.check_dedup(seen, _msg(...))`; the misnamed `test_window_zero_disabled_by_default` tests only the first call at the default value 3, not the `<= 0` disable. | `tests/agent/test_tool_loop_guard.py` | Verified |

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
| `scripts/agent/services/config_validators.py` | Confirm `validate_tool_dedup_max_repeats` still enforces `>= 1` so the fix stays defensive and does not need a validation change. | `scripts/agent/tool_loop_guard.py` |
| `tests/agent/test_tool_loop_guard.py` | Read the `_cfg`/`_make_ctx` helpers and existing `TestCheckDedup` cases to mirror the established pattern. | `scripts/agent/tool_loop_guard.py` |

## Acceptance Criteria
- `AC-001` (REQ-001): `check_dedup` returns `None` without touching `seen_calls` when
  `tool_dedup_max_repeats <= 0`.
- `AC-002` (REQ-002): For any `tool_dedup_max_repeats >= 1`, dedup detection behaves exactly
  as before (first block on the Nth identical call).
- `AC-003` (REQ-002): With the guard effectively disabled via a `<= 0` value, no tool call is
  blocked.
- `AC-004` (REQ-003): A regression test covers the `<= 0` disable and the unchanged positive
  path.

## Tests
- `TEST-001` (REQ-003): Assert `check_dedup` returns `None` and leaves `seen_calls` empty when
  `tool_dedup_max_repeats` is `0` (and/or negative).
- `TEST-002` (REQ-002): Confirm detection is unchanged for a positive value.
- `TEST-003` (REQ-001/REQ-002): Run `uv run ruff check` and `uv run mypy --no-namespace-packages`
  on the touched file, and `uv run pytest tests/agent/test_tool_loop_guard.py`.

## Documentation Impact
N/A: the disable semantics are already documented for the sibling guards; making dedup
consistent is internal. If the config documentation lists per-guard disable semantics in
prose, dedup's `<= 0` disable could be added there for completeness, but no new config-field
table may be introduced.

## Assumptions
- The fix is behavior-preserving for the current config space (`tool_dedup_max_repeats >= 1`):
  the enabled path behaves exactly as before.
- Config validation stays at `>= 1`, so the new guard is dead-code protection against a
  loosened validation, a programmatic/test invocation, or a future refactor.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether `tool_dedup_max_repeats` should remain strictly `>= 1` (dedup always enabled) or whether a `<= 0` disable should be a supported, documented policy. | Resolved by evidence: the parity fix is harmless either way — dead-code protection when always-on, correct disable when disableable — so it does not depend on the policy decision. Policy stays out of scope (validation unchanged). | Recorded as resolved; no doc/validation change planned. | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/agent/tool_loop_guard.py` | Modify | Low — one early return in one guard method; behavior unchanged for all valid configs | N/A | N/A | not applicable (rsynced) |
| `tests/agent/test_tool_loop_guard.py` | Modify | Low — additive regression test; existing tests unaffected | N/A | N/A | not applicable (rsynced) |

## Design
Path A (small task). Classification rationale: affects 2 files (one source, one test), no
public or runtime-facing interface change, no database schema change. The change is a single
early-return mirroring the sibling guards; no design decision beyond placing it correctly is
required. The enabled path (`tool_dedup_max_repeats >= 1`) is preserved byte-for-byte; the
guard only adds an off-ramp for values that config validation currently forbids.

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

1. **Phase 1: Core logic**
   - [ ] REQ-001: In `scripts/agent/tool_loop_guard.py` `check_dedup`, add
     `if ctx.cfg.tool.tool_dedup_max_repeats <= 0: return None` before the
     `_iter_tool_call_keys` loop. Preserve the increment-and-compare logic for the enabled
     case and leave all other guards untouched.
2. **Phase 2: Tests**
   - [ ] REQ-003: In `tests/agent/test_tool_loop_guard.py` `TestCheckDedup`, add a case
     asserting `check_dedup` returns `None` and leaves `seen_calls` empty when
     `tool_dedup_max_repeats` is `0` (and/or negative); confirm detection is unchanged for a
     positive value.
3. **Phase 3: Verification**
   - [ ] REQ-001/REQ-002: Run `uv run ruff check`, `uv run mypy --no-namespace-packages`, and
     `uv run pytest tests/agent/test_tool_loop_guard.py`.

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/agent/tool_loop_guard.py` | Unit: drive `check_dedup` with `tool_dedup_max_repeats=0` and a positive value. | `uv run pytest tests/agent/test_tool_loop_guard.py` | New and existing tests pass. |
| `scripts/agent/tool_loop_guard.py` | Static: lint and type-check the touched file. | `uv run ruff check` / `uv run mypy --no-namespace-packages` | Clean. |

## Risks
- **Risk**: Placing the guard after the first iteration would still mutate `seen_calls` for
  the disabled case. → **Mitigation**: Place the early-return before the `_iter_tool_call_keys`
  loop so `seen_calls` is never touched when disabled.
- **Risk**: Accidentally changing an enabled-path comparison. → **Mitigation**: Add only the
  single early-return; leave the increment-and-compare logic verbatim; the positive-value
  regression test guards the enabled path.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Core logic: add `<= 0` early-return to `check_dedup` | Pending | — | — | |
| 2 | Tests: regression test for `<= 0` disable and unchanged positive path | Pending | — | — | |
| 3 | Verification: ruff, mypy, pytest | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: `issues/20261117-181638_tlg002_dedup-disable-parity.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261117-201452
- **Related target files**: `scripts/agent/tool_loop_guard.py`, `tests/agent/test_tool_loop_guard.py`

### Requirement Traceability
See `templates/requirement-traceability.md` for the canonical column format.
