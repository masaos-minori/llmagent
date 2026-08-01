# Implementation Procedure: Enforce Encryption for Diagnostic Data

## Goal
Ensure that diagnostic data containing sensitive fields is always encrypted before being saved. If encryption is not available, refuse to save the data.

## Scope
- Implement detection of sensitive information within `DiagnosticStore.save()`.
- Refuse save operation (raise exception) if sensitive data is detected and no encryption key is provided.

## Assumptions
- A mechanism to define "Sensitive Information" (e.g., regex patterns for API keys, etc.) is established.
- `DiagnosticsConfig` correctly provides the `encryption_key`.

## Design decisions
- Use regex-based pattern matching to identify potential secrets in the JSON payload.
- Raise a custom `RuntimeError` or specialized security exception when a violation occurs.

## Alternatives considered
- N/A

## Implementation
### Target file
`scripts/agent/diagnostic_store.py`

### Procedure
1. Define a set of sensitive patterns (regex) for common secrets (API keys, tokens).
2. In `DiagnosticStore.save()`:
    a. Load `DiagnosticsConfig`.
    b. If `diagnostics_cfg.encryption_key` is empty:
        i. Scan `content` for sensitive patterns.
        ii. If match found, raise an exception with a descriptive message.
    c. Proceed with normal flow if no violation.

### Method
Regex scanning of the `content` string.

### Details
The check should occur inside `save()` before any database operations.

## Compatibility considerations
- Breaking change: Existing workflows that rely on unencrypted diagnostic logs containing sensitive data will fail.

## Security considerations
- Prevents accidental leakage of credentials in plaintext diagnostic logs.

## Rollback considerations
- Reverting the code changes will restore the opt-in behavior.

## Validation plan
- Unit test: Verify refusal when sensitive data is present without a key.
- Unit test: Verify successful encryption when a key is provided.
- Unit test: Verify non-sensitive data is saved normally without encryption.

## Out of scope
- Modifying other storage mechanisms.

## Traceability
- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: requires/20260731-071637_require.md
- Source plan: plans/20260731-090702_plan.md
- Source implementation procedure: N/A
- Generated at: 20260731-194407
- Related target files: scripts/agent/diagnostic_store.py
