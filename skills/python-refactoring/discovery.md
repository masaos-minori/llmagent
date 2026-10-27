# Python Refactoring — Discovery Vocabulary, Technical Debt, Drift, Responsibility

Load this file at Step 2 (unconditionally — applies to every Path A/B/C target file);
`workflow.md` Step 0 deliberately does not list it.
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
- **Proposal**: a behavior-changing idea surfaced during work on the target file; MUST use
  the `report-template.md` "Proposals not implemented" format (no second format).
- **Approved Change**: a change explicitly authorized for this refactoring cycle; only an
  Approved Change may be transformed in `workflow.md` Step 6.
- **Blocked**: a Finding, Candidate, or Proposal that cannot be evaluated further without
  additional evidence or a decision outside this workflow's scope.
- **Not Applicable**: a Finding, Candidate, or Proposal determined, after evaluation, not to
  apply to the current target file or refactoring cycle.

Finding, Candidate, and Proposal never authorize implementation; only an Approved Change may be
transformed in `workflow.md` Step 6. `workflow.md` Step 2's stop rule (`Expected behavior
change` other than `none`) is unchanged. An unapproved Path C idea is a Proposal only; the
approval checklist is in `path-c.md`.

---

## Technical Debt Discovery (Step 3)

Every Path; report-only, not subject to the `path-*.md` tooling-depth rules. While reading the
target file, record a Finding for these six categories only:
- Duplicate logic
- Duplicate validation
- Unclear ownership
- Excessive indirection
- Responsibility concentration
- Testability concerns

Every Finding records all six fields (a Finding without `Evidence` MUST NOT be recorded):
- **ID**: short unique identifier within the cycle
- **Category**: one of the six above
- **Severity**: `skills/DESIGN.md` Severity levels
- **Evidence**: file path and line range, or a command and its output
- **Impact**: consequence if left unaddressed
- **Recommendation**: what a future Approved Change could do (does not authorize acting now)

---

## Responsibility Analysis (Step 3)

Every Path. For each function/class in the target file, record:
- **Responsibilities**: what it is accountable for
- **Dependencies**: what it relies on
- **Side effects**: beyond its return value (`validation.md` Side-Effect Inventory)
- **State ownership**: what state it owns or mutates
- **Branching**: its decision points

A split candidate is reported as a Proposal; MUST NOT implement the split automatically.

---

## Documentation Drift Detection (Step 3)

Every Path, scaled: Path A compares only documents that directly mention the target module or
its public symbols (`rg -l "<module or symbol>" docs/ routing.md AGENTS.md rules/ config/`);
Path B and C compare all seven sources: `routing.md`, `AGENTS.md`, README, design documents,
coding and toolchain rules, configuration specifications, deployment definitions. Locate design
documents via `docs/00_index.md`'s "Document References by Task" table, not by scanning
`docs/*.md`.

Record each discrepancy as a Drift Finding with exactly six fields (none may be unpopulated):
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

Confidence and classification:

| Evidence state | Confidence value |
|---|---|
| Sufficient to decide | one of `rules/coding.md`'s five "Current behavior" categories (Accepted current specification / Implementation fix required / Documentation fix required / Issue already tracked / Obsolete and removable); populate "possible source of truth" and "suggested follow-up" from it |
| Drift claim cannot yet be confirmed | `Unverified` |
| Discrepancy confirmed, authoritative side unclear | `Ambiguous Source of Truth` |

`Ambiguous Source of Truth` MUST NOT be auto-resolved by `rules/coding.md`'s "ambiguous cases
default to Implementation fix required" rule (calibrated for a single `docs/*.md` note, not for
drift across deployment definitions, toolchain rules, routing, etc.). It needs explicit
maintainer confirmation (`rules/coding.md` "Explicit sign-off gates", or a Proposal) before it
is routed into one of the five categories. This divergence is scoped to this section only.

Drift Detection edits no document. A suggested documentation change is recorded as a
`report-template.md` "Proposals not implemented" entry and MUST NOT be applied in Step 3.

A listed target with no file in the repository (e.g. no root `README.md`) is skipped: MUST NOT
fabricate a comparison or record a Drift Finding for the absence itself.
