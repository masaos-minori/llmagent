---
title: "ADR-010: In-Process Fallback When External RAG Execution Fails"
area: governance
tags:
  - rag
  - fallback
  - in-process
related:
  - rag_03_01_query_pipeline-overview.md
  - rag_03_05_query_pipeline-augment-stages.md
  - rag_05_04-error-handling-reference.md
  - rag_05_01-configuration-reference.md
  - db_02_architecture_and_schema-schema-reference.md
  - governance_01_documentation-policy.md
---

# ADR-010: In-Process Fallback When External RAG Execution Fails

## Keywords

- rag
- fallback
- http service
- in-process

## Status

Withdrawn

RAG is reached only through the rag-pipeline MCP server over the common MCP transport, and no remote delegation or fallback to another execution path exists. The text below remains as the record of the withdrawn decision.

## Summary

Canonicalizes the automatic fallback to the in-process local RAG when the RAG pipeline's external service fails (see Decision).

## Context

### Problem

The RAG pipeline depends heavily on the external RAG service, so a network failure or a service outage stops the whole search function. In addition, because the distinction between an empty result and a technical failure is unclear, appropriate recovery is difficult.

This problem applies only to a process that delegates over HTTP. No production process delegates today: the rag-pipeline MCP server always runs in-process, and no configuration file sets `rag_query_service_url` (renamed from `rag_service_url`). This ADR therefore governs the delegation code path as a capability that is not currently exercised in production.

### Constraints

- Execution on a single host with multiple processes is assumed
- The RAG pipeline has two execution modes, selected only by whether `rag_query_service_url` is configured
- The external RAG service is reached through `POST /v1/call_tool` with the `rag_run_pipeline` tool, and the call carries an authentication token when one is configured
- The in-process mode needs the local `rag.sqlite` and the sqlite-vec extension in the calling process
- The RAG pipeline served by the external RAG service must not itself delegate over HTTP (its own `rag_query_service_url` is empty)

## Assumptions

- Target environment: a single host, multiple processes
- The HTTP delegation mode has no production caller; the decisions below apply when a process is configured with a non-empty `rag_query_service_url`
- Expected scale: limited concurrency
- Trust boundary: the external RAG service authenticates callers with a token; the local mode needs no network access
- External dependencies: the external RAG service is reachable over HTTP; it is the dependency whose failure triggers the fallback
- The external and the in-process mode are expected to read one canonical `rag.sqlite`: every configuration file sets the same `rag_db_path`. This sharing is a deployment arrangement by convention; it is not enforced and the repository records no requirement for it
- Items to re-evaluate if the assumptions no longer hold: multi-host configuration, distributed execution, the external RAG service using a corpus other than the local one

## Decision

### Decision Details

1. When `rag_query_service_url` is set, an HTTP POST is sent to the external RAG service.
2. When `rag_query_service_url` is not set, the in-process local RAG is executed.
3. The HTTP call to the external RAG service is bounded per attempt by a configured timeout.
4. HTTP errors (401, 403, 4xx, 5xx) are distinguished from empty results (`""`).
5. An empty result is treated as a valid result and does not trigger fallback.
6. Only technical failures are fallback conditions: timeouts and connection errors, HTTP 5xx after the bounded retries are exhausted, HTTP 4xx other than 401/403, and an HTTP 200 response carrying `is_error=true`. Authentication errors (401/403) do not fall back.
7. On fallback, the whole pipeline MQE → KNN/BM25 → RRF → Rerank → Augment is re-executed.
8. The result source (Remote/Local/Fallback) is tracked and recorded in metrics and logs.
9. Parse errors (an unparsable body or a non-string `result`) are logged and treated as empty results without fallback; the caller can tell this from a valid empty answer only through the log.
10. Local DB access uses only `rag.sqlite`.
11. Result consistency between the external RAG and the local RAG is detected on every fallback: the remote and local corpus identities are compared before a fallback result is accepted (`rag_05_07-rag-index-consistency-checks.md`), and a mismatch between two present identities is enforced per `rag_identity_mismatch_policy` (`rag_05_01-configuration-reference.md`, `reject` default), while an unverifiable identity (either side absent) proceeds and is recorded. This detects a divergence; it is not corpus synchronization. Equal identities mean the same corpus identity, not identical search results. The two modes still read from their own configured database paths, and the availability-first fallback is unchanged.
12. The result vocabulary is `remote_nonempty`, `remote_empty`, `in_process_fallback`, `auth_error` (internal to `HttpAugment`), and the public enums `ResultSource` and `HttpResultKind` (`SUCCESS`, `EMPTY`, `ERROR`, `NOT_USED`, `AUTH_ERROR`).
13. The failure outcomes of the HTTP delegation path are fixed by the table below; each cause has exactly one outcome.

    | Cause | Outcome |
    | --- | --- |
    | Valid empty result (HTTP 200, `result` absent or `""`) | Empty result `""`; no fallback |
    | HTTP 401 or 403 | `auth_error`; fail closed with `RagPipelineError`; no fallback |
    | HTTP 4xx other than 401/403 | `transient_failure` without retry; falls back |
    | HTTP 5xx or transport error after the bounded retries | `transient_failure`; falls back |
    | HTTP 200 with `is_error=true` | `transient_failure`; falls back |
    | Unparsable body or non-string `result` | Empty result; no fallback |
    | Identity mismatch (both identities present and unequal) | Fallback rejected under the default `reject` policy; tolerated and marked degraded under `degraded` |
    | Identity unverifiable (either identity absent) | Fallback proceeds and the unverifiable state is recorded |
    | Local `rag.sqlite` cannot be opened during fallback | `RagPipelineError`; no further fallback |

