# Short-circuit RAG consistency check on tool-discovery FATAL

## Priority
Low

## Summary
Add a `has_fatal` short-circuit after the MCP tool discovery step in
`StartupValidationPipeline.check_services` so a tool-discovery FATAL skips the RAG
consistency check instead of running it unconditionally.

## Background
Evidence (Explicit in code): in `scripts/agent/startup_validation.py`,
`StartupValidationPipeline.check_services` runs the readiness check first, then
returns early when `pipeline.has_fatal` is set, then runs MCP tool discovery, then
runs the RAG consistency check. The early return after readiness means a readiness
FATAL skips both tool discovery and the RAG check. There is no equivalent re-check
after tool discovery, so a tool-discovery FATAL does not prevent the RAG check from
running.

Evidence (Documentation only): the startup validation operations doc states the
runtime stage "skips tool discovery and the RAG check when readiness already reported
a FATAL". The doc scopes the skip to readiness, so this is an internal control-flow
inefficiency, not a doc/code mismatch.

Related, not overlapping: `issues/done/20261115-214906_startrev006_rag-check-timeout-executor.md`
makes the RAG check cancellable at exit; `issues/done/20261104-143443_ragverify001_complete-fail-closed-rag-consistency.md`
makes the RAG report internally complete and fail-closed; `issues/done/20261016-133921_startup001_classify-rag-consistency-startup-exceptions-instead-of-skipping-all.md`
classifies RAG exceptions. None addresses the control-flow short-circuit between tool
discovery and the RAG check.

## Problem
On a tool-discovery FATAL the process is already failing and will abort startup. The
RAG consistency check still runs anyway, consuming up to the startup bound and adding
a further `rag_consistency` warning to an already-failing path. The RAG result is only
ever a warning (the check stays soft), so it changes nothing about the outcome; it only
delays the abort and adds noise.

## Reason for Change
The wasted work happens on an already-failing path, so correctness is unaffected. It is
Low: it is a non-blocking efficiency and log-noise improvement, not a correctness,
data-integrity, or reliability defect.

## Implementation Intent
Mirror the readiness short-circuit: after the MCP tool discovery block, if
`pipeline.has_fatal` is set, return `pipeline` before the RAG consistency step. Keep the
RAG check's existing soft semantics (fatal findings stay fatal, timeout and other
failures stay warnings, startup proceeds) for every path that still reaches it. Do not
touch the readiness short-circuit or any other check.

## Target Files or Areas
- `scripts/agent/startup_validation.py` (`StartupValidationPipeline.check_services`)
- `tests/agent/test_startup_validation.py`

## Required Changes
- After the MCP tool discovery block in `check_services`, add an early return when
  `pipeline.has_fatal` is set, placed before the RAG consistency step.
- Add a regression test asserting that a tool-discovery FATAL skips the RAG consistency
  check (the RAG service is not invoked and no `rag_consistency` outcome is recorded).
- Preserve the existing readiness FATAL short-circuit and its test.

## Constraints
- Do not change the readiness short-circuit or the order of the readiness check.
- Do not change what the RAG consistency check verifies or how it classifies severity;
  the check stays soft and never aborts startup.
- Preserve the startup bound and the fail-closed-downstream behavior of an unverified
  RAG state.
- Keep changes confined to the runtime-stage control flow; do not touch the config-only
  stage or other checks.

## Acceptance Criteria
- A tool-discovery FATAL returns before the RAG consistency check runs.
- The RAG consistency check still runs when no fatal exists (readiness OK and discovery
  OK or warning-only).
- The readiness FATAL short-circuit still skips tool discovery and the RAG check.
- Existing startup validation tests still pass.

## Testing Expectations
- Unit test: inject a tool-discovery FATAL and assert the RAG consistency service is not
  called and no `rag_consistency` outcome is recorded.
- Unit test: confirm the RAG check still runs on a discovery warning-only path.
- Run `uv run pytest tests/agent/test_startup_validation.py`.
- Run `uv run ruff check scripts/agent/startup_validation.py` and
  `uv run mypy --no-namespace-packages scripts/agent/startup_validation.py`.

## Documentation Impact
Optional. If the fix lands, update the startup validation operations doc to state that
the RAG consistency check is skipped on any runtime-stage FATAL (readiness or tool
discovery), not only on a readiness FATAL. Keep it high-level (intent and failure
behavior); do not add implementation-location detail or line numbers.

## Out of Scope
- Changing the readiness short-circuit logic or its position.
- Changing what the RAG consistency check verifies or its severity classification.
- Making other runtime-stage checks short-circuit each other.
- The config-only stage or the non-RAG pipeline checks.

## Dependencies
N/A: none. Related but independent:
`issues/done/20261115-214906_startrev006_rag-check-timeout-executor.md` (makes the RAG
check cancellable); implementing it first does not change this issue.

## Unresolved Questions
- Should the operations doc be updated as part of this change or left for a separate
  documentation pass? (Needs confirmation)

## AI Implementation Instruction
Add one early return after the tool discovery block, guarded by `pipeline.has_fatal`,
before the RAG consistency step. Do not reorder the readiness check, do not change the
RAG check's soft/fail-closed-downstream contract, and do not touch other checks. Keep
the change scoped to `startup_validation.py` plus its test file. Stop and report the
Unresolved Question only if deciding whether to update the ops doc affects another
document.

## Traceability
- **Workflow phase**: python-code-review
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261117-175055
- **Related target files**: `scripts/agent/startup_validation.py`, `tests/agent/test_startup_validation.py`
