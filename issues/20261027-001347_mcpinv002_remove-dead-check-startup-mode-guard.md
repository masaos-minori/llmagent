# Remove dead `ToolExecutor._check_startup_mode` guard

## Priority
Low

## Summary
Delete `ToolExecutor._check_startup_mode`, a method that is defined but never called anywhere in the repository. Its disabled-server rejection is already covered by live guards elsewhere.

## Background
`ToolExecutor` (`scripts/shared/tool_executor.py`) defines `_check_startup_mode(server_key)`, which returns an error `ToolCallResult` when a server's `startup_mode` is `StartupMode.NONE`. A repository-wide search finds zero call sites for this method. The equivalent behavior is enforced live in two other places:

- `ToolTransportInvoker._run_precall_gates()` (`scripts/shared/tool_transport_invoker.py`) rejects `startup_mode == StartupMode.NONE` servers before any HTTP is sent.
- `ToolTransportInvoker.__init__` skips building a transport for any server where `cfg.is_disabled` (i.e. `startup_mode == StartupMode.NONE`), so no transport exists for a disabled server.

## Problem
A defensive-looking guard that never runs is worse than no guard: a maintainer reading `_check_startup_mode` reasonably concludes there is a startup-mode check at the `ToolExecutor` layer. When a bug is later traced there, the guard will be found to be dead, wasting investigation time and creating a false sense of defense-in-depth.

## Reason for Change
The method is misleading dead code. Removing it makes the actual (live) guard locations the single source of truth for disabled-server handling and removes a trap for future maintainers.

## Implementation Intent
Remove the unused `_check_startup_mode` method and its docstring from `ToolExecutor`. Confirm via a fresh `rg` that no caller (including tests) references it, then delete. Do not alter the live guards in `_run_precall_gates` or `__init__`.

## Target Files or Areas
- `scripts/shared/tool_executor.py` — `ToolExecutor._check_startup_mode`

## Required Changes
- Delete the `_check_startup_mode` method definition.
- Remove any import or reference left behind (verify none exist).
- Update any test that referenced the method (if present).

## Constraints
- Must not change runtime behavior; the disabled-server rejection must remain via the live guards.
- Must not touch `ToolTransportInvoker` or `mcp_config`.

## Acceptance Criteria
- No symbol reference to `_check_startup_mode` remains in `scripts/` or `tests/`.
- A `startup_mode=none` server is still rejected at the invocation boundary (covered by the live guards).
- Existing tests pass.

## Testing Expectations
- Run the shared/agent test suite for the tool executor and transport invoker to confirm no regression.
- `rg _check_startup_mode scripts/ tests/` returns no hits.

## Documentation Impact
None expected.

## Out of Scope
- Any change to the disabled-server policy or its live guard locations.
- Refactoring `ToolTransportInvoker`.

## Dependencies
N/A: none

## Unresolved Questions
- Confirm no external plugin or generated test references the method before deletion (a fresh `rg` at implementation time).

## AI Implementation Instruction
In `scripts/shared/tool_executor.py`, delete the `_check_startup_mode` method. First confirm with `rg -n _check_startup_mode scripts/ tests/` that it is unreferenced. Do not modify the live disabled-server guards in `ToolTransportInvoker`.

## Traceability
- **Workflow phase**: python-code-review
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261027-001347
- **Related target files**: scripts/shared/tool_executor.py

---

**Adversarial Verification** (2026-10-27): verified against current source per `rules/ai-execution.md` Adversarial Verification (Base).

Examined: `scripts/shared/tool_executor.py::_check_startup_mode` (lines 68-79), `scripts/shared/tool_transport_invoker.py` (`_run_precall_gates` 262-295, `__init__` 56-63), `scripts/shared/mcp_config.py` (`is_disabled` 110-112), `scripts/mcp_servers/dispatch.py`.

Claims:

- `_check_startup_mode` is defined but has zero callers — CONFIRMED. `rg -n _check_startup_mode scripts/ tests/` returns only the definition (`tool_executor.py`:68); no production or test caller exists.
- `is_disabled` equals `startup_mode == StartupMode.NONE` — CONFIRMED (`mcp_config.py`:110-112).
- Live guards cover the disabled-server rejection: `_run_precall_gates` rejects `startup_mode == NONE` (`tool_transport_invoker.py`:268-275) and `__init__` skips building a transport for `cfg.is_disabled` (58-59) — CONFIRMED.

CORRECTION REQUIRED — recommended fix violates the deprecation policy:

- The issue instructs direct deletion ("Delete the `_check_startup_mode` method"). `rules/coding.md` Deprecation Policy (lines 16-21) forbids immediate deletion: a deprecated symbol is removed "the next time `plans/` touches the corresponding file for an unrelated reason, provided a zero-caller `rg` re-check still holds." Archived implementation docs (e.g. `implementations/done/20261003-174413_04_scripts_shared_tool_transport_invoker.py.md`) already recorded that removing it conflicts with this policy.
- Corrected approach: mark `@deprecated` with a comment citing `rules/coding.md` Deprecation Policy; defer removal to a future plan that touches `tool_executor.py`. Do NOT delete outright in this change.

Minor incompleteness: the Summary characterizes the method as rejecting only `startup_mode == NONE`, but it also rejects `cfg is None` ("No validated configuration"), a branch the live guards do NOT replicate (they fall through to "No transport configured"). The dead-code conclusion is unaffected; the Background is slightly incomplete.

Assessment: The "dead code" premise is CORRECT. The fix approach must be corrected from "delete" to "deprecate then remove on a later plan touch."
