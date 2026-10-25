# Plan: agent001 orchestrator turn path typing

## Goal
- Add type annotations to `Orchestrator.handle_turn` and `Orchestrator._execute_turn`
  in `scripts/agent/orchestrator.py` so the core REPL turn-execution body is checked by
  mypy, eliminating the three `annotation-unchecked` notes at lines 165-167 without any
  runtime or API change.

## Priority
Medium

## Scope
- **In-Scope**:
  - Annotate `handle_turn(self, line)` → `handle_turn(self, line: str) -> None` and
    `_execute_turn(self, line)` → `_execute_turn(self, line: str) -> None`
    (scripts/agent/orchestrator.py:157, :164).
  - Run the mypy gate and minimally fix only type errors the newly-checked bodies
    surface inside these two methods.
- **Out-of-Scope**:
  - Annotating other untyped functions in `scripts/agent` (e.g. `_on_pause_blocked`),
    enabling `--check-untyped-defs` repo-wide, or refactoring the turn bracket logic.
  - Changing the `line` parameter type at the call site — the call site already passes
    a `str` (verified).
- **Dependencies**: N/A: none.

## Background
Review finding F-001 (High confidence): mypy does not check the bodies of untyped
functions by default, and the Orchestrator is the per-turn hub of the REPL runtime
(`ReplInputLoop._dispatch_line` → `handle_turn`). The highest-traffic code path
therefore bypasses the type gate while the rest of `scripts/agent` passes it.

