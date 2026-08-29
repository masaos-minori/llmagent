# Test Audit — Safety Evaluation, Execution Scope, and Abort Conditions

Load this file at Step 0 (unconditionally). It covers Step 2's safety evaluation and
the scope/abort rules `workflow.md` Steps 2-3 apply.

---

## Safety Evaluation (Step 2)

For every command `discovery.md` Step 1 discovered, classify it before anything is
executed. Do not run any command in this step (see `SKILL.md` Phase Boundaries — this
is an Analysis step).

### When starting local test infrastructure is allowed

You may start local, ephemeral test infrastructure (a container, a local SQLite/Postgres
instance, a cloud-service emulator) only when all of the following hold:
- it is already defined by repository configuration or tooling (e.g. a
  `docker-compose.test.yml`, an existing `testcontainers`/emulator fixture, a
  documented local setup command) — do not invent new infrastructure the repository
  does not already define;
- it is isolated from production (no production hostnames, credentials, or shared
  state);
- it can be torn down after the run without leaving persistent state behind;
- starting it requires no production credential and no unverified external service.

A command that only needs infrastructure meeting all four bullets is classified `Safe
with isolated infrastructure`; record the exact setup/teardown commands alongside it.

### No test-only configuration changes

Do not change configuration, environment variables, feature flags, or other runtime
settings solely to make a test runnable. If a test cannot run without such a change,
do not make the change — classify it `Blocked` or `Not runnable` (see `evidence.md`
Result Classification) and record the specific missing environment requirement.

### Prohibited test execution

Classify a command `Prohibited` (do not run it in `workflow.md` Step 3/4) per the
conditions in `rules/ai-execution.md` Repository Tool Usage rule 7.

If a safe isolated test environment is unavailable, or starting one would require a
change forbidden above:
- Mark the command `Blocked` or `Not runnable` (see `evidence.md` Result
  Classification).
- Record the missing environment, service, or credential.
- Do not report it as passed.

Output: every Step 1 command classified as one of `Safe` / `Safe with isolated
infrastructure` / `Blocked` / `Not runnable` / `Prohibited`, plus the Full-Suite
Execution Scope this defines for Step 3 below.

---

## Full-Suite Execution Scope and Abort Conditions (Step 2-3)

**Scope**: "all existing tests" means every command Step 1 discovered that Safety
Evaluation classifies `Safe` or `Safe with isolated infrastructure` above. It does not
mean literally every test in the abstract — a command classified
`Blocked`/`Not runnable`/`Prohibited` is out of this cycle's execution scope by
definition, not a shortfall to apologize for.

**Do not stop after the first failure** within that scope — this remains the default
for a command that is running normally.

**Abort conditions — stop the current command** (not the whole Step 3 run) and record
it as `Blocked`, instead of letting it run to exhaustion, when any of the following
happens mid-execution:
- the command exceeds a clear timeout with no progress output (a hang, not a slow but
  progressing suite),
- the command begins behaving in a way Safety Evaluation did not clear (e.g.
  attempting network access to a non-local host, prompting for credentials, writing
  outside the isolated test environment),
- 3 or more consecutive environment-level errors occur (e.g. "connection refused",
  import errors unrelated to the code under test) — this indicates a broken harness,
  not real test failures; stop that command, classify the whole command `Blocked`, and
  do not continue interpreting its remaining output as individual test failures.

**Stop the entire Step 3 run** (not just one command) only when: the isolated test
environment itself becomes unusable (e.g. an ephemeral DB/container Safety Evaluation
started has crashed and cannot be restarted per its own teardown/setup commands), or a
Prohibited test execution condition is detected that Safety Evaluation did not catch.
Report exactly which commands were and were not attempted.
