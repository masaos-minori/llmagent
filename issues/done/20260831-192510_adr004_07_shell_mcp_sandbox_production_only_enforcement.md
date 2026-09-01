# shell-mcp's `sandbox_backend="none"` enforcement is documented as production-only, contradicting ADR-004's single common environment policy

## Priority
Low

## Summary
`docs/04_mcp_04_02_file-write-file-delete-shell.md` documents a safety enforcement
(`sandbox_backend="none"` is rejected with a startup `RuntimeError`) as applying only "In
production mode (`security_profile = "production"` in `agent.toml`)". `docs/adr/ADR-004-environment-failure-handling-policy.md`
now requires a single common failure-handling policy where environment names do not weaken
safety enforcement, so a safety check that is described as active only in one environment
contradicts the current ADR.

## Background
Found while compiling the related-document impact analysis for the 2026-08-31 ADR-004 rewrite.
This is a distinct file from the ones already covered by
`issues/20260831-185650_adr004_04_remaining_local_dev_mode_language_in_specs.md` (which covers
`05_agent_10_01`, `04_mcp_05_03`, and `90_shared_03_01`).

## Problem
(Evidence: Explicit in code as documented) `docs/04_mcp_04_02_file-write-file-delete-shell.md`:
"**Enforcement in Production:** In production mode (`security_profile = "production"` in
`agent.toml`), `sandbox_backend = "none"` is not allowed. If this combination is detected, the
agent will raise a `RuntimeError` at startup. In production environments, either set
`sandbox_backend = "firejail"` or disable `shell-mcp`." This describes the `RuntimeError`
enforcement as conditioned on `security_profile`, implying it does not apply, or applies
differently, outside "production."

## Reason for Change
Whether the underlying code genuinely relaxes this check outside `security_profile="production"`
is not yet confirmed. If it does, this is a safety-relaxation-by-environment gap that ADR-004
now prohibits (Decision Group 1). If it does not — i.e., the check is actually unconditional and
only the documentation's framing is environment-specific — this is a documentation-accuracy issue
of the same kind already being tracked for the other three files.

## Implementation Intent
Confirm against current source (likely `scripts/mcp_servers/shell/service_static_helpers.py` or
wherever `shell_sandbox_backend` is validated at startup) whether the `RuntimeError` for
`sandbox_backend="none"` is actually conditioned on `security_profile`, or is unconditional and
only described as production-specific. If conditioned: raise this as a safety-relaxation gap
against ADR-004 and decide whether the check should become unconditional. If unconditional:
reword the Specification to remove the production-only framing, consistent with the approach
used for the other three files in `adr004_04`.

## Target Files or Areas
- `docs/04_mcp_04_02_file-write-file-delete-shell.md` — the quoted passage
- The shell-mcp startup validation source (exact file needs confirmation) — read-only reference

## Required Changes
- Confirm current behavior in source before editing the document.
- If the check is unconditional: reword the passage to state the FATAL enforcement without the
  "in production mode" framing.
- If the check is genuinely conditioned on `security_profile`: do not silently reword the
  documentation to hide the gap — raise it as a separate ADR-004 conformance gap instead.

## Constraints
- Do not change the underlying safety check's substance based on a guess — confirm actual
  behavior first.
- Do not perform a broader rewrite of this document beyond the identified passage.

## Acceptance Criteria
- The document's description of `sandbox_backend="none"` enforcement matches confirmed current
  behavior, with no implication that a non-production environment relaxes it (unless that gap is
  separately raised and tracked, not hidden).

## Testing Expectations
Documentation-only unless a genuine code gap is confirmed, in which case follow that gap's own
testing expectations in a separate issue.

## Documentation Impact
This issue is itself the documentation-accuracy fix (or the trigger for a follow-up
implementation issue) for the identified passage.

## Out of Scope
- The three files already covered by `issues/20260831-185650_adr004_04_remaining_local_dev_mode_language_in_specs.md`.
- Any other content in `04_mcp_04_02_file-write-file-delete-shell.md` unrelated to this passage.

## Dependencies
Related to `issues/20260831-185650_adr004_04_remaining_local_dev_mode_language_in_specs.md` (same
class of finding, different file, found after that issue was filed). Follows the 2026-08-31
ADR-004 rewrite.

## Unresolved Questions
Whether `sandbox_backend="none"` rejection is actually conditioned on `security_profile` in
current code — needs source confirmation before deciding whether this is a doc fix or a
code-conformance gap.

## AI Implementation Instruction
Read the actual shell-mcp startup validation source before editing the document. Do not assume
the Specification text is wrong without checking source — if the code genuinely relaxes this
check outside production, file that as a separate ADR-004 conformance issue instead of silently
rewording the Specification to hide it.
