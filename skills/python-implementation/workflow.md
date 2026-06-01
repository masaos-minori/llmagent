# Python Implementation — Detailed Workflow

## Toolchain

| Tool | Phase | Role |
|---|---|---|
| `rg` | Repository Intelligence | Search for patterns, call sites, symbol definitions |
| `ast-grep` | Repository Intelligence | Structural code search: find usages, classes, exceptions by shape |
| `pydeps` | Repository Intelligence | Visualize import graphs; assess blast radius |
| `git` | Repository Intelligence | Review history; stage selectively |
| `import-linter` | Architecture Boundary Analysis | Enforce module boundary rules |
| `libcst` | Semantic Safe Modification | CST-based code transforms |
| `pydantic` | Runtime Contract Validation | Define and validate data models |
| `schemathesis` | Runtime Contract Validation | Property-based HTTP API contract testing |
| `structlog` | Observability Injection | Structured log context |
| `opentelemetry-api` / `-sdk` | Observability Injection | Structured tracing for production code paths |
| `bandit` | Security Validation | Static security analysis |
| `ruff` | Validation Orchestration | Format and lint |
| `mypy` | Validation Orchestration | Type check |
| `pytest` | Validation Orchestration | Behavior verification |
| `pre-commit` | Validation Orchestration | Final gate |
| `diff-cover` | Scope Control | Coverage scoped to changed lines |
| `pytest-benchmark` | Scope Control | Performance regression guard |

---

## Phase 1: Task Classification

Before reading any code, classify the task:

- **Task type**: new feature / bug fix / refactor / integration / cleanup
- **Target scope**: identify target files and likely call paths
- **Blast radius**: is this a shared utility (`llm_client`, `rag_utils`, `formatters`) or a leaf module?
- **Interface impact**: does this change a public function signature, a config key, or a DB schema?

If requirements are ambiguous, state what is unknown and proceed conservatively.
Do not proceed to implementation until task type and target scope are clear.

---

## Phase 2: Repository Intelligence

#### rg — text search

```bash
rg "<symbol>" scripts/             # find all usages of a symbol
rg "def <function_name>" scripts/  # locate the implementation
rg "class <ClassName>" scripts/    # find class definitions
rg "import <module>" scripts/      # find all importers of a module
```

#### ast-grep — structural search

`ast-grep` (binary at `~/.local/bin/ast-grep`) matches by code shape, not just text:

```bash
ast-grep --pattern 'ConfigLoader().load($ARG)' --lang python scripts/
ast-grep --pattern 'class $NAME(BaseModel): $$$' --lang python scripts/
ast-grep --pattern 'raise $EXPR' --lang python scripts/tool_executor.py
ast-grep --pattern 'json.load($$$)' --lang python scripts/
ast-grep --pattern 'async def $NAME($$$): $$$' --lang python scripts/agent_repl.py
```

Prefer `ast-grep` over plain `rg` for patterns that must be structurally valid.

#### pydeps — dependency impact analysis

```bash
cd scripts && pydeps <module> --no-output --show-deps
pydeps agent_repl --no-output --show-deps --max-bacon=3
```

Assess blast radius before modifying shared utilities (`llm_client`, `rag_utils`, `formatters`).

#### git — recent change history

```bash
git log --oneline -10 -- scripts/<file>.py
git diff HEAD
git diff HEAD~1 -- scripts/
```

---

## Phase 3: Architecture Boundary Analysis

```bash
lint-imports
cat .importlinter
```

To add a new boundary contract:

```ini
[importlinter]
root_packages =
    scripts

[importlinter:contract:commands-no-repl]
name = CommandRegistry must not import AgentREPL
type = forbidden
source_modules =
    scripts.agent_commands
forbidden_modules =
    scripts.agent_repl
```

Run `lint-imports` after every change that touches import statements.

---

## Phase 4: Convention Extraction

```bash
ast-grep --pattern 'except $TYPE as $E: $$$' --lang python scripts/ | head -30
ast-grep --pattern 'def $NAME($$$) -> $RET: $$$' --lang python scripts/llm_client.py
rg 'cfg\["' scripts/ | sed 's/.*cfg\["\([^"]*\)".*/\1/' | sort -u
rg '\.info\("|\.warning\("|\.error\("|\.debug\("' scripts/ | grep -oP '(?<=")[^"]+' | sort -u
```

Do not introduce a new pattern unless the existing pattern is demonstrably insufficient.

---

## Phase 5: Semantic Safe Modification

#### Implementation rules

- prefer explicit, readable code over compact clever code
- add type annotations where the project already uses them; do not omit return types
- keep functions focused on a single responsibility
- avoid excessive nesting; extract helpers when it improves clarity
- keep side effects visible and localized
- avoid hidden global state
- prefer dependency injection over implicit coupling
- preserve backward compatibility unless the task explicitly allows interface changes

#### Error handling rules

- raise specific exceptions with descriptive messages
- do not swallow exceptions silently
- add context to errors when it improves diagnosis:
  ```python
  raise ValueError(f"floats_to_blob: expected list[float], got {type(v).__name__}")
  ```
- fail fast on invalid input at public boundaries; trust internal invariants
- log errors with sufficient context before re-raising

#### File editing rules

- change only files relevant to the task
- keep diffs small and intentional
- avoid opportunistic unrelated cleanup unless explicitly requested
- when adding/removing a module: update `deploy/deploy.sh` simultaneously
- when renaming a symbol: update all call sites confirmed by `rg` or `ast-grep`

#### LibCST — CST-based refactor transforms

Use LibCST when a refactor must preserve comments, formatting, or docstrings.

