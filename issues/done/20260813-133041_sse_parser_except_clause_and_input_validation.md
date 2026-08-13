# sse_parser.py: redundant except-clause member and missing negative-value validation on constructor args

## Priority
Low

## Summary
Two small, related findings in `scripts/shared/sse_parser.py`:
1. `RobustSSEParser._is_valid_json`'s `except (orjson.JSONDecodeError, ValueError)` is
   redundant — `orjson.JSONDecodeError` is already a `ValueError` subclass
   (`orjson.JSONDecodeError → json.decoder.JSONDecodeError → ValueError`).
2. `RobustSSEParser.__init__`'s `malformed_retry`/`heartbeat_timeout` constructor arguments are
   not validated to reject negative values.

## Reason for Change
Found during a behavior-preserving refactor cycle on `scripts/shared/sse_parser.py`
(2026-08-13). Neither was fixed there: item 1 touches the parser's exception-handling clause
directly, which the task's "Exception behavior freeze... do not change parsing behavior even
incidentally" constraint placed out of scope for that cycle; item 2 would be a genuine behavior
change (rejecting previously-silently-accepted negative inputs), not a structural refactor
(Evidence label: Explicit in code — `orjson.JSONDecodeError.__mro__` confirms the subclass
relationship; the constructor's lack of validation is directly visible).

## Implementation Intent
1. Simplify `except (orjson.JSONDecodeError, ValueError)` to `except ValueError` (the redundant
   tuple member removal is behavior-neutral by the confirmed subclass relationship, but treat it
   as its own reviewed change given the file's behavior-sensitive nature).
2. Decide whether `malformed_retry`/`heartbeat_timeout` should reject negative values at
   construction time (raise `ValueError`) or continue to accept them silently; check all current
   call sites in `scripts/shared/llm_sse_stream.py` for any that might pass a negative value
   today before adding a check that could newly reject a previously-accepted call.

## Target Files or Areas
- `scripts/shared/sse_parser.py` (`RobustSSEParser.__init__`, `_is_valid_json`)
- `scripts/shared/llm_sse_stream.py` (caller/config source)

## Required Changes
- Item 1: narrow the except clause to `ValueError`; confirm via the existing malformed-JSON
  tests that behavior is unchanged.
- Item 2: audit all constructor call sites for current argument ranges; if adding validation,
  raise a clear `ValueError` with the offending value in the message; add tests for the
  boundary (0 valid vs. negative invalid, matching the project's established boundary-test
  convention).

## Acceptance Criteria
- Item 1: all existing malformed-JSON tests pass unchanged; `except` clause has one member.
- Item 2: either explicit rejection of negative values with a clear error message and a test, or
  an explicit decision (documented in the PR/commit) that negative values remain accepted
  as-is, with a comment explaining why.

## Testing Expectations
Full `tests/agent/test_llm_client.py::TestRobustSSEParserFeed`/`Heartbeat` suite and
`tests/shared/test_llm_sse_helpers.py` before and after both changes.

## Documentation Impact
None expected unless item 2 introduces a new constructor-time exception, in which case any
docstring describing `RobustSSEParser.__init__`'s accepted argument ranges should be updated.

## Out of Scope
- Do not change the parser's SSE frame-parsing logic, heartbeat timing, or malformed-frame
  budget-exceeded behavior.

## AI Implementation Instruction
Treat items 1 and 2 as independently implementable. For item 2, grep all
`RobustSSEParser(` construction call sites across `scripts/`/`tests/` before adding validation,
to confirm no current caller would newly break.
