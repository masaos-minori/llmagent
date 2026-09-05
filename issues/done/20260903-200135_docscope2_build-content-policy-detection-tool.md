# Build a docs/ content-policy detection tool and register it in governance checks

## Priority
Medium

## Summary
Build a new automated check that scans `docs/*.md` for the five
implementation-detail categories the docs content policy prohibits (full file
trees, per-file one-line descriptions, class/function-name indices,
implementation-location mappings, literal port numbers), register it in
`docs/00_governance_04_documentation-checks.md` as a report-only (Warning)
check, and run it once against the current corpus to produce a concrete
violation inventory for follow-up content-migration work.

## Background
This issue depends on the docs/ design-intent content policy being defined
first (see Dependencies) — the detection logic needs the five remove-category
definitions to exist as a precise, agreed specification before it can
implement pattern/heuristic matching for each one.

`docs/00_governance_04_documentation-checks.md`'s Governance Verification
Matrix already has a precedent for landing a corpus-wide check as report-only
first: `GV-020` (removed-name reintroduction detection) shipped as
`Warning`/`Partial`, with an explicit note to "promote to default-on once the
corpus is compliant." This issue follows the same rollout pattern, since the
current corpus has known, extensive violations (the entire
`01_overview-files-*` series, among others) that a day-one hard gate would
turn into a blocking failure for unrelated PRs.

## Problem
There is currently no automated way to find every instance of the five
remove-categories across `docs/*.md`. A manual one-time sweep would also
leave no regression guard — a future document could reintroduce a file tree,
an index table, or a port number with nothing to catch it, the same gap
`GV-020` was created to close for reintroduced removed-names. The known
violation sites are already large enough to matter: at least 6 dedicated
file-tree documents (`docs/01_overview-files-01-build.md` through
`docs/01_overview-files-06-misc.md`) and 5+ additional files containing index
tables or literal port numbers (see the sibling policy-definition issue's
Problem section for the full evidence list).

