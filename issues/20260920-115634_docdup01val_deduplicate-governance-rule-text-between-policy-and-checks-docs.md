# Deduplicate governance rule text between policy and checks docs

## Priority
Medium

## Summary
Remove 3 near-verbatim duplicate rule sections from
`docs/00_governance_04_documentation-checks.md` (the "Checks" document),
keeping `docs/00_governance_01_documentation-policy.md` (the "Policy"
document) as the single canonical source and replacing each duplicate with
a short summary plus a link, so the Checks document states only what to
verify with which tool.

## Background
Direct reading (2026-09-20) confirms 3 sections are duplicated near-verbatim
between the two documents:
- **Merge Conditions**: `documentation-policy.md`'s "## Merge Conditions"
  (Blocking/Non-Blocking condition lists) and "### Merge Workflow" (5-step
  list) vs. `documentation-checks.md`'s "### 13. Merge Condition Validation"
  — identical Blocking-conditions list (4 items) and near-identical
  Non-Blocking-conditions list (Checks has one additional `GV-020`-specific
  bullet Policy lacks) and an identical 5-step Merge workflow list.
- **Change Impact**: `documentation-policy.md`'s "## Change Impact Rule"
  (4-step procedure) and "## Change-Impact Matrix" (4-row table) vs.
  `documentation-checks.md`'s "## Change Impact Assessment" and "### Change-
  Impact Matrix" — both the 4-step procedure text and the 4-row table are
  word-for-word identical between the two files.
- **Review Conditions**: `documentation-policy.md`'s "## Review Rule"
  (4-bullet list) vs. `documentation-checks.md`'s "## Review Gate
  Conditions" — word-for-word identical 4-bullet list.

`documentation-checks.md` already demonstrates the intended non-duplicating
pattern once in the same file (its "Automated"/"Canonical source" note near
line 240 points to `documentation-policy.md`'s dependency-graph taxonomy
instead of repeating it) — this issue brings the 3 sections above in line
with that existing, already-correct pattern in the same document.

The duplication has already begun to drift: `documentation-checks.md`'s
Merge Condition Validation section has one non-blocking condition
(`GV-020`-related) that `documentation-policy.md`'s Merge Conditions section
does not — direct evidence that the two copies are not being kept in sync,
confirming the drift risk this issue addresses is not hypothetical.

## Problem
The same governance rule text (Blocking/Non-Blocking merge conditions, the
change-impact procedure and matrix, the review-gate condition list) exists
in two files with no mechanism keeping them in sync, and has already
diverged in one place.

## Reason for Change
Proven documentation drift risk (an already-observed divergence, not a
hypothetical one), plus the design goal the source memo states explicitly:
`documentation-checks.md`'s purpose is "what to verify with which tool," not
a second copy of the rule text itself, which belongs solely in
`documentation-policy.md`.

## Implementation Intent
For each of the 3 sections in `documentation-checks.md`, replace the full
rule text with a short summary (one or two sentences restating only what
the check verifies, e.g. "Merge is blocked when any of Policy's Blocking
Conditions hold") plus a link to the corresponding section in
`documentation-policy.md`. Preserve `documentation-checks.md`'s own
check-specific additions that are NOT in `documentation-policy.md`'s copy
(the `GV-020`-related non-blocking bullet) by relocating that one addition
into `documentation-policy.md`'s canonical "Non-Blocking Conditions" list
instead of discarding it — this is the one piece of substantive content in
the Checks-doc copies that is not pure duplication and must not be lost.
No other document links by anchor into `documentation-checks.md`'s "13.
Merge Condition Validation"/"Change Impact Assessment"/"Review Gate
Conditions" headings (confirmed via `grep`, 2026-09-20 — see Unresolved
Questions), so heading removal or rename carries no anchor-breakage risk
from this specific concern; the headings are nonetheless kept in this
Plan's Implementation Intent (only their body content is replaced) since
`documentation-checks.md`'s own numbered check list (see Out of Scope)
gives no independent reason to remove them.

## Target Files or Areas
- `docs/00_governance_04_documentation-checks.md` — "### 13. Merge Condition
  Validation" (confirmed), "## Change Impact Assessment" and "### Change-
  Impact Matrix" (confirmed), "## Review Gate Conditions" (confirmed).
- `docs/00_governance_01_documentation-policy.md` — "## Merge Conditions"
  (confirmed; receives the relocated `GV-020`-related bullet per
  Implementation Intent).
