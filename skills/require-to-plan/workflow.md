# Require To Plan — Detailed Workflow

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

## Step 1: Parse the Requirement Document

Extract from the requirement document (`requires/*.md`):

- **Task type**: new feature / bug fix / refactor / integration / performance / security
- **Target scope**: which modules, endpoints, config keys, or DB tables are mentioned
- **Constraints**: deadlines, compatibility requirements, performance targets
- **Ambiguities**: terms with multiple interpretations; unstated assumptions
- **Unknowns**: things that must be discovered before the plan can be concrete

State ambiguities and unknowns explicitly. Do not guess at intent.
If the requirement document is too vague to plan, identify the specific questions that need answers.

---

## Step 2: Architecture Analysis

**Lightweight alternative (always available):**

```bash
# What this module imports:
rg "^from|^import" scripts/<module>.py | sort -u

# What imports this module:
rg "from <module> import\|import <module>" scripts/ | sort -u

# Architecture boundary contracts:
lint-imports
cat .importlinter
```

**Heavy tools (use only if installed and large task routing applies):**

#### grimp — import graph layering

```bash
# Check if installed:
python3 -c "import grimp" 2>/dev/null || { echo "SKIP: grimp not installed"; }

python3 -c "
import grimp
graph = grimp.build_graph('scripts')
for layer in graph.find_modules_that_directly_import('scripts.agent_repl'):
    print(layer)
"
```

#### pyan3 — call graph

```bash
python3 -c "import pyan" 2>/dev/null || { echo "SKIP: pyan3 not installed"; }
pyan3 scripts/*.py --dot --no-defines | dot -Tsvg > call_graph.svg
```

#### networkx — centrality analysis

```bash
python3 -c "import networkx" 2>/dev/null || { echo "SKIP: networkx not installed"; }
```

```python
import networkx as nx
import ast, pathlib

G = nx.DiGraph()
for path in pathlib.Path("scripts").glob("*.py"):
    tree = ast.parse(path.read_text())
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in getattr(node, "names", []):
                G.add_edge(path.stem, alias.name.split(".")[0])

for mod, score in sorted(nx.betweenness_centrality(G).items(), key=lambda x: -x[1])[:5]:
    print(f"{mod}: {score:.3f}")
```

Modules with high betweenness centrality require extra caution.

---

## Step 3: Dependency Graphing

**Lightweight alternative (always available):**

```bash
# Importers of the module:
rg "from <module> import" scripts/
# Definition of the function:
rg "def <function>" scripts/
# Instantiation sites:
ast-grep --pattern '<Class>($$$)' --lang python scripts/
```

Build a concrete list: "these N files will require changes."

**Heavy tools (if installed):**

#### pydeps — visual dependency graph

```bash
python3 -c "import pydeps" 2>/dev/null || { echo "SKIP: pydeps not installed"; }
PYTHONPATH=scripts pydeps <module> --no-output --show-deps
```

#### universal-ctags — symbol index

```bash
which ctags >/dev/null 2>&1 || { echo "SKIP: ctags not installed"; }
ctags -R --languages=Python --python-kinds=cfm scripts/
grep "^<symbol>" tags
```

---

## Step 4: Historical Analysis

#### git churn — change frequency (always available)

```bash
git log --oneline --diff-filter=M -- scripts/ | awk '{print $NF}' | sort | uniq -c | sort -rn | head -20
```

High-churn files are riskier to touch: more merge conflicts, more concurrent changes.

#### git bisect — regression localization

If the plan is for a known regression:

```bash
git bisect start
git bisect bad
git bisect good <last-known-good-sha>
git bisect run pytest tests/test_<module>.py -x -q
git bisect reset
```

#### git-fame — bus factor (if installed)

```bash
python3 -c "import gitfame" 2>/dev/null || { echo "SKIP: git-fame not installed"; }
git fame scripts/<module>.py
```

If a single author owns > 70% of a file: flag as high bus factor.

---

## Step 5: Operational Dependency Inspection

#### lsof — open handles