## Reason for Change
Per `AGENTS.md` Global Rule 7 ("If you perform the same operation three or
more times, extract it into a Python script... and reuse it"), a violation
category recurring across 10+ files already crosses this repository's own
stated threshold for tooling. Building the detection logic once, as a
registered check, also gives the corpus a permanent regression guard instead
of a single manual pass that immediately goes stale.

## Implementation Intent
Implement the detection logic as either a new registered check function in
`tools/check_docs_quality.py` (extending its existing `@register_core_check`
pattern, which several comparable content-shape checks already use — e.g.
`check_stale_patterns`, `check_resolved_in_active`) or as a new dedicated
script, at the implementer's discretion — see Unresolved Questions for the
sizing consideration. Land the check as report-only (Warning), matching
`GV-020`'s own rollout precedent, and register it in
`docs/00_governance_04_documentation-checks.md`'s Automated Checks list and
Governance Verification Matrix (next available `GV-*` ID after the current
highest). After implementation, run the new check against the current
`docs/*.md` corpus once and record its output (file + violated category) —
this becomes the scoping input for whichever follow-up issue(s) perform the
actual content rewrites; do not attempt those rewrites here.

## Target Files or Areas
- `tools/check_docs_quality.py` (candidate location for the new check) or a
  new dedicated script — implementer's decision, see Unresolved Questions
- `docs/00_governance_04_documentation-checks.md` (new Automated Check entry;
  Governance Verification Matrix — new row)
- `docs/*.md` — read-only scan target; **not edited** by this issue (see Out
  of Scope)

## Required Changes
1. Implement detection logic for each of the five remove-categories defined
   by the sibling policy-definition issue: full file tree; per-file one-line
   description embedded in a tree or table; class/function/method
   signature-and-description index table; implementation-location mapping
   statement; literal port number in a heading, table, or prose.
2. Report findings at file + heading/line-level granularity, following this
   repository's existing `Issue` object convention in
   `tools/check_docs_quality.py`/`tools/check_docs_structure.py`.
3. Register the new check in `docs/00_governance_04_documentation-checks.md`'s
   Automated Checks list, describing what it detects and its report-only
   status.
4. Add a new row to the Governance Verification Matrix (next available
   `GV-*` ID), marked Warning/report-only, matching `GV-020`'s "promote to
   default-on once the corpus is compliant" framing.
5. Run the new check once against the current `docs/*.md` corpus and record
   the resulting violation inventory (file + category) as this issue's
   completion evidence.

## Constraints
- The new check must land as a non-blocking Warning, not a hard CI failure —
  the current corpus has known, extensive violations; a day-one hard gate
  would block unrelated PRs.
- Must not flag `rules/env.md` — that document is the canonical, allowed
  location for concrete operational values and is out of this policy's
  scope entirely (it is not a `docs/*.md` file).
- Do not edit any `docs/*.md` file to fix a finding this check reports — see
  Out of Scope.

## Acceptance Criteria
- A new automated check exists that scans `docs/*.md` and reports every
  instance of the five remove-categories.
- The new check is registered in `docs/00_governance_04_documentation-checks.md`'s
  Automated Checks section and Governance Verification Matrix as report-only.
- Running the new check against the current `docs/` corpus produces a
  concrete violation inventory (file + category), attached to this issue.
- The check does not flag `rules/env.md` or any file outside `docs/*.md`.

## Testing Expectations
Unit tests for the new detection logic — one test per remove-category, each
using a small fixture document containing that category's pattern and
confirming it is detected, plus a fixture containing only retain-category
content (per the sibling policy issue) confirming it is not falsely flagged.
`check_docs_quality.py`/`check_docs_structure.py` continue to pass against
the (unmodified by this issue) existing corpus, since the new check is
report-only and this issue does not rewrite any `docs/*.md` content.

## Documentation Impact
Yes — register the new check in
`docs/00_governance_04_documentation-checks.md`'s Automated Checks section
and Governance Verification Matrix, as described in Required Changes.

## Out of Scope
- Rewriting `docs/01_overview-files-*.md`, or any other document the new
  check flags, to actually comply with the policy — a separate,
  multi-file content-migration effort to be scoped into its own follow-up
  issue(s) using this issue's violation inventory.
- Defining the content policy itself (tracked in the sibling
  policy-definition issue this one depends on).
- Deciding `check_port_drift()`/`check_port_range_claim()`'s fate under the
  new policy (tracked separately, see Dependencies).

## Dependencies
Depends on the docs/ design-intent content policy being defined first (issue
`20260903-200135_docscope1_define-design-intent-content-policy.md`) — the
five remove-category definitions must exist before detection logic can be
implemented against them. The violation inventory this issue produces is a
dependency for whichever follow-up issue(s) perform the content rewrites.

## Unresolved Questions
- Whether the new detection check should extend
  `tools/check_docs_quality.py` (following its existing
  `@register_core_check` pattern) or live in a new dedicated script —
  `check_docs_quality.py` is already close to `skills/DESIGN.md` File Split
  Rule's 400-line trigger threshold; decide based on how large the final
  check logic turns out to be.
- Whether a short, explicitly-labeled illustrative example (e.g. a worked
  example showing a port number for pedagogical purposes, per
  `skills/DESIGN.md` "No concrete configuration values"'s own carve-out)
  should be exempted automatically, or flagged with a human confirming the
  exemption during review.

## AI Implementation Instruction
Implement only the detection tool and its registration in
`docs/00_governance_04_documentation-checks.md`. Do not edit any other file
under `docs/` to remove or rewrite content. Land the new check as report-only
(Warning), never a blocking CI failure, on first landing. After implementing,
run the tool against the current `docs/*.md` corpus once and report its
findings (file + category) as this issue's completion evidence — do not
attempt to fix any of the findings yourself. If a category's pattern cannot
be detected reliably without excessive false positives/negatives, stop and
ask rather than shipping a noisy heuristic.
