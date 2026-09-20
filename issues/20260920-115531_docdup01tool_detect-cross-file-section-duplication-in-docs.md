# Detect cross-file section duplication in docs

## Priority
Medium

## Summary
Extend `tools/check_docs_quality.py`'s existing `check_content_similarity`
check — which already detects near-duplicate section bodies, but only
*within* a single document — to also compare sections *across* files, so a
governance rule (or other normative content) copied verbatim into a second
document is automatically flagged.

## Background
`tools/check_docs_quality.py` already implements `check_content_similarity`
(registered via `@register_core_check`), which flags "sections within the
same document with overlapping body text above threshold" using its own
`_compute_section_similarity()` helper. Confirmed by direct reading
(2026-09-20): `check_content_similarity`'s loop structure is
`for doc in files: ... sections = _extract_sections(content); for i...for
j...` — both `i` and `j` index into the *same* document's `sections` list;
there is no cross-document comparison anywhere in the function.

Running the existing tool against
`docs/00_governance_01_documentation-policy.md` and
`docs/00_governance_04_documentation-checks.md` together (2026-09-20)
produces 10 warnings, all *within* `documentation-policy.md` (its RAG/MCP/
Agent/EventBus/Shared-DB per-area sections resembling each other) — zero
warnings comparing the two files against each other, despite the two files
containing at least 3 sections of near-verbatim duplicate content (see the
companion documentation-remediation issue for the confirmed instances):
"Merge Conditions"/"Merge Workflow" (Policy) vs. "Merge Condition
Validation" (Checks); "Change Impact Rule"/"Change-Impact Matrix" (Policy)
vs. "Change Impact Assessment"/"Change-Impact Matrix" (Checks, word-for-word
identical 4-row table); "Review Rule" (Policy) vs. "Review Gate Conditions"
(Checks, identical 4-bullet list).

Notably, `documentation-checks.md` itself already demonstrates the correct,
non-duplicating pattern elsewhere in the same file (line 240: "Canonical
source: the dependency-graph taxonomy... is defined in
`docs/00_governance_01_documentation-policy.md` — see that [document]") —
confirming the desired end state is achievable and already modeled once in
this exact file, just not applied consistently to the 3 sections above.

## Problem
No existing tool detects that the same substantive content (a rule, a
table, a checklist) has been copied into more than one `docs/*.md` file.
`check_content_similarity` has the right underlying mechanism
(`_compute_section_similarity`) already built and tested, but its scope is
artificially limited to comparisons within one file.

## Reason for Change
Cross-file rule duplication carries the same drift risk category this
tool's sibling checks already guard against: a rule edited in one copy (its
canonical source) silently goes stale in the other, uncorrected copy, with
no automated signal. The confirmed governance_01/governance_04 case (see
Background) demonstrates this is not hypothetical — the two copies already
differ in one place (`documentation-checks.md`'s non-blocking conditions
list has one extra `GV-020`-related bullet the Policy copy lacks), showing
the duplication has already begun to diverge.

