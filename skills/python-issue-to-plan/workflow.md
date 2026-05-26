# Issue To Plan — Detailed Workflow

## Step 1: Parse the Request

Extract from the task description:

- **Task type**: new feature / bug fix / refactor / integration / performance / security
- **Target scope**: which modules, endpoints, config keys, or DB tables are mentioned
- **Constraints**: deadlines, compatibility requirements, performance targets
- **Ambiguities**: terms with multiple interpretations; unstated assumptions
- **Unknowns**: things that must be discovered before the plan can be concrete

State ambiguities and unknowns explicitly. Do not guess at intent.
If the task description is too vague to plan, identify the specific questions that need answers.

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
cd scripts && pydeps <module> --no-output --show-deps
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
lsof -i :8004 -i :8005 -i :8006              # MCP server ports
lsof /opt/llm/db/llm.db                       # who has the SQLite file open
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
diff-cover coverage.xml --compare-branch=main    # current baseline
```

Record the current diff-cover baseline. The plan must include raising it to ≥ 90%.

---

## Step 7: Uncertainty Tracking

For each unknown, fill in this template:

```
UNKNOWN: <what is unknown>
Evidence missing: <what information would resolve it>
Resolution: <how to get that information>
Blocking: yes / no
```

Example:

```
UNKNOWN: Whether sqlite-vec supports concurrent writes from multiple threads
Evidence missing: No test exists; documentation is sparse
Resolution: Write a benchmark test with ThreadPoolExecutor(4) against the DB
Blocking: yes — affects whether RagIngester can be parallelized safely
```

A plan with unresolved blocking unknowns is not complete.

---

## Step 8: Produce a Concrete Plan

Structure the plan as:

### 1. Goal

One sentence: what will be true when this is done.

### 2. Scope

**In scope**: specific files, functions, config keys, DB tables, endpoints
**Out of scope**: what will NOT change (prevents scope creep)

### 3. Assumptions

Numbered list. Each assumption must be falsifiable.

### 4. Unknowns

From Step 7. Flag blocking unknowns explicitly.

### 5. Affected Areas

| File | Change | Blast radius | Churn (30d) | Bus factor | deploy.sh |
|---|---|---|---|---|---|
| `scripts/agent_repl.py` | add new handler | high (imported by 3) | 12 commits | 1 author | existing |
| `scripts/new_module.py` | create | low | 0 commits | — | add cp line |
| `config/agent.json` | add config key | low | 3 commits | 2 authors | existing |

Always include `deploy/deploy.sh` impact: "existing", "add cp line", or "remove cp line".

When listing affected documentation, use the current split structure:
- slash command changes → `docs/06_ref-agent-commands.md`
- RAG pipeline changes → `docs/06_ref-rag.md`
- AgentConfig field changes → `docs/06_ref-agent-config.md`
- MCP tool changes → `docs/06_ref-mcp.md`
- new modules → `routing.md` (always update when new modules are added)

### 6. Implementation Steps

Ordered list. Each step:
- is independently committable
- has a clear completion criterion
- includes the deploy step if production files change

### 7. Validation Plan

| Check | Tool | Target |
|---|---|---|
| Lint | `ruff check scripts/` | 0 errors |
| Type check | `mypy scripts/` | no new errors |
| Architecture | `lint-imports` | 0 violations |
| Security | `bandit` | no HIGH unaddressed |
| Tests | `pytest` | all pass |
| Coverage | `diff-cover` | ≥ 90% on changed lines |
| Pre-commit | `pre-commit run --all-files` | pass |

### 8. Risks

Each risk: description + likelihood (low/med/high) + mitigation.

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

Before delivering the plan:

- [ ] goal is one sentence and verifiable
- [ ] scope has explicit in/out boundaries
- [ ] all assumptions are falsifiable
- [ ] no blocking unknowns remain unresolved
- [ ] affected areas table has tool evidence (not guesses)
- [ ] implementation steps are ordered and independently committable
- [ ] validation plan has full table with tools and targets
- [ ] risks are stated with mitigations
- [ ] deploy step included if production files change

---

## Output format

```markdown
## Goal
<one sentence>

## Scope
**In**: ...
**Out**: ...

## Assumptions
1. ...

## Unknowns
| Unknown | Evidence missing | Resolution | Blocking |
|---|---|---|---|

## Affected Areas
| File | Change | Blast radius | Churn | Bus factor |
|---|---|---|---|---|

## Implementation Steps
1. ...

## Validation Plan
| Check | Tool | Target |
|---|---|---|

## Risks
| Risk | Likelihood | Mitigation |
|---|---|---|
```
