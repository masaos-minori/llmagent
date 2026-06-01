---
name: python-issue-to-plan
description: |
  Use this skill PROACTIVELY when converting a feature request, bug report,
  ticket, or vague task into a concrete Python implementation plan.
  Covers: architecture analysis, dependency graphing, historical analysis,
  operational dependency inspection, validation quality analysis, and uncertainty tracking.
  Use when the task needs scope definition, affected files, implementation steps,
  test strategy, risks, assumptions, unknowns, or execution sequencing before coding.
---

# Issue To Plan Skill

## Purpose

Turn a task description into a concrete, reviewable implementation plan grounded in architecture analysis and historical data; clarify scope with evidence before coding.

---

## Routing

**Small task** (affects ≤ 3 files, no interface change, no DB schema change):
→ Skip Steps 2–5. Run Step 1 → Step 6 (validation baseline) → Step 7 → Step 8 → Step 9 → Step 10.

**Large task** (affects > 3 files, new module, interface change, or DB schema):
→ Run all steps. Steps 2–5 provide evidence that prevents invalid scope assumptions.

## Phase overview

| Step | Name | Goal |
|---|---|---|
| 1 | Parse the request | extract constraints, task type, ambiguities |
| 2 | Architecture analysis | import layering; import-linter contracts; call graph; centrality |
| 3 | Dependency graphing | pydeps visual graph; ctags symbol index; locate affected files |
| 4 | Historical analysis | git-fame bus factor; git churn risk; git bisect for regressions |
| 5 | Operational dependency inspection | lsof open handles; pip-audit before dep changes |
| 6 | Validation quality analysis | radon CC; vulture dead code; semgrep; bandit; diff-cover baseline |
| 7 | Uncertainty tracking | template: UNKNOWN / Evidence missing / Resolution / Blocking |
| 8 | Produce a concrete plan | goal, scope, assumptions, unknowns, steps, validation table, risks |
| 9 | Planning rules | evidence-based; small increments; always include deploy step |
| 10 | Completion checklist | all sections present; blocking unknowns resolved |

---

## Output format

1. goal
2. scope (in / out)
3. assumptions
4. unknowns (template; blocking flagged)
5. affected areas (tool evidence; blast radius; churn; bus factor; deploy.sh impact)
6. implementation steps (ordered; deploy step included)
7. validation plan (full table)
8. risks

---

See `workflow.md` for detailed phase content.
See `rules/env.md` for service ports, DB schema, and module decomposition.

## Composes with

- `python-implementation` — execute after the plan is approved by the user
- `python-refactoring` — if the plan involves structural module changes
- `mcp-server-add` — if the plan includes adding a new MCP server

## Improvement feedback

After running this skill, if a tool was not installed or a step produced no useful evidence:
update workflow.md with the lightweight alternative and the "if installed" guard.
