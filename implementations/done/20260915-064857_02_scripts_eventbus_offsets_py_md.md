# Implementation Procedure: Read _sanitize_consumer_id() Behavior for Collision Detection Reference

## Goal

Read and understand `_sanitize_consumer_id()` behavior in `scripts/eventbus/offsets.py` to inform the collision detection implementation in `scripts/eventbus/db.py`. This is a read-only step — no modifications to this file.

## Scope

- Read `scripts/eventbus/offsets.py`: understand `_sanitize_consumer_id()` behavior
- No modifications to this file

## Assumptions

- `_sanitize_consumer_id()` sanitizes consumer IDs by replacing certain characters (e.g., dots, underscores) to produce a normalized form
- Two distinct IDs like `user.1` and `user_1` may sanitize to the same value, causing collision risk

## Design decisions

N/A: This is a read-only reference step. The design decisions are captured in the `scripts/eventbus/db.py` implementation procedure.

## Alternatives considered

### Alternative A: Modify `_sanitize_consumer_id()` to prevent collisions

**Reason for rejection:** Would violate REQ-005 — do not modify the live ACK path or any other part of the system beyond the legacy migration scope. The collision risk is only relevant during one-time migration, not in the live path.

## Implementation

### Target file

`scripts/eventbus/offsets.py` (read-only)

### Procedure

#### Step 1: Locate `_sanitize_consumer_id()` function

Find the `_sanitize_consumer_id()` function in `offsets.py`. Focus on:
- What characters are replaced
- What the replacement character is
- Whether the function is deterministic (same input always produces same output)

#### Step 2: Verify collision examples

Confirm that two distinct IDs like `user.1` and `user_1` sanitize to the same value. For example:
```python
>>> _sanitize_consumer_id("user.1")
"user_1"
>>> _sanitize_consumer_id("user_1")
"user_1"
```

This confirms the collision risk described in EVENTBUS-001.

#### Step 3: Document findings for collision detection

Record the sanitization rules so they can be used in the collision detection implementation. Key questions to answer:
1. Which characters are replaced?
2. What is the replacement character?
3. Is the function idempotent (applying it twice produces the same result)?

### Method

Manual code review — read the `_sanitize_consumer_id()` function and verify collision examples.

### Details

#### Key questions to answer

1. Does `_sanitize_consumer_id("user.1")` equal `_sanitize_consumer_id("user_1")`?
2. Are there other pairs of IDs that could collide?
3. Is the sanitization deterministic across Python versions?

## Compatibility considerations

- No compatibility impact — this is a read-only step
- Findings will inform the `scripts/eventbus/db.py` modification procedure

## Security considerations

- No security impact — this is a read-only step
- Understanding the sanitization rules is critical for implementing correct collision detection

## Rollback considerations

- N/A: No modifications made to this file

## Validation plan

1. Confirm understanding of `_sanitize_consumer_id()` matches the documented behavior
2. Verify that `user.1` and `user_1` sanitize to the same value
3. Verify that the sanitization is deterministic

## Completion criteria

- [ ] Sanitization rules understood
- [ ] Collision examples verified
- [ ] Determinism confirmed

## Out of scope

- Modifying `_sanitize_consumer_id()` itself
- Adding new sanitization rules
- Changing the sanitization behavior

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Locate _sanitize_consumer_id() function | Completed | 20260915-230000 | 20260915-230000 |  |
| 2 | Verify collision examples | Completed | 20260915-230000 | 20260915-230000 |  |
| 3 | Document findings for collision detection | Completed | 20260915-230000 | 20260915-230000 |  |

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
- **Requirement ID**: REQ-001 (understand _sanitize_consumer_id() behavior to implement collision detection)
- **Source issue**: issues/20260914-102632_eventbus11_api-reference-endpoint-contracts.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260914-185056_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260915-064857
- **Related target files**: scripts/eventbus/offsets.py