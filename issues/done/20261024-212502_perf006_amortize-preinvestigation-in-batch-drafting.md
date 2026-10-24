# Amortize Pre-Investigation Cost Across Batch Issue Creation

## Priority
Medium

## Summary
Add an explicit batch mode to the `issue-creator` workflow: when one source yields
multiple findings, run the pre-investigation against current source once per batch and
reuse its results across all drafts. Subsequent drafts reference recorded investigation
notes instead of re-reading sources.

## Background
Measured from opencode session history: 5 pure `issue-creator` sessions (sessions that
wrote only `issues/*.md` and made zero edits to scripts/tests/plans/implementations/docs),
34 issues total (confirmed by measurement). Cost is bimodal per batch:
- Pre-draft work averages 22.8 min per issue; the first issue of each batch took
  17.1 / 24.0 / 32.1 / 40.4 / 596.4 min before its first file write, while every
  subsequent issue in the same batch drafted in 0.0-3.1 min.
- A 21-issue batch spent 92% of its 650.6 active minutes before the first issue file
  was written (confirmed).
- Mid-batch re-investigation: one issue restarted investigation (7.0 min, 23 shell
  calls, 5 reads) for an area the same batch had already investigated (confirmed).
- Merge editing (integrating new findings into existing issue files) took 32.2 min in
  one observed case — 34 edits, 26 reads, 4 checker runs, scattered (confirmed).
Part of the perf001-perf005 measurement-driven performance series.

## Problem
The workflow defines no batch-level pre-investigation step and no reuse mechanism:
- Each draft re-verifies claims against source independently, so source re-reads recur
  mid-batch whenever investigation context is lost or compacted.
- Merge decisions against existing issues read full bodies broadly rather than triaging
  cheaply first.
- Merge execution (integrating a finding into an existing issue) has no procedure: reads,
  edits, and re-verification run scattered per edit instead of batched.
The collapse of subsequent-draft cost already happens informally when context carries the
investigation forward; nothing guarantees it.

## Reason for Change
The measurement corpus shows the payoff of reuse is large (subsequent drafts drop from
17-40+ min of pre-work to 0.0-3.1 min) but incidental — re-investigation and scattered
merge work reappear exactly where reuse failed. Formalizing the shared pass makes the
low marginal draft cost reproducible instead of context-dependent.

## Implementation Intent
- Add a batch-mode decision to Phase 1-2: when one source yields multiple findings, run
  one shared pre-investigation pass before any draft, verifying claims against current
  source once per file/claim group.
- Record the pass results as investigation notes reusable by every later draft in the
  batch; drafts cite the notes instead of re-reading sources, and a source re-read is
  allowed only for a claim the notes do not cover.
- Make the Phase 2 / Phase 4 integration check two-tiered: triage at the level of issue
  filenames/titles/summaries from the `issues/` listing; full-body reads only for issues
  that are merge candidates.
- Define a merge-edit procedure for integrations: one full read per existing issue
  targeted for a merge, all edits to that issue applied in one batch, structure
  re-verification run once after the batched edits rather than per edit.
- Preserve the existing multi-file sequential draft/verify/filename rules and Phase 9 /
  Phase 10 per-issue verification semantics — batch mode changes the pre-investigation
  stage only, not the write/verify order (the sequential rule exists so the filename
  uniqueness check sees each prior file).

## Target Files or Areas
- `skills/issue-creator/workflow.md` (Multi-file processing; Phase 1; Phase 2; Phase 4
  sibling-issue check)
- `skills/issue-creator/SKILL.md` (workflow overview, only if the step list changes)
- `rules/ai-execution.md` — only if the shared-rule placement question (see Unresolved
  Questions) resolves toward a cross-workflow rule

## Required Changes
- Add a batch-mode section to `workflow.md`: entry condition (one source yields multiple
  findings), the shared pre-investigation pass, the investigation-notes recording rule,
  and the note-reuse rule for subsequent drafts.
- Rewrite the Phase 2 / Phase 4 integration check as two-tier triage (listing-level
  first; full-body read only for likely merges).
- Add the merge-edit procedure (one read / batched edits / single re-verification) to the
  same section.
