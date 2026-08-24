# Plan Output Template (Canonical)

Use this exact Markdown structure when generating `plans/{timestamp}_plan.md` in the
`issue-to-plan` workflow (see `skills/issue-to-plan/workflow.md` Step 5). Do not omit
any section.

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

## Acceptance criteria
[Verifiable completion criteria, each referencing a Requirement ID]

## Tests
[Testing expectations, each referencing a Requirement ID]

## Assumptions
- [List any technical or domain assumptions made during analysis]

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | | | | |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns:

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| | | | | | |

## Design
[Architecture/design decisions, grounded in Step 5 analysis]

## Implementation steps
1. **Phase 1: Preparation / Refactoring (if needed)**
   - [ ] Step description (Requirement ID)
2. **Phase 2: Core Logic Implementation**
   - [ ] Step description (Requirement ID)
3. **Phase 3: Deployment & Verification**
   - [ ] Step description (Mandatory: include deployment validation/scripts check)

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
- **Related target files**: {paths}

### Requirement Traceability
See `templates/requirement-traceability.md` for the canonical column format.
```

## Notes on filling "Affected areas"

Populate Churn/Bus Factor from the workflow's Step 5 historical analysis and Blast
Radius from Step 5's dependency graphing — mark `N/A` if Path A skipped that analysis.
Fill `deploy.sh Impact` per `skills/DESIGN.md` Change-impact table — always state it
explicitly. If documentation must be updated, name the target doc via
`docs/00_index.md` Task-specific document reference (or `routing.md` Docs → task
mapping for new modules) — do not hardcode doc filenames here, they change as docs are
split.
