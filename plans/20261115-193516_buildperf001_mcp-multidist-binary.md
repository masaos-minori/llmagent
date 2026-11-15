# Build the MCP server binaries as one multi-entry binary

## Goal
Replace the ten per-server MCP Nuitka `--onefile` binaries with one multi-entry (multidist)
binary installed under the ten existing `mcp_<server>` names, so a rebuild processes, links,
and packages the shared third-party code once instead of ten times, while keeping the
installed interface, freshness/swap/rollback semantics, and per-server configuration
isolation unchanged.

## Priority
Medium

## Scope
- **In-Scope**:
  - Add a multi-main build path to `deploy/build_binaries.sh` that produces one binary for
    the ten MCP servers (one generated launcher per server, each applying
    `ConfigLoader.restrict_to(...)` before that server's import) and installs it under the
    ten existing `mcp_<server>` names; keep the agent as a separate build.
  - Change `tools/manage_binaries.py` so staleness, build info, swap, and rollback treat the
    ten MCP names as one rebuild unit (all-or-nothing).
  - Update `deploy/deploy.sh` so a missing or mismatched name is caught before deploy.
  - Update the tests listed under Testing Expectations.
  - Record measured before/after wall time, extraction size, and time-to-listening in the
    Plan's Execution Status.
  - Update the deployment documentation described under Documentation Impact.
- **Out-of-Scope**:
  - Folding the agent binary into the multi-entry binary.
  - Upgrading Nuitka, or changing the Nuitka flags other than adding the extra mains.
  - Changing MCP server behavior, MCP server configuration files, or `config/agent.toml`
    `cmd` entries.
  - Changing the staleness rule to use per-binary import closures.
  - Removing or changing the already merged ccache, canonical `__helpers.h`, or parallel
    build support.
  - Changing the Event Bus, ingestion, or other components that run from source.

- **Dependencies**: `N/A: none`. The sibling check found no open issue or in-flight plan that
  targets these files; `plans/20261115-061459_deploydoc001_lifecycle-deployment-docs.md`
  edits agent lifecycle documentation only and does not overlap.

## Background
Prior art: `issues/done/20261019-103807_deploybin001_binary-freshness-and-rollback-in-deploy.md`
introduced the per-binary build info, freshness check, staged swap, and rollback that this
change must keep working. `issues/done/20260717-171259_nuitka_onefile_packaging_proposal.md`
introduced the Nuitka `--onefile` packaging.

Current behavior (verified against the current tree, master clean, in sync with
origin/master):
- `Explicit in code`: `deploy/build_binaries.sh` builds the agent and each MCP server as its
  own Nuitka run, each from a generated launcher that applies
  `ConfigLoader.restrict_to(...)` before importing the server module.
- `Explicit in code`: `config/agent.toml` launches each subprocess-mode MCP server through a
  single-element `cmd` that names a per-server file in the production bin directory
  (`[mcp_servers.shell] cmd = ["/opt/llm/bin/mcp_shell"]`, and analogously for the other
  nine); `deploy/deploy.sh` lists the same names in `BINARY_NAMES`
  (`deploy/deploy.sh:90`); `tools/manage_binaries.py` keeps one `BINARY_SOURCES` entry per
  name (`tools/manage_binaries.py:71`).
- `Explicit in code`: `CommandValidator` resolves symlinks with `os.path.realpath`
  (`scripts/agent/http_lifecycle_command_validator.py:144`) and accepts a command in the bin
  directory only when the resolved path is a regular file directly inside that directory and
  the directory is not group- or world-writable (`scripts/agent/http_lifecycle_command_validator.py:199-209`);
  it returns the resolved path.

Measurements (`Operationally observed`, 2026-11-15, a 4-thread 7GB build host, Nuitka 4.2.2,
ccache working after the ccache directory fallback, canonical `__helpers.h` wrapper, and
parallel build work already merged):
- Warm re-build of one MCP server binary: 141-167 seconds; Nuitka's Python-level processing
  and C generation (uncached by ccache) took about 70-80 seconds of that; for the agent it
  was 124 of 233 seconds.
- Third-party code dominates each MCP binary: for the shell server, 332 generated module C
  files of which 33 are project modules (the rest: pydantic, fastapi, uvicorn, anyio,
  starlette, and similar); the ten servers share this set.
- Prototype, outside the repository: one Nuitka invocation with ten mains took 722 seconds
  with a partly warm cache and 293 seconds fully warm against roughly ten times 150 seconds
  sequentially; the single output was 51MB against roughly 320MB for the ten binaries.
- Prototype dispatch: copies of the single binary named after two servers each started the
  matching server; a symlink with a name that is not an entry failed with
  `failed to detect what to do for filename derived name`.
- Prototype startup cost for one server: time to listening rose from about 1.0 to 1.2
  seconds; per-process extraction directory grew from about 110MB to about 192MB.

Deploy pattern (`Operationally observed` from the repository history, computed from commit
paths since 2026-08-01): when about ten commits are deployed together, an average deploy
marks about nine of the eleven binaries stale, so rebuilding most of the set is the typical
case, not the exception.

## Problem
Each of the ten MCP server binaries repeats the same Nuitka Python-level processing, C link,
and onefile packaging for the same third-party dependencies. These costs are not removed by
ccache, so the rebuild time of the MCP set grows linearly with the number of servers even
when every C object is cached.

## Reason for Change
The cheaper speed-ups (ccache directory fallback, canonical `__helpers.h` for cross-binary
ccache hits, parallel builds) are already merged. This is the largest remaining lever for
deploy lead time and build-host load. Nothing here is a correctness defect, so it is not
urgent.

## Implementation Intent
- Build the ten MCP servers in one Nuitka invocation with one main per server; keep one
  generated launcher per server so per-server configuration isolation is applied before that
  server's import, exactly as today. The agent keeps its own binary.
- Keep the installed interface unchanged: ten files with the existing `mcp_<server>` names
  in the bin directory, so `config/agent.toml` `cmd` entries and the start scripts need no
  change. How the ten names are produced from the single build (copies or hardlinks) is a
  design decision for this Plan, constrained by `CommandValidator` (see Constraints and
  Design).
- Treat the combined binary as one rebuild unit: the freshness check, build info, staged
  swap, and rollback must handle the ten names as one artifact and keep the all-or-nothing
  swap semantics.
- Keep the canonical `__helpers.h` ccache wrapper and parallel build; they still apply to
  the agent binary and to partial rebuilds.
- Decide the install method and the host `/tmp` sizing with evidence from a real build on
  the production-like host before the Plan is frozen.

## Requirements
- `REQ-001`: One Nuitka invocation builds all ten MCP servers and installs the resulting
  single binary under the ten existing `mcp_<server>` names, keeping the agent as a
  separate build.
- `REQ-002`: Each generated launcher applies `ConfigLoader.restrict_to(...)` before its
  server's import, and is a top-level module whose name does not collide with a `scripts/`
  package.
- `REQ-003`: `tools/manage_binaries.py` treats the ten MCP names as one rebuild unit: a
  change under any server's embedded paths marks all ten stale, and a swap or rollback
  replaces all ten together; a change that only the agent embeds marks none of them stale.
- `REQ-004`: `deploy/deploy.sh` rejects a bin directory where one of the ten names is
  missing or mismatched before deploy proceeds.
- `REQ-005`: Starting the binary under a name that is not an entry fails with a clear error;
  server selection matches an entry name exactly.
- `REQ-006`: The installed names pass `CommandValidator` for the chosen install method.
- `REQ-007`: The warm rebuild time of the ten MCP names is at most half the sum of the ten
  separate warm builds on the same build host, with extraction size and time-to-listening
  recorded.
- `REQ-008`: Existing tests that read `deploy/build_binaries.sh` and `tools/manage_binaries.py`
  pass after being updated, and `uv run python tools/run_validation_gates.py` reports no
  `Fail`.

## Implementation Target Files
**Freeze status**: Frozen

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `deploy/build_binaries.sh` | Modify | Add a multi-main build path that produces one binary for the ten MCP servers and installs it under the ten existing names; keep the agent as a separate build and keep the per-server launcher generation applying `ConfigLoader.restrict_to(...)` before each server import. | REQ-001, REQ-002 | Ten per-server Nuitka runs today, each from a generated launcher applying `ConfigLoader.restrict_to(...)` before the server import (`deploy/build_binaries.sh`, launcher table + per-server build loop) | `tests/tools/test_build_binaries_script.py` | Verified |
| `tools/manage_binaries.py` | Modify | Make staleness, build info, swap, and rollback treat the ten MCP names as one rebuild unit (a change under any server's embedded paths marks all ten stale; swap/rollback replace all ten together; an agent-only change marks none stale). | REQ-003 | One `BINARY_SOURCES` entry per name and staleness via `_matches` over each name's embedded paths (`tools/manage_binaries.py:71,232`); swap/rollback iterate `BINARY_SOURCES` (`tools/manage_binaries.py:357,440`) | `tests/tools/test_manage_binaries.py` | Verified |
| `deploy/deploy.sh` | Modify | Update the binary list and verification so a missing or mismatched MCP name is caught before deploy. | REQ-004 | `BINARY_NAMES=(...)` lists the ten names and a pre-check loop iterates them (`deploy/deploy.sh:90-109`) | — | Verified |
| `tests/tools/test_build_binaries_script.py` | Modify | Add tests for the multi-main invocation, the ten installed names, and the failure case that leaves `BIN_DIR` untouched (stubbed `uv`). | REQ-001, REQ-004, REQ-007 | Existing script test with a stubbed `uv` reading `deploy/build_binaries.sh` | `tests/tools/test_build_binaries_script.py` | Verified |
| `tests/tools/test_manage_binaries.py` | Modify | Add tests for the combined staleness unit, build info, swap, and rollback across the ten names. | REQ-003 | Existing staleness/swap/rollback tests keyed on `BINARY_SOURCES` (`tools/manage_binaries.py:71`) | `tests/tools/test_manage_binaries.py` | Verified |
| `tests/mcp_servers/test_config_isolation_import.py` | Modify | Update so the entry table still maps each server class to its configuration file under the multi-main build. | REQ-002 | Per-server config isolation via generated launcher + `ConfigLoader.restrict_to(...)` before server import | `tests/mcp_servers/test_config_isolation_import.py` | Verified |
| `tests/deploy/test_start_agent_preflight.py` | Verify | Confirm the agent binary pre-flight needs no change (agent keeps its own binary). | REQ-001 | Agent built as a separate Nuitka run (`deploy/build_binaries.sh`) | `tests/deploy/test_start_agent_preflight.py` | Verified |
| `docs/90_deployment/deployment_01_deployment.md` | Modify | Document that the MCP servers are one built artifact installed under ten names; how freshness, swap, and rollback treat it; the failure behavior when the name does not match an entry; the all-or-nothing coupling; and the `/tmp` sizing note, following `skills/DESIGN.md` Docs content policy. | REQ-007, REQ-008 | Compiled-artifacts section of the deployment document | — | Verified |
| `skills/deploy/SKILL.md` | Modify | Reflect the single-artifact-under-ten-names build and its freshness/swap/rollback treatment. | REQ-008 | Deploy skill describing the current per-binary build | — | Verified |
| `skills/deploy/workflow.md` | Modify | Reflect the single-artifact build and its freshness/swap/rollback treatment in the deploy workflow. | REQ-008 | Deploy workflow describing the current per-binary build | — | Verified |
| `rules/env.md` | Modify | Record the MCP set as one build artifact and the `/tmp` sizing note. | REQ-007 | Environment rules describing the current per-binary build | — | Verified |

Rules:
- One row per file. A directory, glob pattern, component/module name, file group, or vague
  phrase MUST NOT appear as a row.
- Test, configuration, schema, migration, deployment, and documentation files are their own
  rows when they require modification.
- `Validation Status` is `Verified` or `Needs confirmation` per row; every row must be
  `Verified` before this section may be marked `Frozen`.

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `deploy/start_agent.sh` | Confirm the agent binary pre-flight needs no change under the multi-entry build (agent keeps its own binary). | `deploy/build_binaries.sh` / REQ-001 |
| `scripts/agent/http_lifecycle_command_validator.py` | Confirm the chosen install method (copies/hardlinks/symlinks) passes `CommandValidator`, which resolves symlinks via `os.path.realpath` and requires the resolved path to be a regular file directly in the allowed bin dir. | `deploy/build_binaries.sh` / REQ-006 |
| `config/agent.toml` | Confirm the `cmd` entries stay unchanged and name the existing `mcp_<server>` paths. | `deploy/build_binaries.sh` / REQ-001 |
| `issues/done/20261019-103807_deploybin001_binary-freshness-and-rollback-in-deploy.md` | Preserve the per-binary build info, freshness check, staged swap, and rollback that this change must keep working. | `tools/manage_binaries.py` / REQ-003 |

## Acceptance Criteria
- One build run produces the ten `mcp_<server>` executables, and each, started with dummy
  configuration in an isolated environment (never against `/opt/llm`), starts the matching
  server and not another. (REQ-001, REQ-005)
- Starting the binary under a name that is not an entry fails with a clear error, and
  `deploy/deploy.sh` rejects a bin directory where one of the ten names is missing. (REQ-004,
  REQ-005)
- `uv run python tools/manage_binaries.py check` reports all ten MCP names stale after a
  change under any one server's embedded paths, and reports none of them stale after a change
  that only the agent embeds. (REQ-003)
- A swap followed by a rollback restores all ten names together, and a build failure leaves
  the previous ten names untouched. (REQ-003)
- `CommandValidator` accepts the installed names in the bin directory, shown by a test or a
  recorded manual run that uses the chosen install method. (REQ-006)
- On the same build host, the warm rebuild time of the ten MCP names is at most half of the
  sum of the ten separate warm builds, recorded in the Plan's Execution Status together with
  the extraction size and time to listening. (REQ-007)
- The existing tests that read `deploy/build_binaries.sh` and `tools/manage_binaries.py`
  pass after being updated, and `uv run python tools/run_validation_gates.py` reports no
  `Fail`. (REQ-008)

## Tests
- Unit tests in `tests/tools/test_manage_binaries.py` for the combined staleness unit, build
  info, swap, and rollback across the ten names. (REQ-003)
- Script tests with a stubbed `uv` in `tests/tools/test_build_binaries_script.py` for the
  multi-main invocation, the ten installed names, and the failure case that leaves
  `BIN_DIR` untouched. (REQ-001, REQ-004)
- An update of `tests/mcp_servers/test_config_isolation_import.py` so the entry table still
  maps each server class to its configuration file. (REQ-002)
- A `CommandValidator` test or recorded manual run for the chosen install method. (REQ-006)
- Manual verification on a build host: a real build, a start of at least two names with
  dummy configuration, and the timing and size measurements. The real Nuitka build is not
  run in CI. (REQ-007)
- `ruff`, `mypy`, `bash -n`, and `uv run python tools/check_tool_descriptions_sync.py` where
  applicable. (REQ-008)

## Documentation Impact
The compiled-artifacts section of `docs/90_deployment/deployment_01_deployment.md` (named via
`docs/00_index.md` "Document References by Task"), `skills/deploy/SKILL.md`,
`skills/deploy/workflow.md`, and `rules/env.md` must describe: that the MCP servers are one
built artifact installed under ten names; how freshness, swap, and rollback treat it; the
failure behavior when the name does not match an entry; the all-or-nothing coupling; and the
`/tmp` sizing note. The documentation must follow `skills/DESIGN.md` Docs content policy: no
file inventories, no literal ports, and no counts of binaries or servers. Driven by
REQ-007, REQ-008.

## Assumptions
- The prototype result (about 293 seconds warm) carries over to the repository's real
  launchers; the prototype launchers and scripts were session scratch files and are not in
  the repository, so the first implementation step regenerates and re-measures them.
- The multi-main behavior and the name-based dispatch hold on the Nuitka version pinned in
  `pyproject.toml` at implementation time.
- Copies of the single binary under the ten names are acceptable to `CommandValidator`; this
  is confirmed against source in Design rather than assumed.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Which install method works with `CommandValidator` in practice. Copies were verified to dispatch correctly; symlinks and hardlinks were not tried. Check which path the agent actually spawns (the resolved path that `CommandValidator` returns, or the configured path), because dispatch depends on the invoked name. | Practical dispatch through the agent's spawn path for symlink and hardlink installs. | Decide in the implementation from evidence: prefer copies (verified) or hardlinks (once cost once, replaced together on every swap); do not use a symlink unless resolved with evidence that the invoked name survives `CommandValidator`'s realpath resolution. | False |
| UNK-02 | Whether the production host's `/tmp` is memory-backed and has room for the larger per-process extraction of ten concurrent MCP servers (about 192MB each vs about 110MB). | Production `/tmp` backing store and capacity. | Measure the extraction size on the production-like host during the real build; record it in Execution Status; flag sizing if short. | False |
| UNK-03 | Whether the owners accept the coupling that a failure or change in one MCP server rebuilds and replaces all ten binaries. | Explicit acceptance from the deploy/infra owners. | State the coupling explicitly in the documentation and raise with the owners before freeze; proceed with the documented trade-off if unconfirmed. | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`' rows.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `deploy/build_binaries.sh` | Modify | High | N/A | N/A | High: rebuilds most of the MCP set on every typical deploy |
| `tools/manage_binaries.py` | Modify | High | N/A | N/A | High: staleness/swap/rollback gate every deploy |
| `deploy/deploy.sh` | Modify | Medium | N/A | N/A | High: pre-check rejects a missing MCP name |
| `tests/tools/test_build_binaries_script.py` | Modify | Low | N/A | N/A | None |
| `tests/tools/test_manage_binaries.py` | Modify | Low | N/A | N/A | None |
| `tests/mcp_servers/test_config_isolation_import.py` | Modify | Low | N/A | N/A | None |
| `tests/deploy/test_start_agent_preflight.py` | Verify | Low | N/A | N/A | None |
| `docs/90_deployment/deployment_01_deployment.md` | Modify | Low | N/A | N/A | None |
| `skills/deploy/SKILL.md` | Modify | Low | N/A | N/A | None |
| `skills/deploy/workflow.md` | Modify | Low | N/A | N/A | None |
| `rules/env.md` | Modify | Low | N/A | N/A | None |

## Design
Classification: Path B. The change touches more than three files, modifies deployment and
build tooling, and changes how a shared build artifact is produced and tracked; it also
introduces a new module-boundary decision (how one binary yields ten installed names) and a
public/runtime-facing constraint (`CommandValidator`'s realpath resolution). Path B analysis
is therefore required.

**Install method (open design choice).** The single binary must appear as ten
`mcp_<server>` files. Candidates:
- Copies: cost the single binary's size ten times (more than the ten separate binaries
  today); verified to dispatch correctly in the prototype.
- Hardlinks: cost it once but must be replaced together on every swap (consistent with
  treating the set as one rebuild unit).
- Symlinks: risk losing the invoked name, because `CommandValidator` resolves symlinks via
  `os.path.realpath` (`scripts/agent/http_lifecycle_command_validator.py:144`) and requires
  the resolved path to be a regular file directly inside the allowed bin dir
  (`scripts/agent/http_lifecycle_command_validator.py:199-209`); a symlink whose target is
  outside the dir would fail. Not used unless resolved with evidence.

Decision guidance: prefer hardlinks (single cost, consistent with the one-unit swap/rollback
model) or copies (verified dispatch); validate the chosen method against `CommandValidator`
with a test or recorded manual run before freeze. This resolves UNK-01.

**One rebuild unit.** `tools/manage_binaries.py` staleness, build info, swap, and rollback
must treat the ten names as one artifact: a change under any server's embedded paths marks
all ten stale and swaps/rolls back all ten together; an agent-only change marks none stale.
This preserves the all-or-nothing swap semantics from `deploybin001` and must not be
weakened.

**Per-server configuration isolation preserved.** Each generated launcher applies
`ConfigLoader.restrict_to(...)` before its server's import and is a top-level module whose
name does not collide with a `scripts/` package, exactly as today.

**Open item (recorded, not blocking).** The production `/tmp` sizing for ten concurrent
MCP processes (UNK-02) and owner acceptance of the all-or-nothing coupling (UNK-03) are
resolved with evidence before freeze; they do not block writing the plan.

## Implementation steps
Each step description cites the exact file path(s) it touches via `Implementation Target
Files` rows. Steps are small enough to be independently revertable.

1. **Phase 1: Multi-main build and install** (`deploy/build_binaries.sh`)
   - [ ] Add a multi-main build path that runs one Nuitka invocation with one main per MCP
     server and installs the single binary under the ten existing `mcp_<server>` names
     (copies or hardlinks, per the Design decision). (REQ-001)
   - [ ] Keep the agent as a separate build and keep the canonical `__helpers.h` ccache
     wrapper and parallel build. (REQ-001)
   - [ ] Regenerate the per-server launchers so each applies `ConfigLoader.restrict_to(...)`
     before its server's import and is a non-colliding top-level module. (REQ-002)
2. **Phase 2: One-rebuild-unit tracking** (`tools/manage_binaries.py`)
   - [ ] Make staleness mark all ten names stale on any change under any server's embedded
     paths and none stale on an agent-only change. (REQ-003)
   - [ ] Make build info, swap, and rollback replace all ten names together. (REQ-003)
3. **Phase 3: Deploy pre-check** (`deploy/deploy.sh`)
   - [ ] Reject a bin directory where one of the ten names is missing or mismatched before
     deploy proceeds. (REQ-004)
4. **Phase 4: Tests** (`tests/tools/test_build_binaries_script.py`,
   `tests/tools/test_manage_binaries.py`, `tests/mcp_servers/test_config_isolation_import.py`,
   `tests/deploy/test_start_agent_preflight.py`)
   - [ ] Add the multi-main, ten-name, failure-case, combined-staleness, swap/rollback, and
     config-isolation tests; confirm the agent pre-flight needs no change. (REQ-001-REQ-006)
5. **Phase 5: Manual build verification** (build host, out of CI)
   - [ ] Run a real build, start at least two names with dummy configuration in an isolated
     environment, and record warm rebuild time, extraction size, and time-to-listening;
     confirm the rebuild is at most half the sum of the ten separate builds. (REQ-007)
6. **Phase 6: Documentation** (`docs/90_deployment/deployment_01_deployment.md`,
   `skills/deploy/SKILL.md`, `skills/deploy/workflow.md`, `rules/env.md`)
   - [ ] Document the single-artifact-under-ten-names build, freshness/swap/rollback
     treatment, entry-mismatch failure, all-or-nothing coupling, and `/tmp` sizing note.
     (REQ-007, REQ-008)

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `deploy/build_binaries.sh` | Script test (stubbed `uv`) | `bash -n deploy/build_binaries.sh`; `tests/tools/test_build_binaries_script.py` | Multi-main path produces ten names; failure leaves `BIN_DIR` untouched |
| `tools/manage_binaries.py` | Unit | `uv run pytest tests/tools/test_manage_binaries.py`; `uv run ruff check tools/manage_binaries.py`; `uv run mypy tools/manage_binaries.py` | Combined staleness/swap/rollback across ten names; `check` reports all/none stale correctly |
| `deploy/deploy.sh` | Script test | `bash -n deploy/deploy.sh`; deploy pre-check | Missing MCP name rejected before deploy |
| `tests/mcp_servers/test_config_isolation_import.py` | Unit | `uv run pytest tests/mcp_servers/` | Entry table maps each server class to its config file |
| `scripts/agent/http_lifecycle_command_validator.py` | Test/manual for chosen install method | `CommandValidator` test or recorded manual run | Installed names accepted |
| Full suite | Regression | `uv run python tools/run_validation_gates.py` | No `Fail` |

## Risks
- **Risk**: A broken MCP server module fails the single build for all ten servers, and a
  change to any server replaces all ten binaries. → **Mitigation**: State this
  all-or-nothing coupling explicitly in the documentation and raise owner acceptance
  (UNK-03) before freeze; keep the agent as a separate build so an agent change never
  rebuilds the MCP set.
- **Risk**: The chosen install method loses the invoked name through `CommandValidator`'s
  realpath resolution. → **Mitigation**: Validate the chosen method (copies/hardlinks)
  against `CommandValidator` with a test or recorded manual run before freeze; avoid symlinks
  unless resolved with evidence (Design, UNK-01).
- **Risk**: Ten concurrent MCP processes need more `/tmp` space (about 192MB each). →
  **Mitigation**: Measure extraction size on the production-like host; record it and flag
  sizing if short (UNK-02).
- **Risk**: The prototype warm time (about 293s) does not carry over to the repository's
  real launchers. → **Mitigation**: Regenerate and re-measure with the real launchers in the
  first implementation step; record measured before/after in Execution Status.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`.

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Multi-main build and install (`deploy/build_binaries.sh`) | Pending | — | — | REQ-001, REQ-002 |
| 2 | One-rebuild-unit tracking (`tools/manage_binaries.py`) | Pending | — | — | REQ-003 |
| 3 | Deploy pre-check (`deploy/deploy.sh`) | Pending | — | — | REQ-004 |
| 4 | Tests (`tests/tools/*`, `tests/mcp_servers/*`, `tests/deploy/*`) | Pending | — | — | REQ-001-REQ-006 |
| 5 | Manual build verification (build host, out of CI) | Pending | — | — | REQ-007 |
| 6 | Documentation (`docs/90_deployment/*`, `skills/deploy/*`, `rules/env.md`) | Pending | — | — | REQ-007, REQ-008 |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: `issues/20261115-072739_buildperf001_mcp-multidist-binary.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261115-193516
- **Related target files**: `deploy/build_binaries.sh`, `tools/manage_binaries.py`, `deploy/deploy.sh`, `tests/tools/test_build_binaries_script.py`, `tests/tools/test_manage_binaries.py`, `tests/mcp_servers/test_config_isolation_import.py`, `tests/deploy/test_start_agent_preflight.py`, `docs/90_deployment/deployment_01_deployment.md`, `skills/deploy/SKILL.md`, `skills/deploy/workflow.md`, `rules/env.md`

### Requirement Traceability
| Requirement ID | Source Issue Section or Evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Summary, Implementation Intent, Target Files | `deploy/build_binaries.sh` | 1 | AC 1 | script test (stubbed `uv`) | Confirmed by repository evidence |
| REQ-002 | Implementation Intent, Constraints | `deploy/build_binaries.sh` | 1 | AC 1 | `test_config_isolation_import.py` | Confirmed by repository evidence |
| REQ-003 | Required Changes, Constraints | `tools/manage_binaries.py` | 2 | AC 3, AC 4 | `test_manage_binaries.py` | Confirmed by repository evidence |
| REQ-004 | Required Changes | `deploy/deploy.sh` | 3 | AC 2 | deploy pre-check | Confirmed by repository evidence |
| REQ-005 | Constraints, Acceptance Criteria | `deploy/build_binaries.sh` | 1 | AC 1, AC 2 | manual run / script test | Confirmed by repository evidence |
| REQ-006 | Constraints, Acceptance Criteria | `deploy/build_binaries.sh` | 1 | AC 5 | `CommandValidator` test/manual | Confirmed by repository evidence |
| REQ-007 | Acceptance Criteria, Constraints | build host | 5 | AC 6 | manual build timing/size | Needs confirmation |
| REQ-008 | Required Changes, Acceptance Criteria | docs/skills/rules | 6 | AC 7 | `run_validation_gates.py` | Confirmed by repository evidence |
