# rules/toolchain.md — Shared Validation Sequence

## Impact-radius check (before broad behavior changes)

Before changing the default behavior, required arguments, or return contract of a
symbol referenced widely across the codebase (a shared validator, a config
dataclass, a widely-imported helper), measure its blast radius first — do not let a
full test run be the first place the scale of the change shows up:

```bash
rg -l '\bSymbolName\b' tests/ | wc -l   # files that could be affected
rg -c '\bSymbolName\b' tests/           # per-file reference counts
```

Motivated by: a single commit made `ProductionConfigValidator`'s validation
unconditionally strict. The change was correct in isolation, but its blast radius
was never measured before landing, and it broke ~231 tests across 12 files — a
scale that was only discovered after the fact, via a full-suite run.

- Run the `rg` count above (or equivalent) before changing a broadly-referenced
  symbol's behavior in a way existing callers/tests may rely on.
- If the count is large (rule of thumb: more than ~10 files, or more than ~20
  references), record the blast radius — in the Plan's `## Risks` section for a
  `plan`-driven change, or the commit message for a same-session refactor — so the
  follow-up work is budgeted as part of the same unit of work rather than
  discovered mid-implementation.
- This is a measurement step, not a blocker: a large blast radius does not mean
  "don't do it," only "know it before you start."

## Standard validation sequence

Run in this order after each implementation step. As one command, the full sequence runs via `uv run python tools/run_validation_gates.py`: it discovers the changed files, selects the gates each change needs, and runs them in this documented order (fast mode by default; `--full` adds the complete run). Use it as the single entry point for a diff, or follow the steps below for a per-step run.

### 1. Format and lint (ruff)

```bash
uv run ruff format scripts/
uv run ruff check scripts/ --fix
uv run ruff check scripts/       # confirm clean
```

### 2. Type check

```bash
uv run mypy --no-namespace-packages scripts/ tests/eventbus   # primary (same invocation as CI and pre-commit)
uv run pyright scripts/          # alternate (cross-validate)
```

Always pass `--no-namespace-packages`: CI (`.github/workflows/ci.yml`) and the pre-commit mypy hook (which adds `--no-incremental`) run mypy that way. Without it, mypy resolves `scripts/` modules under two names and can abort with `Source file found twice`, and its verdict on `# type: ignore` comments (`warn_unused_ignores`) differs, so a clean result without the flag does not show that CI passes.

Fix type errors at the source. See `rules/coding.md`, section "Suppression governance".

### 3. Architecture check (import-linter)

```bash
PYTHONPATH=scripts uv run lint-imports
```

### 4. Constraint verification (ast-grep)

```bash
ast-grep --pattern 'except: $$$' --lang python scripts/
```

### 5. Security scan (bandit)

```bash
uv run bandit -r scripts/ -c pyproject.toml -ll      # CI gate: medium severity and above
uv run bandit -r scripts/ -c pyproject.toml         # include low severity (informational)
uv run bandit -r scripts/ -l -ii            # high severity only
uv run bandit scripts/<file>.py             # single-file scan
```

Address high/medium severity findings before proceeding.

### 6. Tests (pytest)

```bash
uv run pytest tests/<package>/test_<affected_module>.py -v    # targeted (tests mirror scripts/; see skills/python-test-and-fix/workflow.md Test structure)
uv run pytest -v                                     # full suite
uv run pytest tests/mcp_servers/mdq/test_mdq_rag_boundary.py -v     # boundary enforcement (MDQ/RAG cross-DB and agent-layer direct access)
```

### 7. Diff-scoped coverage (diff-cover)

```bash
uv run coverage run -m pytest tests/
uv run coverage xml
  uv run diff-cover coverage.xml --compare-branch=master --fail-under=90
```

### 8. Pre-commit (final gate)

```bash
uv run pre-commit run --all-files
```

### 9. Diff review

```bash
git diff                  # review every changed line before staging
git add scripts/<file>.py # stage specific files
git diff --staged         # confirm what will be committed
```

Apply `AGENTS.md` Loop Prevention > Attempt Limit (3 attempts) to any step that fails
and is fixed in place before re-running; stop and report `Blocked` rather than
continuing to patch beyond that bound.

## Completion checklist (common to all tasks)

