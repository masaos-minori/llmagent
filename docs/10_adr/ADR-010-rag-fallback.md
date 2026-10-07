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

rag
fallback
http service
in-process

## Status

Accepted

## Summary

This ADR canonicalizes the decision to fall back automatically to the in-process local RAG when execution of the RAG pipeline's external service fails. The execution mode is switched by whether `rag_service_url` is set, HTTP errors are distinguished from empty results, and idempotent re-execution is made possible.

## Context

### Problem

The RAG pipeline depends heavily on the external RAG service, so a network failure or a service outage stops the whole search function. In addition, because the distinction between an empty result and a technical failure is unclear, appropriate recovery is difficult.

### Constraints

- Execution on a single host with multiple processes is assumed
- In the deployment environment, the existence of each DB file must be confirmed before startup
- Because the sqlite-vec extension is used, some standard FK constraints are restricted
- Different tokenizer approaches are used for Japanese and for English/code

### Assumptions

- Target environment: a single host, multiple processes
- Expected scale: limited concurrency
- Trust boundary: privileges are granted only within each DB
- External dependencies: none (SQLite is a local file)
- Items to re-evaluate if the assumptions no longer hold: multi-host configuration, distributed execution, integration with an external event store

## Decision

### Decision Details

1. When `rag_service_url` is set, an HTTP POST is sent to the external RAG service.
2. When `rag_service_url` is not set, the in-process local RAG is executed.
3. The HTTP call is made by `call_rag_service()`, and each attempt is bounded by a configured timeout.
4. HTTP errors (401, 403, 4xx, 5xx) are distinguished from empty results (`""`).
5. An empty result is treated as a valid result and does not trigger fallback.
6. Only technical failures (timeouts, connection errors, HTTP errors other than authentication errors 401/403, which do not fall back) are fallback conditions.
7. On fallback, the whole pipeline MQE → KNN/BM25 → RRF → Rerank → Augment is re-executed.
8. The result source (Remote/Local/Fallback) is tracked and recorded in metrics and logs.
9. Parse errors are logged and treated as empty results.
10. Local DB access uses only `rag.sqlite`.
11. The corpus difference between the external RAG and the local RAG is documented, stating that result consistency is not guaranteed.
12. The terms `remote_nonempty`, `remote_empty`, `in_process_fallback`, `ResultSource`, and `HttpResultKind` are defined.

### Scope

- **Target components**: `RagPipeline`, `call_rag_service()`, `AugmentStage`
- **Target processes**: the Agent process and the ingester process
- **Target data**: `rag.sqlite`, `session.sqlite`
- **Target Environment Profile**: production (the only supported execution mode; ADR-004 applies one failure-handling policy to every environment)
- **Target APIs or processing paths**: `RagPipeline.augment()`, `call_rag_service()`, `AugmentStage.run()`

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

Do not use "the current code is implemented this way" as the sole reason for adoption.

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
- Corpus synchronization costs arise
- Complex error classification is required

### Operational Consequences

- The fallback state is checked at startup
- Manual commands are required when a failure occurs
- Metrics and logs must be checked

If not applicable, write "Not applicable".

### Security Consequences

- Trust boundary: privileges are granted only within each DB
- Secret handling: follow the principle of minimal exposure

If not applicable, write "Not applicable".

## Invariants

- INV-01: The execution mode is switched by whether `rag_service_url` is set.
- INV-02: Each HTTP call attempt is bounded by a configured timeout.
- INV-03: An empty result is treated as a valid result and does not trigger fallback.
- INV-04: Only technical failures (timeouts, connection errors, HTTP errors other than authentication errors 401/403, which do not fall back) are fallback conditions.
- INV-05: On fallback, the whole pipeline MQE → KNN/BM25 → RRF → Rerank → Augment is re-executed.
- INV-06: The result source (Remote/Local/Fallback) is tracked and recorded in metrics and logs.
- INV-07: Parse errors are logged and treated as empty results.
- INV-08: Local DB access uses only `rag.sqlite`.
- INV-09: The corpus difference between the external RAG and the local RAG is documented, stating that result consistency is not guaranteed.
- INV-10: The terms `remote_nonempty`, `remote_empty`, `in_process_fallback`, `ResultSource`, and `HttpResultKind` are defined.

## Exceptions

None

## Failure Policy

### Fail-Fast Conditions

- When the `rag.sqlite` connection fails (RAG functionality stops)
- When the `session.sqlite` connection fails (session functionality stops)
- When local RAG pipeline execution fails

