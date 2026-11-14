# Build the MCP server binaries as one multi-entry binary

## Priority
Medium

## Summary
Replace the ten per-server MCP Nuitka `--onefile` binaries with one multi-entry (multidist) binary that is installed under the ten existing `mcp_<server>` file names and selects the server to run from its own file name. A rebuild of the whole MCP set then processes, links, and packages the shared third-party code once instead of ten times. The agent binary stays separate.

## Background
Prior art: `issues/done/20261019-103807_deploybin001_binary-freshness-and-rollback-in-deploy.md` introduced the per-binary build info, freshness check, staged swap, and rollback that this change must keep working. `issues/done/20260717-171259_nuitka_onefile_packaging_proposal.md` introduced the Nuitka `--onefile` packaging.

Current behavior:
- `Explicit in code`: `deploy/build_binaries.sh` builds the agent and each MCP server as its own Nuitka run, each from a generated launcher that applies `ConfigLoader.restrict_to(...)` before importing the server module.
- `Explicit in code`: `config/agent.toml` launches each subprocess-mode MCP server through a single-element `cmd` that names a per-server file in the production bin directory; `deploy/deploy.sh` lists the same names in `BINARY_NAMES`; `tools/manage_binaries.py` keeps one `BINARY_SOURCES` entry per name.
- `Explicit in code`: `CommandValidator` resolves symlinks with `os.path.realpath` and accepts a command in the bin directory only when the resolved path is a regular file directly inside that directory and the directory is not group- or world-writable. It returns the resolved path.

Measurements (`Operationally observed`, 2026-11-15, a 4-thread 7GB build host, Nuitka 4.2.2, ccache working after the ccache directory fallback, canonical `__helpers.h` wrapper, and parallel build work already merged):
- Warm re-build of one MCP server binary: 141-167 seconds. Nuitka's Python-level processing and C generation, which ccache cannot cache, took about 70-80 seconds of that; for the agent it was 124 of 233 seconds.
- Third-party code dominates each MCP binary: for the shell server, 332 generated module C files of which 33 are project modules (the rest: pydantic, fastapi, uvicorn, anyio, starlette, and similar), and the ten servers share this set.
- Prototype, outside the repository: one Nuitka invocation with ten mains took 722 seconds with a partly warm cache and 293 seconds fully warm (every C file a ccache hit), against roughly ten times 150 seconds sequentially. The single output was 51MB against roughly 320MB for the ten binaries.
- Prototype dispatch: copies of the single binary named after two servers each started the matching server; a symlink with a name that is not an entry failed with `failed to detect what to do for filename derived name`.
- Prototype startup cost for one server: time to listening rose from about 1.0 to 1.2 seconds, and the per-process extraction directory grew from about 110MB to about 192MB.

Deploy pattern (`Operationally observed` from the repository history, computed from commit paths since 2026-08-01): when about ten commits are deployed together, an average deploy marks about nine of the eleven binaries stale, so rebuilding most of the set is the typical case, not the exception.

## Problem
Each of the ten MCP server binaries repeats the same Nuitka Python-level processing, C link, and onefile packaging for the same third-party dependencies. These costs are not removed by ccache, so the rebuild time of the MCP set grows linearly with the number of servers even when every C object is cached.

## Reason for Change
The cheaper speed-ups (ccache directory fallback, canonical `__helpers.h` for cross-binary ccache hits, parallel builds) are already merged. This is the largest remaining lever for deploy lead time and build-host load. Nothing here is a correctness defect, so it is not urgent.

## Implementation Intent
- Build the ten MCP servers in one Nuitka invocation with one main per server; keep one generated launcher per server so per-server configuration isolation is applied before that server's import, exactly as today. The agent keeps its own binary.
- Keep the installed interface unchanged: ten files with the existing `mcp_<server>` names in the bin directory, so `config/agent.toml` `cmd` entries and the start scripts need no change. How the ten names are produced from the single build (copies or hardlinks) is a design decision for the Plan, constrained by `CommandValidator` (see Constraints).
- Treat the combined binary as one rebuild unit: the freshness check, build info, staged swap, and rollback must handle the ten names as one artifact and keep the all-or-nothing swap semantics.
- Keep the canonical `__helpers.h` ccache wrapper and parallel build; they still apply to the agent binary and to partial rebuilds.
- Decide the install method and the host `/tmp` sizing with evidence from a real build on the production-like host before the Plan is frozen.

