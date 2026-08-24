---
name: issue-to-plan
description: |
  Use this skill PROACTIVELY when converting a raw, unformatted issue
  (`issues/*.md`) directly into a concrete Python implementation plan
  (`plans/*.md`), with no standalone requirement document in between.
  Covers: verifying the issue's claims against current source, deciding
  whether the issue is already resolved or too vague to act on, task-size
  classification (Path A/B), architecture/dependency/historical analysis,
  operational dependency inspection, validation quality analysis, and
  uncertainty tracking.
  Use when the task needs scope definition, affected files, implementation
  steps, test strategy, risks, assumptions, unknowns, or execution
  sequencing before coding — starting directly from a raw issue.
---

# Issue To Plan Skill

## Purpose

Turn a raw issue directly into a concrete, reviewable implementation plan: verify the
issue's claims against current source, then ground the plan in architecture analysis and
historical data. No standalone requirement document is produced — evidence verification
and planning happen in one continuous cycle. Document-only — see `skills/DESIGN.md`
Analysis-only phase constraint; this skill's only writes are the plan document in
`plans/`, optional `issues/{timestamp}_unknowns.md` / `issues/{timestamp}_risks.md`
files, and moving the processed issue file to `issues/done/`. It must not modify source
code files or `docs/*.md`.

---

## Phase overview

| Step | Name | Goal / AI Action |
|---|---|---|
| 0 | Load required instructions | Read routing, rules, templates, and this skill before starting. |
| 1 | Identify target Issues | Confirm every specified `issues/{filename}.md` path exists before starting any processing. |
| 2 | Assess the current Issue | Read the Issue in full, verify its claims against current source, and classify each extracted item's evidence basis. If already resolved or no longer applicable, stop and report — do not write a Plan. |
| 3 | Inspect related files | Classify the Issue as Path A or Path B (see Routing below), then inspect related source, tests, config, and docs at the depth Path A/B calls for. |
| 4 | Map Issue information to Plan information | Build an explicit mapping from every extracted Issue item to its Plan destination before writing anything. |
| 5 | Create the Plan | Apply Path B's broader analysis if applicable, then generate `plans/{timestamp}_plan.md` with stable Requirement IDs. |
| 6 | Analyze Unknowns and Risks | Resolve what evidence allows; file unresolved blocking items as issues. |
| 7 | Add Traceability | Fill the canonical Traceability fields and the per-Requirement Requirement Traceability table. |
| 8 | Validate information completeness | Confirm no Issue information was dropped and every Requirement ID is traceable. |
| 9 | Validate and await approval | Report and stop — do not move the Issue in the same response. |
| 10 | Move the Issue after approval | `git mv` only, after explicit approval; no fallback. |

See `workflow.md` for the detailed per-step procedure, toolchain, and multi-file
processing rules.

---

## Routing (AI Task Size Assessment)

Before proceeding to any analysis step, execute **Step 3's classification** (this
skill's task-size assessment, carried forward unchanged from this skill's
predecessor). Assess the current Issue against the following criteria to determine the
execution path.

### [Path A] Small Task
**Criteria (Must satisfy ALL):**
- [ ] Affects ≤ 3 files
- [ ] No public or runtime-facing interface changes
- [ ] No database schema changes

**Execution Path:**
Perform Step 3's direct-verification inspection only (no architecture/dependency/
historical/operational analysis) → establish the Step 6-equivalent validation quality
baseline in Step 5 → Steps 6-10 run unconditionally.

### [Path B] Large Task
**Criteria (Satisfies ANY):**
- [ ] Affects > 3 files
- [ ] Creates a new module or package
- [ ] Changes a public/runtime interface
- [ ] Modifies or adds a database schema

**Execution Path:**
Perform Step 3's full inspection, then Step 5's full analysis (architecture, dependency
graphing, historical analysis, operational dependency inspection, validation quality
analysis). Do not skip any analysis.

> **IMPORTANT — Tool Availability Guard (For AI):** applies to `pydeps`, `radon`,
> `semgrep` and any other tool used in `workflow.md` — see `skills/DESIGN.md` Tool
> availability guard.

---

## Core Execution Rules (Strictly Enforced)

- **No Guesswork**: Verify the Issue's factual claims (affected files, whether the
  described problem still reproduces) against current source before writing anything.
  Every file listed in "Affected Areas" must be verified to exist via environment
  tools — do not guess filenames or directory structures.
- **Isolate Unknowns**: If you lack context or code access to answer a question, mark it
  as `BLOCKING: True` in Step 6 and ask the user for clarification before generating the
  final implementation steps.
- **Incrementalism**: Design the implementation steps in small, reviewable increments.
  Each step must leave the codebase in a testable state.
- **One Issue at a time**: see `workflow.md` Multi-file processing.
- **Mandatory move**: see `workflow.md` Step 10. Do not skip it.
- Out-of-scope paths: see `skills/DESIGN.md` Out-of-scope paths.
- Exception to `skills/DESIGN.md` Output language: write the Plan and any Unknown/Risk
  issue files in clear and concise English (this skill's output feeds directly into
  `python-implementation` / `python-refactoring` for AI consumption).

---

## Output format

Generate `plans/{timestamp}_plan.md` using this exact Markdown structure. Do not omit
any sections.

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

Notes on filling "Affected areas": populate Churn/Bus Factor from Step 5's historical
analysis and Blast Radius from Step 5's dependency graphing — mark `N/A` if Path A
skipped that analysis. Fill `deploy.sh Impact` per `skills/DESIGN.md` Change-impact
table — always state it explicitly. If documentation must be updated, name the target
doc via `docs/00_index.md` Task-specific document reference (or `routing.md` Docs → task
mapping for new modules) — do not hardcode doc filenames here, they change as docs are
split.

## See Also
See `workflow.md` for detailed phase content, commands, and the toolchain reference.
See `rules/env.md` for service ports, DB schema, and module decomposition.
See `prompts/01_issue-to-plan.md` for how this skill is invoked as part of the
document-workflow pipeline.

## Plan output

Save the generated plan to `plans/YYYYMMDD-HHMMSS_plan.md` (e.g.
`plans/20260702-120000_plan.md`). The plan file is the working document: update it as
scope changes, and reference it when starting implementation with `python-implementation`.

## Composes with
- `python-implementation` — execute after the plan is approved by the user
- `python-refactoring` — if the plan involves structural module changes
- `mcp-server-add` — if the plan includes adding a new MCP server

## Improvement feedback

After running this skill, if a tool was not installed or a step produced no useful
evidence: update `workflow.md` with the lightweight alternative and the "if installed"
guard. If the requirement-equivalent section structure was missing a field the user
consistently requested, or a Step needed clarification, update `workflow.md`
accordingly.
