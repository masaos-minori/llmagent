# Implementation Procedure — `scripts/agent/tool_loop_guard.py`

## Goal

Make the effective on/off state of the ToolLoopGuard retry-suppression and empty-result
repeat guards observable at startup. Add a single concise startup diagnostic that reports
whether each guard is enabled for the resolved config, and document nothing here beyond the
code emit (`REQ-001`, `REQ-002`, `REQ-003`). Do NOT change defaults or gating logic
(`REQ-007`).

## Scope

Modify only `scripts/agent/tool_loop_guard.py`. Add:
- a module-level `_STARTUP_REPORTED: bool = False` flag near the top;
- a `ToolLoopGuard.report_effective_state()` method that reads the two config values and
  emits one concise summary line;
- a guarded call from `__init__` so it fires exactly once per process, wrapped in
  try/except so an unavailable logger cannot fail startup.

Do NOT touch the `<= 0` gating at lines 126, 139, 308, the defaults, or any other guard.

## Assumptions

- `logger = logging.getLogger(__name__)` is available at line 31.
- `__init__(self, ctx)` (lines 87–90) stores `self._ctx = ctx` and is called per turn
  (`llm_turn_executor.py:80`: `guard = ToolLoopGuard(self._ctx)`), so an unguarded
  constructor emit would spam every turn.
- Gating reads the same config fields: empty-result detection at lines 126 and 139 on
  `ctx.cfg.tool.tool_empty_result_max_repeats <= 0`; retry suppression at line 308 on
  `ctx.cfg.tool.tool_error_retry_max <= 0`.
- `report_effective_state()` reads `ctx.cfg.tool.tool_error_retry_max` and
  `ctx.cfg.tool.tool_empty_result_max_repeats` and returns/prints a concise summary such as
  `retry_suppression=on(1) empty_result_detection=off(0)`.

## Adversarial verification findings (plan discrepancies)

- **No discrepancy.** Verified against current source:
  - Both gates read `ctx.cfg.tool.* <= 0`; defaults are
    `tool_error_retry_max=1` (on) and `tool_empty_result_max_repeats=0` (off) — confirmed
    in `config_dataclasses.py` (separate row). REQ-007 (no behavior change) is preserved by
    only adding a log emit.
  - The guard is constructed per turn (`llm_turn_executor.py:80`), so the module-once flag
    is required (UNK-01 resolved: use approach (a), the module-once flag in `__init__`).
  - REQ-003 (logging-unavailable safe): wrap the emit in try/except.
  - Design preference UNK-02 (off-case level): recommend `warning` for the empty-result-off
    case (default-off protection gap) and `info` otherwise; non-blocking.

## Design decisions

- Prefer approach (a): module-once flag `_STARTUP_REPORTED` guarding the emit in
  `__init__`. It is self-contained (relocation is a one-line caller change if UNK-01 later
  yields a clean startup hook).
- Emit via the existing `logger` from `tool_loop_guard.__name__` (no new output channel).
- Off-case level: `warning` for empty-result detection off (default-off protection gap);
  `info` otherwise (UNK-02).
- Named boundary: only add reporting + the module flag; the `<= 0` gating, thresholds,
  cycle-detection algorithm, and defaults are untouched (REQ-007).

## Alternatives considered

- Approach (b) — emit from a genuine one-time startup hook: rejected as primary because no
  session-start hook exists on the guard (`llm_turn_runner.py` has only the per-turn
  `check_all()` entry, line 98); the module-once flag is the reliable once-per-process
  mechanism (UNK-01).
- Emitting uniformly at `info`: acceptable, but the default-off empty-result gap warrants a
  `warning` to surface absent protection (UNK-02).

## Implementation

### Target file

`scripts/agent/tool_loop_guard.py`

### Procedure

1. Near the top of the module (after imports, before the guard class), add:
   ```python
   _STARTUP_REPORTED: bool = False
   ```
