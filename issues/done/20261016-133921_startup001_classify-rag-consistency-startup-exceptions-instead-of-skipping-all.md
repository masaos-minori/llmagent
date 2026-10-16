# Classify RAG consistency startup exceptions instead of skipping all

## Priority
Medium

## Summary
The RAG consistency check in the startup validation pipeline currently converts every
raised exception into a `SKIPPED` outcome. Distinguish programming errors from benign or
transient conditions so a genuine defect is not masked as "check skipped", matching the
classification already used for memory-injection failures.

## Background
`StartupValidationPipeline.check_services()` runs the RAG consistency check inside
`asyncio.wait_for(... run_in_executor ...)` and wraps it in `try/except TimeoutError`
plus `try/except Exception`. The broad `except Exception` branch records
`pipeline.add_skipped("rag_consistency", ...)` for any failure.

The project already separates programming errors from benign conditions elsewhere:
`PromptSetup._classify_memory_failure()` returns distinct categories
(`NETWORK_TRANSIENT`, `DATABASE_OR_IO`, `PROGRAMMING_ERROR`, `UNKNOWN`) so a
`PROGRAMMING_ERROR` is logged and surfaced differently from a transient condition. The
RAG check has no equivalent classification.

## Problem
A bug inside `RagMaintenanceService().consistency()` (for example a `KeyError`,
`AttributeError`, or `TypeError`) raises one of the caught exception types and is turned
into a generic `SKIPPED` outcome. The operator sees only "RAG consistency check skipped"
with no signal that the skip was caused by an internal defect rather than a timeout, a
missing embedding endpoint, or a transient IO error. Startup still proceeds, so the defect
is easy to miss until downstream RAG behavior breaks.

## Reason for Change
The startup pipeline is the fail-fast gate for service health. The RAG check is intentionally
soft (it must not abort startup), but soft does not mean unclassified. Without classification
operators cannot triage a skipped RAG check, and the one untested code path (`except Exception`)
has no regression coverage — only the `TimeoutError` path is covered by
`tests/agent/test_startup_validation.py`.

## Implementation Intent
Add exception-type classification to the RAG consistency check that mirrors the existing
memory-failure model. On `TimeoutError` keep the current `SKIPPED` (timeout) behavior. For
other exceptions, classify by root cause (network/timeout vs DB/IO vs programming error) and
record the outcome so a programming error is distinguishable in logs and the readiness
summary. Keep the check non-fatal in all cases — startup must still proceed.

## Target Files or Areas
- `scripts/agent/startup_validation.py` (RAG consistency block)
- `tests/agent/test_startup_validation.py`

## Required Changes
- Classify non-timeout exceptions raised by the RAG consistency check by category
  (network/timeout, DB/IO, programming error, unknown), reusing the same type lists where
  sensible.
- Record a `SKIPPED` outcome for every non-fatal failure, but make the outcome message or a
  status field carry the category so a programming error is distinguishable from a timeout or
  a missing embedding endpoint.
- Do not promote any RAG failure to `FATAL`; the check stays soft.
- Add a regression test asserting a programming-error exception (e.g. `KeyError`) is recorded
  as a classified `SKIPPED` outcome, not an unclassified one.

## Constraints
- Must remain non-fatal: startup proceeds regardless of RAG outcome.
- Preserve the existing 30s `wait_for` timeout and its `TimeoutError -> SKIPPED (timeout)`
  behavior.
- Keep exception messages secret-masked per `skills/DESIGN.md` No secrets in output.

## Acceptance Criteria
- A `TimeoutError` still produces a `SKIPPED` outcome whose message indicates a timeout.
- A programming-error exception (e.g. `KeyError`) produces a `SKIPPED` outcome whose category
  is distinguishable from the timeout case in the logged message or outcome metadata.
- Startup still completes (no `FATAL`) when the RAG check raises any exception.
- A new test covers the programming-error path; existing timeout/success tests still pass.

## Testing Expectations
- Add/extend `tests/agent/test_startup_validation.py` with cases for a programming-error
  exception and confirm the recorded outcome category.
- Run `uv run pytest tests/agent/test_startup_validation.py`.
- Run `uv run ruff check scripts/agent/startup_validation.py` and
  `uv run mypy --no-namespace-packages scripts/agent/startup_validation.py`.

## Documentation Impact
None required. If the readiness summary gains a per-category RAG indicator, document the
meaning of each RAG status line in the reporter's module docstring only.

## Out of Scope
- Changing the fail-fast behavior of other pipeline checks (security audit, MCP auth,
  readiness, tool discovery, routing drift/safety tiers).
- Making the RAG consistency check fatal.
- Refactoring the memory-failure classification in `startup_prompt_setup.py`.

## Dependencies
N/A: none

## Unresolved Questions
- Should a `PROGRAMMING_ERROR` category be surfaced in the human-readable readiness summary
  (currently the RAG line shows only OK/WARN/fatal/warning counts), or is the log + outcome
  message sufficient?

## AI Implementation Instruction
Do not change the fatal/non-fatal contract: the RAG check must stay soft and never abort
startup. Only add classification to the existing `except Exception` branch and surface the
category in the `SKIPPED` message/metadata. Preserve the `TimeoutError` handling exactly.
Keep changes scoped to `startup_validation.py` plus its test file. Stop and report the
Unresolved Question if deciding where to surface the category affects another component.

## Traceability
- **Workflow phase**: python-code review -> issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261016-133921
- **Related target files**: scripts/agent/startup_validation.py, tests/agent/test_startup_validation.py
