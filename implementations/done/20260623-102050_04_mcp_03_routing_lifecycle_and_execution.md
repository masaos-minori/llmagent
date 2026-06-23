## Goal

Update the `McpServerHealthRegistry` section in `docs/04_mcp_03_routing_lifecycle_and_execution.md` to document the new `HALF_OPEN` state, the cooldown mechanism, and the updated `is_unavailable()` behavior.

## Scope

**In-Scope:**
- `docs/04_mcp_03_routing_lifecycle_and_execution.md` lines 190-203 — the state table, method table, and resolved note in the `McpServerHealthRegistry` section

**Out-of-Scope:**
- No other sections of the document
- No production code changes

## Assumptions

1. The state table needs a fourth row for `HALF_OPEN`.
2. The method table needs updated descriptions for `is_unavailable()` and `record_failure()`, plus a note about the new `half_open_cooldown_sec` constructor parameter.
3. The "Resolved" note at line 203 is still accurate and should not be removed.
4. A state transition diagram (ASCII) aids understanding and should be added above the tables, consistent with the plan's design section.

## Implementation

### Target file
`docs/04_mcp_03_routing_lifecycle_and_execution.md`

### Procedure

1. Locate the `McpServerHealthRegistry` section starting at line 186.
2. Replace lines 190-203 with the updated content.

### Method

Single `Edit` operation.

### Details

**Current (lines 190-203):**
```markdown
| State | Condition |
|---|---|
| `HEALTHY` | No failures or after successful call |
| `DEGRADED` | Failure count < threshold (default 3) |
| `UNAVAILABLE` | Failure count ≥ threshold; `_raw_execute()` blocks dispatch |

| Method | Description |
|---|---|
| `record_failure(server_key)` | Increment failure; return new state |
| `record_success(server_key)` | Reset failure count; returns `None` |
| `get_state(server_key)` | Current state; returns HEALTHY for unknown key |
| `is_unavailable(server_key)` | `True` if UNAVAILABLE |

> **Resolved (2026-06-18):** `ToolExecutor._raw_execute()` now calls `record_success()` on transport success and `record_failure()` on `TransportError`. DEGRADED/UNAVAILABLE transitions work correctly.
```

**Replacement:**
```markdown
**State transitions:**
```
HEALTHY ──(failure × threshold)──→ UNAVAILABLE
   ↑                                    │
   │                            (cooldown 30s elapsed)
   │                                    ↓
   └──(record_success)────────── HALF_OPEN (trial probe)
                                        │
                              (failure)─┘ → UNAVAILABLE (cooldown reset)
```

| State | Condition |
|---|---|
| `HEALTHY` | No failures or after successful call |
| `DEGRADED` | Failure count < threshold (default 3) |
| `UNAVAILABLE` | Failure count ≥ threshold; dispatch blocked |
| `HALF_OPEN` | 30s cooldown elapsed; one trial dispatch allowed |

| Method | Description |
|---|---|
| `record_failure(server_key)` | Increment failure count; `HALF_OPEN → UNAVAILABLE` (cooldown reset); threshold reached → `UNAVAILABLE` |
| `record_success(server_key)` | Reset failure count and `_unavailable_since`; `HALF_OPEN → HEALTHY` |
| `get_state(server_key)` | Current state; returns `HEALTHY` for unknown key |
| `is_unavailable(server_key)` | `True` if `UNAVAILABLE` and cooldown not yet elapsed; side effect: transitions to `HALF_OPEN` when cooldown elapses |

**Constructor:** `McpServerHealthRegistry(failure_threshold=3, half_open_cooldown_sec=30.0)`
- `half_open_cooldown_sec`: seconds after entering `UNAVAILABLE` before a trial dispatch is allowed (default 30s, fixed — not exponential backoff)

> **Resolved (2026-06-18):** `ToolExecutor._raw_execute()` now calls `record_success()` on transport success and `record_failure()` on `TransportError`. DEGRADED/UNAVAILABLE transitions work correctly.
```

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| HALF_OPEN state documented | `grep "HALF_OPEN" docs/04_mcp_03_routing_lifecycle_and_execution.md` | ≥ 2 matches |
| cooldown_sec documented | `grep "half_open_cooldown_sec" docs/04_mcp_03_routing_lifecycle_and_execution.md` | 1 match |
| State table has 4 rows | `grep -c "^\| \`" docs/04_mcp_03_routing_lifecycle_and_execution.md` | Count includes new row |
