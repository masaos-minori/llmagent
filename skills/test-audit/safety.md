# Test Audit — Safety Evaluation, Execution Scope, and Abort Conditions

Load this file at Step 0 (unconditionally). It covers Step 2's safety evaluation and
the scope/abort rules `workflow.md` Steps 2-3 apply.

---

## Safety Evaluation (Step 2)

For every command `discovery.md` Step 1 discovered, classify it before anything is
executed. MUST NOT run any command in this step (see `SKILL.md` Phase Boundaries — this
is an Analysis step).

### When starting local test infrastructure is allowed

You may start local, ephemeral test infrastructure (a container, a local SQLite/Postgres
instance, a cloud-service emulator) only when all of the following hold:
- it is already defined by repository configuration or tooling (e.g. a
  `docker-compose.test.yml`, an existing `testcontainers`/emulator fixture, a
  documented local setup command) — MUST NOT invent new infrastructure the repository
  does not already define;
- it is isolated from production (no production hostnames, credentials, or shared
  state);
- it can be torn down after the run without leaving persistent state behind;
- starting it requires no production credential and no unverified external service.

A command that only needs infrastructure meeting all four bullets is classified `Safe
with isolated infrastructure`; record the exact setup/teardown commands alongside it.

### Verify the test suite's own isolation before classifying `Safe`

Running the suite is itself an Execution with real side effects. Before classifying any
test command `Safe`, confirm from files, without executing anything, that the suite
cannot touch production state:
- Read `rules/env.md` for the production paths, databases, and service ports.
- Find the repository's isolation mechanism for tests (for example a guard in
  `conftest.py` that redirects or rejects production paths, or per-test temporary
  directories). Cite the file where it was found, and record what it covers and what it
  does not. Here, `tests/conftest.py` builds a temporary root (a copy of `config/` with
  the writable-state paths rewritten) and an autouse guard that fails a test opening a
  SQLite database or a `FileHandler` under `/opt/llm`; other kinds of write are not
  guarded.
- Classify `Blocked` (and MUST NOT run) only when no mechanism exists for a production
  path that the tests reach, found with `rg` in `tests/` or in the configuration the tests
  load. A kind of write the mechanism does not cover, but that no test reaches, is a
  residual risk: record it for the report's `# 9`, not as a block.
- Tests the mechanism exempts can write production state. In this repository that is the
  `production_paths_allowed` marker (used in `tests/conftest.py`; it is not declared in
  `pyproject.toml` `markers`). List them with `rg -l production_paths_allowed tests` and
  treat them as a separate command, classified `Blocked` by default; run the rest with
  `-m "not production_paths_allowed"`.
- Check the `markers` in `pyproject.toml`. A marker for tests that start real
  subprocesses or services (this repository's `integration` marker) makes those tests a
  separate command, classified on its own — for example `-m "not integration"` and
  `-m integration` are two candidates.

### Collision with running services

The suite runs on a host whose configuration points at `/opt/llm` (see
`tests/conftest.py`), so production services may be listening there. Before classifying
a command that starts subprocesses or servers (the `integration` tests and any test that
binds a socket) `Safe`, compare the ports the tests name with the ports in use:

```bash
rg -n "localhost|127\.0\.0\.1" tests --glob '*.py'    # ports the tests name
ss -ltnH                                               # ports listening now
```

For each overlap, read the test: a URL string passed to a mocked client is harmless; a
real bind or connect to a listening port is a collision. Classify the affected files
`Blocked` (exclude them with `--ignore`/`--deselect`) and record the port and the
listening process (`ss -ltnpH 'sport = :PORT'`). Whether any test here binds a fixed port
was not established when this rule was written; the check decides it per run.

### Commands that modify the working tree

The audit is read-only. A command that rewrites tracked files is not run as written:
- `uv run ruff format scripts/` and `uv run ruff check scripts/ --fix` (the
  `rules/toolchain.md` forms) → run the check-only forms `uv run ruff format --check
  scripts/` and `uv run ruff check scripts/`.
- `pre-commit run` (any form) → `Blocked`: it can rewrite files and stash other sessions'
  unstaged changes; the check-only `ruff`, `mypy`, and `lint-imports` commands cover its
  main hooks.
- Gitignored outputs (`.coverage`, `coverage.xml`, `.testmondata*`) are expected. Any
  other new or modified file after a run is handled by `workflow.md` Step 3's
  post-run check.

### No test-only configuration changes

MUST NOT change configuration, environment variables, feature flags, or other runtime
settings solely to make a test runnable. If a test cannot run without such a change,
classify it `Blocked` or `Not runnable` (see `evidence.md`
Result Classification) and record the specific missing environment requirement.

### Prohibited test execution

Classify a command `Prohibited` (MUST NOT run it in `workflow.md` Step 3/4) per the
conditions in `rules/ai-execution.md` Repository Tool Usage rule 7.

If a safe isolated test environment is unavailable, or starting one would require a
change forbidden above:
- Mark the command `Blocked` or `Not runnable` (`evidence.md` Result Classification), record the missing environment, service, or credential, and MUST NOT report it as passed.

Output: every Step 1 command classified as one of `Safe` / `Safe with isolated
infrastructure` / `Blocked` / `Not runnable` / `Prohibited`, plus the Full-Suite
Execution Scope this defines for Step 3 below.

---

## Full-Suite Execution Scope and Abort Conditions (Step 2-3)

**Scope**: "all existing tests" means every command Step 1 discovered that Safety
Evaluation classifies `Safe` or `Safe with isolated infrastructure` above. A command
classified `Blocked`/`Not runnable`/`Prohibited` is out of this cycle's execution
scope by definition, not a shortfall.

**MUST NOT stop after the first failure** within that scope — this remains the default
for a command that is running normally.

**Abort conditions — stop the current command** (not the whole Step 3 run) and record
it as `Blocked`, instead of letting it run to exhaustion, when any of the following
happens mid-execution:
- the command produces no new output for 10 minutes (a hang, not a slow but progressing
  suite; 10 minutes is the default — use a shorter or longer limit only if the user's
  scope hint or the repository's configured timeout says so). For a background run
  writing to an output file, check the file's modification time (`stat -c %Y <file>`)
  against `date +%s`; `pytest-timeout` is installed but no timeout is configured in
  `pyproject.toml`, so the audit does not rely on it,
- the command begins behaving in a way Safety Evaluation did not clear (e.g.
  attempting network access to a non-local host, prompting for credentials, writing
  outside the isolated test environment),
- 3 or more consecutive environment-level errors occur (e.g. "connection refused",
  import errors unrelated to the code under test) — this indicates a broken harness,
  not real test failures; stop that command, classify the whole command `Blocked`, and
  MUST NOT continue interpreting its remaining output as individual test failures.

**Stop the entire Step 3 run** (not just one command) only when: the isolated test
environment itself becomes unusable (e.g. an ephemeral DB/container Safety Evaluation
started has crashed and cannot be restarted per its own teardown/setup commands), or a
Prohibited test execution condition is detected that Safety Evaluation did not catch.
Report exactly which commands were and were not attempted.
