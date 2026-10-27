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
| `schemathesis` | Runtime Contract Validation | Property-based HTTP API contract testing (isolated ASGI app only, Phase 6) |
| `fmt_kvlog` (`scripts/shared/formatters.py`) | Observability Injection | Repository helper that formats `key=value` log messages |
| `opentelemetry-api` / `-sdk` | Observability Injection | Optional tracing through `scripts/shared/otel_tracer.py` (`build_tracer`, no-op when disabled); used only when the task needs it. `structlog` is declared but not used under `scripts/` |
| `bandit` | Security Validation | Static security analysis |
| `ruff` | Validation Orchestration | Format and lint |
| `mypy` | Validation Orchestration | Type check |
| `pytest` | Validation Orchestration | Behavior verification (after the production-isolation check) |
| `lint-imports` | Validation Orchestration | `PYTHONPATH=scripts uv run lint-imports` (command per `rules/toolchain.md` §3) |
| `tools/run_validation_gates.py` | Validation Orchestration | Selects and runs the project gates the changed files need |
| `pre-commit` | Validation Orchestration | Final gate |
| `diff-cover` | Scope Control | Coverage scoped to changed lines |
| `pytest-benchmark` | Scope Control | Performance regression guard |

Run every Python tool through `uv run`; commands below omit the prefix for brevity.

---

## Phase 1: Task Classification

Before reading code, classify the task:

- **Task type**: new feature / bug fix / refactor / integration / cleanup
- **Target scope**: identify target files and likely call paths
- **Blast radius**: shared utility or leaf module? (assess per Phase 2)
- **Interface impact**: does this change a public function signature, a config key, or a DB schema?

If the task is a refactor with no behavior change (structure only), stop and use
`python-refactoring` (see `SKILL.md` When not to use). For a bug fix, plan the reproducing
test first (Step 5e) so the fix is verified against the failing behavior.

If requirements are ambiguous, state what is unknown and proceed conservatively.

