## Goal

Behavior tests for the compiled-agent pre-flight in `deploy/start_agent.sh`: the presence/executable check (`check_agent_binary (new)`) that fails fast with an actionable rebuild/redeploy message when `/opt/llm/bin/agent` is missing or non-executable. Implements `REQ-001` / `REQ-004` and asserts AC-001 and AC-002.

## Scope

Creates `tests/deploy/test_start_agent_preflight.py (new)`, mirroring the existing `tests/deploy/` subprocess-driver convention (`test_load_env_gate.py`). It drives the real `check_agent_binary (new)` function from `deploy/start_agent.sh` through a sourced bash driver and asserts:

- Missing/non-executable binary → non-zero exit + the actionable `[FATAL]` message and recovery commands (AC-001, `REQ-001`).
- Present, executable binary → startup proceeds (exit 0, no `[FATAL]`) (AC-002, `REQ-001`).

The optional `REQ-002` stale-warning and `REQ-003` missing-dict-warning paths are out of scope for this test (they hardcode `/opt/llm` paths and are environment-coupled); see Out of Scope.

## Assumptions

- `deploy/start_agent.sh` gains a `check_agent_binary (new)` function defined near the top (before the source guard) and a source guard that returns early when the script is sourced (see the `deploy/start_agent.sh` procedure, seq 01).
- Sourcing `deploy/start_agent.sh` therefore defines `check_agent_binary (new)` and returns before the `.env`/required-env-var/deployed-files/workflow gates, so a driver can call it in isolation without hitting the `/opt/llm` upstream checks.
- `check_agent_binary (new)` takes the binary path as its single positional argument (`$1`) and exits non-zero with the message on stderr when the binary is missing or non-executable.
- The driver runs under `bash` with a controlled PATH-only environment; sourcing the script and calling the function needs no `HOME`, network, or `uv`.
- The committed script (HEAD) does not yet contain the function or guard; this test is created in the same cycle that adds them.

## Design decisions

- **Source-a-driver, drive the real function.** The driver writes `source "<repo>/deploy/start_agent.sh"` then calls `check_agent_binary "<path>"`, exactly mirroring `test_load_env_gate.py` (which sources the real `deploy/load_env.sh`). This exercises the shipped artifact, not a copy of the logic.
- **Isolated binary directory via `tmp_path`.** Each test gets a `tmp_path/bin`; the "present" case drops an executable `agent` file there (mode 0755) to simulate a deployed binary, and the "missing" case leaves the directory absent. The driver passes that path as the argument.
- **Exit-code propagation.** The driver runs under `set -euo pipefail`; a failing `check_agent_binary (new)` aborts the driver with exit 1, which `subprocess.run(check=False)` captures as `returncode == 1`. The present case falls through to `echo PRESENT_OK` and exits 0.
- **PATH-only env.** `_run` clears `os.environ` to a minimal PATH (plus `HOME` only if later extended), so the driver cannot reach production paths or the network.

## Alternatives considered

- **Copy the function body into the driver.** Rejected: it tests a copy, not the shipped script; a drift between the two would go undetected.
- **End-to-end launch of the whole script.** Rejected: the upstream deployed-files and workflow gates hardcode `/opt/llm` paths and run `uv run python -m agent.workflow.validate`, so a full run requires production paths and network — impractical for a unit test.
- **Assert the `REQ-002`/`REQ-003` warning paths here.** Rejected: those notices read hardcoded `/opt/llm/dict/system.dic` and invoke `tools/manage_binaries.py check` against repo context, making them environment-coupled and flaky in CI. Keep this test focused on the deterministic `REQ-001` fail-fast path.

## Implementation

### Target file

`tests/deploy/test_start_agent_preflight.py` (new)

### Procedure

1. Create `tests/deploy/test_start_agent_preflight.py` with the driver helper, the run helper, and two behavior tests below.
2. Run the test under pytest and confirm both pass.

### Method

Write the file with the following content (mirroring `test_load_env_gate.py`):

