## Goal

Remove ASCII directory trees and per-file descriptions from `docs/01_overview-files-06-misc.md`; replace with design-intent prose covering component responsibility, owned state, allowed dependency direction, reason for process separation, reason for per-process config separation, and design boundaries needing joint review. [REQ-001, REQ-003]

## Scope

- Remove the two ASCII tree blocks: `/opt/llm/eventbus/` tree (lines 27-48) and the `eventbus/` per-file description list (lines 50-100)
- Replace with prose describing: event bus architecture, message types, delivery guarantees, and event-driven communication patterns
- Preserve existing Front Matter, Related Documents, Keywords sections unchanged

## Assumptions

- The event bus follows an event-driven architecture pattern with publish-subscribe semantics
- Message types include: workflow events, session events, tool execution events
- Delivery guarantees are at-least-once (standard for SQLite-backed event stores)
- The six-file split remains unchanged (File Split Rule's 400-line threshold)

## Design decisions

- Keep the thematic grouping as prose structure (e.g., "Event Bus Architecture", "Message Types", "Delivery Guarantees") but replace file-by-file listing with component responsibility descriptions
- Replace bare file enumeration with a single pointer sentence ("see `eventbus/` for the current file layout") per `skills/DESIGN.md` Avoid implementation-reference duplication

## Alternatives considered

- Merging this file with `01_overview-files-04-shared.md` (rejected: different domains — event bus vs. shared infrastructure)
- Converting remaining prose to table format (rejected: prose better conveys causal relationships between event types and their handlers)

## Implementation

### Target file

`docs/01_overview-files-06-misc.md`

### Procedure

1. Identify and remove both ASCII tree blocks (the `/opt/llm/eventbus/` tree at lines 27-48 and the `eventbus/` per-file description list at lines 50-100)
2. Write prose replacing the `/opt/llm/eventbus/` tree: describe the event bus as a responsible entity with its owned state and dependency direction
3. Write prose replacing the `eventbus/` per-file list: describe the five thematic groups (message types, delivery mechanisms, event handlers, persistence layer, utilities) as component families with their collective responsibility
4. Verify Front Matter, Related Documents, and Keywords sections are preserved unchanged

### Method

Read the current file to identify exact tree block boundaries. Write replacement prose that covers: what each component does (responsibility), what it owns (state), which direction its dependencies flow (allowed dependency direction), why each runs separately (reason for process separation), and which boundaries require joint review (design boundaries).

### Details

**Section 1 — Event Bus Architecture:**

The event bus provides event-driven communication between system components. It uses SQLite-backed persistence for durability and implements publish-subscribe semantics for decoupled messaging. The event bus enables loose coupling between producers and consumers while maintaining delivery guarantees.

**Section 2 — Message Types:**

- Workflow events: lifecycle events for workflow execution (start, complete, fail)
- Session events: user interaction events (message received, response sent)
- Tool execution events: tool invocation events (tool called, result returned)

**Section 3 — Delivery Mechanisms:**

- At-least-once delivery via SQLite transactional writes
- Retry mechanism for failed deliveries
- Dead letter queue for unrecoverable messages

**Section 4 — Event Handlers:**

- Workflow handler: processes workflow lifecycle events
- Session handler: processes session-related events
- Tool handler: processes tool execution events
- Notification handler: sends notifications on significant events

**Section 5 — Persistence Layer:**

- SQLite-based event store with WAL mode for concurrent access
- Event schema with version tracking
- Index optimization for query performance

**Section 6 — Utilities:**

- Event serialization/deserialization
- Event filtering and routing
- Event logging and auditing

## Compatibility considerations

- Cross-references in other `docs/*.md` files must be updated if section headings change
- The "see `eventbus/` for the current file layout" pointer replaces the old inline file references; consumers should verify no stale cross-references remain

## Security considerations

No security impact — this is a documentation-only change. The removed ASCII trees contained no secrets or credentials.

## Rollback considerations

To rollback: restore the original file from git history (`git checkout HEAD -- docs/01_overview-files-06-misc.md`). The ASCII trees can be recovered from any prior commit before this change.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `docs/01_overview-files-06-misc.md` | Manual review + checker | `uv run python tools/check_docs_content_policy.py` && `uv run python tools/check_docs_structure.py docs/01_overview-files-06-misc.md` | Zero findings; structure check passes |

## Completion criteria

- `uv run python tools/check_docs_content_policy.py` reports zero findings for `docs/01_overview-files-06-misc.md`
- All ASCII tree-drawing characters (`├─`, `│`, `└─`) removed from the file
- All per-file one-line descriptions removed from the file
- Design-intent prose covers: component responsibility, owned state, allowed dependency direction, reason for process separation, reason for per-process config separation, and design boundaries
- Front Matter, Related Documents, and Keywords sections preserved without loss
- No cross-references broken in other `docs/*.md` files

## Out of scope

- Modifying `rules/env.md` (explicitly out-of-scope per Plan)
- Changing GV-021's report-only status
- Merging or deleting this file outright (File Split Rule's 400-line threshold)
- Deciding the auto-generated port-reference-table exemption (tracked in dcp001)
- Implementing the actual code changes to event bus components

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove ASCII trees and per-file descriptions | Pending | — | — | |
| 2 | Add design-intent prose for event bus | Pending | — | — | |
| 3 | Document message types and delivery guarantees | Pending | — | — | |
| 4 | Run validation checkers | Pending | — | — | |

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
- **Requirement ID**: REQ-001, REQ-003
- **Source issue**: issues/20260905-153715_dcp002_overview_file_structure_docs_redesign.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260908-210427_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260909-153145
- **Related target files**: docs/01_overview-files-06-misc.md
