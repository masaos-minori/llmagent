# Extract shared console-processor-attach helper in `otel_tracer.py` without changing log wording

## Priority
Low

## Summary
`_attach_console_exporter` and the fallback branch inside `_attach_otlp_exporter` in
`scripts/shared/otel_tracer.py` share a 2-line "create `_ConsoleProcessor`, add_span_processor"
pattern, but log different messages (info "configured" vs. warning "falling back").

## Reason for Change
Found during a behavior-preserving refactor cycle on `scripts/shared/otel_tracer.py`
(2026-08-13). Not merged there because extracting a shared helper would either duplicate the
divergent log call inside the helper (defeating the purpose) or require parameterizing the log
message/level, which risks a visible-output change if done carelessly (Evidence label: Explicit
in code — both call sites and their distinct log calls are directly visible in the source).

## Implementation Intent
If pursued, parameterize the shared helper with the log level and message text as explicit
arguments (not inferred), so the exact current log wording and level at each call site is
preserved byte-for-byte. Add a characterization test asserting the exact log text at both call
sites before making the change.

## Target Files or Areas
- `scripts/shared/otel_tracer.py` (`_attach_console_exporter`, `_attach_otlp_exporter`)
- `tests/shared/test_otel_tracer.py`

## Required Changes
- Add characterization tests asserting exact log message text/level at both call sites (if not
  already present after the 2026-08-13 refactor's added tests — check first).
- Extract a shared helper parameterized by log level/message, called from both sites.

## Acceptance Criteria
- Log message text and level at both call sites remain byte-identical to current behavior.
- No change to which processor/exporter is attached under which condition.

## Testing Expectations
`tests/shared/test_otel_tracer.py` full suite, including log-message assertions via `caplog`,
before and after.

## Documentation Impact
None expected.

## Out of Scope
- Do not change the fallback logic (when console vs. OTLP is used) — only the shared
  code structure for attaching the console processor.

## AI Implementation Instruction
Check whether `tests/shared/test_otel_tracer.py` already asserts exact log text at both call
sites (added during the 2026-08-13 refactor cycle) before writing new characterization tests —
avoid duplicating existing coverage.
