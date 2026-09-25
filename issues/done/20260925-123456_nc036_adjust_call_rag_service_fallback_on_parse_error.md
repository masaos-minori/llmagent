# Adjust `call_rag_service()` Fallback Logic for JSON Parse Errors

## Background

The current implementation of `scripts/rag/pipeline_service.py::call_rag_service()` triggers an in‑process RAG fallback whenever the external RAG service returns malformed JSON.  The `except ValueError` block logs a warning and then calls `_set_fallback_reason()` before returning an empty string and a `None` status code.  Downstream logic treats any `None` status code as a failure and therefore initiates a local RAG run.

This behaviour contradicts ADR‑010 Decision #9, which states that *JSON parse errors should be treated as empty results* and **should not trigger a fallback**.  The mismatch is already recorded as NC‑036 in the Needs Confirmation inventory.

## Problem

* Unintended double processing*: A malformed response causes the local pipeline to run again unnecessarily.
* Hidden bugs*: Malformed JSON will silently fall back, making it hard to surface errors.
* Performance overhead*: In‑process fallback adds extra latency when the remote call merely failed to parse its payload.
* Test inconsistency*: Existing tests expect the fallback callback to fire on a parse error, which diverges from the documented policy.

## Reason for Change

Align the implementation with the documented governance decision (ADR‑010).  Keeping the code consistent with the ADR improves predictability, reduces hidden failures, and brings the test suite in line with policy.

## Implementation Intent

Modify the `except ValueError` clause in `pipeline_service.py` so that:
1. It logs a warning indicating a parse error.
2. It does **not** call `_set_fallback_reason()`.
3. It returns an empty string, a `None` status code, and zero elapsed time – exactly the contract for an *empty result*.

No other part of the system relies on receiving a fallback reason when a parse error occurs; removing the fallback will not affect functional behaviour.

## Affected Files

- `scripts/rag/pipeline_service.py`

## Acceptance Criteria

1. Running `call_rag_service()` with a mocked HTTP client that returns a body which cannot be parsed as JSON should result in:
   - A warning logged.
   - The `set_fallback_reason` callback is **not** invoked.
   - The return value is `("", None, 0.0)`.
2. Unit tests that previously expected the fallback callback to be called on a parse error must be updated accordingly.
3. No new runtime errors are introduced.

## Documentation Impact

* Update the explanation in ADR‑010 to clarify that JSON parse errors do **not** trigger a fallback.
* Add a note in the Needs Confirmation inventory (NC‑036) that this change aligns the code with the ADR.

## Priority

Medium – the change is non‑critical for current releases but fixes a documented discrepancy and prevents future regressions.

---

**Labels:** `bug`, `governance`, `runnable`