```bash
lsof -p <PID> | grep -E 'REG|IPv4|IPv6'      # open files and sockets
lsof -i :<PORT>                              # affected service port — see rules/env.md
lsof <path/to/*.sqlite>                      # who has the SQLite file open — see rules/env.md
```

Before planning a change to MCP servers or the DB: confirm no process holds locks.

#### pip-audit — dependency vulnerabilities

```bash
pip-audit
pip-audit --fix --dry-run    # preview auto-upgrades
```

Run before planning any dependency upgrade. Document vulnerabilities found.

---

## Step 6: Validation Quality Analysis

#### radon — cyclomatic complexity

```bash
radon cc scripts/ -s -n C         # grade C or worse (CC ≥ 10)
radon mi scripts/ -s              # maintainability index
radon cc scripts/<module>.py -s   # single module
```

Modules with CC ≥ 15 require additional test coverage before changes.

#### vulture — dead code

```bash
vulture scripts/ --min-confidence 80
```

Before adding new code to a module: confirm the module has no dead code that could be removed instead.

#### semgrep — semantic patterns

```bash
semgrep --config=p/python scripts/
semgrep --config=p/security scripts/
semgrep --pattern 'json.load($F)' --lang python scripts/
```

#### bandit — security baseline

```bash
bandit -r scripts/ -c pyproject.toml
```

Document any existing findings that the planned change touches.

#### diff-cover baseline

```bash
coverage run -m pytest tests/
coverage xml
diff-cover coverage.xml --compare-branch=master    # current baseline
```

Record the current diff-cover baseline. The plan must include raising it to ≥ 90%.

---

## Step 7: Uncertainty Tracking

For each unknown, add a row to the "Unknowns & Gaps" table defined in `SKILL.md` §Output
format §4 (`ID | Unknown Description | Evidence Missing | Resolution Path | Blocking?`).

Example row: `UNK-01 | Whether sqlite-vec supports concurrent writes from multiple threads |
No test exists; documentation is sparse | Write a benchmark test with
ThreadPoolExecutor(4) against the DB | True — affects whether RagIngester can be
parallelized safely`

A plan with unresolved blocking unknowns is not complete.

---

## Step 8: Produce a Concrete Plan

Fill in the exact template from `SKILL.md` §Output format, section by section, using the
evidence gathered above:

| Section | Populate from |
|---|---|
| 1. Goal | Step 1 (parsed request) |
| 2. Scope | Step 1, refined by Steps 2-5 findings |
| 3. Assumptions | Falsifiable assumptions surfaced across Steps 1-6 |
| 4. Unknowns & Gaps | Step 7 |
| 5. Affected Areas & Tool Evidence | Steps 2-6 (architecture, blast radius, churn/bus-factor, validation baseline) |
| 6. Implementation Steps | Ordered, independently committable; include the deploy step if `scripts/`/`config/` changes |
| 7. Validation Plan | Per-file/module test strategy; for the project-wide gate sequence (lint/type/arch/security/test/coverage), see `rules/toolchain.md` |
| 8. Risks & Mitigations | Risk + likelihood (low/med/high) + mitigation |

---

## Step 9: Planning Rules

- every claim must be backed by evidence from the tools run in Steps 2–6
- implementation steps must be small enough to be independently revertable
- always include a deploy step if `scripts/` or `config/` changes
- always include an MCP service map update if a new server is added
- do not include speculative steps — only steps required by the stated goal
- if two approaches are equally valid, state the tradeoff explicitly

---

## Step 10: Completion Checklist

Before delivering the plan, cross-check against the Step 7-9 gates stated above — do not re-derive them, just confirm:

- [ ] goal is one sentence and verifiable
- [ ] scope has explicit in/out boundaries
- [ ] assumptions are falsifiable (Step 8 §3)
- [ ] Step 7 gate met: no blocking unknowns remain unresolved
- [ ] Step 9 rules followed: claims backed by tool evidence, implementation steps independently revertable, deploy step included if production files change
- [ ] validation plan has full table with tools and targets
- [ ] risks are stated with mitigations

---

## Output format

See `SKILL.md` §Output format for the exact Markdown structure to generate.