- Unknown: the broader `docs/` corpus, for the remaining categories the
  source memo named (ADR section structure, dependency-graph explanation,
  Configuration Isolation, RAG pipeline, Fail-open/Fail-closed table,
  Related Documents, Known Issue reference method) — this issue's own
  manual review confirmed only the Merge-Conditions/Change-Impact/Review
  cluster; the companion tool issue (see Dependencies) is needed for a
  systematic full-corpus sweep of the rest. A spot-check during this
  issue's own investigation found no similarly blatant verbatim duplication
  for "ADR Section Header Standardization" or "Software Runtime Dependency
  Graph" (both confirmed present only in `documentation-policy.md`, with
  other files pointing to it rather than repeating it) — these two
  categories from the source memo appear to already be handled correctly
  and likely do not need remediation, but this was a spot-check, not
  exhaustive verification.

## Required Changes
- Replace `documentation-checks.md`'s 3 confirmed sections with summary +
  link, per Implementation Intent.
- Relocate the `GV-020`-related non-blocking-condition bullet from
  `documentation-checks.md`'s copy into `documentation-policy.md`'s
  canonical "Non-Blocking Conditions" list.
- Once the companion tool issue lands, run it across the full `docs/` tree
  and remediate any further confirmed finding from the source memo's
  remaining named categories.

## Constraints
Do not remove any substantive content — only the duplicated restatement.
Do not change any rule's actual meaning (blocking vs. non-blocking
classification, matrix values, review-gate conditions) — this is a
deduplication, not a policy change. Do not break any existing anchor link
into the 3 sections being edited (verify first).

## Acceptance Criteria
- `documentation-checks.md`'s 3 confirmed sections no longer restate the
  full rule text; each states a short summary and links to
  `documentation-policy.md`'s corresponding section.
- `documentation-policy.md`'s "Non-Blocking Conditions" list includes the
  `GV-020`-related bullet that was previously only in
  `documentation-checks.md`'s copy.
- `tools/check_docs_quality.py`'s extended cross-file check (once the
  companion tool issue lands) reports zero new findings for these 3
  sections.
- No other `docs/*.md` file's link into any of the 3 edited sections is
  broken (verified via `grep -rn "documentation-checks.md#" docs/`, per
  Testing Expectations — no governance-domain automated checker exists for
  this).

## Testing Expectations
Not required for code (documentation-only, no behavior or public API
change). Run `tools/check_docs_quality.py` and `tools/check_docs_structure.py`
on both edited files. `tools/check_docs_consistency.py --domain` does not
support a governance-specific domain (confirmed via `--help`, 2026-09-20:
valid values are `agent`, `mcp`, `rag`, `deployment`, `overview` only) — it
does not apply here; instead, manually verify anchor-link integrity via
`grep -rn "documentation-checks.md#" docs/` (already confirmed zero matches
pre-edit, per Unresolved Questions — re-run post-edit to confirm still
zero, or that any new anchor a link now targets still resolves).

## Documentation Impact
This issue is itself a documentation change. Apply `routing.md`'s
Documentation row per `AGENTS.md` Global Rule 10.

## Out of Scope
- Extending `tools/check_docs_quality.py` for cross-file detection —
  tracked as the companion issue (see Dependencies).
- Remediating any `docs/*.md` file/category not confirmed in this issue
  (the source memo's other 7 named categories) — deferred to full-corpus
  discovery once the companion tool lands.
- Any change to `config/*.toml` files or source code.
- Renumbering `documentation-checks.md`'s numbered check list (e.g. "13.
  Merge Condition Validation") if removing content shifts numbering —
  preserve numbering unless the section is fully removed, in which case
  follow the file's own existing renumbering convention (confirm during
  implementation).

## Dependencies
Depends on the companion issue "Detect cross-file section duplication in
docs" (filed the same day) for full-corpus discovery of duplication beyond
the 3 confirmed sections, and for automated post-edit validation. This
issue's own 3 confirmed sections can be planned and remediated without
waiting for the companion issue to land, since they were confirmed by
direct reading.

## Unresolved Questions
Resolved during adversarial verification (2026-09-20): `grep -rn
"documentation-checks.md#" docs/` finds zero matches anywhere in the
`docs/` tree — no file links by anchor into
`docs/00_governance_04_documentation-checks.md` at all, let alone into the
3 target sections specifically. The anchor-breakage risk named in
Implementation Intent does not apply; no confirmation is needed before
removing or renaming any of the 3 target headings on this basis (Constraints'
more general "do not break any existing anchor link" instruction still
applies as a standing precaution, but this specific named risk is cleared).

## AI Implementation Instruction
Confirm both files' 3 target sections still contain the described
duplication before editing — do not edit based solely on this issue's
citation if content has since changed. Check for anchor links into the 3
`documentation-checks.md` sections before removing or renaming any heading.
Do not discard the `GV-020`-related bullet — relocate it to
`documentation-policy.md`, per Implementation Intent. Do not change any
rule's substantive meaning.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260920-115634
- **Related target files**: docs/00_governance_04_documentation-checks.md,
  docs/00_governance_01_documentation-policy.md
