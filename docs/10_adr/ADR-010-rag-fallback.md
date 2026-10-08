---
title: "ADR-010: In-Process Fallback When External RAG Execution Fails"
area: governance
tags:
  - rag
  - fallback
  - in-process
related:
  - ADR-002-config-isolation.md
  - rag_03_01_query_pipeline-overview.md
  - rag_03_05_query_pipeline-augment-stages.md
  - rag_05_04-error-handling-reference.md
  - rag_05_01-configuration-reference.md
  - db_02_architecture_and_schema-schema-reference.md
  - ADR-005-rag-source-derived-index-relationships.md
  - ADR-004-environment-failure-handling-policy.md
---

# ADR-010: In-Process Fallback When External RAG Execution Fails

## Keywords

- rag
- fallback
- http service
- in-process

## Status

Accepted

## Summary

This ADR canonicalizes the decision to fall back automatically to the in-process local RAG when execution of the RAG pipeline's external service fails. The execution mode is switched by whether `rag_service_url` is set, HTTP errors are distinguished from empty results, and idempotent re-execution is made possible.

## Context

### Problem

The RAG pipeline depends heavily on the external RAG service, so a network failure or a service outage stops the whole search function. In addition, because the distinction between an empty result and a technical failure is unclear, appropriate recovery is difficult.

### Constraints

- Execution on a single host with multiple processes is assumed
- The RAG pipeline has two execution modes, selected only by whether `rag_service_url` is configured
- The external RAG service is reached through `POST /v1/call_tool` with the `rag_run_pipeline` tool, and the call carries an authentication token when one is configured
- The in-process mode needs the local `rag.sqlite` and the sqlite-vec extension in the calling process
- The RAG pipeline served by the external RAG service must not itself delegate over HTTP (its own `rag_service_url` is empty)

## Assumptions

- Target environment: a single host, multiple processes
- Expected scale: limited concurrency
- Trust boundary: the external RAG service authenticates callers with a token; the local mode needs no network access
- External dependencies: the external RAG service is reachable over HTTP; it is the dependency whose failure triggers the fallback
- The external and the in-process mode read their corpus from separately configured database paths (`rag_db_path`), which are identical by configuration convention only
- Items to re-evaluate if the assumptions no longer hold: multi-host configuration, distributed execution, the external RAG service using a corpus other than the local one

## Decision

### Decision Details

1. When `rag_service_url` is set, an HTTP POST is sent to the external RAG service.
2. When `rag_service_url` is not set, the in-process local RAG is executed.
3. The HTTP call is made by `call_rag_service()`, and each attempt is bounded by a configured timeout.
4. HTTP errors (401, 403, 4xx, 5xx) are distinguished from empty results (`""`).
5. An empty result is treated as a valid result and does not trigger fallback.
6. Only technical failures are fallback conditions: timeouts and connection errors and HTTP 5xx after the bounded retries are exhausted, and HTTP 4xx other than 401/403. Authentication errors (401/403) do not fall back.
7. On fallback, the whole pipeline MQE → KNN/BM25 → RRF → Rerank → Augment is re-executed.
8. The result source (Remote/Local/Fallback) is tracked and recorded in metrics and logs.
9. Parse errors are logged and treated as empty results.
10. Local DB access uses only `rag.sqlite`.
11. Result consistency between the external RAG and the local RAG is not guaranteed, because each mode reads the corpus from its own configured database path.
12. The result vocabulary is `remote_nonempty`, `remote_empty`, `in_process_fallback`, `auth_error` (internal to `HttpAugment`), and the public enums `ResultSource` and `HttpResultKind` (`SUCCESS`, `EMPTY`, `ERROR`, `NOT_USED`, `AUTH_ERROR`).

### Scope

