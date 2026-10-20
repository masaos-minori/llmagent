## Goal
Create `tests/deploy/test_load_env_gate.py` so the `.env` parser and the required-variable gate that
`deploy/load_env.sh` provides are executed and asserted, including the already-exported-variable precedence, the
unsafe-line skip, the empty-value rule, and the permission warning.

## Scope
- New file `tests/deploy/test_load_env_gate.py` (new) with one driver-writing helper, one runner helper, and
  eight cases.
- No `tests/deploy/__init__.py`: `tests/agent` and `tests/eventbus` have none, and `pyproject.toml`'s
  `testpaths = ["tests"]` discovers the directory without it.
- No change to `deploy/load_env.sh` (seq 03) or `deploy/start_agent.sh`.

## Assumptions
- The cases run `bash` on a small driver script that sources the real library by absolute repository path and
  passes only `tmp_path` fixtures as its configuration and `.env` files. Nothing under `/opt/llm` is read or
  written, which is the Plan's `T-4` constraint.
- The gate is expected to be reached only through `bash`, so the driver sets `set -euo pipefail` itself; that is
  also what proves the library does not depend on being sourced with particular shell options.
- `collect_required_env_vars` finds references with `grep -oE '\$\{ENV:[A-Za-z_][A-Za-z0-9_]*\}'`
  (`deploy/start_agent.sh` lines 72-80), so a fixture configuration only has to contain the reference text; it is
  not parsed as TOML.
- These cases spawn only `bash`, not a server or a network service, so they are not marked `integration`: the
  marker is documented in `pyproject.toml` as "integration tests that start real subprocesses".

## Design decisions
- Drive the real library instead of reimplementing its logic in Python: a test that copied the rules would keep
  passing when the shell file drifts, which is the failure mode the Plan lists under Risks.
- Build the driver from a list of literal lines with absolute fixture paths instead of a formatted template, so no
  shell `${...}` expansion has to be escaped inside a Python format string.