## Target Files or Areas
- `deploy/build_binaries.sh` (entry table, launcher generation, multi-main invocation, producing the ten names)
- `tools/manage_binaries.py` (staleness table, build info, check, swap, rollback)
- `deploy/deploy.sh` (binary list, placement, pre-checks)
- `deploy/start_agent.sh` (binary pre-flight; confirm no change is needed)
- `scripts/agent/http_lifecycle_command_validator.py` (read only: confirm the install method passes the validator)
- `tests/tools/test_manage_binaries.py`, `tests/tools/test_build_binaries_script.py`, `tests/mcp_servers/test_config_isolation_import.py`, `tests/deploy/test_start_agent_preflight.py`
- `docs/90_deployment/deployment_01_deployment.md` (compiled artifacts section), `skills/deploy/SKILL.md`, `skills/deploy/workflow.md`, `rules/env.md`

## Required Changes
- Add a multi-main build path to `deploy/build_binaries.sh` that produces one binary for the ten MCP servers and installs it under the ten existing names; keep the agent as a separate build.
- Keep each launcher applying `ConfigLoader.restrict_to(...)` before the server import, and keep the launcher a top-level module whose name does not collide with a `scripts/` package.
- Change `tools/manage_binaries.py` so staleness, build info, swap, and rollback treat the MCP set as one unit: a change under any server's embedded paths marks all ten names stale, and a swap or rollback replaces all ten together.
- Update the binary list and verification in `deploy/deploy.sh` so a missing or mismatched name is caught before deploy.
- Update the tests listed under Testing Expectations.
- Record measured before and after wall time, extraction size, and startup time in the Plan's Execution Status.

## Constraints
- The agent must still find each server at the existing `/opt/llm/bin/mcp_<server>` path; `config/agent.toml` `cmd` entries stay unchanged.
- Server selection is by the invoked file name and must match an entry name exactly; any other name fails at startup.
- `CommandValidator` resolves symlinks and returns the resolved path, and accepts only regular files directly in a non-group-writable, non-world-writable bin directory. A symlink install therefore risks losing the invoked name; copies or hardlinks are the candidates. Copies cost the single binary's size ten times (more than the ten separate binaries today); hardlinks cost it once but must be replaced together on every swap.
- Per-process extraction size grows (measured about 110MB to about 192MB for one server), so ten concurrent MCP processes need more `/tmp` space; the production `/tmp` backing is not known.
- One broken MCP server module fails the single build for all ten servers, and a change to any server replaces all ten binaries. This coupling is the accepted trade-off of the design and must be stated in the documentation.
- The multi-main behavior was verified only on Nuitka 4.2.2, which `pyproject.toml` pins.
- Atomic swap and rollback guarantees from `deploybin001` must not weaken.

## Acceptance Criteria
- One build run produces the ten `mcp_<server>` executables, and each, started with dummy configuration in an isolated environment (never against `/opt/llm`), starts the matching server and not another.
- Starting the binary under a name that is not an entry fails with a clear error, and `deploy/deploy.sh` rejects a bin directory where one of the ten names is missing.
- `uv run python tools/manage_binaries.py check` reports all ten MCP names stale after a change under any one server's embedded paths, and reports none of them stale after a change that only the agent embeds.
- A swap followed by a rollback restores all ten names together, and a build failure leaves the previous ten names untouched.
- `CommandValidator` accepts the installed names in the bin directory, shown by a test or a recorded manual run that uses the chosen install method.
- On the same build host, the warm rebuild time of the ten MCP names is at most half of the sum of the ten separate warm builds, recorded in the Plan's Execution Status together with the extraction size and time to listening.
- The existing tests that read `deploy/build_binaries.sh` and `tools/manage_binaries.py` pass after being updated, and `uv run python tools/run_validation_gates.py` reports no `Fail`.