- `uv run ruff check scripts/` passes with no errors
- `uv run mypy --no-namespace-packages scripts/ tests/eventbus` passes (no new regressions vs pre-existing errors; `tests/eventbus` has none)
- `uv run bandit -r scripts/ -c pyproject.toml -ll` passes (no high/medium unaddressed)
- `PYTHONPATH=scripts uv run lint-imports` passes (no architecture boundary violations)
- `uv run pytest` passes with no new failures
- `uv run pytest tests/mcp_servers/mdq/test_mdq_rag_boundary.py` passes (MDQ/RAG boundary clean)
- `uv run diff-cover coverage.xml --compare-branch=master` ≥ 90% on changed lines
- `uv run pre-commit run --all-files` passes
- diff staged per `skills/git-commit-and-sync/SKILL.md`, section "Core rules"
- `deploy/deploy.sh` updated per `rules/env.md`, section "Architecture", if a new `config/*.toml` file was introduced
- `config/agent.toml mcp_servers` updated if a new MCP server was added

## Environment setup

- Do not activate the venv directly — run via `uv run python -m ...` (do not hardcode the venv path).

```bash
uv sync --dev --system-certs   # create .venv/ and install all deps (first time)
```

## Additional static analysis

```bash
uv run radon cc scripts/ -s -n C                   # cyclomatic complexity — grade C or worse
uv run python tools/check_module_size.py --top 5   # module byte-size gate (20480 B, baseline-gated, also pre-commit + CI)
uv run vulture scripts/ --min-confidence 80        # dead code detection
uv run semgrep --config=p/python scripts/          # semantic pattern enforcement
uv run pip-audit                                   # dependency vulnerability scan
```

## Syntax check

```bash
uv run python -m compileall -q scripts/
```

## Documentation consistency (per domain)

See `routing.md` Tools → "When to run which tool" for the full list of documentation checkers
and when to run each one. The domain-specific check:

```bash
uv run python tools/check_docs_consistency.py --domain mcp

# Skip specific checks
uv run python tools/check_docs_consistency.py --domain mcp --skip portdrift --skip tooldrift
```

`uv run check-mcp-docs` and `uv run check-agent-docs` are shorthand for `--domain mcp`/`--domain agent`
(additional args like `--skip` still work — see `tools/check_docs_consistency.py`'s `main_mcp()`/`main_agent()` wrappers).

Also available for `--domain agent|rag|deployment|overview|eventbus|shared|db`. It verifies, among other checks
(`--help` lists all available `--skip` values):
- `portdrift` — doc-mentioned port next to a `<name>-mcp` token vs. the port assigned in
  `config/agent.toml`'s `[mcp_servers.*]` sections
- `tooldrift` — backtick-quoted tool name on a "Tools:"/"ツール:" line vs. live
  `"name": "..."` entries in `scripts/mcp_servers/**/*.py` `TOOL_LIST` definitions
- Generic checks provided via `tools/_docs_consistency_lib.py`: broken internal Markdown
  links, removed-legacy-doc-file references, slash-command drift vs. `command_defs_list.py`,
  `scripts/`-path reference existence, and backtick-quoted function-reference existence

Identifier and config-key matching has an accepted limit: `check_docs_consistency.py` verifies
backtick-quoted `name()` function references and `*_db_path` config keys (extracted from
`scripts/db/config.py`). Bare snake_case variable references and non-`*_db_path` config-key
names are not mechanically verified against `scripts/` or `config/`. This gap is accepted
(owner: OWNER-PENDING) because exact identifier matching against prose yields high false
positives and would require an allowlist. See governance_04 §Accepted Limits.

## Scheduled CI Result Check — Operational Notes

Status as of 2026-10-25: not activated. `gh` is not authenticated on this machine, and the
recurring-task creation is pending owner approval (issue 20261023-173506 plan phase 3).

- Command: `uv run python tools/check_ci_results.py` (defaults: `--limit 10`, `--workflow`,
  `--branch`, and `--before` unset). Exit `0` = all examined runs green and no repeated
  failure; `1` = a failed run or a test failing in two or more examined runs; `2` = any `gh`
  read failure (missing binary, unauthenticated, query error, timeout). The tool is read-only:
  every `gh` call goes through a fixed read-only allowlist. See the `check_ci_results.py` entry
  in `tools/TOOL_DESCRIPTIONS.md`.
- Proposed schedule: a daily 09:00 JST run as a user-approved session recurring task.
  Activation is an owner action, not a tool behavior.
- Owner: the repository owner. Scheduling activation, `gh` re-authentication, and any future
  delivery-channel choice are owner actions.
- Delivery channel: stdout in the session only. No notification or push channel exists.
- Manual follow-up: on exit `1` with reported failures, the operator invokes the
  `python-test-and-fix` workflow (`skills/python-test-and-fix/SKILL.md`) against the reported
  test identifiers. The tool never performs the follow-up itself.
- Disable method: remove the session recurring task. If a schedule is ever added as a GitHub
  Actions workflow instead, disable that workflow.
