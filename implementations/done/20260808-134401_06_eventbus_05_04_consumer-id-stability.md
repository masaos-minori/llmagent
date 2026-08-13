# Implementation Procedure: Event Bus Consumer ID Stability

## Goal

Restructure `docs/06_eventbus_05_04_consumer-id-stability.md` to reduce duplication while preserving critical facts about consumer_id stability requirements.

## Scope

**In-Scope**: `docs/06_eventbus_05_04_consumer-id-stability.md` — restructure to reduce duplication while preserving stability-critical facts
**Out-of-Scope**: Other eventbus chapters (`docs/06_eventbus_*.md`), source code changes, tests

## Assumptions

- `memo-doc-eventbus-review.md` has been deleted but its guidance for this chapter remains valid based on independent verification against the source codebase
- Consumer_id stability requirements (must be stable across restarts, volatile IDs like PIDs should not be used, collision risk when multiple consumers share an ID) must survive the cleanup intact
- Existing internal links and cross-references must remain valid after editing

## Design decisions

- This chapter serves as the canonical source for consumer responsibility regarding consumer_id management
- Consumer_id is entirely client-managed; server never auto-generates it
- The chapter's primary value is preventing the misunderstanding that consumer_id can be transient (PID-based)

## Alternatives considered

- Moving consumer_id stability content into `06_eventbus_02_02_subscribe-ack.md` (where subscribe/ack is discussed) — rejected because consumer_id stability is a client-side concern distinct from the ack protocol itself
- Removing this chapter entirely — rejected because the PID-avoidance guidance and collision risk are not stated elsewhere

## Implementation

### Target file

`docs/06_eventbus_05_04_consumer-id-stability.md`

### Procedure

1. Read the current chapter to identify duplicated content vs. unique stability-critical statements
2. Remove verbatim duplication with `06_eventbus_02_02_subscribe-ack.md` and `06_eventbus_03_persistence_schema_and_replay.md`
3. Replace mechanical query-parameter framing with cross-references to canonical source chapter
4. Preserve all stability-critical statements listed in the keep list below
5. Confirm the chapter follows the standard template from `memo-doc-eventbus-review.md` §「修正後の章構成テンプレート」

### Method

Compress over delete strategy — remove full field lists, method signatures, dataclass definitions, and exhaustive enumerations but preserve references to source modules.

### Details

**Remove:**
- Verbatim duplication with `06_eventbus_02_02_subscribe-ack.md` and `06_eventbus_03_persistence_schema_and_replay.md`
- Mechanical query-parameter framing (consumer_id as a URL parameter detail)

**Keep:**
- consumer_id must be managed stably by the client
- consumer_id is required for resuming replay after a restart
- volatile IDs like PIDs should not be used
- sharing the same ID across multiple consumers causes offset collisions
- the server does not detect collisions

## Compatibility considerations

- Internal Markdown links and cross-references must remain valid after editing
- Cross-references to `06_eventbus_02_02_subscribe-ack.md` and `06_eventbus_03_persistence_schema_and_replay.md` should be present where detail was removed

## Security considerations

- Consumer_id collision risk is a correctness/security issue — if two consumers share an ID, one may receive messages intended for another
- This is the canonical source for the "server does not detect collisions" statement

## Rollback considerations

- Revert to the original chapter if stability-critical statements are accidentally weakened during trimming
- The "503 is degraded, not down" clarification is not applicable here; rollback concern is specifically about consumer_id stability statements

## Validation plan

| Check | Tool | Target |
|---|---|---|
| Stability model preserved | Manual | Consumer_id stability requirement, PID-avoidance guidance, collision risk all explicit |
| No verbatim duplication | Manual | No content duplicates other chapters verbatim |
| Internal links valid | Manual | All cross-references valid, especially new references to `06_eventbus_02_02_subscribe-ack` and `06_eventbus_03_persistence_schema_and_replay` |
| Cross-references present | Manual | References to canonical source chapters where detail was removed |
| Template compliance | Manual | Follows `memo-doc-eventbus-review.md` §「修正後の章構成テンプレート」 |

## Out of scope

- Other eventbus chapters (`docs/06_eventbus_*.md`)
- Source code changes
- Tests

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: issues/20260805-103037_eventbus_05_04_consumer-id-stability_design-intent-cleanup.md
- Source requirement: requires/20260807-175941_require.md
- Source plan: plans/20260808-054741_plan.md
- Source implementation procedure: N/A
- Generated at: 20260808-134401
- Related target files: docs/06_eventbus_05_04_consumer-id-stability.md