- Update `SKILL.md`'s step overview only if new required steps are introduced.

## Constraints
- MUST NOT weaken per-issue evidence verification: every claim in every issue stays
  evidence-backed or explicitly assumption-labeled per `skills/DESIGN.md` Evidence labels
  (Phase 9a).
- MUST NOT change Phase 10 filename-uniqueness behavior or the Multi-file processing
  sequential rule.
- MUST NOT introduce a new pipeline artifact type for investigation notes without an
  explicit placement decision (see Unresolved Questions).
- Preserve AGENTS.md stop-and-ask semantics for semantically incomplete requirements.

## Acceptance Criteria
- `workflow.md` defines batch mode with an entry condition, a shared pre-investigation
  pass, and a note-reuse rule that subsequent drafts explicitly reference instead of fresh
  source reads.
- The integration check is documented as two-tiered, with full-body reads restricted to
  issues identified as merge candidates by listing-level triage.
- The merge-edit procedure (one read / batched edits / single re-verification) is
  documented.
- Multi-file sequential processing, the Phase 9c checklist, and Phase 10 steps are
  unchanged, and the skills structure checker passes in both modes.

## Testing Expectations
Documentation-only change:
- Run `check_skills_structure.sh` in both modes.
- Verify payoff by replaying a small multi-issue batch under the new guidance and
  comparing the pre-investigation vs per-draft cost split against this issue's baseline
  numbers (follow-up measurement, not a unit test).

## Documentation Impact
The skill workflow files themselves are the documentation: batch-mode contract,
two-tier integration triage, and merge-edit procedure become new workflow guidance. If
perf001's shared-rule placement resolves toward `rules/ai-execution.md`, mirror the same
placement here for consistency.

## Out of Scope
- Step 0 mandatory-read trimming — absorbed by prompt cache; no action needed (same
  decision as all other issues in this series).
- `question` tool blocking policy — `perf005`.
- Re-read / turn-overhead rules for issue-to-plan and code-implementation — `perf001`;
  validation-sequence iteration — `perf004`; adversarial verification cost — `perf002`.
- Review-side investigation performed inside `python-code-review` when a review is the
  source; the 596.4-min pre-work of the 21-issue batch includes review-side work whose
  attribution is unconfirmed (see Unresolved Questions) — not changed here.
- Turning the ad-hoc session-measurement scripts into a production tool.

## Dependencies
- `perf001` — same theme (redundant re-reads / turn overhead) and the same open
  shared-rule placement question. Fix order: resolve placement in `perf001` first and
  apply it consistently here.
- `perf004`, `perf005` — same measurement corpus, no edit conflict (different target
  files).
- The target skill files churn frequently (remote commits touched them during the
  measurement period): re-anchor against current file content before editing.

## Unresolved Questions
- Where shared investigation notes live: session context only, or a durable artifact? If
  durable, which existing pipeline artifact carries them (avoid a new file type). Unknown.
- Batch-mode entry threshold: payoff is proven at 21 issues; marginal benefit at 2-3
  issues is unmeasured. Needs confirmation.
- Attribution of the 21-issue batch's 596.4-min pre-work between `python-code-review`
  investigation and `issue-creator` pre-work. Needs confirmation.
- Absolute minute figures are wall-clock estimates from part timings and include model
  generation time; treat them as approximate. The relative pattern (first-draft
  dominance, subsequent-draft collapse, mid-batch re-investigation) is confirmed.
- Shared-rule placement (workflow-local vs `rules/ai-execution.md`) — same open question
  as `perf001` / `perf005`.

## AI Implementation Instruction
Limit edits to the `issue-creator` skill files unless the placement question is resolved
toward `rules/ai-execution.md`. Do not renumber existing phases; do not modify Phase 9c
checklist items or Phase 10 steps. Re-anchor against current file content before editing —
these files change often. Do not implement tooling for investigation notes while the
notes-placement question is open. If the batch entry condition needs a numeric threshold
not provided here, stop and report rather than inventing one.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261024-212502
- **Related target files**: `skills/issue-creator/workflow.md`, `skills/issue-creator/SKILL.md`