2. Add a method to `ToolLoopGuard`:
   ```python
   def report_effective_state(self) -> str:
       \"\"\"Return a concise summary of the effective on/off state of both guards.\"\"\"
       cfg = self._ctx.cfg.tool
       retry_on = cfg.tool_error_retry_max > 0
       empty_on = cfg.tool_empty_result_max_repeats > 0
       return (
           f"retry_suppression={'on' if retry_on else 'off'}({cfg.tool_error_retry_max}) "
           f"empty_result_detection={'on' if empty_on else 'off'}("
           f"{cfg.tool_empty_result_max_repeats})"
       )
   ```
3. In `__init__`, after `self._ctx = ctx`, guard the emit:
   ```python
   global _STARTUP_REPORTED
   if not _STARTUP_REPORTED:
       _STARTUP_REPORTED = True
       try:
           state = self.report_effective_state()
           if "empty_result_detection=off" in state:
               logger.warning("%s startup diagnostic: %s", __name__, state)
           else:
               logger.info("%s startup diagnostic: %s", __name__, state)
       except Exception:
           # REQ-003: an unavailable logger must not fail startup.
           pass
   ```
4. Confirm the `<= 0` gating at lines 126, 139, 308 is byte-for-byte unchanged (REQ-007).
5. Confirm defaults are unchanged (see `config_dataclasses.py` row; REQ-004).

### Method

Edit the module top (add flag) and the class (add method + guarded `__init__` call);
re-run the guard test suite.

### Details

- The flag lives inside the module so relocation to a startup hook is a one-line caller
  change (risk mitigation in plan).
- Keep the summary string concise and single-line (REQ-001).
- Do not add the summary to any other method or call site.

## Compatibility considerations

- REQ-007: no runtime guard behavior, gating, or thresholds changed; existing gating tests
  (`test_retry_max_zero_disabled`, `test_window_zero_disabled`, `TestCheckAll`) still pass.
- REQ-004: defaults unchanged.
- Only adds a method + a module flag + one guarded log call.

## Security considerations

Operational reliability: surfaces whether retry/empty-result protection is active without
changing any protection behavior. The try/except ensures the diagnostic cannot crash
startup (REQ-003).

## Rollback considerations

Revert the commit to `scripts/agent/tool_loop_guard.py`.

## Validation plan

- Unit (`tests/agent/test_tool_loop_guard.py`):
  - `report_effective_state()` reflects the configured on/off state for both enabled and
    disabled configs (REQ-001).
  - Repeated construction emits only once (module-flag behavior) (REQ-002).
  - A guard whose logger is unavailable does not raise on construction (REQ-003).
  - Defaults unchanged (REQ-004).
  - Existing gating tests still pass (REQ-007).
- Command: `uv run pytest tests/agent/test_tool_loop_guard.py -q`.
- Static: `uv run python -c "from agent.config_dataclasses import ToolConfig as T; c=T(); print(c.tool_error_retry_max, c.tool_empty_result_max_repeats)"` → `1 0`.
- Lint/type: `uv run ruff check scripts/agent/tool_loop_guard.py` and `uv run mypy
  scripts/agent/tool_loop_guard.py` clean.

## Completion criteria

A single concise startup log line reports retry-suppression and empty-result detection
on/off for the resolved config, emitted once per process, safe when logging is unavailable,
and no guard behavior, gating, threshold, or default changed.

## Out of scope

Defaults, gating logic, cycle-detection algorithm, thresholds, other guards, the
`config_dataclasses.py` docstrings (separate row), the test file (separate row), and the
Known Limitations doc update (separate row).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add report_effective_state() + module-once flag emit in __init__ | Pending | — | — | approach (a); warning for empty-result-off |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: test file is a separate row |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: docs are separate rows |

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
- **Requirement ID**: `REQ-001` (single concise startup diagnostic), `REQ-002` (once per
  process), `REQ-003` (logging-unavailable safe), `REQ-007` (no behavior change)
- **Source issue**: `issues/done/20261017-123510_retrysup01_make-retry-suppression-and-empty-result-defaults-observable.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261017-153234_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261017-162934
- **Related target files**: `scripts/agent/tool_loop_guard.py`