- **Target components**: `RagPipeline`, `AugmentRefiner`, `HttpAugment`, `call_rag_service()`, `AugmentStage`
- **Target processes**: any process that constructs `RagPipeline` with a non-empty `rag_service_url`. The rag-pipeline MCP server always constructs it with an empty `rag_service_url`, so it never delegates; no other production caller of the HTTP mode exists (Confirmed by repository evidence — `RagPipeline` is constructed only in the rag-pipeline MCP service). The Agent REPL does not call `RagPipeline` directly, and the ingester does not use `augment()`.
- **Target data**: `rag.sqlite`
- **Target Environment Profile**: production (the only supported execution mode; ADR-004 applies one failure-handling policy to every environment)
- **Target APIs or processing paths**: `RagPipeline.augment()`, `HttpAugment.run()`, `call_rag_service()`, `AugmentStage.run()`

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

Distinguishing empty results from technical failures prevents unnecessary fallback. The meanings differ: an empty result means "searched but nothing matched", while a technical failure means "could not search".

### 3. Third Reason for Adoption — Observability

Tracking the result source makes it possible to know which path produced the result, which helps debugging and operations.

## Alternatives Considered

### Alternative A: No Fallback

#### Description

Return an error when the external RAG service fails.

#### Advantages

- Simple implementation
- Result consistency is ensured

#### Disadvantages

- Availability decreases
- The user experience deteriorates

#### Reason for Rejection

Rejected to prioritize Availability and keep the search function working even when the external service fails.

#### Reconsideration Conditions

- Result consistency becomes mandatory
- Fallback causes confusion

### Alternative B: Fallback Only on Specific Errors

#### Description

Make only specific HTTP status codes (for example, 5xx) fallback conditions.

#### Advantages

- Prevents unintended fallback
- Improves result consistency

#### Disadvantages

- Cannot handle other errors such as network failures
- Requires complex rules

#### Reason for Rejection

Rejected to prioritize Availability and handle every technical failure.

#### Reconsideration Conditions

- It becomes necessary to make only specific errors fallback conditions
- Result consistency becomes important

### Alternative C: Separate Corpus for Local

#### Description

Use different corpora for the local RAG and the external RAG.

#### Advantages

- Result consistency is ensured
- Corpus independence improves

#### Disadvantages

- Corpus synchronization becomes complex
- Data redundancy increases

#### Reason for Rejection

Rejected to prioritize Availability and avoid the cost of corpus synchronization.

#### Reconsideration Conditions

- Result consistency becomes mandatory
- The cost of corpus synchronization becomes acceptable

## Consequences

### Positive Consequences

- The search function continues even when the external RAG service fails
- Empty results can be distinguished from technical failures
- The result source can be tracked
- Debugging and operations become easier

### Negative Consequences

- Performance may degrade during fallback
- Result consistency is not guaranteed
- Both modes must be configured with the same `rag_db_path`; a divergent configuration is not detected
- Complex error classification is required

### Operational Consequences

- A fallback is visible through `ResultSource`, `HttpResultKind`, and the fallback reason in the pipeline diagnostics and logs
- A recurring fallback points to a failing or misconfigured external RAG service, which must be repaired outside this process

### Security Consequences

- Trust boundary: the external RAG service is authenticated by a token; an authentication failure is a configuration error and is not masked by the local fallback
- Secret handling: follow the principle of minimal exposure

## Invariants

- INV-01: The execution mode is switched by whether `rag_service_url` is set.
- INV-02: Each HTTP call attempt is bounded by a configured timeout.
- INV-03: An empty result is treated as a valid result and does not trigger fallback.
- INV-04: Only technical failures (timeouts, connection errors, HTTP 5xx after retries, HTTP 4xx other than 401/403) are fallback conditions; authentication errors 401/403 do not fall back.
- INV-05: On fallback, the whole pipeline MQE → KNN/BM25 → RRF → Rerank → Augment is re-executed.
- INV-06: The result source (Remote/Local/Fallback) is tracked and recorded in metrics and logs.
- INV-07: Parse errors are logged and treated as empty results.
- INV-08: Local DB access uses only `rag.sqlite`.
- INV-09: Result consistency between the external RAG and the local RAG is not guaranteed, because each mode reads the corpus from its own configured database path.
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
- Errors not retried: HTTP 4xx and response parse errors (Explicit in code — `scripts/rag/pipeline_service.py` `call_rag_service()`)