14. Identity sources: the remote identity is parsed from the `corpus_identity` object of a successful response and is absent after a failed call, so it is always absent on the fallback path; the local identity is read from the local corpus metadata at fallback time. Both are evaluated per request, never cached, and the remote value is self-reported by the authenticated service and not independently verified.

### Amendment (ragcorpus001, 2026-10-31)

In force: this records the rationale of Decision Details item 11. It previously stated that result consistency between the external and local RAG "is not guaranteed" with no way to detect a divergence. The RAGCORPUS001 identity-contract plan replaced that with the detection contract now recorded as item 11: a fallback result is accepted only after the remote and local corpus identities are compared (`rag_05_07-rag-index-consistency-checks.md`); a mismatch between two present identities is enforced per `rag_identity_mismatch_policy` (`rag_05_01-configuration-reference.md`, `reject` default), while an unverifiable identity proceeds and is recorded. It is a detection contract, not corpus synchronization. The availability-first trade-off and the Alternative C rejection are unchanged. Adopted under the task-level approval decision referenced in this Approval Record and links `20261030-013620_ragcorpus001_rag-corpus-identity.md`.

### Amendment (adrrag002, 2026-11-08)

In force: this rewords INV-01, INV-04, INV-07, INV-09 and the pipeline-models Implementation Reference. No decision changed: INV-01 and the reference use the current key `rag_query_service_url`; INV-04 and INV-07 carry the item 13 fallback conditions (including `is_error=true` and a non-string `result`); INV-09 separates database sharing (a convention, not enforced), corpus identity (compared at fallback) and search-result equivalence (never promised). The earlier "not guaranteed, no detection" wording is superseded by the amendment above.

### Scope

- **Target components**: `RagPipeline`, `AugmentRefiner`, `AugmentStage`, and the removed HTTP augment and remote call components
- **Target processes**: any process that constructs `RagPipeline` with a non-empty `rag_query_service_url`. The rag-pipeline MCP server always constructs it with an empty `rag_query_service_url`, so it never delegates; no other production caller of the HTTP mode exists (Explicit in code — `RagPipeline` is constructed only in the rag-pipeline MCP service). The Agent REPL does not call `RagPipeline` directly, and the ingester does not use `augment()`.
- **Target data**: `rag.sqlite`
- **Target Environment Profile**: production (the only supported execution mode; ADR-004 applies one failure-handling policy to every environment)
- **Target APIs or processing paths**: `RagPipeline.augment()`, `AugmentStage.run()`, and the removed remote call path

### Out of Scope

- Detailed handling of individual HTTP status codes
- Detailed parameters of the retry policy
- How metrics are collected
- Log output format
- Corpus synchronization protocol

## Rationale

### 1. Primary Reason for Adoption — Availability

If the search function stops when the external RAG service fails, the user experience suffers greatly. In-process fallback maintains availability.

### 2. Second Reason for Adoption — Error Classification

Distinguishing empty results from technical failures prevents unnecessary fallback: an empty result means "searched but nothing matched", a technical failure "could not search".

### 3. Third Reason for Adoption — Observability

Tracking the result source shows which path produced the result, which helps debugging and operations.

## Alternatives Considered

### Alternative A: No Fallback

- **Advantages:** simple implementation; result consistency is ensured
- **Disadvantages:** availability decreases; the user experience deteriorates
- **Reason for Rejection:** Rejected to prioritize Availability and keep the search function working even when the external service fails.
- **Reconsideration Conditions:** result consistency becomes mandatory; fallback causes confusion

### Alternative B: Fallback Only on Specific Errors

- **Advantages:** prevents unintended fallback; improves result consistency
- **Disadvantages:** cannot handle other errors such as network failures; requires complex rules
- **Reason for Rejection:** Rejected to prioritize Availability and handle every technical failure.
- **Reconsideration Conditions:** it becomes necessary to make only specific errors fallback conditions; result consistency becomes important