## Implementation Intent
Extend `check_content_similarity` (or add a closely related function reusing
its existing `_compute_section_similarity` helper unchanged) to also compare
each document's sections against every other document's sections, not only
its own. Preserve the existing within-file behavior and its current 10
findings exactly — this is an additive capability, not a replacement. Report
a cross-file finding with a distinct message (e.g. "Content similarity
detected between `{file_a}#{heading_a}` and `{file_b}#{heading_b}`") so it
is visually distinguishable from the existing within-file message in tool
output. Reuse the existing `_extract_sections`/`_compute_section_similarity`
helpers rather than reimplementing section extraction or the similarity
metric.

## Target Files or Areas
- `tools/check_docs_quality.py`
- `tests/tools/test_check_docs_quality.py` (confirmed to exist, 2026-09-20)

`tools/TOOL_DESCRIPTIONS.md` is confirmed NOT a target (verified during
adversarial verification, 2026-09-20): its two `check_docs_quality.py`
entries (lines 23, 71) describe the tool generically ("コアチェック...
重複見出し番号... 等") and do not name `content_similarity`/
`check_content_similarity` individually — unlike `check_docs_content_policy.py`'s
entries, which enumerate every category by name. No update is needed here.

## Required Changes
- Add cross-file comparison logic reusing `_extract_sections`/
  `_compute_section_similarity`, without changing either helper's existing
  behavior or the within-file check's existing output.
- Add unit tests: a positive case (two fixture documents sharing a
  near-duplicate section body) and a negative case (two fixture documents
  with unrelated content, confirming no cross-file false positive).

## Constraints
Report-only (`WARNING` severity), consistent with `check_content_similarity`'s
existing registration. Must not change the within-file check's existing
findings (10 on the current corpus subset checked in Background) or its
message text. Must not introduce O(n²) full-corpus comparison cost that
makes the tool impractically slow — if performance is a concern at full
corpus scale, consider a reasonable filter (e.g. only compare sections above
a minimum body length, matching an existing conservatism pattern elsewhere
in this codebase's doc-checking tools) — do not over-engineer or add
memoization not otherwise needed at the current corpus's actual size.

## Acceptance Criteria
- The new/extended check produces a finding for at least each of: Merge
  Conditions/Merge Workflow (Policy) vs. Merge Condition Validation
  (Checks); Change Impact Rule/Matrix (Policy) vs. Change Impact
  Assessment/Matrix (Checks); Review Rule (Policy) vs. Review Gate
  Conditions (Checks).
- The existing 10 within-file findings on
  `docs/00_governance_01_documentation-policy.md` are unchanged (same count,
  same messages) after this change.
- New unit tests pass; the full existing test suite for this tool passes
  with no regression.
- Running the tool against the full `docs/` tree completes without a
  material performance regression (informal check: compare wall-clock time
  before/after on the full corpus).

## Testing Expectations
Unit tests for the new cross-file comparison path (positive and negative
cases), added to `tests/tools/test_check_docs_quality.py`'s existing
`TestContentSimilarity` class (confirmed present, 4 tests, all currently
single-document/within-file per `_make_doc_file`'s one-`DocFile`-at-a-time
fixture pattern — verified during adversarial verification, 2026-09-20) or
a sibling class for the cross-file path specifically. Run the tool against
the full `docs/` tree before and after the change and diff the output to
confirm the within-file findings are unchanged and the expected new
cross-file findings appear — this repository already has an established
precedent for exactly this kind of check, `TestRegressionFullDocsTree`
(confirmed present, verified 2026-09-20): it runs `check_docs_quality.py`
against the real `docs/` tree via `subprocess` and asserts no unwanted
false-positive substring appears in the output (currently written for the
`duplicate_heading_numbers` check's numeric-subsection false positives).
Follow this same pattern for the new cross-file capability instead of
inventing a new regression-testing approach.

## Documentation Impact
None: `tools/TOOL_DESCRIPTIONS.md` does not name `check_content_similarity`
individually (verified during adversarial verification — see Target Files
or Areas), so no update is needed there. No `docs/*.md` content file is
edited by this issue — the companion issue (see Dependencies) owns
remediating the duplication this check newly detects.

## Out of Scope
- Editing any `docs/*.md` file to fix a finding this extended check
  produces — tracked as a separate, dependent issue (see Dependencies).
- Detecting duplication of content that is not organized into a
  Markdown-heading-delimited "section" (e.g. duplicate sentences scattered
  within otherwise-unrelated prose) — this issue's scope matches
  `check_content_similarity`'s existing section-body granularity.
- Any change to `check_docs_content_policy.py` (a different tool, covering
  a different category of documentation issue — implementation-reference/
  config-value duplication, not cross-file rule duplication).
- Tuning the similarity threshold itself (`_compute_section_similarity`'s
  existing threshold) — reuse it as-is unless implementation reveals it
  must change to avoid an unacceptable false-positive rate at
  cross-file scale, in which case flag this as a Plan Unknown rather than
  silently retuning it.

## Dependencies
None block this issue — it can proceed independently. The companion
documentation-remediation issue (filed the same day, titled "Deduplicate
governance rule text between documentation-policy.md and
documentation-checks.md") depends on this issue for full-corpus discovery
of further duplication beyond the 3 confirmed sections, though its own 3
confirmed locations can be remediated without waiting for this issue to
land.

## Unresolved Questions
Whether `_compute_section_similarity`'s existing similarity threshold
(tuned for within-file comparison, where sections often share intentional
per-area structural similarity — see the 10 existing "RAG"/"MCP"/"Agent"
etc. findings) produces an acceptable false-positive rate when applied
cross-file at full corpus scale (hundreds of files) — not verified in this
issue; the source memo's own examples (ADR section structure, "Related
Documents" section headings, which are near-identical *by design* across
many unrelated files) suggest a real risk of substantial noise if applied
naively to every section. Flagged for confirmation during plan creation —
the plan should explicitly re-run the extended check against the full
`docs/` tree and assess whether a stricter threshold, minimum body length,
or heading-name exclusion list (e.g. skip generic headings like "Related
Documents", "Keywords") is needed before this check can be treated as
useful signal rather than noise. This resolution path already has a
concrete implementation precedent to follow: `TestRegressionFullDocsTree`
in `tests/tools/test_check_docs_quality.py` (see Testing Expectations) —
extend or sibling that class rather than designing a new regression-check
mechanism.

## AI Implementation Instruction
Reuse `_extract_sections`/`_compute_section_similarity` unchanged — do not
reimplement section parsing or the similarity metric. Do not modify the
within-file check's existing behavior, message text, or finding count. Do
not touch `check_docs_content_policy.py` or any `docs/*.md` file. Before
finalizing, run the extended check against the full `docs/` tree (not only
the governance_01/governance_04 pair) and manually review the finding list
for the false-positive risk named in Unresolved Questions — if the noise
level is high, propose a mitigation (minimum body length, heading exclusion
list) in the implementation procedure rather than shipping an unusably
noisy check.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260920-115531
- **Related target files**: tools/check_docs_quality.py
