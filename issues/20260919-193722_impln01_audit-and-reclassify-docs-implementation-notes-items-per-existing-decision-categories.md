# Audit and reclassify docs/*.md "## Implementation Notes" items per the existing Decision Categories policy

## Priority
Medium

## Summary
Audit every `## Implementation Notes` bullet across `docs/*.md` (20 files currently
carry this section, 14 of them ADRs) against
`docs/00_governance_02_documentation-metadata.md`'s existing "Decision Categories" table
(Delete / Compress / Replace with Source Reference / Retain / Move to Known Issues / Move
to Needs Confirmation), and reclassify each item accordingly — deleting mechanically
verifiable trivia, promoting design-rationale items to the ADR or main design body,
moving implementation/design mismatches to Known Issues, and moving unresolved-intent
items to the Needs Confirmation Inventory. Also decide, and record the decision here,
whether a supporting tool should be built to help detect candidates for reclassification.

## Background
Filed from a user request (`memo3.md`) describing 4 classification buckets for
`Implementation Notes` content, closely mirroring criteria already codified in
`docs/00_governance_02_documentation-metadata.md`'s "Guidelines for Recording Information
Verifiable via Implementation Reference" section (added in a prior session):

| Bucket (memo3.md wording) | Existing policy equivalent |
|---|---|
| 削除 (file/line/function-name-describable, unambiguous from source, easily stale, mere execution order) | `Delete` / `Compress` rows — "verifiable from code... alone; changes only when the code changes; a wrong statement is caught by execution, not review" |
| ADRまたは設計本文へ昇格 (explains why an order matters; breaking it risks data corruption/security; multiple implementations must honor it; should survive refactoring) | `Retain` row — "Design intent and reasons", "Correlated constraints and their rationale", "Security-boundary defaults and why" |
| Known Issueへ移動 (design/implementation mismatch; unclear if intentional or a bug; implementation is provisional) | `Move to Known Issues` row |
| Needs Confirmationへ移動 (basis for a value/behavior is unknown; behavior is visible in code but designer intent is not) | `Move to Needs Confirmation` row |

This issue applies that **existing** policy to `Implementation Notes` sections
specifically, rather than defining new classification criteria — the criteria already
exist; they have not yet been systematically applied to this section type.

A quick sample already surfaced a concrete promotion candidate:
`docs/04_mcp_01_system_overview.md`'s Implementation Notes states `record_degraded()`
does not overwrite `UNAVAILABLE`/`HALF_OPEN` state "to avoid breaking the circuit breaker
and trial window" — this is a rationale statement (why, and what breaks if violated), which
per the `Retain` criteria belongs in the design body rather than a code-derived
Implementation Notes bullet.

## Problem
`Implementation Notes` sections were populated ad hoc across `docs/*.md` without applying
the classification criteria `docs/00_governance_02_documentation-metadata.md` now defines.
Some items are pure code trivia (candidates for deletion), some carry real design
rationale that is at risk of being lost or overlooked because it is filed under
"Implementation Notes" instead of the ADR/design body where a reader would expect to find
binding constraints, and some may describe stale implementation/design mismatches that
belong in the Known Issues inventory (`docs/00_governance_03_issue-and-uncertainty-management.md`
Part 1) instead.

## Reason for Change
Misfiled rationale under "Implementation Notes" is easy to overlook during design review
(a reviewer checking ADR/design-body constraints would not think to also check
Implementation Notes for binding rules) and easy to lose during future documentation
slimming passes that target Implementation Notes as inherently disposable
implementation-reference content. Correctly bucketing each item prevents both failure
modes.

## Implementation Intent
For each of the 20 `docs/*.md` files carrying `## Implementation Notes`, read every bullet
and classify it against `docs/00_governance_02_documentation-metadata.md`'s Decision
Categories table. Apply the corresponding action per bullet:
- `Delete`/`Compress`: remove or shorten in place.
- `Retain` (promote): move the content into the file's own design body, or — for an ADR
  file — into its `## Rationale`/`## Invariants` section, per `docs/00_governance_01_documentation-policy.md`'s
  ADR Section Header Standardization; do not leave a duplicate copy in both places.