## Problem
`scripts/agent/orchestrator.py:157` `async def handle_turn(self, line):` and
`:164` `async def _execute_turn(self, line):` carry no annotations. Re-measured at
HEAD `b0415bd3d`: mypy emits 3 `annotation-unchecked` notes at lines 165-167 (the
untyped bodies' local annotations). Pause-check, turn bracket, error-kind
classification, and audit emission are invisible to static checking.

## Reason for Change
Every per-turn change goes through these two methods; without annotations the static
gate provides no protection there, so a type error introduced in the turn path ships
undetected.

## Implementation Intent
Signature-only annotations with the real types determined from verified call-site and
callee contracts: `line: str` (call site `_dispatch_line(self, line: str, ...)`) and
`-> None` (both methods return only via early return / completion). Expected zero body
fixes: pre-verification shows every callee return type already matches the bodies'
existing local annotations.

## Requirements
- `REQ-001`: Annotate both signatures: parameter `line: str`, return `None`; no
  runtime behavior or public API change.
- `REQ-002`: After annotation, mypy reports no `annotation-unchecked` notes for these
  methods and `uv run mypy --no-namespace-packages scripts/` passes; any type error
  newly surfaced inside the two bodies is fixed minimally (stop-and-report if a fix
  would reach outside the two methods or change behavior).
- `REQ-003`: The full test suite result is unchanged from the pre-fix baseline;
  existing Orchestrator/turn-path tests pass unchanged.

## Implementation Target Files
**Freeze status**: Frozen

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| scripts/agent/orchestrator.py | Add `line: str` / `-> None` annotations to `handle_turn` and `_execute_turn` | Only untyped pair on the turn path; 3 unchecked-body notes measured at HEAD | REQ-001, REQ-002 / AC-1, AC-2 | orchestrator.py:157, :164 untyped; `uv run mypy ... orchestrator.py` prints 3 `annotation-unchecked` notes at 165-167 | tests/agent/test_orchestrator.py, tests/agent/test_orchestrator_bg_failure_threshold.py, tests/agent/test_repl.py | Verified |

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| scripts/agent/repl_input_loop.py | Call site: `_dispatch_line(self, line: str, ...)` at :210 calls `handle_turn(line)` at :223 — confirms the `str` parameter type (resolves the Issue's open question) | REQ-001 |
| scripts/agent/workflow_engine_adapter.py | `execute_turn(self, line: str, turn_started_at: float, session_id: str, ...) -> tuple[str, str | None, bool]` at :148-154 — matches `_execute_turn`'s unpacking targets | REQ-002 |
| scripts/agent/audit_event_emitter.py | `emit_turn_end(line: str, answer: str, turn_started_at: float, error_kind: str | None, is_partial: bool = False)` at :126-132 — matches the finally-bracket call | REQ-002 |
| scripts/agent/bg_task_monitor.py | `check_pause_state()` returns `tuple[bool, list[str]]` — matches the unpack at orchestrator.py:158 | REQ-002 |

## Acceptance Criteria
- `AC-1` (REQ-001): Both signatures carry `line: str` and `-> None`; diff is
  annotation-only (no statement changes in the bodies).
- `AC-2` (REQ-002): `uv run mypy --no-namespace-packages scripts/` exits 0 and emits
  no `annotation-unchecked` note for `handle_turn`/`_execute_turn`;
  `uv run ruff check scripts/agent` passes.
- `AC-3` (REQ-003): `uv run pytest tests/agent -q` result equals the pre-fix baseline
  (no new failures), with test files unmodified.

## Tests
- `REQ-003`: Run existing turn-path tests unchanged: tests/agent/test_orchestrator.py,
  tests/agent/test_orchestrator_bg_failure_threshold.py, tests/agent/test_repl.py
  (these mock `handle_turn` and call it with plain `str` values — compatible with the
  new annotations). No new tests: annotation-only change adds no behavior to cover.

## Documentation Impact
N/A: annotation-only change; the Issue states no documentation update required, and no
docs file quotes these signatures.

## Assumptions
- `line` is always a `str` at runtime (the REPL input loop is the only production call
  site; verified at repl_input_loop.py:223). Tests only pass `str`.
- The three unchecked-body notes at 165-167 are the complete set of mypy visibility
  gaps for these two methods today.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| — | None. The Issue's one open question (the `line` parameter type) is resolved: call site passes `str` (repl_input_loop.py:210, :223). | N/A: resolved by repository evidence | N/A | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| scripts/agent/orchestrator.py | Signature annotations only | REPL runtime turn path — but zero runtime effect (annotations are not evaluated) | N/A: Path A skipped historical analysis | N/A: Path A skipped historical analysis | rsynced to `/opt/llm/scripts/` by deploy.sh; no new dependencies; deployed repl restart picks it up on next regular deploy/restart, none required for correctness |

## Design
No design decision: the annotation types are fixed by existing callee/call-site
contracts, all verified in Reference Files. Keeping the pair typed while leaving
`_on_pause_blocked` untyped is acceptable — mypy treats calls into untyped functions
as `Any` and raises no error, so no scope creep is needed for the gate to pass.

## Implementation steps

1. **Phase 1: Annotation**
   - [ ] Add `line: str` and `-> None` to `handle_turn` and `_execute_turn` (REQ-001; scripts/agent/orchestrator.py)
2. **Phase 2: Gate and body verification**
   - [ ] Run `uv run mypy --no-namespace-packages scripts/` and `uv run ruff check scripts/agent`; fix minimally only errors newly surfaced inside the two bodies (REQ-002; scripts/agent/orchestrator.py)
3. **Phase 3: Regression and deployment check**
   - [ ] Run `uv run pytest tests/agent -q` and compare against baseline (REQ-003; scripts/agent/orchestrator.py)
   - [ ] Deployment validation: file is rsynced by deploy.sh; no new deps; no service restart required for this annotation-only change (REQ-001; scripts/agent/orchestrator.py)

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/agent/orchestrator.py | Static type gate | `uv run mypy --no-namespace-packages scripts/` | exit 0; 0 `annotation-unchecked` notes for the two methods |
| scripts/agent/orchestrator.py | Static lint gate | `uv run ruff check scripts/agent` | exit 0 |
| scripts/agent/orchestrator.py | Regression (existing suites, unchanged) | `uv run pytest tests/agent -q` | same pass/fail counts as pre-fix baseline |

## Risks
- **Risk**: Newly-checked bodies could surface latent type errors requiring fixes
  outside the two methods (the Issue forbids that scope). → **Mitigation**:
  pre-verification of all four callee contracts (Reference Files) shows every body
  statement already type-matches; expected fix count is zero. If an error does appear,
  the AI Implementation Instruction (stop and report, do not widen scope) applies.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Annotate handle_turn / _execute_turn | Completed | — | 2026-10-26 | Phase 1 implemented and verified in-session |
| 2 | mypy + ruff gate verification | Completed | — | 2026-10-26 | Phase 2 implemented and verified in-session |
| 3 | pytest regression + deploy.sh check | Completed | — | 2026-10-26 | Phase 3 implemented and verified in-session |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | N/A: no blockers identified | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261025-210023_agent001_orchestrator-turn-path-typing.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261025-214319
- **Related target files**: scripts/agent/orchestrator.py

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Issue Summary / Required Changes; untyped signatures at orchestrator.py:157, :164 | scripts/agent/orchestrator.py | Phase 1 | AC-1 | Validation plan row 1 | Explicit in issue |
| REQ-002 | Issue Acceptance Criteria; measured 3 `annotation-unchecked` notes at 165-167; callee contracts verified | scripts/agent/orchestrator.py | Phase 2 | AC-2 | Validation plan rows 1-2 | Confirmed by repository evidence |
| REQ-003 | Issue Acceptance Criteria / Testing Expectations | scripts/agent/orchestrator.py | Phase 3 | AC-3 | Validation plan row 3 | Explicit in issue |