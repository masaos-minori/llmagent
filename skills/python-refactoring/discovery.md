# Python Refactoring — Discovery Vocabulary, Technical Debt, Drift, Responsibility

Load this file at Step 2 (unconditionally — applies to every Path A/B/C target file).
It defines the vocabulary and investigation subsections used throughout Steps 2-10.

---

## Discovery Vocabulary

While investigating the target file (Steps 2-10), use these six states to record what is
observed without expanding the approved change scope:

- **Finding**: an evidence-based observation of a concrete problem (e.g. duplicate logic,
  unclear ownership) recorded per the Finding record schema (see Technical Debt
  Discovery below). Requires a populated `evidence` field.
- **Candidate**: a Finding assessed as potentially actionable, not yet evaluated for
  approval.
- **Proposal**: a behavior-changing idea surfaced during work on the target file. This is
  the same concept as, and must use, the existing "Proposals not implemented" format defined
  in `report-template.md` (Title / Reason / Behavior risk / Affected files / Suggested
  follow-up issue / Recommended validation) — this section does not define a second
  Proposal format.
- **Approved Change**: a change explicitly authorized for this refactoring cycle; only an
  Approved Change may be transformed in `workflow.md` Step 6.
- **Blocked**: a Finding, Candidate, or Proposal that cannot be evaluated further without
  additional evidence or a decision outside this workflow's scope.
- **Not Applicable**: a Finding, Candidate, or Proposal determined, after evaluation, not to
  apply to the current target file or refactoring cycle.

Discovery (Finding, Candidate, Proposal) does not authorize implementation — only an
Approved Change may be transformed in `workflow.md` Step 6. This does not weaken or
replace `workflow.md` Step 2's rule that any `Expected behavior change` other than `none`
must stop work and be recorded under `Proposals not implemented`; that rule continues to
apply unchanged.

An unapproved Path C idea is a Proposal only, per the Proposal state defined above (added
per `implementations/20260826-155803_01_prompts_04_refactor.md.md` `REQ-001`); it must not
be transformed in Step 6 until it becomes an Approved Change per this same section's rule
that only an Approved Change may be transformed in Step 6 — see `path-c.md` for the full
approval checklist a Path C idea must satisfy before it becomes an Approved Change.

---

## Technical Debt Discovery (Step 3)

Applies regardless of Path A/B/C classification (lightweight and report-only; not subject
to `path-a.md`/`path-b.md`/`path-c.md`'s tooling-depth rules).

While reading the target file, record a Finding (see Discovery Vocabulary above) for
observations in these six categories only:
- Duplicate logic
- Duplicate validation
- Unclear ownership
- Excessive indirection
- Responsibility concentration
- Testability concerns

Every Finding must record all six fields:
- **ID**: a short unique identifier for this Finding within the cycle
- **Category**: one of the six categories above
- **Severity**: `Critical` / `High` / `Medium` / `Low` / `Informational`, per
  `skills/python-code-review/SKILL.md` Severity
- **Evidence**: a concrete repository location — file path and line range, or a command and
  its output. A Finding with no populated evidence field must not be recorded.
- **Impact**: the concrete consequence if left unaddressed
- **Recommendation**: what a future Approved Change could do about it — recording the
  recommendation does not authorize acting on it now

Recording a Finding here never authorizes implementing it in this cycle.

---

## Responsibility Analysis (Step 3)

Applies regardless of Path A/B/C classification, for the same reason as Technical Debt
Discovery above.

For each function/class in the target file, record:
- **Responsibilities**: what it is accountable for
- **Dependencies**: what it relies on
- **Side effects**: what it does beyond its return value (see `validation.md` Side-Effect
  Inventory for the full inventory)
- **State ownership**: what state it owns or mutates
- **Branching**: its decision points

When this analysis identifies a split candidate (a function/class whose responsibilities
should be divided), report it using the Proposal format (Discovery Vocabulary above) — do
not implement the split automatically. This is the same "discovery does not authorize
implementation" rule applied specifically to split candidates.

---

## Documentation Drift Detection (Step 3)

Applies regardless of Path A/B/C classification (uniform across all paths; does not
reference Path classification).

While investigating the target file (Steps 2-10), compare relevant implementation
details against these seven document sources: `routing.md`, `AGENTS.md`, README,
design documents, coding and toolchain rules, configuration specifications, deployment
definitions. For "design documents," use `docs/00_index.md`'s "Document References by
Task" table to locate the documents actually governing the target file's behavior,
rather than scanning all of `docs/*.md`.

Record each discovered discrepancy as a Drift Finding with exactly six fields — a
Drift Finding with any field unpopulated must not be recorded:
- **Document**: the document source compared against (one of the seven above)
- **Implementation evidence**: a concrete repository location — file path and line
  range, or a command and its output
- **Drift description**: what the document says versus what the implementation
  actually does
- **Confidence**: `Unverified`, `Ambiguous Source of Truth`, or one of
  `rules/coding.md`'s five "Current behavior" categories (see below)
- **Possible source of truth**: which of the document or the implementation is likely
  authoritative, once confidence supports a choice
- **Suggested follow-up**: what a future Approved Change or documentation update could
  do about it — recording it here does not authorize acting on it now

When evidence is sufficient to decide, populate "possible source of truth" and
"suggested follow-up" using `rules/coding.md`'s existing five-category "Current
behavior" classification (Accepted current specification / Implementation fix required
/ Documentation fix required / Issue already tracked / Obsolete and removable) directly
— this subsection does not define a second, parallel classification.

When evidence is not yet sufficient to select one of the five categories, classify the
Drift Finding's confidence as one of two pre-classification states instead. These two
states are additions to, not replacements for, the five-category system:
- **Unverified**: the drift claim itself cannot yet be confirmed from available
  evidence.
- **Ambiguous Source of Truth**: evidence confirms a discrepancy but does not indicate
  which of the document or the implementation is authoritative.

A Drift Finding classified `Ambiguous Source of Truth` must NOT be auto-resolved via
`rules/coding.md`'s "ambiguous cases default to Implementation fix required" rule —
that default is calibrated for authoring a single `docs/*.md` note about an
already-known gap, not for a drift-detection process spanning a wider, more
consequential document set (deployment definitions, toolchain rules, routing, etc.). An
`Ambiguous Source of Truth` finding requires explicit maintainer confirmation — via the
sign-off channel defined in `rules/coding.md` "Explicit sign-off gates," or the unified
Proposal mechanism above — before it is routed into one of the five categories. This is
a documented, deliberate divergence from `rules/coding.md`'s default-ambiguous
behavior, scoped only to this Documentation Drift Detection section;
`rules/coding.md`'s own default continues to apply unchanged everywhere else.

Documentation Drift Detection does not modify any document: no automatic edit to
`docs/*.md`, `routing.md`, `AGENTS.md`, README, design documents, coding/toolchain
rules, configuration specifications, or deployment definitions. Any suggested
documentation change is recorded using the existing `report-template.md` "Proposals not
implemented" format (Title / Reason / Behavior risk / Affected files / Suggested
follow-up issue / Recommended validation) — the same format this workflow already uses
for behavior-changing ideas — never applied directly during Step 3.

If a listed comparison target has no corresponding file in the repository (e.g. no
repository-root `README.md` as of this writing), skip that target for the current
cycle — do not fabricate a comparison, and do not record a Drift Finding for the
target's mere absence. A missing document is a documentation-completeness question
outside this section's scope (comparing an existing document's claims against the
implementation), not a drift between the two.
