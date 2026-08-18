# Migrate `mcp_servers/audit.py` JSON audit-record serialization from stdlib `json` to `orjson`

## Priority
Low

## Summary
`scripts/mcp_servers/audit.py`'s `_audit_log` function serializes each audit record with stdlib
`json.dumps(record, ensure_ascii=False)`. `rules/coding.md`'s "Key library choices" mandates
`orjson` (not stdlib `json`) for all JSON serialization repo-wide.

## Reason for Change
Found during a `prompts/04_refactor.md` cycle on `audit.py` (2026-08-14). Not implemented there
because switching serializers risks subtle output differences (float representation, key
ordering, non-ASCII byte-vs-str handling) that would count as a visible-output change for this
audit-log line format — audit logs are potentially consumed/parsed by downstream tooling, so a
byte-level behavior change requires explicit verification, not a blind swap under a
behavior-preserving refactor's constraints.

## Implementation Intent
Before switching, write a characterization test comparing `orjson.dumps(record, ...).decode()`
output against the current `json.dumps(record, ensure_ascii=False)` output across the existing
test suite's representative record shapes (all field combinations, `detail` present/absent).
Only switch once byte-identical (or an intentional, documented difference is signed off).

## Target Files or Areas
- `scripts/mcp_servers/audit.py` (`_audit_log`)
- `tests/mcp_servers/test_audit_log_format.py` (existing 12-test characterization suite for
  this exact output format)

## Required Changes
- Add a test asserting `orjson.dumps(record).decode()` (with whatever `option=` flags reproduce
  `ensure_ascii=False`'s effect) equals `json.dumps(record, ensure_ascii=False)` for every
  existing test case's record shape.
- If byte-identical, switch `_audit_log` to use `orjson.dumps(...).decode()`.
- If not byte-identical, document the specific difference and get explicit sign-off before
  proceeding (per `rules/coding.md`'s explicit sign-off gates).

## Acceptance Criteria
- `_audit_log`'s output uses `orjson` for serialization.
- All 12 existing tests in `tests/mcp_servers/test_audit_log_format.py` pass unchanged (same
  assertions, same expected output), or are updated with explicit justification if the output
  format intentionally changes.
- No other MCP server's audit-log call site behavior changes (this module is shared).

## Testing Expectations
Run `tests/mcp_servers/test_audit_log_format.py` and the full `tests/mcp_servers/` suite
before and after (every MCP server calls `_audit_log`). Byte-level output comparison required
per the Implementation Intent above.

## Documentation Impact
None expected — internal serialization detail, not a public API or schema change.

## Out of Scope
- Do not change the audit record's field set, field names, or logical content.
- Do not change any other module's JSON serialization as part of this issue.

## AI Implementation Instruction
Do the byte-comparison characterization step first and report the result before switching the
implementation — if `orjson`'s output differs from `json`'s in any way (even key ordering), stop
and report rather than silently accepting the difference.
