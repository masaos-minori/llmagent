---
name: require-to-plan
description: |
  Use this skill PROACTIVELY when converting a formal requirement document
  (`requires/*.md`) into a concrete Python implementation plan.
  Covers: architecture analysis, dependency graphing, historical analysis,
  operational dependency inspection, validation quality analysis, and uncertainty tracking.
  Use when the task needs scope definition, affected files, implementation steps,
  test strategy, risks, assumptions, unknowns, or execution sequencing before coding.
---

# Require To Plan Skill

## Purpose

Turn a formal requirement document into a concrete, reviewable implementation plan grounded in architecture analysis and historical data; clarify scope with evidence before coding.

---

## Routing (AI Task Size Assessment)

Before proceeding to any analysis step, execute **Step 0: Classification**. Assess the user request against the following criteria to determine the execution path.

### [Path A] Small Task
**Criteria (Must satisfy ALL):**
- [ ] Affects ≤ 3 files
- [ ] No public or runtime-facing interface changes
- [ ] No database schema changes

**Execution Path:**
Run Step 1 → Skip Steps 2–5 → Run Step 6 (validation baseline) → Steps 7–10.

### [Path B] Large Task
**Criteria (Satisfies ANY):**
- [ ] Affects > 3 files
- [ ] Creates a new module or package
- [ ] Changes a public/runtime interface
- [ ] Modifies or adds a database schema

**Execution Path:**
Run all steps (1 through 10) sequentially. Do not skip any analysis.

---

## Phase overview

| Step | Name | Goal / AI Action |
|---|---|---|
| 1 | Parse the request | Extract explicit constraints, task type, and identify ambiguities. |
| 2 | Architecture analysis | Inspect import layering, import-linter contracts, call graphs, and component centrality. |
| 3 | Dependency graphing | Use `pydeps` or file inspection to locate affected files and map the blast radius. |
| 4 | Historical analysis | Run git diagnostics (`git log`, `git blame`) to assess churn risk and bus factor. |
| 5 | Operational dependency inspection | Inspect `lsof` open handles or `pip-audit` if dependency changes are required. |
| 6 | Validation quality analysis | Establish code quality baselines using `radon`, `vulture`, `semgrep`, `bandit`, or `diff-cover`. |
| 7 | Uncertainty tracking | Isolate all missing evidence, gaps in knowledge, and blocking unknowns. |
| 8 | Produce a concrete plan | Generate the final structured plan using the exact Output Format below. |
| 9 | Planning rules | Enforce evidence-based increments. **Always include a deployment/verification step**. |
| 10 | Completion checklist | Verify all required sections are complete and blocking unknowns are resolved. |

> **IMPORTANT — Tool Availability Guard (For AI):** applies to `pydeps`, `radon`, `semgrep` and any other tool listed above — see `skills/DESIGN.md` Tool availability guard.

---

## Core Execution Rules (Strictly Enforced)

- **No Guesswork**: Every file listed in "Affected Areas" must be verified to exist via environment tools. Do not guess filenames or directory structures.
- **Isolate Unknowns**: If you lack context or code access to answer a question, you must mark it as `BLOCKING: True` in Step 7 and ask the user for clarification before generating the final implementation steps.
- **Incrementalism**: Design the implementation steps in small, reviewable increments. Each step must leave the codebase in a testable state.

---

## Output format

Generate your final response using the exact Markdown structure below. Do not omit any sections.

```markdown
## 1. Goal
- [Clear statement of what the program will achieve and what problem it solves]

## 2. Scope
- **In-Scope**: [List of explicit items to be implemented]
- **Out-of-Scope**: [List of items explicitly excluded from this task]

## 3. Assumptions
- [List any technical or domain assumptions made during analysis]

## 4. Unknowns & Gaps
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | | | | |

## 5. Affected Areas & Tool Evidence

`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor` columns:

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| | | | | | |

## 6. Implementation Steps
1. **Phase 1: Preparation / Refactoring (if needed)**
   - [ ] Step description
2. **Phase 2: Core Logic Implementation**
   - [ ] Step description
3. **Phase 3: Deployment & Verification**
   - [ ] Step description (Mandatory: include deployment validation/scripts check)

## 7. Validation Plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| | | | |

## 8. Risks & Mitigations
- **Risk**: [Description] → **Mitigation**: [Description]
```

Notes on filling section 5: populate Churn/Bus Factor from Step 4 (Historical Analysis) and
Blast Radius from Step 3 (Dependency Graphing) — mark `N/A` if that step was skipped (Path A).
Fill `deploy.sh Impact` per `skills/DESIGN.md` Change-impact table — always state it explicitly.
If documentation must be updated, name the
target doc via `docs/00_index.md` Task-specific document reference (or `routing.md` Docs → task
mapping for new modules) — do not hardcode doc filenames here, they change as docs are split.

## See Also
See `workflow.md` for detailed phase content and commands.
See `rules/env.md` for service ports, DB schema, and module decomposition.

## Plan output

Save the generated plan to `plans/YYYYMMDD-HHMMSS_plan.md` (e.g. `plans/20260702-120000_plan.md`).
The plan file is the working document: update it as scope changes, and reference it when starting implementation with `python-implementation`.

## Composes with
- `python-implementation` — execute after the plan is approved by the user
- `python-refactoring` — if the plan involves structural module changes
- `mcp-server-add` — if the plan includes adding a new MCP server

## Called by
- `issue-to-require` — the requirement document it produces is the input to this skill

## Improvement feedback

After running this skill, if a tool was not installed or a step produced no useful evidence:
update workflow.md with the lightweight alternative and the "if installed" guard.
