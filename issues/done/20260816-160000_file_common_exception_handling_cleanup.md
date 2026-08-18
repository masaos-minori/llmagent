# `mcp_servers/file/common.py`: consolidate exception handlers and add exception chaining

## Priority
Low

## Summary
Two related, deferred ideas from `scripts/mcp_servers/file/common.py`'s 2026-08-14 refactor
cycle:
1. `_on_auth_error`/`_on_not_found`/`_on_validation_error` are three structurally identical
   one-line async exception handlers (differ only by an HTTP status-code literal).
2. `resolve_safe`'s and `check_size_limit`'s `except OSError:` blocks re-raise as
   `FileValidationError` without `from e` exception chaining, losing the original traceback.

## Reason for Change
Both were identified during the refactor cycle but deferred:
1. Converting the three handlers to closures produced by a shared factory function would change
   each handler's `__name__`/`__qualname__` from e.g. `_on_auth_error` to a shared closure name —
   a subtle behavior difference if anything downstream (logging, FastAPI's exception-handler
   registry introspection, docs generation) ever observes handler identity, and the duplication
   removed (3 one-line bodies) was judged too small to justify the indirection without first
   ruling out that risk.
2. Adding `from e` sets `__cause__` on the raised exception, changing traceback rendering — not
   enforced by this repo's ruff config (no `B904`/bugbear rule selected) and not verified against
   any log-scraping tooling that might parse traceback text.

## Implementation Intent
For (1): search `docs/`, logging call sites, and `check-mcp-docs` output for any reliance on
these handlers' `__name__` before consolidating; if none found, extract a
`_make_error_handler(status_code: int) -> Callable` factory.
For (2): confirm no test asserts on `__cause__` or traceback text, and confirm no log-scraping
tooling parses tracebacks, before adding `from e`. This could also be bundled with a repo-wide
decision to adopt `B904` (bugbear) — check whether that's already under consideration elsewhere
before doing it ad hoc here.

## Target Files or Areas
- `scripts/mcp_servers/file/common.py` (`_on_auth_error`, `_on_not_found`,
  `_on_validation_error`, `resolve_safe`, `check_size_limit`)

## Required Changes
- Search for handler-`__name__` dependencies (docs, logs, introspection) before consolidating.
- If none found, extract a shared handler factory; re-verify FastAPI still registers/dispatches
  correctly.
- Confirm no traceback-text/`__cause__` test dependency, then add `from e` to both `OSError`
  re-raise sites.

## Acceptance Criteria
- All 3 exception-handler behaviors (status code, response body) are unchanged for callers.
- `resolve_safe`/`check_size_limit`'s raised `FileValidationError` instances have `__cause__` set
  to the original `OSError` (if that change is made).
- `tests/mcp_servers/file/test_file_common.py`'s 38 existing tests pass unchanged.

## Testing Expectations
Full `tests/mcp_servers/file/test_file_common.py` suite; `tests/mcp_servers/file/` full
regression run.

## Documentation Impact
None expected.

## Out of Scope
- Do not change the HTTP status codes or response bodies these handlers produce.
- Do not adopt `B904` repo-wide as part of this issue — scope any such decision separately if it
  affects more than this file.

## AI Implementation Instruction
These are two independent, low-risk cleanups — implement and verify each separately. Confirm the
absence of handler-identity or traceback-text dependencies before making either change, per the
Reason for Change above.
