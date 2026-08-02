# Fix docs/04_mcp_06_13 watchdog inaccuracies: degraded_reason dead-code contradiction and nonexistent config/log strings

## Priority
Medium

## Summary
`docs/04_mcp_06_13-part1` describes `record_failure(reason=...)` as if it is a working mechanism for recording degraded reasons, but `docs/04_mcp_06_12` (confirmed accurate against source) states `record_degraded` has zero call sites and is dead code — the two files directly contradict each other on the same mechanism. Separately, `06_13-part2` references configuration/log strings that do not exist in source: `repeated_tool_error_threshold`, a `[debug]`-prefixed log format, and `error_type=tool/transport` grep patterns — actual logs are structured JSON.

## Reason for Change
This is a confirmed factual contradiction (degraded_reason) plus confirmed-nonexistent configuration/log strings — an operator building monitoring around the documented grep patterns would find zero matches, and anyone reading `06_13-part1` alone would believe degraded-reason recording works when it does not.

## Implementation Intent
Rewrite `06_13-part1` to match `06_12`'s confirmed-accurate description (degraded_reason recording is dead code, not a working mechanism). Replace the nonexistent config/log strings in `06_13-part2` with the actual JSON structured log field names and correct grep/jq patterns.

## Target Files or Areas
`docs/04_mcp_06_13-part1`, `docs/04_mcp_06_13-part2`, cross-referenced against `docs/04_mcp_06_12`

## Required Changes
- Rewrite `06_13-part1`'s `record_failure(reason=...)` description to align with `06_12`: state explicitly that `record_degraded`/degraded-reason recording has no call sites in current code (dead code), not an active mechanism.
- Investigate the actual structured JSON log format and field names used by the watchdog/tool-error-recording mechanism (likely a different layer's `_record_tool_error()`, per this review's hypothesis) and replace the nonexistent `repeated_tool_error_threshold`/`[debug]`/`error_type=tool/transport` references in `06_13-part2` with the confirmed actual format.

## Acceptance Criteria
`06_13-part1` and `06_12` no longer contradict each other on degraded_reason's operational status; `06_13-part2` contains only configuration/log-format references confirmed to exist in current source.

## Testing Expectations
Not required (documentation-only). Manually verify via `grep -rn "repeated_tool_error_threshold\|record_degraded\|record_failure" scripts/` and by inspecting actual structured log output before finalizing.

## Documentation Impact
Both parts of `06_13` corrected for internal and cross-file consistency with `06_12`.

## Out of Scope
Do not implement a working degraded-reason recording mechanism in this issue — documentation only, reflecting current (dead-code) reality.

## AI Implementation Instruction
Verify both claims (degraded_reason status and the log-format strings) directly against source before rewriting — do not simply merge the two files' wording without confirming which one (06_12, per this review) is actually correct.

## Traceability
- Workflow phase: issue-creation
- Source: docs_review_mcp.md §1 (全体評価 items 9-10), §6A (watchdog degraded_reasonの自己矛盾, 存在しない設定・ログ文字列)
- Generated at: 2026-08-02
