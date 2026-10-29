# Plan: `run_http()` posture-gate runs outside the try block that is documented to catch it

## Goal
- Align the `run_http()` docstring and the `# noqa: BLE001` justification in `scripts/mcp_servers/server.py` with the actual control flow — the posture gate runs before the `try` and its `SystemExit` is intentionally not caught there — without changing any runtime behavior.

## Priority
Medium

## Scope
- **In-Scope**: rewriting the false docstring sentences (lines 272-274) and the inaccurate `# noqa: BLE001` justification (line 328) on the `except SystemExit` handler in `MCPServer.run_http()`.
- **Out-of-Scope**: the gate call placement, the handler's executable code, the handler's log message string (`"Posture-gate failure during startup: %s"`), and its `raise`/exit behavior (all runtime behavior is frozen per the Issue's constraints); other servers' posture gates; the loopback-binding logic.
- **Dependencies**: N/A: none.

## Background
`MCPServer.run_http()` (`scripts/mcp_servers/server.py:266`) enforces, in order at call time: loopback-only host check (lines 281-285), config isolation via `ConfigLoader.restrict_to` or `ConfigPermissionError` (lines 287-297), then `self._enforce_startup_posture_gate()` (line 299, base method at lines 255-264 invoking the server module's `_enforce_posture_gate()`, which raises `SystemExit(1)` on policy violation). Only after that does it build `uvicorn.Config` / `_LoopbackVerifyingServer` (lines 320-324) and enter `try: server.run()` (lines 326-327) with `except SystemExit` (line 328, logging + re-raise) and `except KeyboardInterrupt` (lines 333-334).

## Problem
The docstring (lines 272-274) claims run_http "Catches ``SystemExit`` raised by ``_enforce_startup_posture_gate()`` during startup so that the failure reason is logged before the process terminates", and the `# noqa: BLE001` comment justifies the handler as existing for "posture-gate failure during startup". Step 2 verification confirms both are false: the gate call at line 299 runs before the `try` at line 326, so a gate `SystemExit` propagates uncaught out of `run_http()`. The existing test `tests/mcp_servers/test_posture_gate_start_path.py::test_failed_posture_exits_before_binding` (lines 36-48) pins exactly this: it patches `uvicorn.Config` to raise `AssertionError("uvicorn was built")` and asserts `SystemExit(1)` escapes `run_http()` — the log handler at lines 329-331 never runs for a gate failure. A residual wart is recorded, not fixed: the handler's log message string itself is a gate-specific label, but changing it is a runtime-text change the Issue's constraints exclude (flagged for a possible follow-up decision).

## Reason for Change
The documented and commented contract is the opposite of the control flow: the logging handler that the docstring credits for gate failures never runs for them, and the `# noqa` suppresses the lint rule with a justification for a branch that does not cover its stated purpose — misleading maintainers about where startup failures are handled.

## Implementation Intent
Adopt the Issue's recommended option (b): a pure documentation fix. Rewrite the docstring to state that the posture gate runs before the `try`/`except SystemExit`, so its `SystemExit` is intentionally not handled inside `run_http()` (fail-fast, process terminates via the uncaught `SystemExit(1)`), and rewrite the `# noqa` justification to describe what the handler actually covers (`SystemExit` originating from `server.run()` itself, logged and re-raised).

## Requirements
- `REQ-001`: the `run_http()` docstring states the true control flow: loopback check, config isolation, then posture gate — all before the `try` — and the gate's `SystemExit` propagates uncaught by design; no claim that `run_http()` catches the gate's `SystemExit` remains.
- `REQ-002`: the `# noqa: BLE001` comment on `except SystemExit` justifies the handler by what it really covers (`SystemExit` raised during `server.run()`; logged and re-raised, plus the `if not server.started: sys.exit(1)` fail-closed follow-up at lines 335-336), not by a posture-gate purpose.
- `REQ-003`: zero runtime behavior change: the gate call site, the handler's code and log message string, the `raise`, and all exit paths stay byte-identical; `test_failed_posture_exits_before_binding` and `test_validated_posture_reaches_uvicorn` stay green.

## Implementation Target Files
**Freeze status**: Frozen (the single row is `Verified`; `issue-to-plan` Step 8b
Implementation Target Files Validation passed — see `rules/workflow-lifecycle.md`
Implementation Target Files Validation (Plan Freeze)).

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| scripts/mcp_servers/server.py | Modify | Rewrite the false `run_http()` docstring sentences and the inaccurate `# noqa: BLE001` justification; docstring/comment-only edit | REQ-001, REQ-002, REQ-003 | Docstring claim at `server.py:272-274`; gate call at line 299 before `try` at line 326; `except SystemExit as e:  # noqa: BLE001 — posture-gate failure during startup` at line 328 (checked in Step 2) | `tests/mcp_servers/test_posture_gate_start_path.py::test_failed_posture_exits_before_binding`, `test_validated_posture_reaches_uvicorn` | Verified |

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| tests/mcp_servers/test_posture_gate_start_path.py | Pins the current uncaught-propagation behavior the rewritten docstring must describe (lines 36-48); explicitly "reference only" per the Issue | REQ-001, REQ-003 |

## Acceptance Criteria
- `AC-1` (REQ-001): the docstring no longer claims `run_http()` catches the posture gate's `SystemExit`; it states the gate runs before the `try` and its `SystemExit` intentionally propagates (fail-closed).
- `AC-2` (REQ-002): the `# noqa: BLE001` comment justifies the handler only by `SystemExit` originating from `server.run()` (logged and re-raised).
- `AC-3` (REQ-003): the diff of `scripts/mcp_servers/server.py` touches only the docstring lines and the noqa comment text; `uv run pytest tests/mcp_servers/test_posture_gate_start_path.py` passes unchanged; ruff / mypy stay clean.

## Tests
- `T1` (REQ-003): `uv run pytest tests/mcp_servers/test_posture_gate_start_path.py -v` — both existing tests green (the Issue's named Testing Expectation).
- `T2` (REQ-001, REQ-002): documentation consistency check — re-read `server.py:266-336` after the edit and confirm every docstring/comment sentence matches the control flow at lines 281-299 (before-try gates) and 326-336 (the handler's actual coverage).
- `T3` (REQ-003): `uv run ruff check scripts/mcp_servers`; `uv run mypy --no-namespace-packages scripts/mcp_servers`; `git diff` review confirming a comment/docstring-only diff.

## Documentation Impact
N/A: no `docs/*.md` update required. The Issue's documentation correction is the in-code docstring and noqa comment in the target file (carried in the `Implementation Target Files` table).

## Assumptions
- Option (b) (documentation-only) is the chosen resolution of the Issue's Unresolved Question, per the Issue's own recommendation and the fail-closed intent the existing test pins. Falsifiable: if the user later wants gate failures logged inside `run_http()`, option (a) (move the gate call into the `try`) becomes a separate behavior change needing a new log-assertion test — the Issue notes the existing test would also survive option (a) because the handler re-raises.
- `except SystemExit` is not dead code: it is kept as a fail-safe for a `SystemExit` originating from `server.run()` / uvicorn internals; no test currently exercises that path, and none is added (Issue: no behavioral tests required for a documentation fix).
- The `# noqa: BLE001` suppression must stay on line 328 (only its justification text changes), because removing it would fail ruff with a new finding — verified by `T3`.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| — | N/A: no unresolved unknowns; the Issue's Unresolved Question (option a vs b) is resolved to option (b) per the Issue's recommendation and AI Implementation Instruction — recorded in Design | — | — | — |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here is a subset of `Implementation Target Files`' rows.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| scripts/mcp_servers/server.py | Modify (docstring/comment only) | Low — base class imported by every MCP server module; change is text-only, no call-site or behavior impact (checked in Step 2) | 7 commits | N/A | not applicable (rsynced) |

## Design
Design decision (resolves the Issue's Unresolved Question): option (b), documentation-only. Grounds, from Step 2 verification:

1. The uncaught `SystemExit(1)` is the intended fail-closed outcome and is pinned by `test_failed_posture_exits_before_binding` (which patches `uvicorn.Config` to prove the gate fires before uvicorn is even built) — the current behavior is correct; only its description is wrong.
2. Option (a) (moving the gate call into the `try`) would add a log line — a behavior change the Issue's Constraints and AI Implementation Instruction forbid absent an explicit request.
3. New docstring text must state the actual order (loopback check → config isolation → posture gate → try) and that the gate's `SystemExit` deliberately bypasses the handler. New noqa text must name the handler's real coverage: a `SystemExit` from `server.run()` itself, logged then re-raised, with `if not server.started: sys.exit(1)` preserving fail-closed exit.
4. The handler's gate-specific log message string stays unchanged (REQ-003); its inaccuracy for the rare `server.run()` case is recorded as a report flag for a possible future behavior decision, not fixed here.

Path A classification: 1 modification target, documentation-only, no interface/schema change.

## Implementation steps
1. **Phase 1: Docstring & Comment Correction**
   - [ ] Rewrite the `run_http()` docstring (lines 272-274) and the `# noqa: BLE001` justification (line 328) per the Design, changing no executable code (REQ-001, REQ-002; File Path: scripts/mcp_servers/server.py)
2. **Phase 2: Verification & Deployment Hand-off**
   - [ ] Run `T1`-`T3`: posture-gate test file, consistency re-read, ruff/mypy, docstring/comment-only `git diff` review (REQ-003; File Path: scripts/mcp_servers/server.py)
   - [ ] Deployment validation/scripts check: commit and push the change, then hand off to `skills/deploy/SKILL.md`; `server.py` is embedded in every MCP server NUITKA onefile binary, so the hand-off notes the binary rebuilds are optional for a comment-only change; deploying is the user's decision (approval gate) (REQ-003; File Path: scripts/mcp_servers/server.py)

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/mcp_servers/server.py | Regression | `uv run pytest tests/mcp_servers/test_posture_gate_start_path.py -v` | Both existing tests green, unchanged |
| scripts/mcp_servers/server.py | Documentation consistency (`T2`) | Re-read `server.py:266-335` after the edit | Every rewritten sentence matches the control flow |
| scripts/mcp_servers/server.py | Static + diff scope | `uv run ruff check scripts/mcp_servers`; `uv run mypy --no-namespace-packages scripts/mcp_servers`; `git diff` review | No errors (noqa still suppressed correctly); diff touches only docstring/comment text |
| whole change | Architecture | `PYTHONPATH=scripts uv run lint-imports` | No import-layer violations (no imports change) |

## Risks
- **Risk**: the rewritten text mis-describes the order or coverage, creating a new doc/behavior mismatch → **Mitigation**: `T2` re-reads the exact line ranges; the Design records the verified control flow.
- **Risk**: an accidental executable edit (moving the gate call or changing the log message) violates the Issue's Constraints → **Mitigation**: `AC-3` docstring/comment-only `git diff` review plus the unchanged regression test (`T1`).
- **Risk**: rewording the noqa line could drop the `BLE001` code token and un-suppress the ruff finding → **Mitigation**: keep the `# noqa: BLE001` token byte-identical, change only the text after it; ruff gate in `T3` confirms.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`.

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Rewrite `run_http()` docstring + noqa justification (scripts/mcp_servers/server.py) | Completed | 20261029-150227 | 20261029-150227 | REQ-001, REQ-002 |
| 2 | Run posture-gate tests, consistency check, static gates, diff review; deploy hand-off | Pending | — | — | REQ-003; deploy is user-gated |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | N/A: no blocker recorded | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261029-140245_01_scripts_mcp_servers_server.py.md | 1 | Procedure | Completed | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261029-012525_ebrev003_serverbase-posture-gate-outside-try.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261029-080042
- **Related target files**: scripts/mcp_servers/server.py

### Requirement Traceability

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Summary / Problem (control-flow sketch, docstring quote); confirmed at `server.py:272-274,299,325` (Step 2) | scripts/mcp_servers/server.py | Phase 1 | AC-1 | T2 | Explicit in issue |
| REQ-002 | Problem (noqa quote) / Required Changes; confirmed at `server.py:328` (Step 2) | scripts/mcp_servers/server.py | Phase 1 | AC-2 | T2 | Explicit in issue |
| REQ-003 | Constraints ("preserve fail-closed behavior", "keep the test green") / AI Implementation Instruction | scripts/mcp_servers/server.py | Phase 2 | AC-3 | T1, T3 | Explicit in issue |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261029-140245 -->