- `Move to Known Issues`: file a new entry per `docs/00_governance_03_issue-and-uncertainty-management.md`
  Part 1's Entry Template, then remove the item from Implementation Notes (or replace with
  a short cross-reference).
- `Move to Needs Confirmation`: file a new entry per that same document's Part 2 Inventory
  Entry Fields, then remove or cross-reference from Implementation Notes.
Do this per-file rather than as one giant sweep, since each file's context is needed to
classify its own items correctly — a Path A/B split by file count is appropriate once this
issue reaches `issue-to-plan`.

Separately, and before deciding whether to build a tool, note that these 4 buckets are not
equally automatable:
- `Delete`/`Compress` candidates are the most mechanically detectable — largely the same
  signal `tools/check_docs_content_policy.py`'s existing mechanical-content checks already
  target (bare file/line/function citations, no rationale keyword like "because"/"to
  avoid"/"必要"/"why").
- `Retain` (promotion), `Known Issues`, and `Needs Confirmation` classification require
  semantic judgment (does this explain *why*, is a mismatch intentional or a bug, is intent
  actually unknown) that cannot be reliably automated with pattern matching alone.
Given this asymmetry, a full auto-classifier is not recommended. A lighter **inventory
tool** is: one that walks `docs/*.md`, extracts every `## Implementation Notes` bullet
into a flat list (file, line, text), and flags likely `Delete`/`Compress` candidates via
a heuristic (e.g. presence/absence of a rationale keyword, or a bare `(Explicit in code,
<path>)` citation with no accompanying "why") for human/AI triage — leaving the other 3
buckets to manual/AI classification per bullet. This mirrors the existing
`tools/check_needs_confirmation_inventory.py`'s role (inventory + registration-consistency
check, not automatic resolution) and would be reusable for future documentation-slimming
passes, not just this one-off audit. Whether to build this tool, versus doing the one-off
audit by hand/AI without it, is a decision for whoever picks up this issue's Path A/B sizing
— record the decision in the resulting Plan.

## Target Files or Areas
- The 20 files currently carrying `## Implementation Notes`: 14 ADRs under `docs/adr/`
  (`ADR-001` through `ADR-010`, `ADR-012` through `ADR-015` — `ADR-011` is retired/merged
  and carries no such section; verify current list with
  `grep -rl "^## Implementation Notes" docs/adr/*.md` at execution time) and 6 non-ADR
  design docs (`docs/03_rag_04_02_dto-models_result.md`, `docs/03_rag_04_04_dto-models_config.md`,
  `docs/03_rag_04_05_dto-types.md`, `docs/03_rag_05_3-logging.md`,
  `docs/03_rag_05_4-error-handling-reference.md`, `docs/04_mcp_01_system_overview.md`, plus
  any others matching the same grep at execution time).
- `docs/00_governance_02_documentation-metadata.md` (Decision Categories — read-only,
  reference for classification).
- `docs/00_governance_03_issue-and-uncertainty-management.md` (Known Issues / Needs
  Confirmation entry templates — modified only to add new entries discovered by this
  audit).
- Conditionally, a new tool under `tools/` — only if the Plan decides to build the
  inventory tool described in Implementation Intent above.

## Required Changes
- Enumerate every `docs/*.md` file with a `## Implementation Notes` section (re-run the
  grep above at execution time — the list may have grown since this issue was filed).
- For each file, classify every bullet against the 4 Decision Categories buckets and apply
  the corresponding action (delete/compress in place, promote to design body or ADR
  section, file a Known Issue entry, or file a Needs Confirmation entry).
- Decide whether to build the inventory-assist tool described above; record the decision
  and rationale in the resulting Plan.

## Constraints
Apply the existing `docs/00_governance_02_documentation-metadata.md` Decision Categories
criteria as-is — do not invent a parallel classification scheme. Do not delete a bullet
whose classification is ambiguous without first checking whether it should instead move to
Known Issues or Needs Confirmation (ambiguity about design/implementation mismatch is
itself a signal for one of those two buckets, not for silent deletion).

