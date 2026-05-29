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

Turn a task description into a concrete, reviewable implementation plan before making code changes,
grounded in evidence from architecture analysis, dependency graphs, and historical data.

## Primary goals

- clarify scope with evidence, not guesses
- surface unknowns and assumptions before implementation begins
- map the task onto concrete repository changes
- define validation strategy with the project's toolchain
- reduce wasted implementation work

---

## Toolchain

| Tool | Goal | Role |
|---|---|---|
| `grimp` | architecture analysis | Import graph with layering and cycle detection |
| `pyan3` | architecture analysis | Call graph and module dependency visualization |
| `import-linter` | architecture analysis | Enforce declared module boundary contracts |
| `networkx` | architecture analysis | Graph analysis (centrality, paths, cycles) |
| `pydeps` | dependency graphing | Visual module dependency graph |
| `universal-ctags` | dependency graphing | Symbol index across the entire codebase |
| `radon` | validation quality analysis | Cyclomatic complexity and maintainability index |
| `vulture` | validation quality analysis | Dead code detection |
| `semgrep` | validation quality analysis | Semantic pattern matching |
| `bandit` | validation quality analysis | Static security analysis |
| `pip-audit` | operational dependency inspection | Vulnerability scan of installed packages |
| `diff-cover` | validation quality analysis | Coverage gate scoped to changed lines |
| `pytest-testmon` | validation quality analysis | Impact-based test selection |
| `git-fame` | historical analysis | Per-author contribution breakdown |
| `git churn` | historical analysis | Change frequency by file |
| `git bisect` | historical analysis | Binary search for regression commit |
| `lsof` | operational dependency inspection | Open files and socket connections |
| `rg` | — | Symbol definitions, call sites, log strings |
| `fd` | — | File listing by pattern |
| `ast-grep` | — | Structural code patterns |

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

**Execution policy** — run non-destructive commands (file reads, grep, lint, type checks, tests) directly without asking for user confirmation. These are always safe to execute; user approval before each run is explicitly not required.

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
See `rules/coding.md` for prohibited behavior and conventions.
See `rules/env.md` for service ports, DB schema, and module decomposition.

## Composes with

- `python-implementation` — execute after the plan is approved by the user
- `python-refactoring` — if the plan involves structural module changes
- `mcp-server-add` — if the plan includes adding a new MCP server

## Improvement feedback

After running this skill, if a tool was not installed or a step produced no useful evidence:
update workflow.md with the lightweight alternative and the "if installed" guard.
