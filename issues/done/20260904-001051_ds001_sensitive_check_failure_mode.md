# Add defensive check for DiagnosticStore sensitive field detection failure mode

## Summary

DiagnosticStore.save checks for sensitive patterns AFTER _filter_sensitive_fields runs. If _filter_sensitive_fields fails (e.g., JSON decode error), the original content with raw artifacts/RAG outcomes reaches the sensitive check, triggering RuntimeError. This crashes session diagnostics persistence during shutdown — a worst-case scenario where the user loses their session summary.

## Background

session_persister.py persists diagnostics summary containing artifacts and rag_stage_outcomes fields. These are flagged as sensitive at lines 131-137. _filter_sensitive_fields replaces them with {"_redacted": True, "count": N}. Then save() validates the filtered content against sensitive patterns.

## Problem

If _filter_sensitive_fields fails, the unfiltered content triggers a RuntimeError in save(), causing session data loss during shutdown.

## Reason for Change

Data integrity risk: a single point of failure in the filtering step cascades into complete session data loss. The error path is not graceful.

## Implementation Intent

Option A: Wrap _filter_sensitive_fields in try/except and handle failures gracefully (log warning, skip sensitive check, proceed with unfiltered save). Option B: Move the sensitive check INSIDE _filter_sensitive_fields so it can fail early without crashing. Option C: Add a fallback path in save() that retries with a simpler redaction strategy. Choose the approach that minimizes behavioral change while eliminating the crash path.

## Target Files or Areas

- scripts/agent/diagnostic_store.py
- scripts/agent/session_persister.py

## Required Changes

- Add error handling around _filter_sensitive_fields call
- Ensure session persistence does not crash on filter failure
- Document the failure mode and mitigation

## Constraints

- Must not change the sensitive field detection logic itself
- Must preserve the security boundary (sensitive data must still be protected)

## Out of Scope

- Redesigning the sensitive field detection system
- Adding new encryption features

## Dependencies

N/A: none

## Acceptance Criteria

- [ ] Session persistence completes even if _filter_sensitive_fields fails
- [ ] Sensitive data protection is maintained (either filtered or rejected explicitly)
- [ ] No crash during shutdown with corrupted diagnostic data

## Testing Expectations

- Unit test: inject failing _filter_sensitive_fields, verify graceful degradation
- Integration test: verify session persistence during shutdown with malformed diagnostics

## Documentation Impact

Document the failure mode and mitigation in the diagnostic_store module docstring.

## Priority

Medium

## AI Implementation Instruction

Add defensive error handling only around the _filter_sensitive_fields call. Do not redesign the sensitive field detection. Preserve the security boundary. Stop and report if the failure mode is unclear from context.