Record `git status --short` as the working-tree baseline before any edit. Changes already
present (another session's edits, earlier work) are not this task's; Phases 2, 10, and 11 rely on
it when they review a diff.

**Completed when**: task type, target scope, blast radius, and interface impact are all
recorded, each as a determined value or an explicit unknown.
**Stop and ask the user before Phase 2 when**: the target scope cannot be determined even
provisionally (no candidate files or call path from the task description and a first-pass
`rg`/`grep`). Any other ambiguity is recorded as unknown; Phase 2 resolves it with
repository evidence.

---

## Phase 2: Repository Intelligence

Run in this order: `rg` first (always), `ast-grep` next only if a structurally-valid match
is needed (a pattern `rg` cannot express, e.g. a class body or async signature), `pydeps`
only when the target is a shared utility (anything with more than one importer per
`rg "import <module>"`; the importer count decides, not the module name — for example
`scripts/shared/llm_client.py` and `scripts/shared/formatters.py` usually qualify; each exists in more than one package, so use full paths), and
`git` last, only when the current behavior's origin or recent change history is relevant.

Blast radius: before changing the default behavior, a required argument, or the return
contract of a widely referenced symbol, apply `rules/toolchain.md` "Impact-radius check
(before broad behavior changes)" (`rg -l '\bSymbol\b' tests/ | wc -l` and the per-file counts).
If the count exceeds that section's rule of thumb, record the blast radius in the plan's
Risks section or in the Output expectations' limitations, as that section directs.

#### rg — text search

```bash
rg "<symbol>" scripts/             # find all usages of a symbol
rg "def <function_name>" scripts/  # locate the implementation
rg "class <ClassName>" scripts/    # find class definitions
rg "import <module>" scripts/      # find all importers of a module
```

#### ast-grep — structural search

`ast-grep` (binary at `~/.local/bin/ast-grep`) matches by code shape:

```bash
ast-grep --pattern 'class $NAME(BaseModel): $$$' --lang python scripts/
ast-grep --pattern 'raise $EXPR' --lang python scripts/shared/tool_executor.py
ast-grep --pattern 'async def $NAME($$$): $$$' --lang python scripts/agent/repl.py
```

Prefer `ast-grep` over `rg` for patterns that must be structurally valid.

#### pydeps — dependency impact analysis

```bash
PYTHONPATH=scripts uv run pydeps scripts/<package>/<module>.py --no-output --show-deps [--max-bacon=3]
```

`pydeps` takes a file path: a dotted module name (`agent.repl`) fails with `No such file or
directory`. Do not `cd` into `scripts/` (the shell keeps the directory for later commands).

#### git — recent change history

```bash
git log --oneline -10 -- scripts/<file>.py
git log -p -3 -- scripts/<file>.py      # how the file's behavior changed recently
```

Do not use `git diff HEAD` for history: it shows the whole working tree, including other sessions'
uncommitted changes.

**Completed when**: every symbol/module in Phase 1's target scope has a confirmed set of
usages (`rg`/`ast-grep`), and blast radius is assessed for any shared utility touched.

---

## Phase 3: Architecture Boundary Analysis

See `rules/toolchain.md` section 3 for the `lint-imports` command, and `skills/DESIGN.md`
Import layer contract for the canonical layer diagram (MUST NOT re-derive it here).

To add a forbidden-import contract, add an `[importlinter:contract:<name>]` section to
`.importlinter`, using the existing contracts as a template. Read the current `root_packages`
list from `.importlinter` rather than assuming it.

Run `PYTHONPATH=scripts uv run lint-imports` after every change that touches import
statements (the Fast path skips this phase only because it forbids import changes).

**Completed when**: `lint-imports` passes, or any new violation is resolved by an
explicit, documented contract change in `.importlinter` rather than a suppressed
failure.

---

## Phase 4: Convention Extraction

```bash
ast-grep --pattern 'except $TYPE as $E: $$$' --lang python scripts/ | head -30
ast-grep --pattern 'def $NAME($$$) -> $RET: $$$' --lang python scripts/shared/llm_client.py
rg 'cfg\["' scripts/ | sed 's/.*cfg\["\([^"]*\)".*/\1/' | sort -u
rg '\.info\("|\.warning\("|\.error\("|\.debug\("' scripts/ | grep -oP '(?<=")[^"]+' | sort -u
```

The `cfg["..."]` search reflects one config-access style; if it returns nothing, find the real
access style from `scripts/shared/config_loader.py` usages instead of concluding that no
convention exists (a zero-match search is evidence of absence only after confirming the
pattern and path are right).

Implement the task using the pattern the commands above surface. Introduce a new pattern
only when the existing one would violate a concrete requirement from Phase 1/2 (e.g. the
existing exception-handling pattern swallows an error the task requires to propagate) — cite
that requirement when deviating.

**Completed when**: the conventions above (exception handling, config-key access, typed
signatures, log message format) are each confirmed in nearby code, or the requirement
justifying deviation is cited.

---

## Phase 5: Semantic Safe Modification

This phase has four sub-steps, applied in order: write the code (5a), handle its errors
(5b), scope the diff (5c), then run any required CST transform (5d).

### Step 5a: Implementation rules

- prefer explicit, readable code over compact clever code
- annotate every parameter and return type of new or modified functions (existing untouched
  code keeps its current annotations); MUST NOT omit return types on code this task writes
- keep functions focused on a single responsibility
- avoid excessive nesting; extract helpers when it improves clarity
- keep side effects visible and localized
- avoid hidden global state
- prefer dependency injection over implicit coupling
- public interface: see `SKILL.md` Compatibility policy (no shims or aliases; change the interface and every caller together)

### Step 5b: Error handling rules

Applies `skills/DESIGN.md` Pythonic safety constraints (specific exceptions, no bare
`except Exception` without re-raising, fail-fast) to this phase:

- add context to an error when the raw exception does not identify which value or call site
  failed — name the function and the invalid value:
  ```python
  raise ValueError(f"floats_to_blob: expected list[float], got {type(v).__name__}")
  ```
- trust internal invariants; validate only at public boundaries
- put the context in the raised error (per the example above) and log it once, where the error
  is finally handled or the process boundary is crossed; MUST NOT log-and-re-raise at every
  layer (duplicate log lines) unless a layer adds information the caller lacks

### Step 5c: File editing rules

- Scope discipline: see `AGENTS.md` Global Rule 5; keep diffs small and intentional
- when adding/removing a module: `deploy/deploy.sh` needs no change — `scripts/` is rsynced wholesale (see `rules/env.md` Architecture); only a new `config/*.toml` file needs a `cp` line there
- when renaming a symbol: update all call sites confirmed by `rg` or `ast-grep`

### Step 5d: LibCST — CST-based refactor transforms

Run this step only when the task includes a rename or structural edit that must preserve
comments, formatting, or docstrings; otherwise skip to Phase 6.

If required, use the LibCST transform recipe in `skills/python-refactoring/workflow.md`
Step 6 (Transformation), applied to explicit file paths only, then run `ruff format` and
`ruff check --fix` on exactly the files you changed (never on all of `scripts/`, which would
reformat unrelated files and break the small-diff rule).

### Step 5e: Tests for the change

Every behavior change ships with tests; a task is not complete without them:

- bug fix: write the reproducing test first and confirm it fails without the fix
  (`python-test-and-fix` Path A)
- new feature or new branch: add tests for the new behavior, edge cases, and failure paths
  (`python-test-and-fix` Path B)

Delegate the test work to `python-test-and-fix` (its production-isolation check applies
before any test run) and keep the tests in the mirrored `tests/<package>/test_<module>.py`
path. The tests also supply the changed-line coverage Phase 10 measures.

**Completed when**: 5a–5c have been applied to every file in scope, (if 5d ran)
`ruff format`/`ruff check --fix` have been re-run on the changed files, and 5e's tests exist
for every changed behavior (or the change has no behavior change, recorded as such).

---

## Phase 6: Runtime Contract Validation

#### Pydantic — data model boundaries

Use `pydantic.BaseModel` (`Field` constraints, `field_validator`) at module boundaries only — not as internal data holders.

#### Schemathesis — API contract testing for MCP endpoints

MUST NOT point Schemathesis at a running service. On this host the repository configuration
points at `/opt/llm`, and `--checks all` fuzzes POST endpoints such as `/v1/call_tool`, which
can execute tools against production state. Run it only against an isolated instance:

- the MCP servers are FastAPI apps, so load the app object in a test and use the ASGI entry
  (Schemathesis 4.x: `schemathesis.openapi.from_asgi("/openapi.json", app)` with
  `@schema.parametrize()`), under the test-suite isolation in `tests/conftest.py`; confirm
  the exact API with `uv run schemathesis --help` for the installed version (4.21.0 at the
  time of writing) before use;
- the server's port and base URL come from its `http_port` class variable and
  `config/agent.toml` `[mcp_servers.*]` `url` (`rules/env.md` Service endpoints and ports);
  do not copy a fixed port into the command;
- if no isolated instance can be started (the isolation check in `python-test-and-fix` Core
  rules finds no mechanism for a production path the instance reaches, or `schemathesis`
  unavailable), record the check as `Needs confirmation` per
  `skills/DESIGN.md` Tool availability guard and continue.

Run this check before each MCP server change is considered complete.

**Completed when**: new module-boundary data is validated at a Pydantic boundary where the
codebase convention calls for one, and Schemathesis has been run against an isolated instance
for any changed MCP endpoint, or recorded `Needs confirmation` (or this Phase does not apply,
since no boundary/endpoint changed).

---

## Phase 7: Observability Injection

This project uses `logging.getLogger(__name__)` in library modules. `structlog` is declared
in `pyproject.toml` but not used under `scripts/`. OpenTelemetry is optional: tracing is built
through `scripts/shared/otel_tracer.py` (`build_tracer`, a no-op tracer when disabled; wired in
`scripts/agent/factory.py`). Add tracing only when the task asks for it, and then only through
that module — never by calling `trace.set_tracer_provider()` directly.

For new I/O-bound or cross-service code paths, make log output filterable: use `key=value`
pairs in the message (not free-form prose). Prefer the repository helper `fmt_kvlog`
(`scripts/shared/formatters.py`) where nearby code does (it is used in the MCP servers, e.g.
`scripts/mcp_servers/cicd/cicd_server.py`); otherwise write the pairs directly, as below:

```python
logger.info(fmt_kvlog("tool_called", name=name, session=session_id))
logger.warning("tool_timeout elapsed=%.2fs tool=%s", elapsed, name)
```

Log at `INFO` for normal operations, `WARNING` for degraded-but-continuing, `ERROR` for failures.
MUST NOT log at `DEBUG` without a corresponding `if logger.isEnabledFor(logging.DEBUG)` guard.

**Completed when**: new I/O-bound or cross-service code paths use the `key=value` log
format (via `fmt_kvlog` where the neighboring code does), or this Phase was correctly skipped
(no tracing request, no new I/O-bound/cross-service path).

---

## Phase 8: Security Validation

See `rules/toolchain.md` section 5 for bandit commands.

Priority findings: see `rules/coding.md` Bandit priority findings.

Also check by hand what `bandit` cannot see in the changed code:
- SQL built by string formatting or concatenation instead of bound parameters (SQLite
  queries and sqlite-vec `MATCH` calls take parameters)
- deserialization of untrusted input (`pickle`, `yaml.load`, unvalidated JSON fed into
  dynamic dispatch)
- file paths or subprocess arguments built from external input without validation
- a new tool-execution path that skips the approval or permission checks neighboring paths use

**Completed when**: `bandit` has been run, the manual checks above have been applied to the
changed code, and every high/medium-severity finding (per
`rules/coding.md` Bandit priority findings) is resolved or suppressed with an inline
justification (per `rules/coding.md` Suppression governance) — MUST NOT proceed to Phase 9
with an unresolved, unjustified high/medium finding.

---

## Phase 9: Validation Orchestration

See `rules/toolchain.md` for the full sequence and `rules/coding.md` Constraint checks for
the `ast-grep` commands.

Before the first test run, apply `python-test-and-fix` Core rule "Verify Production Isolation
Before Running Tests": record what the guard in `tests/conftest.py` covers and does not (it fails
a test that opens a SQLite database or a `FileHandler` under `/opt/llm`; it does not guard ports
or other kinds of write), and stop only when no mechanism exists for a production path the tests
you run reach (record `Needs confirmation`). Default to
`-m "not integration and not production_paths_allowed"`: `integration` tests start real
subprocesses and `production_paths_allowed` tests are exempt from the guard; run either group only
when the task needs it and the user agrees.

