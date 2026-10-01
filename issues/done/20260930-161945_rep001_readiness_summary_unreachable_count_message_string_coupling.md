# Readiness summary unreachable-server count couples to a message substring

## Priority
Low

## Summary
In `ReadinessReporter.report_readiness()` (`scripts/agent/startup_reporter.py`), the "Unreachable servers" line counts outcomes by matching the literal substring `unreachable` inside `outcome.message.lower()`. This couples display logic to an exact wording in the discovery service's messages. Derive the unreachable set from structured data instead.

## Background
`McpToolDiscoveryService.discover_all()` returns a structured `unreachable: list[str]` of server keys, and `StartupValidationResult` holds flat `outcome` records whose messages embed human text. The readiness reporter aggregates these for display.

## Problem
Counting `"unreachable" in o.message.lower()` (lines ~94-98) breaks silently if the discovery message wording changes even slightly, and double-counts if any unrelated message happens to contain the word "unreachable". It duplicates information already available structurally.

## Reason for Change
Display-only fragility; low impact now but a latent footgun as message text evolves.

## Implementation Intent
Prefer the structured `discovery.unreachable` / `runtime_tools.unavailable_servers` data (already used elsewhere in the same method) to compute the unreachable count, and drop the substring scan. If only the display line needs fixing, scope the change to that computation.

## Target Files or Areas
- `scripts/agent/startup_reporter.py` (`report_readiness()`, the `unreachable_count` computation)

## Required Changes
- Compute the unreachable-server count from structured sources instead of substring matching.
- Keep the emitted "Unreachable servers: N" line stable in format.

## Constraints
- No change to other reported lines or readiness semantics.

## Acceptance Criteria
- The unreachable count matches the structured unavailable set exactly.
- Renaming the discovery message substring does not change the reported count.

## Testing Expectations
- Unit test with a pipeline containing an unreachable outcome whose message wording differs, asserting the count is derived from structure, not text.

## Documentation Impact
N/A: no doc change required.

## Out of Scope
- Any change to the tool-discovery service or its messages.

## Dependencies
N/A: none.

## Unresolved Questions
N/A: none.

## AI Implementation Instruction
Scope is display-only. Replace the substring match with the structured unreachable/unavailable source; do not touch other reporter logic.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260930-161945
- **Related target files**: scripts/agent/startup_reporter.py
