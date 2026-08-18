---
title: "Terminology Glossary"
category: governance
tags:
  - governance
  - terminology
related:
  - 00_index.md
  - 00_governance_01_documentation-governance.md
---

# Terminology Glossary

This glossary defines preferred terms, alternative forms, and abbreviations used across all design documentation. It eliminates ambiguity and enables cross-area communication.

## Terms

| Term | Preferred Form | Alternative Forms | Notes |
|------|---------------|-------------------|-------|
| EventBus | EventBus | event bus, event-bus | CamelCase as proper noun; use "Event Bus" (with space) in Japanese text |
| Needs Confirmation | Needs Confirmation | Needs confirmation, 要確認, Need Confirmation, 未決事項 | Abbreviation: NC; always capitalize both words in English |
| Known Issue | Known Issue | Known Issues, 既知の問題, 既知の不整合, 既知の不具合と不整合 | Plural form is acceptable when referring to multiple items |
| Deprecated Item | Deprecated Item | deprecated item, 非推奨項目 | Capitalize when referring to the governance document title |
| Canonical Source Rule | Canonical Source Rule | canonical source rule | Always capitalize as proper noun |
| Evidence Label | Evidence Label | evidence label | Capitalize when referring to the governance document title |
| Schema Registry | Schema Registry | schema registry | Proper noun; used sparingly in this project |
| At-Least-Once Delivery | At-Least-Once Delivery | at-least-once delivery, at least once delivery | Abbreviation: ALOD; hyphenate when used as adjective |
| Message Queue | MQ | message queue, msg-queue | Abbreviation: MQ; not currently used in this project |
| Document Guide | Document Guide | document guide | Capitalize when referring to area-specific document-guide files |
| Governance | Governance | governance | Capitalize when referring to the governance category |
| Shared/DB | Shared/DB | shared/db, shared-db | Use slash notation in filenames; "shared database" in prose |
| Inconsistency | Inconsistency | inconsistency | Capitalize when part of document title (e.g., "Inconsistencies and Known Issues") |
| Deferred Item | Deferred Item | deferred item | Capitalize when referring to the governance concept |
| AI Reading Metadata | AI Reading Metadata | ai reading metadata | Capitalize as proper noun |
| Tool Registry | Tool Registry | tool registry | Capitalize when referring to `ToolRegistry` class or its governance role |
| Runtime Tool Registry | Runtime Tool Registry | runtime tool registry | Capitalize when referring to `RuntimeToolRegistry` class |
| Workflow Engine | Workflow Engine | workflow engine | Capitalize when referring to `WorkflowEngine` class |
| Query Pipeline | Query Pipeline | query pipeline | Capitalize when referring to RAG query pipeline component |
| Ingestion Pipeline | Ingestion Pipeline | ingestion pipeline | Capitalize when referring to RAG ingestion pipeline component |
| Memory Module | Memory Module | memory module | Capitalize when referring to agent memory subsystem |
| Operation Observability | Operation Observability | operation observability | Capitalize when referring to the operations domain |
| DLQ | DLQ | dead letter queue | Abbreviation: DLQ; always uppercase |
| Offset | Offset | offset | Capitalize when referring to EventBus offset concept |
| Nak | NAK | nak, negative acknowledgment | Abbreviation: NAK; uppercase in technical context |
| Ack | ACK | ack, acknowledgment | Abbreviation: ACK; uppercase in technical context |
| DTO | DTO | data transfer object | Abbreviation: DTO; always uppercase |
| DDL | DDL | data definition language | Abbreviation: DDL; always uppercase |
| SSE | SSE | server-sent events | Abbreviation: SSE; always uppercase |
| CLI | CLI | command-line interface | Abbreviation: CLI; always uppercase |
| REPL | REPL | read-eval-print loop | Abbreviation: REPL; always uppercase |
| MCP | MCP | Model Context Protocol | Abbreviation: MCP; always uppercase |
| RAG | RAG | Retrieval-Augmented Generation | Abbreviation: RAG; always uppercase |
| LLM | LLM | Large Language Model | Abbreviation: LLM; always uppercase |
| OTel | OTel | OpenTelemetry | Abbreviation: OTel; camelCase |
| ETag | ETag | etag, entity tag | Abbreviation: ETag; camelCase |
| UUID | UUID | universally unique identifier | Abbreviation: UUID; always uppercase |
| JSON | JSON | JavaScript Object Notation | Abbreviation: JSON; always uppercase |
| YAML | YAML | Yet Another Markup Language | Abbreviation: YAML; always uppercase |
| TOML | TOML | Tom's Obvious Minimal Language | Abbreviation: TOML; always uppercase |
| HTTP | HTTP | Hypertext Transfer Protocol | Abbreviation: HTTP; always uppercase |
| TCP | TCP | Transmission Control Protocol | Abbreviation: TCP; always uppercase |
| TLS | TLS | Transport Layer Security | Abbreviation: TLS; always uppercase |
| WAL | WAL | Write-Ahead Logging | Abbreviation: WAL; always uppercase |
| LRU | LRU | Least Recently Used | Abbreviation: LRU; always uppercase |
| TTL | TTL | Time-To-Live | Abbreviation: TTL; always uppercase |
| CPU | CPU | Central Processing Unit | Abbreviation: CPU; always uppercase |
| RAM | RAM | Random Access Memory | Abbreviation: RAM; always uppercase |
| PID | PID | Process ID | Abbreviation: PID; always uppercase |
| EOF | EOF | End Of File | Abbreviation: EOF; always uppercase |
| UTF-8 | UTF-8 | utf-8 | Hyphenated; case-insensitive in practice but prefer uppercase |
| SQLite | SQLite | sqlite | Proper noun; camelCase |
| Vec | Vec | vector | Short for vector; capitalized when referring to sqlite-vec extension |
| vec0 | vec0 | Vec0 | Refers to sqlite-vec extension; lowercase in code, uppercase in prose |
| Chunk Splitter | Chunk Splitter | chunk splitter | Capitalize when referring to `chunk_splitter.py` module |
| Ingester | Ingester | ingester | Capitalize when referring to `ingester.py` module |
| Crawler | Crawler | crawler | Capitalize when referring to `crawler.py` module |
| Health Check | Health Check | health check | Capitalize when referring to the operational concept |
| Audit Log | Audit Log | audit log | Capitalize when referring to the logging subsystem |
| Slash Command | Slash Command | slash command | Capitalize when referring to `/command` syntax |
| Configuration | Configuration | configuration | Capitalize when referring to config files/system |
| Config | Config | config | Abbreviation: Config; capital when referring to specific config files |
| Migration | Migration | migration | Capitalize when referring to DB migration process |
| Rollback | Rollback | rollback | Capitalize when referring to DB rollback procedure |
| Deployment | Deployment | deployment | Capitalize when referring to the operations domain |
| Provisioning | Provisioning | provisioning | Capitalize when referring to the operations domain |
| Runtime | Runtime | runtime | Capitalize when referring to application runtime |
| Lifecycle | Lifecycle | lifecycle | Capitalize when referring to component lifecycle management |
| Boundary | Boundary | boundary | Capitalize when referring to architectural boundaries |
| Allowlist | Allowlist | allow list, whitelist | Prefer "allowlist"; avoid "whitelist" |
| Denylist | Denylist | deny list, blacklist | Prefer "denylist"; avoid "blacklist" |
| Fail-Closed | Fail-Closed | fail closed | Hyphenate as adjective; "fail-closed mode" |
| Fail-Open | Fail-Open | fail open | Hyphenate as adjective; "fail-open mode" |
| Idempotent | Idempotent | idempotent | Capitalize when starting sentence; otherwise lowercase |
| Deterministic | Deterministic | deterministic | Capitalize when starting sentence; otherwise lowercase |
| Stale | Stale | stale | Capitalize when starting sentence; otherwise lowercase |
| Dead Code | Dead Code | dead code | Capitalize when referring to the concept |
| Stub | Stub | stub | Capitalize when referring to test stubs |
| Mock | Mock | mock | Capitalize when referring to test mocks |
| Fixture | Fixture | fixture | Capitalize when referring to pytest fixtures |
| Test Suite | Test Suite | test suite | Capitalize when referring to the collection of tests |
| Coverage | Coverage | coverage | Capitalize when referring to test coverage metric |
| Lint | Lint | lint | Capitalize when referring to linting tool/command |
| Type Check | Type Check | type check | Capitalize when referring to mypy/type checking |
| CI | CI | continuous integration | Abbreviation: CI; always uppercase |
| CD | CD | continuous delivery/deployment | Abbreviation: CD; always uppercase |
| PR | PR | pull request | Abbreviation: PR; always uppercase |
| Issue | Issue | issue | Capitalize when referring to GitHub Issue |
| Plan | Plan | plan | Capitalize when referring to implementation plan document |
| Requirement | Requirement | requirement | Capitalize when referring to formal requirement document |
| Artifact | Artifact | artifact | Capitalize when referring to build artifacts |
| Build | Build | build | Capitalize when referring to the build process |
| Release | Release | release | Capitalize when referring to software releases |
| Sprint | Sprint | sprint | Capitalize when referring to development sprints |
| Milestone | Milestone | milestone | Capitalize when referring to project milestones |
| Priority | Priority | priority | Capitalize when referring to classification system |
| Status | Status | status | Capitalize when referring to item lifecycle state |
| Owner | Owner | owner | Capitalize when referring to responsibility assignment |
| Assignee | Assignee | assignee | Capitalize when referring to responsibility assignment |
| Reviewer | Reviewer | reviewer | Capitalize when referring to review process participant |
| Approver | Approver | approver | Capitalize when referring to approval gate participant |
| Gate | Gate | gate | Capitalize when referring to approval gates |
| Sign-off | Sign-off | signoff | Hyphenate as noun; "sign off" as verb |
| Traceability | Traceability | traceability | Capitalize when referring to traceability section |
| Out-of-Scope | Out-of-Scope | out of scope | Hyphenate as adjective; "out of scope" as phrase |
| In-Scope | In-Scope | in scope | Hyphenate as adjective; "in scope" as phrase |
| Non-Goal | Non-Goal | non goal | Hyphenate as noun; "non-goal" as compound word |
| Assumption | Assumption | assumption | Capitalize when referring to documented assumptions |
| Risk | Risk | risk | Capitalize when referring to risk assessment |
| Mitigation | Mitigation | mitigation | Capitalize when referring to risk mitigation strategy |
| Constraint | Constraint | constraint | Capitalize when referring to design constraints |
| Decision | Decision | decision | Capitalize when referring to design decision |
| Alternative | Alternative | alternative | Capitalize when referring to considered alternatives |
| Trade-off | Trade-off | tradeoff | Hyphenate as noun; "tradeoff" acceptable as single word |
| Specification | Specification | specification | Capitalize when referring to formal spec document |
| Standardization | Standardization | standardisation | Use American English spelling (z) per project convention |
| Localization | Localization | Localisation | Use American English spelling (z) per project convention |
| Authorization | Authorization | Authorisation | Use American English spelling (or) per project convention |
| Behavior | Behavior | Behaviour | Use American English spelling (or) per project convention |
| Optimize | Optimize | Optimise | Use American English spelling (ze) per project convention |
| Organize | Organize | Organise | Use American English spelling (ze) per project convention |

## Usage Rules

1. **Proper nouns**: Always capitalize CamelCase terms (EventBus, ToolRegistry, WorkflowEngine).
2. **Abbreviations**: Always use uppercase form (MQ, NC, DLQ, ACK, DTO, etc.).
3. **Bilingual text**: Use English preferred form with Japanese alternative in parentheses on first occurrence.
4. **Hyphenation**: Use hyphens for compound adjectives (at-least-once delivery, fail-closed mode).
5. **Plurals**: Plural forms are acceptable when referring to multiple items (Known Issues, Needs Confirmations).
6. **First occurrence**: On first use in a document, include both preferred and alternative forms: "Needs Confirmation (要確認)".
7. **Subsequent occurrences**: Use only the preferred form after first definition.