- Pass a minimal `env` (`PATH` only, plus the case's own variables) to `subprocess.run`: it keeps a developer's
  or CI runner's exported variables from silently satisfying the gate, the same reason
  `tests/agent/test_http_lifecycle_env_allowlist_integration.py` uses `clear=True`.
- Assert the missing-variable message on its contract parts (`[FATAL]`, the variable name, the generation hint,
  the re-run command) rather than the whole multi-line string, so wording tweaks that keep the contract do not
  break the suite.

## Alternatives considered
- Use `bash -c` with an inline script: rejected; the quoting of the driver becomes the thing under test.
- Test the gate by running `deploy/setup_services.sh`: rejected; that script reaches the remote LLM health gate,
  which ebops002 has not made skippable yet.
- Skip the permission-warning case: rejected; the warning moved into `parse_env_file` (seq 03) is behavior no
  other test observes.

## Implementation
### Target file
`tests/deploy/test_load_env_gate.py` (new)

### Procedure
1. Create the `tests/deploy` directory by writing this file into it.
2. Write the module docstring, the `import` lines, and the two path constants.
3. Write the driver helper and the runner helper.
4. Write the eight cases listed below.

### Method
Helpers (the imports are written as plain module imports so no name has to be imported from another module):

```python
"""tests/deploy/test_load_env_gate.py

Behavior tests for deploy/load_env.sh: the .env parser and the required-variable gate.
"""

import os
import pathlib
import subprocess

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
_LIBRARY = _REPO_ROOT / "deploy" / "load_env.sh"
_SHARED_TOKEN = "EVENTBUS_AUTH_TOKEN"


def _write_driver(tmp_path: pathlib.Path, *, config_text: str, with_env_file: bool) -> pathlib.Path:
    """Fixture configuration plus a driver script that sources the real library."""
    config_path = tmp_path / "eventbus.toml"
    config_path.write_text(config_text, encoding="utf-8")
    env_path = tmp_path / ".env"
    if with_env_file:
        env_path.write_text("", encoding="utf-8")
        # Default to a tight mode so the permission warning stays out of the cases that
        # are not about permissions.
        env_path.chmod(0o600)
    driver_path = tmp_path / "driver.sh"
    driver_path.write_text(
        "\n".join(
            [
                "set -euo pipefail",
                f'REPO_ROOT="{tmp_path}"',
                f'source "{_LIBRARY}"',
                f'if [[ -f "{env_path}" ]]; then',
                f'    ENV_FILE="{env_path}"',
                '    parse_env_file "${ENV_FILE}"',
                "fi",
                f'require_env_vars "Event Bus" "bash deploy/setup_services.sh" "{config_path}"',
                'echo "GATE_OK ${EVENTBUS_AUTH_TOKEN:-unset}"',
                "",
            ]
        ),
        encoding="utf-8",
    )
    return driver_path


def _run(driver_path: pathlib.Path, *, extra_env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    env: dict[str, str] = {"PATH": os.environ.get("PATH", "/usr/local/bin:/usr/bin:/bin")}
    env.update(extra_env or {})
    return subprocess.run(
        ["bash", str(driver_path)],
        capture_output=True,
        text=True,
        env=env,
        timeout=30,
        check=False,
    )
```

Cases:

| Case | Fixture | Assertion |
|---|---|---|
| `test_missing_variable_aborts_and_names_it` | configuration references the shared token, no `.env`, nothing exported | returncode 1; stderr contains `[FATAL]`, the variable name, `openssl rand -hex 32`, and `Then re-run: bash deploy/setup_services.sh`; stdout has no `GATE_OK` |
| `test_exported_variable_satisfies_the_gate` | same configuration, `extra_env` exports the variable | returncode 0; stdout ends with the exported value |
| `test_exported_variable_is_not_overridden_by_the_env_file` | `.env` defines a different value, `extra_env` exports the other | returncode 0; stdout shows the exported value, not the file's |
| `test_empty_value_in_the_env_file_counts_as_missing` | `.env` line `EVENTBUS_AUTH_TOKEN=` | returncode 1; stderr names the variable |
| `test_command_substitution_in_a_value_is_not_executed` | `.env` line assigns `$(touch <tmp_path>/pwned)` and a second valid variable | returncode 0; `pwned` does not exist; stdout shows the literal `$(touch` text |
| `test_unsafe_line_is_skipped_with_a_warning` | `.env` contains `export BAD=1` plus a valid token line | returncode 0; stderr contains `Skipping unsafe .env line` and `BAD` is not exported |
| `test_loose_permissions_are_warned_and_tight_ones_are_not` | `.env` with mode `0o644`, then the same file at `0o600` | first run's stderr contains `permissions are 644` and `chmod 600`; second run's stderr contains neither |
| `test_gate_only_scans_the_files_it_is_given` | a second configuration file that references another variable but is never passed to the gate | returncode 0 |

The last case is the one that protects `deploy/start_agent.sh`: its own gate scans
`config/agent.toml` and `config/*_mcp_server.toml` only, so a variable that appears only in the Event Bus
configuration cannot make the agent refuse to start.

### Details
The fixture file is created by the case that needs it, after the helper's empty placeholder, so the driver's
existence check stays the only path-selection logic under test, and rewriting an existing file keeps its `0o600`
mode:

```python
env_path = tmp_path / ".env"
env_path.write_text("EVENTBUS_AUTH_TOKEN=\n", encoding="utf-8")
```

No `pytest` import is needed: every case asserts on the `CompletedProcess` the runner returns. The permission case
is the one that calls `chmod(0o644)` on the fixture file before running the driver.

## Compatibility considerations
- The cases depend on seq 03 existing; run them after it, and use the revert-and-bite check to confirm they fail
  against `HEAD`.
- `deploy/start_agent.sh` is unchanged, so its gate keeps its own wording; the shared contract is asserted here
  through the library, not through that script.
- No case reads `config/eventbus.toml`, so the suite does not need the variable to be set in a developer
  environment.

## Security considerations
- Every fixture secret is an obviously fake string, and no case prints a secret: the missing-variable assertions
  check names, not values.
- The command-substitution case is the guard that the parser stays parse-only.
- Fixtures live under `tmp_path`, so nothing is written into the repository or the production install root.

## Rollback considerations
Single-target removal: `git rm tests/deploy/test_load_env_gate.py` (or revert the commit that adds it). Removing
the last file in `tests/deploy` leaves the directory behind locally but untracked in git.

## Validation plan
| Check | Command | Expected outcome |
|---|---|---|
| Targeted | `uv run pytest tests/deploy/test_load_env_gate.py -q -p no:randomly` | eight cases green |
| Revert-and-bite | run the same command with `deploy/load_env.sh` temporarily absent | the cases fail at the `source` step, proving they bite |
| Static | `uv run ruff check tests/deploy/test_load_env_gate.py` | no findings (in particular no unused import) |
| Stale procedure, pre-implementation | `uv run python tools/stale_detector.py implementations/20261020-112551_06_tests_deploy_test_load_env_gate.py.md` | reports only `new_target_dir_missing` for `tests/deploy`: this procedure creates that directory, and `stale_detector` requires the parent of a declared-new target to exist before it will check anything else |
| Stale procedure, post-implementation | same command after the file is written | reports only `new_target_exists`, the accepted reading for an implemented declared-new target (the archived procedures under `implementations/done/` keep their `(new)` markers for the same reason) |

## Completion criteria
- The file exists with eight cases and both helpers, and `uv run pytest tests/deploy -q` is green.
- No fixture path points at `/opt/llm`.
- The command-substitution case proves no file is created by a `.env` value.

## Out of Scope
- `deploy/load_env.sh` (seq 03) and `deploy/setup_services.sh` (seq 04).
- `tests/agent/test_http_lifecycle_env_allowlist_integration.py` (seq 09).
- Any test that runs `deploy/setup_services.sh` end to end, which ebops002 has to unblock first.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261020-130913 | 20261020-130913 | after seq 03 file created (creates tests/deploy); helpers and eight cases per Details |
| 2 | Add or update tests per Validation plan | Completed | — | 20261020-130913 | this document is the test target this document is the test target: 8 cases green |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261020-130913 | ruff format/check and mypy clean; revert-and-bite: library absent -> 8 failed, restored -> 8 passed; stale_detector pre-implementation reported only new_target_dir_missing, post-implementation only new_target_exists, both the accepted readings recorded in this doc's Validation plan |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20261020-130913 | docs are owned by seq 07, 08 N/A: docs owned by seq 07, 08 |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-003, REQ-006
- **Source issue**: `issues/20261019-210937_ebsec001_eventbus_auth_token_startup_block.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/done/20261020-111348_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261020-112551
- **Related target files**: `tests/deploy/test_load_env_gate.py`, `deploy/load_env.sh` (seq 03),
  `deploy/start_agent.sh` (read-only reference for the gate semantics),
  `tests/agent/test_http_lifecycle_env_allowlist_integration.py` (seq 09)