### Fail-Open or Degraded Conditions

- None: ADR-004 defines a single common failure-handling policy, and no environment-specific downgrade to warnings exists

### Retry Policy

Not applicable (this ADR defines no retry policy of its own)

If not applicable, write "Not applicable".

### Fallback Policy

- Fallback target: technical failures
- Fallback destination: the in-process local RAG
- Conditions that prohibit Fallback: consistency-check mismatches
- Where Fallback reasons are recorded: audit log

If not applicable, write "Not applicable".

## Data Ownership and Persistence

- **System of Record**: `rag.sqlite` (shared by both the local and remote RAG modes)
- **Derived Data**: regenerable derived data (FTS5, Vector Index)
- **Ownership**: RAG team (owner of the canonical data)
- **Persistence**: file system (the configured DB directory)
- **Transaction Boundary**: per DB
- **Recovery Source**: manual recovery of each DB
- **Deletion Rule**: each DB is deleted independently

If not applicable, write "Not applicable".

## Verification

### Automated Tests

- **Test**: Falls back to the in-process local RAG when the external RAG service fails
  - **Verifies**: INV-04
  - **Type**: Integration
  - **Blocking**: Yes

- **Test**: An empty result is treated as a valid result
  - **Verifies**: INV-03
  - **Type**: Regression
  - **Blocking**: Yes

- **Test**: The result source is tracked correctly
  - **Verifies**: INV-06
  - **Type**: Integration
  - **Blocking**: Yes

- **Test**: The pipeline is re-executed idempotently on fallback
  - **Verifies**: INV-05
  - **Type**: Integration
  - **Blocking**: Yes

### Startup Validation

- The fallback state is checked at startup
- Whether configuration files are valid (parseable TOML, required fields)

### Deployment Validation

- Check the fallback state before and after deployment
- The post-deployment consistency check passes

### Runtime Monitoring

- Health Check: fallback state
- Metrics: fallback count, distribution of result sources
- Logs: fallback events, error events
- Alert conditions: `fallback_count > threshold`
- Degraded condition: failure of a dependency

### Manual Review

- Fallback state verification before deployment

Register any Invariant without Verification as an unverified item in an Issue.

## Implementation Notes

Briefly describe how the current implementation realizes the Decision.

See Implementation References for the current file/symbol list.

This chapter is not a basis for design decisions. List detailed APIs, Classes, and Functions in the Implementation References.

Do not record line numbers; reference by File Path and Symbol name.

## Known Deviations

Record any discrepancy between this ADR and the current implementation, configuration, tests, or documents.



Do not unconditionally align the ADR text with the current implementation; manage discrepancies as Known Issues.

## Review Triggers

Re-evaluate this ADR when any of the following conditions occurs.

- The operational scale or concurrency changes significantly
- The deployment changes from a single host to multiple hosts or a distributed configuration
- Security or audit requirements change
- Performance targets or resource constraints change
- An external protocol or adopted library is changed or discontinued
- Failure history shows that the assumptions or the Failure Policy are no longer valid
- The reasons for rejecting an alternative no longer hold

Add review conditions specific to this ADR.

- sqlite-vec supports FK constraints
- FTS5 supports standard DELETE
- A new shared configuration file becomes necessary
- Persistent storage moves to something other than files

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

- `scripts/rag/pipeline.py` — `RagPipeline.augment()`, `_format_chunks()` in `scripts/rag/stages/augment.py`
- `scripts/rag/pipeline_service.py` — `call_rag_service()`
- `scripts/shared/config_loader.py` — `ConfigLoader.restrict_to()`, `ConfigLoader.load()`
- `scripts/rag/stages/augment.py` — `AugmentStage.run()`
- `rag.sqlite` — `documents`, `chunks`, `chunks_fts`, `chunks_vec`
- Triggers — `chunks_ai`, `chunks_au`, `chunks_ad`
- Tests — `tests/rag/test_rag_pipeline.py`, `tests/rag/test_rag_pipeline_stage.py`

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
- [x] Each Invariant has a corresponding Verification
- [x] Automatable verification does not rely only on Manual Review
- [x] Migration, or the reason no migration is needed, is recorded
- [x] The relationship with existing ADRs is recorded
- [x] The ADR does not contradict related Specifications
- [ ] Discrepancies with the current implementation are registered as Known Issues
- [x] The Owner and required Reviewers are defined
- [x] Review Triggers are recorded
- [ ] The ADR is registered in the ADR index and the Document Guides of related areas