## Acceptance Criteria
- Every bullet in every `docs/*.md` file's `## Implementation Notes` section (as of the
  Plan's own Frozen file list) has been classified into exactly one of the 4 buckets and
  the corresponding action applied.
- No content is lost: a promoted item appears in its new location (design body/ADR
  section) with the Implementation Notes copy removed (or replaced with a short
  cross-reference, not a duplicate); a Known-Issues/Needs-Confirmation item has a
  corresponding registered entry.
- `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py`,
  and `uv run python tools/check_adr_structure.py` report no new findings.
- If a Needs Confirmation or Known Issue marker was added, `uv run python tools/check_needs_confirmation_inventory.py`
  passes.
- The tool-vs-manual decision from Implementation Intent is explicitly recorded (built, or
  explicitly decided against, with reasoning) — not silently skipped.

## Testing Expectations
Not required for behavior — this is a documentation reclassification. If the inventory
tool described above is built, it needs unit tests per `routing.md`'s "Adding a new tool"
validation sequence (ruff, mypy, bandit, smoke test against real `docs/` content).

## Documentation Impact
This issue's entire scope is a documentation reclassification across up to 20 `docs/*.md`
files, plus possibly a new `docs/00_governance_03_issue-and-uncertainty-management.md`
entries for anything moved to Known Issues/Needs Confirmation. No other documentation
impact.

## Out of Scope
Defining new classification criteria (the criteria already exist in
`docs/00_governance_02_documentation-metadata.md`) — this issue only applies them.
Auditing sections other than `## Implementation Notes` (e.g. a design doc's main body,
`## Known Limitations`, or ADR `## Known Deviations`) even if similar drift may exist
there — track separately if found.

## Dependencies
N/A: none.

## Unresolved Questions
Whether to build the inventory-assist tool, or classify all 20 files' bullets by hand/AI
without it, is left as a sizing decision for the Plan (Path A vs. Path B), not resolved
here — see Implementation Intent's asymmetric-automatability reasoning.

## AI Implementation Instruction
When this issue reaches `plan-to-implementation-procedure`, process one `docs/*.md` file
per implementation procedure row rather than batching several files' Implementation Notes
edits into one row — each file's classification decisions are independent and reviewable
separately. Do not reclassify content outside `## Implementation Notes` sections even if
similar issues are noticed there; file a separate issue instead. Re-verify the file list in
Target Files or Areas at execution time rather than trusting this issue's snapshot, since
new `Implementation Notes` sections may have been added since this issue was filed.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260919-193722
- **Related target files**: docs/adr/ADR-001-workflow-engine-mandatory.md, docs/adr/ADR-002-config-isolation.md, docs/adr/ADR-003-runtime-tool-registry-routing-authority.md, docs/adr/ADR-004-environment-failure-handling-policy.md, docs/adr/ADR-005-rag-source-derived-index-relationships.md, docs/adr/ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md, docs/adr/ADR-007-http-mcp-adoption-and-stdio-non-support.md, docs/adr/ADR-008-sqlite-4db-separation.md, docs/adr/ADR-009-rag-ft5-text-separation.md, docs/adr/ADR-010-rag-fallback.md, docs/adr/ADR-012-git-mcp-server-side-write-enforcement.md, docs/adr/ADR-013-eventbus-authentication-authorization.md, docs/adr/ADR-014-agent-control-plane-responsibility-boundaries.md, docs/adr/ADR-015-reference-document-class-disposition.md, docs/03_rag_04_02_dto-models_result.md, docs/03_rag_04_04_dto-models_config.md, docs/03_rag_04_05_dto-types.md, docs/03_rag_05_3-logging.md, docs/03_rag_05_4-error-handling-reference.md, docs/04_mcp_01_system_overview.md, docs/00_governance_02_documentation-metadata.md, docs/00_governance_03_issue-and-uncertainty-management.md
