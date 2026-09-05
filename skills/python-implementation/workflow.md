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
- **Blast radius**: shared utility or leaf module? (see Phase 2 pydeps for how to assess this)
- **Interface impact**: does this change a public function signature, a config key, or a DB schema?

If requirements are ambiguous, state what is unknown and proceed conservatively.

**Completed when**: task type, target scope, blast radius, and interface impact are all
recorded — each either as a determined value or as an explicit unknown.
**Stop and ask the user before Phase 2 when**: the target scope cannot be determined even
provisionally (no candidate files or call path can be identified from the task description
and a first-pass `rg`/`grep` of the repository) — proceeding without any scope would mean
guessing which files to change. Any other ambiguity is recorded as unknown and Phase 2
proceeds to resolve it with repository evidence.

---

## Phase 2: Repository Intelligence

Run in this order: `rg` first (always — locates the symbols and call sites in scope),
`ast-grep` next only if a structurally-valid match is needed (a pattern `rg` cannot express,
e.g. matching a class body or an async signature), `pydeps` only when the target is a shared
utility (`llm_client`, `rag_utils`, `formatters`, or anything with more than one importer per
`rg "import <module>"`), and `git` last, only when the current behavior's origin or recent
change history is relevant to the task.

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
ast-grep --pattern 'raise $EXPR' --lang python scripts/shared/tool_executor.py
ast-grep --pattern 'json.load($$$)' --lang python scripts/
ast-grep --pattern 'async def $NAME($$$): $$$' --lang python scripts/agent/repl.py
```

Prefer `ast-grep` over plain `rg` for patterns that must be structurally valid.

#### pydeps — dependency impact analysis

```bash
cd scripts && PYTHONPATH=. pydeps <module> --no-output --show-deps
PYTHONPATH=scripts pydeps agent.repl --no-output --show-deps --max-bacon=3
```

Assess blast radius before modifying shared utilities (`llm_client`, `rag_utils`, `formatters`).

#### git — recent change history

```bash
git log --oneline -10 -- scripts/<file>.py
git diff HEAD
git diff HEAD~1 -- scripts/
```

**Completed when**: every symbol/module identified in Phase 1's target scope has a confirmed
set of usages (`rg`/`ast-grep`), and blast radius is assessed for any shared utility touched.

---

## Phase 3: Architecture Boundary Analysis

See `rules/toolchain.md` section 3 for the `lint-imports` command, and `skills/DESIGN.md`
Import layer contract for the canonical layer diagram (do not re-derive it here).

To add a new forbidden-import contract, add an `[importlinter:contract:<name>]` section to
the repository's `.importlinter` file, following the existing contracts there as a template.
Read the current `root_packages` list from `.importlinter` itself rather than assuming it —
it changes if a top-level package is added or removed.

Run `lint-imports` after every change that touches import statements.

---

## Phase 4: Convention Extraction

```bash
ast-grep --pattern 'except $TYPE as $E: $$$' --lang python scripts/ | head -30
ast-grep --pattern 'def $NAME($$$) -> $RET: $$$' --lang python scripts/llm_client.py
rg 'cfg\["' scripts/ | sed 's/.*cfg\["\([^"]*\)".*/\1/' | sort -u
rg '\.info\("|\.warning\("|\.error\("|\.debug\("' scripts/ | grep -oP '(?<=")[^"]+' | sort -u
```

Implement the task using the pattern the commands above surface. Introduce a new pattern
only when applying the existing one would violate a concrete requirement from Phase 1/2
(e.g. the existing exception-handling pattern swallows an error the task requires to
propagate) — cite that requirement when deviating.

**Completed when**: the conventions above (exception handling, config-key access, typed
signatures, log message format) have each been confirmed present in nearby code, or the
requirement that justifies deviating from them has been cited.

---

## Phase 5: Semantic Safe Modification

This phase has four sub-steps, applied in order: write the code (5a), handle its errors
(5b), scope the diff (5c), then run any required CST transform (5d).

#### Step 5a: Implementation rules

- prefer explicit, readable code over compact clever code
- add type annotations where the project already uses them; do not omit return types
- keep functions focused on a single responsibility
- avoid excessive nesting; extract helpers when it improves clarity
- keep side effects visible and localized
- avoid hidden global state
- prefer dependency injection over implicit coupling
- preserve backward compatibility unless the task explicitly allows interface changes

#### Step 5b: Error handling rules

Applies `skills/DESIGN.md` Pythonic safety constraints (specific exceptions, no bare
`except Exception` without re-raising, fail-fast) to this phase:

- add context to an error when the raw exception does not already identify which value or
  call site failed — name the function and the invalid value, as below:
  ```python
  raise ValueError(f"floats_to_blob: expected list[float], got {type(v).__name__}")
  ```
- trust internal invariants; validate only at public boundaries
- log errors with sufficient context before re-raising

#### Step 5c: File editing rules

- Scope discipline: see `AGENTS.md` Global Rule 5.
- keep diffs small and intentional
- when adding/removing a module: `deploy/deploy.sh` does not need a change for this — `scripts/` is rsynced wholesale (see `rules/env.md` Architecture); only a new `config/*.toml` file needs a `cp` line added there
- when renaming a symbol: update all call sites confirmed by `rg` or `ast-grep`

#### Step 5d: LibCST — CST-based refactor transforms

Run this step only when the task includes a rename or structural edit that must preserve
comments, formatting, or docstrings; otherwise skip directly to Phase 6.

If required, use the LibCST transform recipe in `skills/python-refactoring/workflow.md`
Step 6 (Transformation), then run `ruff format scripts/` and `ruff check scripts/ --fix`.

**Completed when**: 5a–5c have been applied to every file in scope, and (if 5d ran)
`ruff format`/`ruff check --fix` have been re-run after the transform.

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

For new I/O-bound or cross-service code paths, make log output filterable: use
`key=value` pairs in the message (not free-form prose) so `grep`/log-aggregator queries can
match on a specific field, as in the examples below:

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

See `rules/toolchain.md` section 5 for bandit commands.

Priority findings: see `rules/coding.md` Bandit priority findings.

---

## Phase 9: Validation Orchestration

See `rules/toolchain.md` for the full sequence and `rules/coding.md` Constraint checks for
the `ast-grep` commands.

**Completed when**: `pytest`, `ruff check`, and `mypy`/`pyright` all pass, and
`tools/check_compat_shims.py` reports no new backward-compatibility leftovers.
Apply `rules/ai-execution.md` Step-Level Failure Triage (Base): on a task-caused
failure, delegate to `python-test-and-fix` (test failures) or `python-lint-typecheck`
(lint/type failures) per `SKILL.md` Composition rules — do not proceed to Phase 10 with
a known failure. On a pre-existing failure, record it in Output expectations'
"unresolved questions or known limitations" and proceed.

---

## Phase 10: Scope Control

#### diff-cover

See `rules/toolchain.md` section 7.

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
rg "<old_module_name>" scripts/
```

Checklist (in addition to `rules/toolchain.md`):
- If a new MCP server was added, its `config/<key>_mcp_server.toml` setup follows `skills/mcp-server-add/workflow.md` — do not re-derive that checklist here.

---

## Phase 12: Knowledge Compression

- **`routing.md`**: add a task-type → doc mapping entry for new modules if none of the existing "Docs → task mapping" entries already cover the area
- **Affected docs**: look up the correct target document via `routing.md` "Docs → task mapping" (which delegates to `docs/00_index.md`) — do not guess a filename; the doc set has been restructured and old single-file names no longer exist
- **`deploy/deploy.sh`**: add a `cp` line only if a new `config/*.toml` file was introduced (see Phase 5 File editing rules — module add/remove alone does not require a `deploy.sh` change)

When removing a module: remove its entry from the above, delete the file, run `rg` for dangling imports.

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

## Required behavior

(Unrelated-change prohibition: see `AGENTS.md` Global Rule 5 — not repeated here.)
- Build architecture only for the requirements recorded in Phase 1/2 — if a broader need is
  suspected, record it as an open question in Output expectations rather than building for it.
- Implement only requirements stated in the task or confirmed in Phase 1/2 — record anything
  else as an open question instead of adding it.
- If a public API must change, state the change and its impact explicitly in the
  implementation summary (Output expectations) — never leave it undocumented.
- Fix the cause of a validation/test/type-check failure per Phase 9 — never disable the
  check itself to make the task appear complete.

See also `rules/coding.md` for project-wide prohibitions (suppression governance, commit hygiene).