```python
import libcst as cst

class RenameArg(cst.CSTTransformer):
    def leave_Arg(self, original_node: cst.Arg, updated_node: cst.Arg) -> cst.Arg:
        if (
            isinstance(updated_node.keyword, cst.Name)
            and updated_node.keyword.value == "old_name"
        ):
            return updated_node.with_changes(keyword=cst.Name("new_name"))
        return updated_node

source = open("scripts/tool_executor.py").read()
tree = cst.parse_module(source)
new_tree = tree.visit(RenameArg())
open("scripts/tool_executor.py", "w").write(new_tree.code)
```

After any LibCST transform: run `ruff format scripts/` and `ruff check scripts/ --fix`.

---

## Phase 6: Runtime Contract Validation

#### Pydantic — data model boundaries

```python
from pydantic import BaseModel, Field, field_validator

class MyRequest(BaseModel):
    query: str = Field(..., min_length=1)
    limit: int = Field(default=10, ge=1, le=100)

    @field_validator("query")
    @classmethod
    def strip_query(cls, v: str) -> str:
        return v.strip()
```

Use at module boundaries only — not as internal data holders.

#### Schemathesis — API contract testing for MCP endpoints

```bash
schemathesis run http://localhost:8005/openapi.json --checks all --max-examples 50
schemathesis run http://localhost:8005/openapi.json --endpoint /v1/call_tool --method POST
```

Run before each MCP server change is considered complete.

---

## Phase 7: Observability Injection

This project uses `logging.getLogger(__name__)` in library modules.
structlog and OpenTelemetry are not currently adopted project-wide — skip this phase
unless the task explicitly requests OTel instrumentation.

For new I/O-bound or cross-service code paths, ensure log output is filterable:

```python
logger = logging.getLogger(__name__)
logger.info("tool_called name=%s session=%s", name, session_id)
logger.warning("tool_timeout elapsed=%.2fs tool=%s", elapsed, name)
logger.error("mcp_call_failed tool=%s error=%s", name, exc)
```

Log at `INFO` for normal operations, `WARNING` for degraded-but-continuing, `ERROR` for failures.
Do not log at `DEBUG` without a corresponding `if logger.isEnabledFor(logging.DEBUG)` guard.

---

## Phase 8: Security Validation

```bash
bandit -r scripts/ -c pyproject.toml
bandit scripts/web_crawler.py
bandit -r scripts/ -l -ii    # high severity only
```

Priority findings:
- `B105`/`B106`: hardcoded credentials → move to env/conf.d
- `B301`/`B302`: pickle → replace with JSON or pydantic
- `B501`/`B502`: TLS disabled → never in production
- `B608`: SQL injection → parameterized queries

---

## Phase 9: Validation Orchestration

See `rules/toolchain.md` for the full sequence.

Additional constraint checks:
```bash
ast-grep --pattern 'json.load($$$)' --lang python scripts/ | grep -v 'config_loader.py'
ast-grep --pattern 'except: $$$' --lang python scripts/
```

---

## Phase 10: Scope Control

#### diff-cover

```bash
coverage run -m pytest tests/
coverage xml
diff-cover coverage.xml --compare-branch=main
diff-cover coverage.xml --compare-branch=main --fail-under=90
```

#### pytest-benchmark

```python
def test_floats_to_blob_perf(benchmark):
    data = [0.1] * 384
    result = benchmark(floats_to_blob, data)
    assert len(result) == 384 * 4
```

```bash
pytest tests/ --benchmark-only
pytest tests/ --benchmark-save=baseline
pytest tests/ --benchmark-compare=baseline --benchmark-compare-fail=mean:10%
```

---

## Phase 11: Production Readiness

```bash
grep -c "cp scripts/" deploy/deploy.sh
rg "<old_module_name>" scripts/
grep "mcp_servers" config/agent.json
```

Checklist (in addition to `rules/toolchain.md`):
- OTel spans added for new I/O-bound or cross-service code paths
- `config/agent.json mcp_servers` updated if a new MCP server was added

---

## Phase 12: Knowledge Compression

- **`CLAUDE.md` Architecture section**: add one-line role description for each new module
- **`routing.md`**: add task-type → doc mapping entry for new modules
- **`docs/06_ref-agent-commands.md`**: update if slash commands changed
- **`docs/06_ref-rag.md`**: update if RAG pipeline modules changed
- **`docs/06_ref-mcp.md`**: update if MCP tools changed
- **`docs/06_ref-agent-config.md`**: update if `AgentConfig` fields changed
- **`deploy/deploy.sh`**: add `cp` lines for new files; remove lines for deleted files

When removing a module: remove from all of the above, delete the file, run `rg` for dangling imports.

---

## Output expectations

- changed files
- implementation summary
- pydantic models introduced (if any)
- architecture boundary check result (`lint-imports`)
- security scan result (`bandit`)
- diff coverage (`diff-cover`)
- deploy.sh impact (if any)
- MCP service map impact (if any)
- validation results (ruff, mypy, pytest, pre-commit)
- unresolved questions or known limitations

---

## Composes with

- `python-lint-typecheck` — if Phase 9 reveals pre-existing lint/type errors outside task scope
- `python-test-and-fix` — if Phase 9 reveals test failures not introduced by the task
- `deploy` — after Phase 11 if scripts/ or config/ files changed

---

## Prohibited behavior

- do not rewrite large unrelated sections without request
- do not introduce speculative architecture
- do not invent requirements that are not present
- do not change public APIs silently
- do not disable validation, tests, or type checking to make the task appear complete

See also `rules/coding.md` for project-wide prohibitions (suppression governance, commit hygiene).
