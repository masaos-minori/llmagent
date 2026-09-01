# Add ADR-vs-code compliance checks to CI (GV-014)

## Priority
Medium

## Summary
`docs/00_governance_04_documentation-checks.md` lists GV-014 ("Code is NOT
canonical for adopted design decisions") as `Auto` / `Missing`, with Follow-up
Work item #9: "Add ADR-vs-code contradiction detection to CI". This issue adds
that check in three staged, independently shippable steps, building on the
existing `docs/adr-index.md` ADR Invariant Verification Matrix rather than
inventing a new mechanism.

## Background
Evidence: Confirmed by repository evidence.

- `docs/00_governance_04_documentation-checks.md:286,304` — GV-014 is defined
  and its Follow-up Work explicitly requests ADR-vs-code contradiction
  detection in CI; current tooling column says `check_compat_shims.py`, but
  that tool only greps for backward-compatibility text patterns and stale
  identifiers — it does not check ADR compliance.
- `docs/adr-index.md` already maintains an "ADR Invariant Verification
  Matrix" (INV-001 through INV-022): each row names an ADR, an invariant, a
  verification `Type`, and a `Verification Status` that, for many rows,
  names a specific test path in backticks (e.g. `` `tests/agent/test_startup.py::test_aborts_on_missing_workflow_definition` ``).
  Most rows currently say "Confirmed in code; no test yet" — i.e. the matrix
  itself documents where automated coverage is missing.
- `tools/check_known_deviation_sync.py` already implements the closest
  precedent: it cross-checks ADR `## Known Deviations` bullets against
  per-area `docs/*_90_inconsistencies_and_known_issues.md` Status fields, and
  is wired into a `.pre-commit-config.yaml` hook alongside
  `check_compat_shims.py`, `check_docs_quality.py`,
  `check_tool_descriptions_sync.py`, `check_suppression_justification.py`.
- Grepping `scripts/` for `ADR-[0-9]{3}` finds only 3 files with an inline
  ADR reference comment (`scripts/agent/tool_policy.py`,
  `scripts/db/recovery.py`, `scripts/shared/tool_registry.py`) — there is no
  existing convention of code systematically citing the ADR it implements.

## Problem
There is no automated check that (a) a test path cited in the ADR Invariant
Verification Matrix as "Confirmed ... passing" actually exists and passes,
or (b) code contains a pattern an Accepted ADR explicitly prohibits. Both gaps
let an ADR's documented guarantee silently drift from the code without CI
noticing — exactly the risk GV-014 exists to close.

## Reason for Change
GV-014 is currently `Missing` and explicitly named as follow-up work in the
governance document itself; this issue closes that documented gap using
infrastructure (the Invariant Matrix, the `check_known_deviation_sync.py`
pattern) that already exists, rather than requiring a new design.

## Implementation Intent
Ship as three independent, incrementally-valuable checks rather than one
combined feature. Full natural-language semantic verification of "does this
code match this ADR's intent" is not achievable by automation — scope every
check to a narrow, literally-machine-checkable claim.

1. **Invariant Matrix test-path verification** (highest value, lowest risk):
   for every `docs/adr-index.md` INV-XXX row whose `Verification Status`
   cites a backtick-quoted `path/to/test.py::test_name` path, verify the path
   exists and (optionally, as a separate CI step) that running it passes.
   Rows saying "no test yet" / "Not verified" / "Not implemented" are
   correctly out of scope for this check — the matrix already flags them.
2. **Per-ADR prohibited-pattern registry**: extend the
   `check_compat_shims.py` pattern (or add a sibling tool) with an
   ADR-scoped pattern table, keyed by ADR ID, for statements an Accepted ADR
   phrases as a prohibition (e.g. ADR-001 "Workflow無効化モードおよび
   Workflowを迂回する直接実行経路は設けない"). Seed the table only from
   patterns an implementer can point at in ADR text, not speculative rules.
3. **Scoped ADR-reference requirement**: require an inline `ADR-XXX`
   reference comment only on the specific files/functions already named by
   an Invariant Matrix row (not a repository-wide mandate) — enforcing this
   broadly is not maintainable given the current 3-file baseline.

## Target Files or Areas
- `docs/adr-index.md` (ADR Invariant Verification Matrix — read, not
  restructured, by step 1)
- New tool, e.g. `tools/check_adr_invariant_matrix.py` (step 1)
- `tools/check_compat_shims.py` or a new sibling tool (step 2)
- `.pre-commit-config.yaml`, `.github/workflows/ci.yml` (hook registration)
- `docs/00_governance_04_documentation-checks.md` (GV-014 status update once
  implemented)

## Required Changes
- Step 1: implement a checker that parses `docs/adr-index.md`'s Invariant
  Verification Matrix table, extracts backtick-quoted test paths from
  `Verification Status` cells, and fails if a cited path does not resolve to
  an existing test node.
- Step 2: implement or extend a checker with an ADR-ID-keyed prohibited
  pattern table (structurally similar to `check_compat_shims.py`'s
  `COMPAT_PATTERNS`), seeded from at least one real prohibition per ADR that
  has one.
- Step 3: implement a scoped-reference check limited to files/functions named
  in Invariant Matrix rows.
- Register each new check as its own `.pre-commit-config.yaml` hook (matching
  the existing one-hook-per-hard-crash-mode convention) and add it to the CI
  `lint` job in `.github/workflows/ci.yml`.
- Update `docs/00_governance_04_documentation-checks.md` GV-014's
  `Implementation Status` column and remove Follow-up Work item #9 once step
  1 ships (steps 2-3 may close it further or be tracked as separate GV
  sub-items — see Unresolved Questions).

## Constraints
- Do not attempt full natural-language semantic verification of ADR intent
  against code; every check must reduce to a literal, machine-checkable
  claim (a path exists, a pattern is absent, a comment is present).
- Do not mark Invariant Matrix rows that already say "no test yet" / "Not
  verified" / "Not implemented" as failures — those are known, documented
  gaps, not regressions.
- Do not change the Invariant Matrix's existing content or numbering as part
  of this issue; only read it.

## Acceptance Criteria
- Step 1 checker fails when a `docs/adr-index.md` INV-XXX row cites a test
  path that does not exist, and passes on the current repository state
  (verify against current rows before merging — some may need correction as
  a byproduct).
- Step 2 checker fails when a seeded ADR prohibition pattern is detected in
  `scripts/` and passes on the current repository state.
- Step 3 checker fails when a file named by an Invariant Matrix row lacks its
  required ADR reference comment.
- All three checks are wired into `.pre-commit-config.yaml` and
  `.github/workflows/ci.yml`'s `lint` job.
- `docs/00_governance_04_documentation-checks.md` GV-014 row reflects the new
  implementation status.

## Testing Expectations
- Unit tests for each new/extended tool under `tests/tools/`, following the
  existing pattern in `tests/tools/test_generate_workitem.py` and sibling
  test files for other `tools/check_*.py` scripts.
- Run each new checker against the live repository as part of implementation
  to confirm it does not produce false positives against current, correct
  content.

## Documentation Impact
`docs/00_governance_04_documentation-checks.md` must be updated: GV-014's
`Implementation Status` column, and removal or narrowing of Follow-up Work
item #9 to reflect what remains after steps 1-3.

## Out of Scope
- Full semantic ADR-vs-code contradiction detection (not achievable by
  automation).
- Auditing or fixing existing Invariant Matrix rows beyond what step 1's
  acceptance criteria requires to pass cleanly.
- Retrofitting ADR-reference comments onto code not named by an Invariant
  Matrix row (step 3 is intentionally scoped, not repository-wide).
- GV-016 ("no unimplemented auto-checks documented as implemented"), a
  related but separately tracked governance rule.

## Dependencies
N/A: none — builds on existing `docs/adr-index.md` content and the
`check_known_deviation_sync.py` precedent, both already in the repository.

## Unresolved Questions
- Whether steps 2 and 3 should be split into their own GV sub-items (e.g.
  GV-014a/b/c) or tracked under the single GV-014 row — leave this decision
  to whoever plans this issue, informed by how the Plan phase scopes the
  work (Path A vs Path B).
- Whether the CI test-execution sub-step of Step 1 (actually running cited
  tests, not just checking path existence) belongs in this issue or a
  follow-up — flagged here as a scope choice, not resolved.

## AI Implementation Instruction
Read `docs/adr-index.md`'s full Invariant Verification Matrix and
`tools/check_known_deviation_sync.py` before implementing Step 1 — model the
new tool's structure (argument parsing, `--format json`, exit codes) on the
latter for consistency with existing `tools/check_*.py` conventions. Implement
and land Step 1 first; do not attempt Steps 2-3 in the same pass unless the
Plan phase explicitly scopes them together.
