# Remove placeholder methods and align Git MCP documentation with verified implementation

## Priority
Low

## Summary
Restore clear module boundaries in `repository_state.py` after the functional security fixes
(`gitauth`, `gitpipeline`, `gitdryrun`) are complete, then update documentation and active Known
Issues using implementation and regression-test evidence.

## Background
`issues/done/20260831-115635_gitsec01_gitsecurityguards_dead_class_and_doc_drift.md` already
removed a different dead class, `GitSecurityGuards`. This issue covers a separate set of
placeholders investigation found still present in `repository_state.py`:
`verify_authorization()` (no call sites), `_is_protected_branch()` (always returns `False`),
and `verify_postcondition()` (always returns success) — see `gitauth` and `gitpipeline`, filed
alongside this issue, for the functional fixes this cleanup depends on.

## Problem
`repository_state.py` contains empty service, dispatch, formatter, tool-handler, and guard
methods that are outside the module's stated responsibility. Some of these placeholders return
success-like values and can be mistaken for active security behavior by maintainers, tests, or
automated documentation tooling. Design documents must not claim that safeguards are complete
while placeholders or disconnected paths remain — `docs/04_mcp_90_inconsistencies_and_known_issues.md`'s
`MCP-003` currently illustrates this risk (see `gitpipeline`'s Background).

## Reason for Change
This cleanup is intentionally sequenced after `gitauth`/`gitpipeline`/`gitdryrun` land, because
removing a placeholder before its functional replacement exists would delete the only code
location the replacement is meant to occupy — cleanup and documentation alignment both depend
on identifying the canonical implementation first.

## Implementation Intent
Remove empty service-construction, dispatch, formatter, and tool-handler methods from
`repository_state.py` after confirming they have no active callers; remove duplicate guard
helpers that unconditionally allow access; retain compatibility shims only when a verified
caller and removal plan exist; move any required behavior to its canonical module. Correct
documentation that describes protected-branch enforcement, ref validation, postcondition
verification, or the nine-stage pipeline as complete when the implementation does not support
that claim. Register unresolved deviations as active Known Issues; remove resolved entries from
active inventories per the documentation-governance policy. Map each ADR-012 invariant to
concrete implementation and regression-test evidence.

## Target Files or Areas
- `scripts/mcp_servers/git/repository_state.py`
- `scripts/mcp_servers/git/git_service.py`
- `scripts/mcp_servers/git/format_output.py`
- `docs/04_mcp_04_05_git.md`
- `docs/04_mcp_90_inconsistencies_and_known_issues.md`
- `docs/adr/ADR-012-git-mcp-server-side-write-enforcement.md`
- `docs/00_security_02_high-risk-tool-common-policy.md`
- `tests/test_git_security_compliance.py`

Confirm file existence and responsibility before editing; modify only files required by the
verified implementation path.

## Required Changes
- Remove empty service-construction, dispatch, formatter, and tool-handler methods from `repository_state.py` after confirming they have no active callers.
- Remove duplicate guard helpers that unconditionally allow access, once `gitauth`/`gitpipeline` provide the real implementation.
- Retain compatibility shims only when a verified caller and removal plan exist.
- Move any required behavior to its canonical module.
- Correct documentation that describes protected-branch enforcement, ref validation, postcondition verification, or the nine-stage pipeline as complete when the implementation does not support that claim.
- Register unresolved deviations as active Known Issues; remove resolved entries from active inventories per the documentation-governance policy.
- Map each ADR-012 invariant to concrete implementation and regression-test evidence.
- Reconcile `plans/20260901-223706_plan.md`'s pending NC-019/`MCP-003` documentation update with this issue's and `gitpipeline`'s findings before that plan proceeds.

## Constraints
- Do not guess unverified behavior; record unresolved design decisions as Needs Confirmation.
- Preserve unrelated behavior.
- Do not introduce a second authorization or dispatch path.
- Update documentation only after implementation and tests establish the current behavior.
- If investigation disproves an assumption in this issue, update the issue with evidence before implementation.

## Acceptance Criteria
- `repository_state.py` contains only repository-state and pipeline responsibilities.
- No empty production method returns a success-like value.
- Static analysis and tests confirm that removed methods have no callers.
- Documentation clearly distinguishes current behavior from target design.
- Every ADR-012 invariant has implementation and test evidence or an active Known Issue.
- No placeholder behavior is described as an implemented safeguard.
- Related documents use consistent terminology and valid links.

## Testing Expectations
Add focused unit tests for all changed rules. Add or update integration tests for the HTTP and
service dispatch paths. Confirm each new test fails before the fix and passes after the fix.
Run the complete existing Git MCP test suite and resolve regressions. Do not treat
documentation statements as proof of runtime behavior.

## Documentation Impact
Yes — this issue's entire second half is the ADR-012/Known Issues/Specification alignment
listed in Target Files, to be done only after `gitauth`/`gitpipeline`/`gitdryrun`/`gitdispatch`
establish the actual, current behavior.

## Out of Scope
- The functional fixes themselves (`gitauth`, `gitpipeline`, `gitdryrun`, `gitdispatch`, `gitpathaudit`, `gitremote`, `giterrors`) — this issue only cleans up and documents once those land.
- Re-opening `issues/done/20260831-115635_gitsec01_gitsecurityguards_dead_class_and_doc_drift.md`'s already-resolved `GitSecurityGuards` scope.

## Dependencies
Depends on `gitauth`, `gitpipeline`, and `gitdryrun` landing first — removing
`verify_authorization()`/`_is_protected_branch()`/`verify_postcondition()` as placeholders is
only safe once their functional replacements exist. Should be sequenced before or alongside
re-attempting `plans/20260901-223706_plan.md`'s `MCP-003` resolution.

## Unresolved Questions
N/A: none

## AI Implementation Instruction
Do not begin the removal tasks until `gitauth`, `gitpipeline`, and `gitdryrun` have landed and
their tests pass — confirm this by re-reading those issues' final state, not by assuming from
this issue's filing time. Do not mark any ADR-012 invariant as verified without a concrete
implementation and regression-test citation.
