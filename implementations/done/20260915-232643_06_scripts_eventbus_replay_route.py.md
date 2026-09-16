## Goal

Evidence for replay endpoint contract during eventbus11's API reference documentation. Read-only verification. REQ-005.

## Scope

Verify replay_route.py's replay endpoint contract (SSE/JSON formats, pagination). This row is read-only evidence gathering.

## Assumptions

- replay_route.py exists at `scripts/eventbus/replay_route.py`
- GET /replay supports both SSE and JSON formats with pagination
- Parameters: since_seq (default=0), format (default="sse"), limit (default=100), offset (default=0)
- Operator role required

## Design decisions

- Read-only verification: confirm current state without independently modifying
- If the replay endpoint already matches the plan's documented contract, mark this step as complete
- If stale contract exists, report Plan Gap

## Alternatives considered

- Independently updating replay_route.py: rejected because eventbus11's scope is documentation only
- Deferring until eventbus11 executes: not viable since eventbus11 depends on eventbus02/eventbus03 landing first

## Implementation

### Target file

`scripts/eventbus/replay_route.py`

### Procedure

1. Check whether replay_route.py defines GET /replay endpoint
2. Verify SSE format support
3. Verify JSON format support
4. Verify pagination parameters (since_seq, limit, offset)
5. If all checks pass, mark this step as complete
6. If any check fails, determine whether eventbus02 has landed:
   - If eventbus02 has not landed: missing endpoint is expected, no action needed
   - If eventbus02 has landed but contract doesn't match: report Plan Gap

### Method

Adversarial verification: treat the plan's description of current replay_route.py state as unverified. Check each claim against the actual file content.

### Details

**Step 1: Verify replay endpoint**

Expected: GET /replay handler supporting SSE and JSON formats with pagination.

Pre-migration state: replay endpoint was pending per ADR-013 (now stale).

**Step 2: Verify SSE format**

Expected: SSE format example matching the plan's documented contract (id:{seq}\ndata:{json_data}\n\n).

**Step 3: Verify JSON format**

Expected: JSON format with total, limit, offset, items fields.

**Step 4: Verify pagination**

Expected: Parameters since_seq (>=0), limit (1-1000), offset (>=0).

## Compatibility considerations

- This verification must occur after eventbus02 lands; executing before eventbus02 would produce false positives
- The replay endpoint may have been updated since eventbus02's approval — verify alignment rather than duplicating the edit
- If replay_route.py still lacks expected functionality after eventbus02 lands, the gap belongs to eventbus02's execution, not eventbus11

## Security considerations

- None applicable: documentation reconciliation only, no code changes or security boundary modifications

## Rollback considerations

- No rollback needed: this is a verification step, not a modification
- If replay_route.py needs correction, defer to eventbus02's implementation rather than applying an independent fix

## Validation plan

| Target File | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| scripts/eventbus/replay_route.py | Manual review: verify replay endpoint contract | Manual inspection | Contract matches documented API reference |

## Completion criteria

- replay_route.py defines GET /replay endpoint
- Both SSE and JSON formats are supported
- Pagination parameters (since_seq, limit, offset) are correct

## Out of scope

- Modifying replay_route.py directly (unless stale content requires correction, which should be deferred to eventbus02)
- Re-deciding the replay endpoint design (answered by eventbus02)
- Creating API reference documents (separate row in this plan)

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Verify replay endpoint exists and matches documented contract | Passed | — | — | replay関数定義済み（replay_route.py:27） |
| 2 | Verify SSE format support | Passed | — | — | StreamingResponse + text/event-stream（replay_route.py:71） |
| 3 | Verify JSON format support | Passed | — | — | Literal["sse", "json"] alias="format"（replay_route.py:30） |
| 4 | Verify pagination parameters | Passed | — | — | since_seq(default=0,ge=0)、format(default="sse")、limit(default=100,ge=1,le=1000)、offset(default=0,ge=0) — 全パラメータが計画と一致 |

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
- **Requirement ID**: REQ-005
- **Source issue**: issues/20260914-102632_eventbus11_api-reference-endpoint-contracts.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260914-181638_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260915-232643
- **Related target files**: scripts/eventbus/replay_route.py
