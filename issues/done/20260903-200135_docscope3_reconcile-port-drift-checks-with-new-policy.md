# Reconcile check_port_drift/check_port_range_claim with the no-port-numbers policy

## Priority
Medium

## Summary
`tools/check_docs_consistency.py` already contains `check_port_drift()` and
`check_port_range_claim()` — automated checks that assume port numbers *are*
documented in `docs/*.md` and verify they match the actual configuration. The
new docs/ content policy (see Dependencies) says port numbers should not be
documented at all. Decide and implement how these two existing checks should
change under the new policy: deprecate, narrow to an exempt file set, or keep
pending a documented exemption list.

## Background
This issue depends on the docs/ design-intent content policy being defined
first (see Dependencies), and is best informed by the detection tool's
violation inventory (also see Dependencies) so the decision accounts for how
many files and port references are actually affected, rather than guessing.

## Problem
`check_port_drift()` and `check_port_range_claim()` currently operate on the
premise that `docs/*.md` files legitimately state port numbers and that the
check's job is to catch when a stated number drifts from the real
configuration. Under the new policy, the correct end state for most of these
files is that the port number is removed entirely, not merely kept accurate.
Left unreconciled, these two checks would continue enforcing accuracy of
content the new policy says should not exist — an internal contradiction in
this repository's own governance tooling.

## Reason for Change
Leaving `check_port_drift()`/`check_port_range_claim()` unreconciled would
mean the repository simultaneously tells writers "do not document port
numbers" (new policy) and "keep documented port numbers accurate" (existing
check) — a direct contradiction that would confuse both human writers and any
future automation relying on either signal being authoritative.

## Implementation Intent
Using the sibling detection-tool issue's violation inventory as evidence,
choose one of: (a) deprecate `check_port_drift()`/`check_port_range_claim()`
entirely once the corresponding `docs/*.md` files no longer state port
numbers; (b) narrow their scope to only the files the new policy explicitly
exempts (e.g. a worked example explicitly labeled illustrative, per
`skills/DESIGN.md` "No concrete configuration values"'s carve-out); or (c)
leave them active pending a documented, explicit exemption list, if the
content-migration follow-up work has not yet landed. Record the chosen
option and its rationale directly in
`docs/00_governance_04_documentation-checks.md`'s existing description of
these checks, so the decision is visible alongside the checks themselves.

## Target Files or Areas
- `tools/check_docs_consistency.py` (`check_port_drift()`,
  `check_port_range_claim()`)
- `docs/00_governance_04_documentation-checks.md` (existing description of
  the Domain Consistency Check, `check_docs_consistency.py`)

## Required Changes
1. Review the sibling detection-tool issue's violation inventory for how many
   `docs/*.md` files and port references are affected.
2. Decide and record which of the three options (deprecate / narrow / keep
   pending exemption list) applies, with a one-paragraph rationale.
3. Implement the chosen option in `tools/check_docs_consistency.py`.
4. Update `docs/00_governance_04_documentation-checks.md`'s existing
   description of the Domain Consistency Check to reflect the decision.

## Constraints
- Do not remove port-number verification for any file the new policy exempts
  (e.g. `rules/env.md`, which is out of this policy's scope entirely and
  never touched by this issue).
- Do not perform the actual `docs/*.md` content edits that remove port
  numbers from individual files — that is the separate content-migration
  follow-up work this issue's decision informs, not something this issue
  performs itself.

## Acceptance Criteria
- `check_port_drift()`/`check_port_range_claim()`'s continued applicability
  under the new policy is explicitly decided and implemented — not left
  silently inconsistent with the policy.
- The decision and its rationale are recorded in
  `docs/00_governance_04_documentation-checks.md`.
- Existing tests for `check_port_drift()`/`check_port_range_claim()` (or
  their replacement/removal) pass and reflect the new intended behavior.

## Testing Expectations
Update or remove existing unit tests for `check_port_drift()`/
`check_port_range_claim()` to match whichever option is chosen. If narrowed
to an exempt file set, add a test confirming files outside that set are no
longer checked. If deprecated, confirm removal does not break
`tools/check_docs_consistency.py`'s `main`/`main_mcp`/`main_agent` entry
points.

## Documentation Impact
Yes — update `docs/00_governance_04_documentation-checks.md`'s existing
Domain Consistency Check description to reflect the decision made here.

## Out of Scope
- Rewriting individual `docs/*.md` files to remove port numbers — a separate
  content-migration follow-up.
- Defining the content policy itself, or building the detection tool
  (tracked in the sibling issues this one depends on).

## Dependencies
Depends on the docs/ design-intent content policy being defined first (issue
`20260903-200135_docscope1_define-design-intent-content-policy.md`), and
should be informed by the detection tool's violation inventory (issue
`20260903-200135_docscope2_build-content-policy-detection-tool.md`) before
the decision in Implementation Intent is finalized.

## Unresolved Questions
Which of the three options (deprecate / narrow / keep pending exemption
list) applies cannot be decided until the sibling detection-tool issue's
violation inventory is available — recorded here as the primary open
question this issue must resolve once that evidence exists.

## AI Implementation Instruction
Wait for the sibling detection-tool issue's violation inventory before
choosing an option, unless the user explicitly directs a specific option in
advance. Edit only `tools/check_docs_consistency.py` and
`docs/00_governance_04_documentation-checks.md`. Do not edit any other
`docs/*.md` file. Stop and ask if the violation inventory does not clearly
support one option over the others.
