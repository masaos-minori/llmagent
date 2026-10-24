# Issue To Plan — Path B Analysis

Load this file only after Step 3 classifies the current Issue as Path B (see `SKILL.md`
Routing). Path A tasks never load this file; Path A's direct-verification inspection and
the Validation quality analysis baseline (`workflow.md` Step 5) suffice.

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
| `git bisect` | historical analysis | Binary search for a regression commit; only on the user's explicit instruction, in a dedicated worktree (it moves `HEAD` and rewrites the working tree) |
| `ss` | operational dependency inspection | Listening sockets and the processes holding them (`lsof` is not installed on this dev host) |

Tools used by both paths (`rg`, `fd`, `ast-grep`, `radon`, `vulture`,
`bandit`, `diff-cover`) are not repeated here — see `workflow.md`
Step 3 and Step 5's Validation quality analysis baseline.

Lightweight alternatives are always available; heavy tools only if installed — see
`skills/DESIGN.md` Tool availability guard.

Per `rules/ai-execution.md` Repository Tool Usage #8: for every command below, an
empty output is evidence of "nothing found" only after confirming the command targeted
an existing file/path (e.g. the `<path>`/`<dotted>`/`<PID>`/`<PORT>` placeholder was
resolved to a real value; `<path>` and `<dotted>` are defined in `workflow.md` Step 3);
an empty result from a mistyped or non-existent target looks identical.

---

## Architecture analysis

```bash
rg "^from|^import" <path> | sort -u
lint-imports
cat .importlinter
```

`grimp` / `pyan3` / `networkx` for deeper import-graph, call-graph, and centrality
analysis if installed — see the Toolchain table for tool roles.

## Dependency graphing

```bash
rg "from <dotted> import" scripts/
rg "def <function>" scripts/
ast-grep --pattern '<Class>($$$)' --lang python scripts/
```

Build a concrete list: "these N files will require changes." `pydeps` /
`universal-ctags` if installed.

## Historical analysis

```bash
git log --name-only --pretty=format: --since=30.days -- scripts/ | sed '/^$/d' | sort | uniq -c | sort -rn | head -20
```

This lists each file with its number of commits in the last 30 days (the `Churn (30d)`
column). Do not use `--oneline` with `awk '{print $NF}'`: that counts the last word of
each commit subject, not file names. High-churn files are riskier to touch. For a known
regression the Issue describes, localize it with `git log -S`/`git log -L` (read-only);
`git bisect` only per the Toolchain table's condition. `git-fame` for bus-factor if installed (>70% single
author = flag as high bus factor).

## Operational dependency inspection

```bash
ss -ltnpH 'sport = :<PORT>'    # who listens on a port
ss -tnp                       # established connections with their processes
```

Before planning a change to MCP servers or the DB: confirm no process holds locks (database files: `fuser <file>` if available; otherwise state the check as not run).
`pip-audit` before planning any dependency upgrade.

---

Return to `workflow.md` Step 5 > Generate the Plan once all four analyses above are complete.