### Fallback Policy

- Fallback targets: a technical failure of the external RAG HTTP call (see Decision item 6)
- Fallback destination: the in-process local RAG (the whole pipeline is re-executed)
- Conditions that prohibit Fallback: an empty result (`""`) from the external RAG, a response parse error (treated as an empty result), authentication errors 401/403, and any safety or integrity failure (ADR-004: a safety/integrity failure must not trigger an availability Fallback)
- Where Fallback reasons are recorded: the fallback reason in the stage result and search diagnostics (`ResultSource.FALLBACK`, `HttpResultKind`) and the application log

## Data Ownership and Persistence

- **System of Record**: `rag.sqlite` (shared by both the local and remote RAG modes)
- **Derived Data**: the FTS5 and Vector indexes of `rag.sqlite` (defined by ADR-005)
- **Ownership**: RAG team (owner of the canonical data)
- **Persistence**: file system (the configured DB directory); the fallback itself persists nothing
- **Transaction Boundary**: not applicable (the fallback only reads `rag.sqlite`)
- **Recovery Source**: not applicable (see ADR-005 and ADR-008 for `rag.sqlite`)
- **Deletion Rule**: not applicable

## Verification

### Automated Tests

- **Test**: Falls back to the in-process local RAG when the external RAG service fails
  - **Verifies**: INV-04
  - **Type**: Integration
  - **Blocking**: Yes
  - **Implementation**: `tests/rag/test_rag_http_mode.py::test_in_process_fallback_sets_result_source_fallback`, `tests/rag/test_rag_pipeline_service.py::TestResponseParsing::test_5xx_retries_and_returns_none`, `tests/rag/test_rag_pipeline_service.py::TestAuthErrorHandling::test_400_still_triggers_fallback`

- **Test**: An empty result is treated as a valid result
  - **Verifies**: INV-03
  - **Type**: Regression
  - **Blocking**: Yes
  - **Implementation**: `tests/rag/test_rag_http_mode.py::test_remote_empty_does_not_trigger_in_process`

- **Test**: The result source is tracked correctly
  - **Verifies**: INV-06
  - **Type**: Integration
  - **Blocking**: Yes
  - **Implementation**: `tests/rag/test_rag_http_mode.py::test_remote_empty_sets_result_source_remote`, `tests/rag/test_rag_http_mode.py::test_in_process_fallback_sets_result_source_fallback`, `tests/rag/test_pipeline_http_result_kind.py`

- **Test**: The pipeline is re-executed idempotently on fallback
  - **Verifies**: INV-05
  - **Type**: Integration
  - **Blocking**: Yes
  - **Implementation**: `tests/rag/test_rag_http_mode.py::test_in_process_fallback_sets_result_source_fallback` (the in-process `run` is stubbed; no test asserts the full stage sequence)

- **Test**: The mode is selected by whether `rag_service_url` is set
  - **Verifies**: INV-01
  - **Type**: Integration
  - **Blocking**: Yes
  - **Implementation**: `tests/rag/test_pipeline_http_result_kind.py::test_no_http_mode`

- **Test**: A response parse error is treated as an empty result
  - **Verifies**: INV-07
  - **Type**: Unit
  - **Blocking**: Yes
  - **Implementation**: `tests/rag/test_rag_pipeline_service.py::TestFallbackReasonCallback::test_json_parse_error_does_not_call_set_fallback_reason`

- **Test**: The external call is tagged `auth_error` for 401/403 and records an authentication reason; `augment()` raises `RagPipelineError` and never enters the in-process pipeline
  - **Verifies**: INV-04
  - **Type**: Unit
  - **Blocking**: Yes
  - **Implementation**: `tests/rag/test_rag_pipeline_service.py::TestAuthErrorHandling::test_401_no_fallback`, `tests/rag/test_rag_pipeline_service.py::TestAuthErrorHandling::test_403_no_fallback`, `tests/rag/test_pipeline_http_result_kind.py::test_auth_error_fails_closed_without_in_process_fallback`

