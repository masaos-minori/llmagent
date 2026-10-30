# Implementation Procedure: eventbus_09_publish_durability.md derived-artifact semantics

## Goal

Update the derived-artifact durability wording in
`docs/24_eventbus/eventbus_09_publish_durability.md` so a committed DLQ state implies a
durable generation request rather than an already-written file (REQ-004, REQ-009; plan AC-1,
AC-3).

## Scope

**In scope:**
- The authority-model passage at `eventbus_09_publish_durability.md:21-23` and the
  rationale bullets that restate the file-first guarantee.

**Out of scope:**
- Publish-commit guarantee (unchanged), JSONL archive text (unchanged), SSE delivery text.

## Assumptions
- Verified at HEAD `124e340b4`: `:21-23` states SQLite canonical for events and DLQ state,
  DLQ JSON files as derived artifacts; nearby rationale text presumes the file exists at
  commit time.

## Design decisions
- Keep the canonical-store framing word-for-word where it is about events/JSONL; only the
  DLQ-derived-artifact sentence changes: the commit pairs `dlq_at` with an outbox request,
  the background worker fulfills it, and generation failures are recorded durably and
  reported (never silently dropped) — the fail-closed rule moves from write-ordering to the
  persisted failure record.
- One sentence maximum per paragraph: this doc is about durability guarantees, not DLQ
  operations (operational detail stays in docs-03; cross-link by doc name only).

## Alternatives considered
- Removing the DLQ mention from docs-09 entirely: rejected — the durability guarantee for
  derived artifacts is exactly this doc's subject.

## Implementation
### Target file
`docs/24_eventbus/eventbus_09_publish_durability.md`

### Procedure
1. Rewrite the DLQ clause of the authority-model passage.
2. Adjust any rationale bullet that asserts the file exists at commit time.

### Method
Two-sentence-level edits; no section restructuring.

### Details
- Do not name implementation symbols here (doc policy); refer to "the DLQ outbox" in prose.

## Compatibility considerations
- Same-release deploy rule as row 12.

## Security considerations
- N/A.

## Rollback considerations
- Revert with rows 03-06.

## Validation plan
- Docs checkers per `routing.md` docs gate.

## Completion criteria
- The durability doc describes committed-first + durable-request semantics with no file-first
  residue.

## Out of Scope
- Operational lifecycle detail (row 12), reference surface (row 14).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Rewrite DLQ durability clause | Completed | 20261031-074833 | 20261031-074833 | Plan Phase 6 DLQ clause rewritten to committed-first + durable request; rationale bullets already file-neutral |
| 2 | Run docs checkers | Completed | 20261031-074833 | 20261031-074833 | Docs checkers pass |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-004`, `REQ-009`
- **Source issue**: `issues/20261029-104501_dlqbox001_dlq-sqlite-outbox.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/done/20261029-221254_dlqbox001_dlq-sqlite-outbox.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-103000
- **Related target files**: `docs/24_eventbus/eventbus_09_publish_durability.md`