Run, in this order, each through `uv run`:

```bash
ruff format <changed files> && ruff check <changed files>
mypy --no-namespace-packages <changed files>              # or pyright; pass paths explicitly (mypy's configured scope omits tools/)
PYTHONPATH=scripts lint-imports   # when imports changed
pytest <tests for the change> -m "not integration and not production_paths_allowed"   # then the wider suite (below)
python tools/run_validation_gates.py          # project gates for the changed files
python tools/check_compat_shims.py
pre-commit run --files <changed files>        # final gate (rules/toolchain.md §8)
```

The wider suite is `uv run pytest -m "not integration and not production_paths_allowed" -q`, not the
unfiltered `uv run pytest -v` that `rules/toolchain.md` section 6 lists (that one also runs the
integration and guard-exempt tests). Follow `python-test-and-fix` Step 10 for it: run it in the
background with the output in a temporary directory outside the repository, check
`pgrep -af "pytest|mutmut"` first so another session's run is not using the same checkout, and
compare `git rev-parse HEAD` and `git status --short` before and after.

`run_validation_gates.py` reports `Fail`/`Blocked` rows that matter and `Not available` rows that
do not; treat a `Fail` as a stop unless it is unrelated to this change (names none of the
changed files and the same gate did not pass earlier in this run), in which case record it.