### Startup Validation

- No startup check of the external RAG service or of the fallback state exists; the mode is decided per request from `rag_service_url`

### Deployment Validation

- Confirm that `rag_service_url` and the RAG token are set as intended for the deployed process

### Runtime Monitoring

- Diagnostics: `ResultSource`, `HttpResultKind`, the remote status code and latency, and the fallback reason in the search diagnostics
- Logs: fallback events, authentication-error events, retry events
- Degraded condition: the external RAG service fails and the in-process mode serves the request

### Manual Review

- Verification of the RAG service URL and token configuration before deployment
- INV-02, INV-05 (full re-execution), INV-08, INV-09, INV-10 have no dedicated automated test

## Implementation Notes

- `RagPipeline.augment()` delegates to `HttpAugment` when `rag_service_url` is set; a non-`None` result (including `""`) is returned as final, and `None` makes `augment()` run the in-process pipeline.
- `call_rag_service()` posts to the RAG service, retries 5xx and transport errors a bounded number of times, returns `""` for an empty or unparsable response, and returns `None` for exhausted retries and for 4xx.
- `HttpAugment.run()` classifies the outcome (`remote_nonempty`, `remote_empty`, `in_process_fallback`) and `run_http_augment()` records `ResultSource` and `HttpResultKind` in the search diagnostics.
- The rag_pipeline MCP server builds its pipeline configuration with an empty `rag_service_url`, so a call served by the external service never delegates again.

See Implementation References for the current file/symbol list.

This chapter is not a basis for design decisions.

## Known Deviations

No confirmed deviations.

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

- **Approved By**: Task-level approval decision (repository administrator; individual reviewer names are not recorded)
- **Approval Date**: Not recorded (individual approval dates are not recorded for a task-level approval decision)
- **Approval Reference**: `docs/00_governance/governance_01_documentation-policy.md` ADR Acceptance Evidence Standard

This ADR's `Accepted` status uses the task-level approval decision defined by the governance document above as its acceptance evidence. No formal Approval Record with individual reviewer names and approval dates has been created.

## Related ADRs

- ADR-002: Per-Process Configuration Ownership and Config Isolation
- ADR-005: Relationship Between RAG Canonical Data and Derived Indexes
- ADR-004: Failure Handling Policy Across Environments

## Implementation References

- `scripts/rag/pipeline.py` — `RagPipeline.augment()`
- `scripts/rag/augment.py` — `AugmentRefiner.run_http_augment()`
- `scripts/rag/http_augment.py` — `HttpAugment.run()`
- `scripts/rag/pipeline_service.py` — `call_rag_service()`
- `scripts/rag/models_result.py` — `ResultSource`, `HttpResultKind`
- `scripts/rag/stages/augment.py` — `AugmentStage.run()`, `_format_chunks()`
- `scripts/mcp_servers/rag_pipeline/rag_pipeline_models.py` — pipeline configuration with an empty `rag_service_url`
- Tests — `tests/rag/test_rag_http_mode.py`, `tests/rag/test_rag_pipeline_service.py`, `tests/rag/test_pipeline_http_result_kind.py`

## Completion Checklist

Confirm the following before changing the ADR to Accepted.

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
- [ ] Each Invariant has a corresponding Verification (INV-02, INV-08, INV-09, INV-10 have no automated test; INV-05 is only partly verified)
- [x] Automatable verification does not rely only on Manual Review
- [x] The relationship with existing ADRs is recorded
- [x] The ADR does not contradict related Specifications
- [x] Discrepancies with the current implementation are registered as Known Issues (no confirmed deviations)
- [x] The Owner and required Reviewers are defined
- [x] Review Triggers are recorded
- [x] The ADR is registered in the ADR index and the Document Guides of related areas