## Testing Expectations
- Unit tests in `tests/tools/test_manage_binaries.py` for the combined staleness unit, build info, swap, and rollback across the ten names.
- Script tests with a stubbed `uv` in `tests/tools/test_build_binaries_script.py` for the multi-main invocation, the ten installed names, and the failure case that leaves `BIN_DIR` untouched.
- An update of `tests/mcp_servers/test_config_isolation_import.py` so the entry table still maps each server class to its configuration file.
- A `CommandValidator` test or recorded manual run for the chosen install method.
- Manual verification on a build host: a real build, a start of at least two names with dummy configuration, and the timing and size measurements. The real Nuitka build is not run in CI.
- `ruff`, `mypy`, `bash -n`, and `uv run python tools/check_tool_descriptions_sync.py` where applicable.

## Documentation Impact
Yes. The compiled-artifacts section of the deployment document, `skills/deploy/SKILL.md`, `skills/deploy/workflow.md`, and `rules/env.md` must describe: that the MCP servers are one built artifact installed under ten names; how freshness, swap, and rollback treat it; the failure behavior when the name does not match an entry; the all-or-nothing coupling; and the `/tmp` sizing note. The documentation must follow `skills/DESIGN.md` Docs content policy: no file inventories, no literal ports, and no counts of binaries or servers.

## Out of Scope
- Folding the agent binary into the multi-entry binary.
- Upgrading Nuitka, or changing the Nuitka flags other than adding the extra mains.
- Changing MCP server behavior, MCP server configuration files, or `config/agent.toml` `cmd` entries.
- Changing the staleness rule to use per-binary import closures.
- Removing or changing the already merged ccache, canonical `__helpers.h`, or parallel build support.
- Changing the Event Bus, ingestion, or other components that run from source.

## Dependencies
N/A: none. The sibling check found no open issue or in-flight plan that targets these files; `plans/20261115-061459_deploydoc001_lifecycle-deployment-docs.md` edits agent lifecycle documentation only and does not overlap.

## Unresolved Questions
- `不明`: which install method works with `CommandValidator` in practice. Copies were verified to dispatch correctly; symlinks and hardlinks were not tried. Check which path the agent actually spawns (the resolved path that `CommandValidator` returns, or the configured path), because dispatch depends on the invoked name.
- `不明`: whether the production host's `/tmp` is memory-backed and has room for the larger per-process extraction of ten concurrent MCP servers.
- `不明`: whether the owners accept the coupling that a failure or change in one MCP server rebuilds and replaces all ten binaries.
- Assumption: the prototype result (about 293 seconds warm) carries over to the repository's real launchers; the prototype launchers and scripts were session scratch files and are not in the repository, so the first implementation step regenerates and re-measures them.
- Assumption: the multi-main behavior and the name-based dispatch hold on the Nuitka version pinned in `pyproject.toml` at implementation time.

## AI Implementation Instruction
- Do not modify files outside Target Files or Areas, and do not implement anything listed under Out of Scope.
- Keep per-server configuration isolation and the existing launcher import order intact; do not move `ConfigLoader.restrict_to(...)` after the server import.
- Do not weaken the atomic swap, rollback, or integrity checks in `tools/manage_binaries.py`.
- Do not use a symlink install unless the open `CommandValidator` question is resolved with evidence.
- Never run a build or a started server against `/opt/llm`; use temporary directories and dummy configuration.
- If an Unresolved Question blocks a design choice, stop and report it instead of guessing.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261115-072739
- **Related target files**: `deploy/build_binaries.sh`, `tools/manage_binaries.py`, `deploy/deploy.sh`, `deploy/start_agent.sh`, `scripts/agent/http_lifecycle_command_validator.py`, `tests/tools/test_manage_binaries.py`, `tests/tools/test_build_binaries_script.py`, `tests/mcp_servers/test_config_isolation_import.py`, `tests/deploy/test_start_agent_preflight.py`, `docs/90_deployment/deployment_01_deployment.md`, `skills/deploy/SKILL.md`, `skills/deploy/workflow.md`, `rules/env.md`