**Completed when**: `pytest`, `ruff check`, `mypy`/`pyright`, `lint-imports` (when imports
changed), the project gates, and `pre-commit` all pass, and
`tools/check_compat_shims.py` reports no new backward-compatibility leftovers.
Apply `rules/ai-execution.md` Step-Level Failure Triage (Base): on a task-caused
failure, delegate to `python-test-and-fix` (test failures) or `python-lint-typecheck`
(lint/type failures) per `SKILL.md` Composition rules — MUST NOT proceed to Phase 10 with
a known failure. On a pre-existing failure, record it in Output expectations'
"unresolved questions or known limitations" and proceed.

---

## Phase 10: Scope Control

#### diff-cover

See `rules/toolchain.md` section 7 and `python-test-and-fix` Step 11: measure with the marker
filter from Phase 9 and report the result as `measured with the marker filter; CI measures all
tests` (a pass here also passes in CI; a miss here may pass in CI).

#### pytest-benchmark

Write a test that calls the `benchmark` fixture (`result = benchmark(fn, data)`) with an assertion on the result.

```bash
uv run pytest <benchmark test file> -m "not integration and not production_paths_allowed" --benchmark-only
uv run pytest <benchmark test file> -m "not integration and not production_paths_allowed" --benchmark-save=baseline
uv run pytest <benchmark test file> -m "not integration and not production_paths_allowed" --benchmark-compare=baseline --benchmark-compare-fail=mean:10%
```