```python
"""tests/deploy/test_start_agent_preflight.py

Behavior tests for the compiled-agent pre-flight in deploy/start_agent.sh:
the presence/executable check that fails fast before launch.
"""

import os
import pathlib
import subprocess

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
_SCRIPT = _REPO_ROOT / "deploy" / "start_agent.sh"
_AGENT = "agent"


def _write_driver(tmp_path: pathlib.Path, *, binary_present: bool) -> pathlib.Path:
    """Isolated bin dir plus a driver that sources the real script."""
    bin_dir = tmp_path / "bin"
    agent = bin_dir / _AGENT
    if binary_present:
        bin_dir.mkdir(parents=True)
        agent.write_text("#!/bin/sh\necho ok\n", encoding="utf-8")
        agent.chmod(0o755)
    driver_path = tmp_path / "driver.sh"
    driver_path.write_text(
        "\n".join(
            [
                "set -euo pipefail",
                f'source "{_SCRIPT}"',
                f'check_agent_binary "{agent}"',
                'echo PRESENT_OK',
                "",
            ]
        ),
        encoding="utf-8",
    )
    return driver_path


def _run(driver_path: pathlib.Path) -> subprocess.CompletedProcess[str]:
    env: dict[str, str] = {
        "PATH": os.environ.get("PATH", "/usr/local/bin:/usr/bin:/bin")
    }
    return subprocess.run(
        ["bash", str(driver_path)],
        capture_output=True,
        text=True,
        env=env,
        timeout=30,
        check=False,
    )


def test_missing_binary_aborts_and_names_recovery(tmp_path: pathlib.Path) -> None:
    driver = _write_driver(tmp_path, binary_present=False)
    result = _run(driver)
    assert result.returncode == 1
    assert "[FATAL]" in result.stderr
    assert "Agent binary not found or not executable" in result.stderr
    assert "deploy/build_binaries.sh" in result.stderr
    assert "deploy/deploy.sh" in result.stderr
    assert "PRESENT_OK" not in result.stdout


def test_present_binary_proceeds(tmp_path: pathlib.Path) -> None:
    driver = _write_driver(tmp_path, binary_present=True)
    result = _run(driver)
    assert result.returncode == 0
    assert result.stdout.strip().endswith("PRESENT_OK")
```

### Details

- The driver's `check_agent_binary "<agent>"` line is the single point of failure: under `set -euo pipefail` a non-zero exit stops the driver, so the missing-binary case yields `returncode == 1` and the present case reaches `echo PRESENT_OK`.
- The present-case `agent` file is written with mode 0755 so `-x` is true even when the test runner is not the file owner.
- Driver strings are single-quoted where literal and only the two known paths are interpolated; no command substitution is introduced into the driver.
- `check=False` on `subprocess.run` so the non-zero missing-binary exit is captured rather than raised.

## Compatibility considerations

- New file under `tests/deploy/`; does not modify or import any existing test. It reuses the same subprocess-driver idiom as `test_load_env_gate.py` but is independent.
- Depends on the source guard being added to `deploy/start_agent.sh` (seq 01). Without it, sourcing the script executes the whole body and the driver never reaches `check_agent_binary (new)`.

## Security considerations

- The driver sources the real repo script but returns before any `/opt/llm` access; the only filesystem writes are into `tmp_path`.
- No command substitution is interpolated into the driver beyond the two absolute paths; single-quote the literal lines to avoid shell expansion.
- `check_agent_binary (new)` inspects file existence/executability under a `tmp_path`-supplied path, not under `/opt/llm`.

## Rollback considerations

- N/A: delete the new test file. The change adds one file only.

## Validation plan

- Run `uv run pytest tests/deploy/test_start_agent_preflight.py -v`. Both tests must pass.
- Optionally run the whole `tests/deploy/` suite to confirm no cross-contamination.

## Completion criteria

- `test_missing_binary_aborts_and_names_recovery (new)` asserts exit 1, the `[FATAL]` message, the recovery commands, and absence of `PRESENT_OK (new)` (AC-001).
- `test_present_binary_proceeds (new)` asserts exit 0 and `PRESENT_OK (new)` (AC-002).
- `uv run pytest tests/deploy/test_start_agent_preflight.py -v` passes.

## Out of Scope

- The optional `REQ-002` stale-binary warning and `REQ-003` missing-dict warning assertion paths (environment-coupled; see Alternatives considered).
- Modifying `deploy/start_agent.sh` itself (that is the seq 01 target).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A (this doc is the test) |

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
- **Requirement ID**: `REQ-001`, `REQ-004`
- **Source issue**: `issues/20261029-233829_deploy001_missing-binary-precheck.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261030-114844_deploy001_missing-binary-precheck.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-125450
- **Related target files**: `tests/deploy/test_start_agent_preflight.py`
