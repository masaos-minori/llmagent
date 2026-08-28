# Plan Output Template (Canonical)

Use this exact Markdown structure when generating `plans/{timestamp}_plan.md` in the
`issue-to-plan` workflow (see `skills/issue-to-plan/workflow.md` Step 5). Do not omit
any section. Write every section's body text in English, regardless of the chat
language (see `skills/issue-to-plan/SKILL.md` Core Execution Rules).

```markdown
## Goal
- [Clear statement of what the program will achieve and what problem it solves]

## Priority
High / Medium / Low

## Scope
- **In-Scope**: [List of explicit items to be implemented]
- **Out-of-Scope**: [List of items explicitly excluded from this task]

## Background
[Why this requirement exists]

## Problem
[The concrete problem being solved]

## Reason for change
[Why this change is needed now]

## Implementation intent
[High-level approach, without prescribing exact code]

## Requirements
- `REQ-001`: [...]
- `REQ-002`: [...]

## Implementation Target Files
**Freeze status**: Draft (set to `Frozen` only once `issue-to-plan` Step 8's
Implementation Target Files Validation passes — see `rules/workflow-lifecycle.md`
Implementation Target Files Validation (Plan Freeze)).

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| | | | | | | |

Rules (see `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan
Freeze) for the full validation procedure):
- One row per file. A directory, glob pattern (`*`, `**`), component/module name, file
  group, or a vague phrase (e.g. "related files", "as necessary", "etc.") MUST NOT
  appear as a row — list each file individually by its exact repository-relative path.
- Record a test, configuration, schema, migration, deployment, or documentation file as
  its own row when it requires modification — do not fold it into the row for the
  source file it accompanies.
- `Validation Status` is `Verified` or `Needs confirmation` per row; every row must be
  `Verified` before this section may be marked `Frozen`.

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same
one-file-per-row discipline as `Implementation Target Files` above — no directories,
glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| | | |

## Acceptance criteria
[Verifiable completion criteria, each referencing a Requirement ID]

## Tests
[Testing expectations, each referencing a Requirement ID]

## Documentation Impact
[State whether `docs/*.md` must be updated for this Plan, and which Requirement(s)
drive it. Name the target doc via `docs/00_index.md`'s "Document References by Task"
table (or `routing.md` Docs → task mapping for new modules) — do not hardcode doc
filenames here, they change as docs are split. Use `N/A: {short reason}` if no doc
requires updating.]

## Assumptions
- [List any technical or domain assumptions made during analysis]

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | | | | |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| | | | | | |

## Design
[Architecture/design decisions, grounded in Step 5 analysis]

## Implementation steps
Each step description MUST cite the exact file path(s) it touches by referencing rows
of `Implementation Target Files` above — do not restate file-level detail
independently of that frozen table.

1. **Phase 1: Preparation / Refactoring (if needed)**
   - [ ] Step description (Requirement ID; File Path from Implementation Target Files)
2. **Phase 2: Core Logic Implementation**
   - [ ] Step description (Requirement ID; File Path from Implementation Target Files)
3. **Phase 3: Deployment & Verification**
   - [ ] Step description (Mandatory: include deployment validation/scripts check;
     Requirement ID; File Path from Implementation Target Files)

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| | | | |

## Risks
- **Risk**: [Description] → **Mitigation**: [Description]

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| — | — | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: {path}
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: {timestamp}
- **Related target files**: {paths} — the full list of `File Path` values from
  `Implementation Target Files` above, once `Frozen`

### Requirement Traceability
See `templates/requirement-traceability.md` for the canonical column format.
```

## Notes on filling "Implementation Target Files" and "Reference Files"

See `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan Freeze)
for the full validation procedure (what "exists", "requires modification", "has
supporting evidence", and "linked to a Plan requirement" mean per row, and how the
section is marked `Frozen`). Populate these two sections from `issue-to-plan`
`workflow.md` Step 3's inspection findings — a file inspected only to confirm current
behavior or a dependency belongs in `Reference Files`, not `Implementation Target
Files`.

## Notes on filling "Affected areas"

Populate Churn/Bus Factor from the workflow's Step 5 historical analysis and Blast
Radius from Step 5's dependency graphing — mark `N/A` if Path A skipped that analysis.
Fill `deploy.sh Impact` per `skills/DESIGN.md` Change-impact table — always state it
explicitly. Naming the target doc for a required documentation update belongs in the
"Documentation Impact" section above, not here.
