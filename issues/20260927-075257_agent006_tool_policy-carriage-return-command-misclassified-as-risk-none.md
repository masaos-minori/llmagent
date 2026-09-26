# tool_policy carriage return command misclassified as risk none

## Priority
High

## Summary
`tests/agent/test_tool_policy.py::TestPrefixCollision` has 2 tests expecting a carriage-return-injected command to be classified as `RiskLevel.HIGH`, but it is now classified as `RiskLevel.NONE` — a potential security-classification regression for a command-injection-style evasion technique.

## Background
Discovered during the post-docs-reorg full-suite validation sweep (`implementations/20260925-111411_04_tests___full_suite_.md`), which surfaced 97 failing tests; this is one root-cause cluster from that investigation.

## Problem
- `test_prefix_collision_carriage_return_rejected`: `assert <RiskLevel.NONE: 'none'> == 'high'`
- `test_carriage_return_in_command_rejected`: `assert <RiskLevel.NONE: 'none'> == 'high'`

Both tests assert that a command containing a carriage return (`\r`), likely used to attempt a prefix-collision bypass of tool-allowlist checks, must be classified as high risk. It is currently classified as no risk at all.

## Reason for Change
This is a security-relevant classification: if a carriage-return-based prefix-collision technique can now bypass risk classification (going from `high` to `none`), a previously-blocked command-injection/allowlist-bypass vector may currently be permitted. This should be prioritized above most other clusters in this investigation given its security nature.

## Implementation Intent
Read the current risk-classification logic in `agent/tool_policy.py` (confirm exact path) for how it detects/handles carriage returns and prefix-collision patterns. Determine whether a recent change to string-normalization, command-parsing, or prefix-matching logic caused carriage-return-containing commands to fall through to the default `NONE` classification instead of being flagged.

## Target Files or Areas
- `scripts/agent/tool_policy.py` (confirm exact path)
- `tests/agent/test_tool_policy.py`

## Required Changes
- Identify why carriage-return-containing commands no longer classify as `RiskLevel.HIGH`.
- Restore the correct classification, treating this as a security regression fix unless investigation shows the test's expectation itself is outdated/incorrect (Needs confirmation, but security-sensitive changes should default to restoring the stricter behavior pending confirmation).

## Constraints
Do not weaken risk classification elsewhere while fixing this — scope the fix to the carriage-return/prefix-collision detection path specifically.

## Acceptance Criteria
- Both listed tests pass with `RiskLevel.HIGH` restored for the carriage-return scenarios.
- No other currently-passing risk-classification test regresses.

## Testing Expectations
Run `tests/agent/test_tool_policy.py` in full (not just the 2 failing tests) to confirm no regression in other classification cases; run full suite once after the fix.

## Documentation Impact
If risk-classification logic changes, update any tool-policy/security documentation describing prefix-collision or carriage-return handling (confirm exact doc path, Needs confirmation).

## Out of Scope
Other unrelated failing tests from the same full-suite run.

## Dependencies
N/A: none

## Unresolved Questions
Needs confirmation: whether this is a genuine regression (production code changed) or the test's expectation is stale relative to an intentional design change — treat as a regression by default given the security implications, but confirm via git history/blame on the classification function before concluding.

## AI Implementation Instruction
Treat this as security-sensitive: do not relax the test's expectation to match current (weaker) behavior without explicit confirmation that the `NONE` classification is intentional. Check git blame/history on the risk-classification function for the carriage-return path before deciding the fix direction.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: implementations/20260925-111411_04_tests___full_suite_.md
- **Generated at**: 20260927-075330
- **Related target files**: tests/agent/test_tool_policy.py