### Alternative C: Separate Corpus for Local

- **Advantages:** result consistency is ensured; corpus independence improves
- **Disadvantages:** corpus synchronization becomes complex; data redundancy increases
- **Reason for Rejection:** Rejected to prioritize Availability and avoid the cost of corpus synchronization.
- **Reconsideration Conditions:** result consistency becomes mandatory; the cost of corpus synchronization becomes acceptable

## Consequences

### Positive Consequences

- The search function continues even when the external RAG service fails
- Empty results can be distinguished from technical failures
- The result source can be tracked
- Debugging and operations become easier

### Negative Consequences

- Performance may degrade during fallback
- Search-result equivalence between the two modes is not guaranteed
- Both modes are expected to use the same `rag_db_path` by convention; a divergence is not prevented and is detected only at fallback time, by the corpus identity comparison
- Error classification is complex

### Operational Consequences

- A fallback is visible through `ResultSource`, `HttpResultKind`, and the fallback reason in the pipeline diagnostics and logs
- A recurring fallback points to a failing or misconfigured external RAG service, to be repaired outside this process

### Security Consequences

- Trust boundary: the external RAG service is authenticated by a token; an authentication failure is a configuration error and is not masked by the local fallback
- Secret handling: follow the principle of minimal exposure

## Invariants

- INV-01: The execution mode is switched by whether `rag_query_service_url` is set.
- INV-02: Each HTTP call attempt is bounded by a configured timeout.
- INV-03: An empty result is treated as a valid result and does not trigger fallback.
- INV-04: Only technical failures (timeouts, connection errors, HTTP 5xx after retries, HTTP 4xx other than 401/403, and an HTTP 200 response carrying `is_error=true`) are fallback conditions; authentication errors 401/403 do not fall back.
- INV-05: On fallback, the whole pipeline MQE → KNN/BM25 → RRF → Rerank → Augment is re-executed.
- INV-06: The result source (Remote/Local/Fallback) is tracked and recorded in metrics and logs.
- INV-07: Parse errors (an unparsable body or a non-string `result`) are logged and treated as empty results.
- INV-08: Local DB access uses only `rag.sqlite`.
- INV-09: Search-result equivalence between the external RAG and the local RAG is not guaranteed. Database sharing is a deployment convention that is not enforced, and a corpus divergence is detected only by the identity comparison at fallback (Decision Details item 11), which is a detection and not a synchronization.
- INV-10: The result vocabulary is `remote_nonempty`, `remote_empty`, `in_process_fallback`, `auth_error`, `ResultSource`, and `HttpResultKind` (including `AUTH_ERROR`).

## Failure Policy

### Fail-Fast Conditions

- When the `rag.sqlite` connection cannot be opened in the in-process mode, `RagPipeline.augment()` raises `RagPipelineError` and no further fallback exists (Explicit in code — `scripts/rag/pipeline.py`)

### Fail-Open or Degraded Conditions

- None: ADR-004 defines a single common failure-handling policy, and no environment-specific downgrade to warnings exists

### Retry Policy

- Retry target: HTTP 5xx and transport errors (timeouts, connection errors) of the external RAG call
- Retry count: bounded; the fallback starts after the last attempt fails
- Backoff: increasing delay between attempts
- Errors not retried: HTTP 4xx and response parse errors (recorded when the remote call path existed)

### Fallback Policy

- Fallback targets: a technical failure of the external RAG HTTP call (see Decision Details item 6 and the item 13 decision table)
- Fallback destination: the in-process local RAG (the whole pipeline is re-executed)
- Conditions that prohibit Fallback: an empty result (`""`) from the external RAG, a response parse error (an unparsable body or a non-string `result`, treated as an empty result), authentication errors 401/403, and any safety or integrity failure (ADR-004: a safety/integrity failure must not trigger an availability Fallback)
- Where Fallback reasons are recorded: the fallback reason in the stage result and search diagnostics (`ResultSource.FALLBACK`, `HttpResultKind`) and the application log

## Data Ownership and Persistence

- **System of Record**: `rag.sqlite` (expected to be shared by both the local and remote RAG modes by convention; the sharing is not enforced)
- **Derived Data**: the FTS5 and Vector indexes of `rag.sqlite` (defined by ADR-005)
- **Ownership**: RAG layer (owner of the canonical data)
- **Persistence**: file system (the configured DB directory); the fallback itself persists nothing
- **Transaction Boundary**: not applicable (the fallback only reads `rag.sqlite`)
- **Recovery Source**: not applicable (see ADR-005 and ADR-008 for `rag.sqlite`)
- **Deletion Rule**: not applicable

