# Re-baseline docs/ inventory metrics before scoping documentation-slimming work

## Priority
High

## Summary
A proposed documentation-slimming policy's line/file-count analysis was performed
against a "connected/concatenated" snapshot of `docs/` that no longer matches the
current repository. Re-run the inventory directly against the current `docs/` tree
before any of that policy's scoping decisions (targets, line-count estimates,
prioritization) are trusted or acted upon.

## Background
N/A: covered by Summary.

## Problem
The proposal's foundational metrics (251 total documents; 175 with front matter / 76
without; 26,496 total lines; per-category deletion-candidate line estimates of
~2,300–2,600 lines) were checked against the current `docs/` tree and do not match:
`docs/` currently contains 185 `.md` files (across `docs/`, `docs/adr/`,
`docs/databases/`, `docs/eventbus/`), of which 184 already carry front matter and only
1 does not. The categorical analysis (which kinds of content are duplicated/mechanical)
still appears directionally valid on spot-check (e.g. the EventBus configuration-field
drift described in a related issue), but the file/line-count basis used to size and
prioritize the work is stale.

## Reason for Change
Scoping decisions, task-list line estimates, and "41 of 251 already migrated" framing
all derive from the stale count. Filing or sizing follow-up work (content-migration
issues, tool-work estimates) against these numbers risks under- or over-scoping the
actual remaining work, and the "76 files without attributable front matter" claim (used
to argue that per-file boundaries are unrecoverable from the connected file) does not
reflect current reality, where nearly every file already has front matter.

## Implementation Intent
Re-run the inventory directly against `docs/**/*.md` (not a separately maintained
"connected file" snapshot) using existing enumeration facilities (e.g.
`tools/_docs_consistency_lib.py`'s file-discovery helper, or an equivalent `find`/glob
pass), and recompute: total file count, front-matter coverage, target-template
adoption count, and a fresh estimate of mechanical-content line counts per category. Do
not reuse or trust the earlier "connected file"-derived figures for any further
planning.

## Target Files or Areas
`docs/` (all files, read-only for this issue). No specific file is modified by this
issue itself — its output is a corrected inventory used to re-scope follow-up issues.

## Required Changes
- Enumerate all `docs/**/*.md` files and record: total count, front-matter
  presence/absence per file, and (if practical) the target-template (Purpose / Design
  Intent / Responsibility Boundary / Key Constraints / Operational Notes / Known
  Limitations) adoption count.
- Recompute a fresh, current-state estimate for each mechanical-content category
  (default-value restatement, field/type lists, API signature tables, file/structure
  listings, config-file inventory tables, CLI command listings, environment-setup
  steps, DDL/schema blocks) — a rough line-count band is sufficient; exhaustive
  per-line classification is not required.
- Record the corrected figures somewhere reusable (e.g. an updated version of the
  original slimming-policy note, or a fresh short note) so downstream issues cite the
  corrected numbers, not the stale ones.

## Constraints
Do not delete or edit any `docs/` content as part of this issue — it is inventory-only.

## Acceptance Criteria
- A current file count, front-matter-coverage count, and template-adoption count for
  `docs/**/*.md` are recorded and independently reproducible (state the exact command
  used).
- Any prioritization or line-count estimate published for the broader slimming
  initiative going forward cites these corrected figures, not the original
  "251/175/76/26,496" figures.

## Testing Expectations
Not required — this is an analysis/inventory task with no code or documentation
behavior change.

## Documentation Impact
If the original slimming-policy note is kept as a living artifact, its summary/metrics
sections should be corrected to the newly-measured values; if it is not a tracked
document, no `docs/*.md` update is required.

## Out of Scope
Performing the actual content migration/deletion work described by the broader
slimming initiative — that is scoped by separate issues once this re-baseline is
complete.

## Dependencies
Blocks accurate scoping of any follow-up "content migration" issues for the slimming
initiative (not yet filed, pending this re-baseline).

## Unresolved Questions
N/A: none — the discrepancy and the corrective action are both directly confirmed
against the current repository.

## AI Implementation Instruction
Re-measure only; do not delete or rewrite any `docs/` content in this issue. Use a
reproducible command (record it) rather than a one-off manual count. Do not assume the
categorical findings (e.g. the EventBus config-field drift) are also stale — they were
independently spot-checked and confirmed current as of this issue's filing.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260918-130014
- **Related target files**: docs/
