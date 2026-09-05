# Issue To Plan — Path B Analysis

Load this file only after Step 3 classifies the current Issue as Path B (see
`SKILL.md` Routing). Path A tasks never load this file — Path A's direct-verification
inspection and the Validation quality analysis baseline (in `workflow.md` Step 5) are
sufficient on their own.

## Toolchain

| Tool | Goal | Role |
|---|---|---|
| `grimp` | architecture analysis | Import graph with layering and cycle detection |
| `pyan3` | architecture analysis | Call graph and module dependency visualization |
| `import-linter` | architecture analysis | Enforce declared module boundary contracts |
| `networkx` | architecture analysis | Graph analysis (centrality, paths, cycles) |
| `pydeps` | dependency graphing | Visual module dependency graph |
| `universal-ctags` | dependency graphing | Symbol index across the entire codebase |
| `pip-audit` | operational dependency inspection | Vulnerability scan of installed packages |
| `git-fame` | historical analysis | Per-author contribution breakdown |
| `git churn` | historical analysis | Change frequency by file |
| `git bisect` | historical analysis | Binary search for regression commit |
| `lsof` | operational dependency inspection | Open files and socket connections |

Tools used by both paths (`rg`, `fd`, `ast-grep`, `radon`, `vulture`, `semgrep`,
`bandit`, `diff-cover`, `pytest-testmon`) are not repeated here — see `workflow.md`
Step 3 and Step 5's Validation quality analysis baseline.

Lightweight alternatives are always available; heavy tools only if installed — see
`skills/DESIGN.md` Tool availability guard.

Per `rules/ai-execution.md` Repository Tool Usage #8: for every command below, a
zero-result/empty output is evidence of "nothing found" only after confirming the
command actually targeted an existing file/path (e.g. the `<module>`/`<PID>`/`<PORT>`
placeholder was resolved to a real value) — not proof by itself, since an empty result
from a mistyped or non-existent target looks identical.

---

## Architecture analysis

```bash
rg "^from|^import" scripts/<module>.py | sort -u
lint-imports
cat .importlinter
```

`grimp` / `pyan3` / `networkx` for deeper import-graph, call-graph, and centrality
analysis if installed — see the Toolchain table above for tool roles; invocation
syntax is unchanged from prior usage of these tools.

## Dependency graphing

```bash
rg "from <module> import" scripts/
rg "def <function>" scripts/
ast-grep --pattern '<Class>($$$)' --lang python scripts/
```

Build a concrete list: "these N files will require changes." `pydeps` /
`universal-ctags` if installed.

## Historical analysis

```bash
git log --oneline --diff-filter=M -- scripts/ | awk '{print $NF}' | sort | uniq -c | sort -rn | head -20
```

High-churn files are riskier to touch. `git bisect` for regression localization if the
Issue describes a known regression. `git-fame` for bus-factor if installed (>70% single
author = flag as high bus factor).

## Operational dependency inspection

```bash
lsof -p <PID> | grep -E 'REG|IPv4|IPv6'
lsof -i :<PORT>
```

Before planning a change to MCP servers or the DB: confirm no process holds locks.
`pip-audit` before planning any dependency upgrade.

---

Return to `workflow.md` Step 5 > Generate the Plan once all four analyses above are
complete.