## Verification

### Automated Tests

Withdrawn: the integration and unit tests that verified this decision exercised the remote delegation path and its fallback; they were deleted together with that code path, so no automated test remains for this ADR.

### Startup Validation

- None: the decision is withdrawn and no fallback state exists

### Deployment Validation

- Confirm that no deployed configuration file carries the removed keys `rag_query_service_url`, `rag_auth_token`, or `rag_identity_mismatch_policy` (configuration loading rejects them)

### Runtime Monitoring

- None: the withdrawn decision's diagnostics (result source, HTTP result kind, remote status and latency) no longer exist

### Manual Review

- INV-02, INV-08, INV-09, INV-10 have no dedicated automated test; INV-05 is verified for stage order only

## Implementation Notes

- Withdrawn: the remote delegation code (the HTTP augment stage, the remote call function, and the result source and HTTP result kind diagnostics) and the fallback identity gate were removed. `RagPipeline.augment()` now runs the in-process pipeline only, and the rag_pipeline MCP server is the only access path to RAG.

See Implementation References for the current file/symbol list.

## Known Deviations

Not applicable

## Review Triggers

Re-evaluate this ADR when any of the following conditions occurs.

- The operational scale or concurrency changes significantly
- The deployment changes from a single host to multiple hosts or a distributed configuration
- Security or audit requirements change
- Performance targets or resource constraints change
- An external protocol or adopted library is changed or discontinued
- Failure history shows that the assumptions or the Failure Policy are no longer valid
- The reasons for rejecting an alternative no longer hold
- The external RAG service and the in-process RAG must return consistent results
- The `rag_identity_mismatch_policy` is changed below `reject`, or the remote/local identity-comparison gate (`rag_05_07-rag-index-consistency-checks.md`) is extended to a fallback path other than the HTTP delegation path
- The set of failures that trigger the fallback (including the 401/403 handling) changes
- Fallback to a destination other than the in-process RAG is proposed

## Approval

### Required Reviewers

- Architecture Owner
- Affected Component Owner
- Security Reviewer: when there is a security impact
- Operations Reviewer: when operations, monitoring, or recovery are affected
- Data Owner: when data ownership, schema, or retention are affected

### Approval Record

- **Approved By**: Task-level approval decision (repository owner; individual reviewer names are not recorded)
- **Approval Date**: Not recorded (individual approval dates are not recorded for a task-level approval decision)
- **Approval Reference**: `docs/00_governance/governance_01_documentation-policy.md` ADR Acceptance Evidence Standard

### Withdrawal Approval Record

- **Withdrawn By**: Pending maintainer statement (the maintainer's approval of the withdrawal has not been given; it is not written by the implementer)
- **Withdrawal Date**: Pending maintainer statement
- **Withdrawal Reference**: ADR-004 Decision Group 10 (Fallback prohibited without exception)

The `Withdrawn` status takes effect for this repository's documents with this change, and the record above is completed when the maintainer states the decision.

This ADR's former `Accepted` status used the task-level approval decision defined by the governance document above as its acceptance evidence. No formal Approval Record with individual reviewer names and approval dates has been created.

## Related ADRs

- ADR-002: Per-Process Configuration Ownership and Config Isolation
- ADR-005: Relationship Between RAG Canonical Data and Derived Indexes
- ADR-004: Failure Handling Policy Across Environments

## Implementation References

- `scripts/rag/pipeline.py` — `RagPipeline.augment()` (in-process pipeline only after the withdrawal)
- `scripts/rag/stages/augment.py` — `AugmentStage.run()`, `_format_chunks()`

## Completion Checklist

Acceptance conditions and their current state.

- [x] The problem to solve is clear
- [x] The Decision is narrowed to one primary design decision
- [x] The Decision is stated in clear terms such as mandatory, prohibited, canonical, or Fallback conditions
- [x] The reasons for adoption are explained from perspectives other than the current implementation
- [x] Substantive alternatives and the reasons for rejecting them are recorded
- [x] Positive Consequences are recorded
- [x] Negative Consequences are recorded
- [x] The impact on Security has been evaluated
- [x] The impact on Operations, Monitoring, and Recovery has been evaluated
- [x] Verifiable Invariants are defined
- [x] Exceptions or out-of-scope cases are clear
- [x] Each Invariant has a corresponding Verification (gaps: Verification > Manual Review)
- [x] Automatable verification does not rely only on Manual Review
- [x] The relationship with existing ADRs is recorded
- [x] The ADR does not contradict related Specifications
- [x] Discrepancies with the current implementation are registered as Known Issues (no confirmed deviations)
- [x] The Owner and required Reviewers are defined
- [x] Review Triggers are recorded
- [x] The ADR is registered in the ADR index and the Document Guides of related areas
