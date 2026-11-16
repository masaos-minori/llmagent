## Goal

Add a multi-main build path to `deploy/build_binaries.sh` that builds the ten MCP
servers in one Nuitka invocation (one main per server) and installs the resulting single
binary under the ten existing `mcp_<server>` names, keeping the agent as a separate build
and preserving per-server configuration isolation (`ConfigLoader.restrict_to(...)` before
each server import). Implements `REQ-001` (one build, ten installed names, agent separate)
and `REQ-002` (launcher isolation and non-collision).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- The prototype's multi-main dispatch and name-based selection hold on the Nuitka version
  pinned for the build group (`4.2.2`); the first step regenerates and re-measures the real
  launchers, because the prototype launchers/scripts were session scratch and are not in the
  repository.
- Copies of the single binary under the ten names are acceptable to `CommandValidator`; this
  is confirmed against source in the plan Design / `UNK-01`, not merely assumed.
- The ten MCP servers share the same third-party dependency set, so one processing/link
  pass is meaningfully cheaper than ten.

## Design decisions

- **Install method (open, `UNK-01`).** The single binary must appear as ten `mcp_<server>`
  files. Prefer hardlinks (single disk cost, replaced together on every swap, consistent
  with treating the set as one rebuild unit) or copies (verified dispatch in the prototype);
  both are regular files directly inside the bin dir and therefore pass
  `CommandValidator`'s `os.path.realpath` + regular-file check. Do not use a symlink unless a
  real build shows the invoked name survives `CommandValidator`'s realpath resolution (a
  symlink whose target is outside the dir fails). Decide from evidence on the production-like
  host before freeze.
- **One invocation for the MCP set, one for the agent.** Ten MCP launchers go into a single
  Nuitka `--onefile` run; the agent keeps its own run, so an agent change never rebuilds the
  MCP set.

## Alternatives considered

- Building each MCP server in its own Nuitka run (the current behavior): rejected — it
  repeats the shared third-party Python processing and C link ~10×, the cost this Plan
  removes.
- Symlink install: rejected unless resolved with evidence, because `CommandValidator`
  resolves symlinks via `os.path.realpath` and requires the resolved path to be a regular
  file directly inside the allowed bin dir (`scripts/agent/http_lifecycle_command_validator.py:144,199-209`).

## Implementation
### Target file
`deploy/build_binaries.sh`

### Procedure

1. Split `ENTRIES` (lines 144-156) into the agent entry and the ten MCP entries so the agent
   builds alone and the ten MCPs build together. Keep the `module:final_name:cls:cfg` shape
   and the `BUILD_ONLY` filter.
2. In the main build loop (lines 446-462), when the agent is selected, run the current
   single-entry `build_one` path for the agent unchanged.
3. When any MCP entry is selected, build the ten MCPs in one Nuitka invocation: generate all
   ten MCP launchers first, invoke Nuitka once with every launcher as a positional main plus
   `BASE_NUTKA_ARGS`, resolve the single produced artifact, then materialize the ten names in
   `STAGE_DIR` as copies or hardlinks (per the install-method decision).
4. Write a `.build-info.json` for each of the ten staged names via
   `tools/manage_binaries.py write-info` against the installed file, so each recorded
   checksum matches its own file.
5. Keep the all-or-nothing contract: if the multi-main build fails, exit before the swap so
   `${BIN_DIR}` is left untouched; `BUILT_NAMES` must list all ten installed names so the
   swap replaces them together.

### Method

- Refactor the main loop into two phases (agent phase, MCP phase) driven by the split
  `ENTRIES`; preserve `BUILD_ONLY` filtering, `NUTKA_PARALLEL`/`NUTKA_JOBS`, the ccache
  `__helpers.h` canonicalization, and the `swap` call.
- For the combined build, call `gen_launcher` (lines 322-349) for each of the ten MCP
  entries, then pass all ten launcher paths to a single Nuitka invocation as positional
  mains. Resolve the single onefile output (name is the implementer's choice, e.g. a shared
  `mcp_*` name), then copy or hardlink it to each `${STAGE_DIR}/${final_name}`.
- Do not change launcher generation: each MCP launcher still runs
  `ConfigLoader.restrict_to("${cfg}")` before `from ${module} import ${cls}`, and the agent
  launcher still calls `main()`. Launchers stay top-level modules named
  `${final_name}_launcher.py`, which the existing comment in `build_one` (lines 358-361)
  already guards against colliding with a `scripts/` package.
- Do not mask Nuitka's dispatch error for a name that is not an entry; a start under such a
  name must fail with Nuitka's filename-derived-name error (`REQ-005`).

### Details

- The single onefile binary dispatches by the invoked filename; copies/hardlinks named after
  different servers each start the matching server (prototype-observed).
- Because the ten names share one artifact, the freshness check, build info, swap, and
  rollback treat them as one rebuild unit — see `tools/manage_binaries.py`; this row only
  ensures `BUILT_NAMES` carries all ten names to the existing swap.
- The agent entry keeps the existing per-entry build, build-info write, and staging, so
  `BUILD_ONLY="agent"` still rebuilds only the agent.

## Compatibility considerations

- The installed interface is unchanged: ten files with the existing `mcp_<server>` names in
  the bin dir, so `config/agent.toml` `cmd` entries and the start scripts need no change.
- `CommandValidator` still accepts the installed names, because copies/hardlinks are real
  files directly inside the bin dir.

## Security considerations

- Per-server configuration isolation is preserved: each launcher applies `restrict_to`
  before its server's import, exactly as today.
- The install method must keep the bin dir holding real files (no symlink pointing outside),
  so `CommandValidator`'s regular-file and non-writable-directory checks continue to hold.

## Rollback considerations

`N/A: revert the commit`; the previous ten names are restored by the existing
`tools/manage_binaries.py rollback` path that `--rollback` already uses.

## Validation plan

- `bash -n deploy/build_binaries.sh`.
- `tests/tools/test_build_binaries_script.py` (companion): stubbed `uv` asserts the
  multi-main invocation (ten mains in one call), the ten installed names, and the failure
  case that leaves `BIN_DIR` untouched.
- Manual build host (out of CI): a real build, start at least two names with dummy
  configuration in an isolated environment, confirm each starts the matching server, and
  record warm rebuild time, extraction size, and time-to-listening (`REQ-007`).

## Completion criteria

- One Nuitka invocation produces the single MCP binary installed under the ten names; the
  agent builds as a separate run.
- Each MCP launcher applies `ConfigLoader.restrict_to(...)` before its server's import and is
  a top-level module whose name does not collide with a `scripts/` package.
- A start under a name that is not an entry fails with a clear error, and `CommandValidator`
  accepts the installed names.

## Out of Scope

- Upgrading Nuitka or changing the Nuitka flags other than adding the extra mains.
- Folding the agent binary into the multi-entry binary.
- Changing the staleness/build-info/swap/rollback model (that is `tools/manage_binaries.py`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | companion `test_build_binaries_script.py` |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: `REQ-001`, `REQ-002`
- **Source issue**: `issues/20261115-072739_buildperf001_mcp-multidist-binary.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261115-193516_buildperf001_mcp-multidist-binary.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261116-104919
- **Related target files**: `deploy/build_binaries.sh`, `tests/tools/test_build_binaries_script.py`

### Companion test files
- `tests/tools/test_build_binaries_script.py`
  - Procedure: update the stubbed `uv` and its assertions for the multi-main invocation (ten
    mains in one Nuitka call), the ten installed `mcp_<server>` names, and the failure case
    that leaves `BIN_DIR` untouched.
  - Validation: `uv run pytest tests/tools/test_build_binaries_script.py`.
