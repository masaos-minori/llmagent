# Fix confirmed-nonexistent `_FORBIDDEN_KEYS` evidence in docs/01_overview-arch-02-pipelines.md "workflow always required" claim

## Priority
High

## Summary
`docs/01_overview-arch-02-pipelines.md` (~lines 64-70) states that `workflow_mode` is included in `_FORBIDDEN_KEYS` (in `build_agent_config()`) and causes a `ConfigLoadError` if missing — but repository-wide grep confirms no `_FORBIDDEN_KEYS` identifier exists anywhere in source. The overall conclusion ("workflow definition is always required, with no fallback path") remains correct and is independently supported by `deploy.sh`/`setup_services.sh`'s `[FATAL]` checks, but the specific mechanism cited as evidence is fictitious.

## Reason for Change
This is a confirmed factual error in the evidence supporting an otherwise-correct and important invariant. An implementer troubleshooting around this claim would search for a nonexistent code path and waste time.

## Implementation Intent
Keep the "workflow definition is always required" conclusion, but replace the fictitious `_FORBIDDEN_KEYS`/`ConfigLoadError` evidence with the actually-verifiable mechanism: fail-fast `[FATAL]` checks in `deploy/deploy.sh` (at deploy time) and `setup_services.sh` (table-existence check at startup time), both causing `exit 1`.

## Target Files or Areas
`docs/01_overview-arch-02-pipelines.md`

## Required Changes
- Remove the `_FORBIDDEN_KEYS`/`build_agent_config()`/`ConfigLoadError` claim (~lines 64-70).
- Replace with: "Workflow definitions are fail-fast checked both at deploy time (`deploy/deploy.sh`) and at startup time (`setup_services.sh`'s table-existence check); a missing definition causes an `[FATAL]` message and `exit 1`."
- Verify the exact check locations and behavior in `deploy/deploy.sh` and `setup_services.sh` before finalizing wording.

## Acceptance Criteria
No reference to `_FORBIDDEN_KEYS` or `ConfigLoadError` remains for this claim; the replacement evidence is verified against actual `deploy.sh`/`setup_services.sh` behavior.

## Testing Expectations
Not required (documentation-only). Manually verify via `grep -r "_FORBIDDEN_KEYS" .` (expect no results) and by reading the actual `[FATAL]` checks in `deploy/deploy.sh`/`setup_services.sh` before finalizing.

## Documentation Impact
`docs/01_overview-arch-02-pipelines.md` corrected with verified evidence.

## Out of Scope
Do not change `deploy/deploy.sh` or `setup_services.sh` behavior in this issue — documentation only.

## AI Implementation Instruction
This is a confirmed factual error (verified via repository-wide grep) — apply the fix directly rather than treating it as speculative. Verify the replacement evidence (deploy.sh/setup_services.sh check details) against actual source before finalizing wording.

## Traceability
- Workflow phase: issue-creation
- Source: docs_review_overview_architecture.md §4 強化候補 (arch-02「ワークフローは常時必須」), §6A (`_FORBIDDEN_KEYS`)
- Generated at: 2026-08-02
