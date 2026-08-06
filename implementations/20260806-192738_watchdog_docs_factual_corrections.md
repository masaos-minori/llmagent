## Goal

Correct factual inaccuracies in watchdog-related documentation to match the actual behavior of the current codebase.

## Scope

- **In-Scope**:
  - `docs/04_mcp_06_13_watchdog-health-reasons-scheduling-part1.md`
  - `docs/04_mcp_06_13_watchdog-health-reasons-scheduling-part2.md`
- **Out-of-Scope**:
  - `docs/04_mcp_06_12_watchdog-configuration-monitoring.md`
  - Any modification to `scripts/` or other source code.
  - Implementation of missing features (thresholds, working degraded-reason recording).

## Assumptions

1. The current source code is the authoritative reference for system behavior.
2. The user intends only documentation fixes, not feature implementations.

## Design decisions

- Use direct verification commands from the validation plan to confirm each claim before editing.
- Keep edits minimal — only correct inaccurate statements, do not rewrite sections.

## Alternatives considered

- Rewrite both watchdog docs entirely: rejected because it risks introducing new errors and exceeds scope.
- Delete the inaccurate sections: rejected because readers lose useful context even if some details are wrong.

## Compatibility considerations

- Readers who previously relied on the incorrect descriptions of `record_degraded`, `record_failure`, and config/log strings will see corrections.
- No API contract changes — this is purely a documentation correction.

## Security considerations

N/A — documentation-only changes.

## Rollback considerations

- If the verification commands reveal different behavior than expected, revert the specific edits and re-verify.
- If the JSON structure of `ToolExecEvent` has changed since the original analysis, update accordingly.

## Implementation

### Target file

`docs/04_mcp_06_13_watchdog-health-reasons-scheduling-part1.md`

### Procedure

**Phase 1: Fix Degraded Reason Contradiction**

1. Verify `record_failure(server_key)` signature — confirm it does not accept a `reason` parameter.
2. Verify `record_degraded()` exists but has zero call sites in `scripts/`.
3. Confirm `get_degraded_reason()` always returns `None` due to this.
4. Update documentation to reflect these facts.
5. Add cross-reference to `docs/04_mcp_06_12_watchdog-configuration-monitoring.md`.

### Method

Verification via grep + direct file edit.

### Details

```bash
# Verify record_failure signature
grep -n "def record_failure" scripts/shared/mcp_health.py

# Verify record_degraded has no call sites
grep -rn "record_degraded(" scripts/

# Verify get_degraded_reason always returns None
grep -A5 "def get_degraded_reason" scripts/shared/mcp_health.py
```

After verification:
- Replace any statement claiming `record_failure` accepts a `reason` parameter with: "`record_failure(server_key)` does not accept a reason argument."
- Replace any statement claiming `record_degraded` is actively used with: "`record_degraded()` exists but has zero call sites and is currently dead code."
- Add: "`get_degraded_reason()` always returns `None` due to the above."
- Add cross-reference: "For configuration details, see [watchdog-configuration-monitoring](04_mcp_06_12_watchdog-configuration-monitoring.md)."

### Target file

`docs/04_mcp_06_13_watchdog-health-reasons-scheduling-part2.md`

### Procedure

**Phase 2: Fix Nonexistent Config/Log Strings**

1. Remove references to `repeated_tool_error_threshold`.
2. Remove references to `[debug]` log prefix and logfmt-style `error_type=...` grep patterns.
3. Describe the actual mechanism: `ToolTransportInvoker` maintains `stat_tool_errors` and `stat_transport_errors` as in-memory counters without thresholds or warning logs.
4. Describe the actual audit logging: `audit_tool_exec()` emits structured JSON via `audit_logger` containing `"event":"tool_exec"` and `"error_type":"tool"|"transport"|""` fields.
5. Provide correct JSON-based grep/jq examples.

### Method

Verification via grep + direct file edit.

### Details

```bash
# Verify stat_tool_errors/stat_transport_errors exist
grep -n "stat_tool_errors\|stat_transport_errors" scripts/shared/tool_transport_invoker.py

# Verify ToolExecEvent error_type field
grep -n "error_type" scripts/agent/shared/models.py

# Verify audit_tool_exec JSON structure
grep -A10 "def audit_tool_exec" scripts/agent/tool_audit.py
```

After verification:
- Remove all references to `repeated_tool_error_threshold` — replace with prose stating no such threshold exists; errors are counted in memory without threshold-based warnings.
- Remove all references to `[debug]` log prefix and logfmt patterns — replace with: "Errors are recorded as in-memory counters (`stat_tool_errors`, `stat_transport_errors`) without threshold-based logging."
- Replace logfmt grep examples with JSON-based examples:
  ```bash
  # Correct way to search audit logs
  grep '"error_type":"tool"' <audit-log>
  jq 'select(.error_type == "tool")' <audit-log>
  ```

## Validation plan

| Check | Tool | Target | Expected Outcome |
|---|---|---|---|
| Doc Accuracy (Part 1) | `grep -rn "record_degraded\|record_failure" scripts/` | Verify `record_failure` lacks `reason` arg and `record_degraded` has no calls | Matches doc description |
| Doc Accuracy (Part 2) | `grep -r "error_type" scripts/agent/shared/models.py` | Verify `ToolExecEvent` contains `error_type` field | Matches doc description |
| Doc Accuracy (Part 2) | `grep -r "stat_tool_errors" scripts/shared/tool_transport_invoker.py` | Verify existence of error counters | Matches doc description |
| Final Review | Manual Inspection | Compare updated docs against source code | No contradictions remain |

## Out of scope

- Source code modifications (`scripts/`).
- Changes to `docs/04_mcp_06_12_watchdog-configuration-monitoring.md`.
- Implementation of missing watchdog features (thresholds, degraded-reason recording).
- Modifications to other documentation not listed above.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260804-121700_plan.md
- Source implementation procedure: N/A
- Generated at: 20260806-192738
- Related target files: docs/04_mcp_06_13_watchdog-health-reasons-scheduling-part1.md, docs/04_mcp_06_13_watchdog-health-reasons-scheduling-part2.md