Benchmark baselines are written to `.benchmarks/`, which `.gitignore` already lists; do not commit them.

Review the diff only for the files this task touched (`git diff -- <files>`); a hunk that was already
in the Phase 1 baseline is not this task's.

**Completed when**: `diff-cover` coverage meets the threshold in `rules/toolchain.md`
Completion checklist, and a `pytest-benchmark` regression check has been run for any
performance-sensitive change (or this Phase does not apply).

---

## Phase 11: Production Readiness

```bash
rg "<old_module_name>" scripts/
```

Checklist (in addition to `rules/toolchain.md`):
- If a new MCP server was added, its `config/<key>_mcp_server.toml` setup follows `skills/mcp-server-add/workflow.md` — MUST NOT re-derive it here.
- Docstrings: update only for non-obvious or public-facing APIs the task changed (PEP 257).
  Run `python tools/check_docstrings.py` (read-only format check) when `scripts/` was touched.
- No placeholders or debug artifacts remain (`rules/coding.md` Constraint checks), per
  `skills/DESIGN.md` Pythonic safety constraints.

**Completed when**: the `rg` search for the old module/symbol name (when renaming/removing)
returns no remaining reference, and the MCP-server checklist in
`skills/mcp-server-add/workflow.md` is satisfied when a new server was added.

---

## Phase 12: Knowledge Compression

Decide what documentation the change implies, then act only within the task's scope
(`AGENTS.md` Global Rule 5):

- **Affected docs**: look up the target document via `routing.md` "Docs → task mapping" (which delegates to `docs/00_index.md`) — MUST NOT guess a filename; old single-file names no longer exist. Edit a doc only when the task requires it or the user asks; otherwise record it in Output expectations as a documentation follow-up (document, section, reason).
- **When a doc is edited**: use `python-documentation`, and run the checkers `routing.md` Tools "When to run which tool" lists for `docs/` changes (`tools/check_docs_quality.py`, `tools/check_docs_structure.py`, and the others that apply; `tools/run_validation_gates.py` selects them).
- **`routing.md`**: the Docs → task mapping lives in `docs/00_index.md`; do not add per-module entries to `routing.md`. Change `routing.md` only if a new task type or skill needs a row, and only when the task asks for it.
- **`deploy/deploy.sh`**: add a `cp` line only if a new `config/*.toml` file was introduced (see Phase 5 Step 5c File editing rules — module add/remove alone does not require a `deploy.sh` change)

When removing a module: delete the file, run `rg` for dangling imports and references, and list any doc that mentioned it as a documentation follow-up.

**Completed when**: each documentation need is either handled (doc edited and checked, or `deploy.sh` updated when required) or recorded as a follow-up, or the task is confirmed to need no documentation update.

---

## Output expectations

- changed files
- implementation summary
- tests added or changed (and, for a bug fix, confirmation that the reproducing test failed before the fix)
- pydantic models introduced (if any)
- architecture boundary check result (`lint-imports`)
- security scan result (`bandit`) and the manual security checks
- diff coverage (`diff-cover`)
- compatibility check result (`tools/check_compat_shims.py`)
- documentation updated, or documentation follow-ups recorded
- deploy.sh impact (if any)
- MCP registration impact (if any: `config/agent.toml`, binary registration; see `skills/mcp-server-add/workflow.md`)
- validation results (ruff, mypy, pytest, project gates, pre-commit)
- unresolved questions or known limitations (including pre-existing failures and any `Needs confirmation` check)
- next steps: the changes are uncommitted, so `git-commit-and-sync` commits them on request

---

## Required behavior

(Unrelated-change prohibition: see `AGENTS.md` Global Rule 5 — not repeated here.)
- Build architecture and implement only requirements stated in the task or confirmed in Phase 1/2 — record a suspected broader need or anything else as an open question in Output expectations instead of adding it.
- If a public API must change, state the change and its impact explicitly in the
  implementation summary (Output expectations) — never leave it undocumented.
- Fix the cause of a validation/test/type-check failure per Phase 9 — never disable the
  check itself to make the task appear complete.

See also `rules/coding.md` for project-wide prohibitions (suppression governance, commit hygiene).
