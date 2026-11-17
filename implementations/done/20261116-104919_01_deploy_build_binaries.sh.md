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

- **Install method (`UNK-01`): hardlinks, with a copy fallback.** Decided 2026-11-17 from
  source evidence. The single binary must appear as ten `mcp_<server>` regular files. Dispatch
  reads the invoked filename (see Details), and a hardlink's `os.path.realpath` resolves to
  itself, so `CommandValidator` (which validates and launches the resolved path,
  `scripts/agent/http_lifecycle_command_validator.py:144,199-209`) still invokes the installed
  name — dispatch-safe, one disk cost, replaced together on every swap. A copy is equally safe
  (prototype-verified) and is the fallback when `ln` fails (cross-device). A symlink is rejected
  for a dispatch-specific reason beyond the realpath check: realpath resolves to the target's
  name, so every symlinked name would dispatch the target's server. Re-confirm on the build
  host in the manual step (`REQ-007`).
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
   ten MCP launchers first, invoke Nuitka once with every launcher as a repeated `--main=PATH`
   flag (Nuitka 4.2.2 rejects more than one positional main) plus `BASE_NUTKA_ARGS`, resolve
   the single produced artifact, then materialize the ten names in `STAGE_DIR` as hardlinks
   (copy fallback per the install-method decision).
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
  entries, then pass all ten launcher paths to a single Nuitka invocation as repeated
  `--main=PATH` flags. Resolve the single onefile output (named `<first-main>.bin`), then
  hardlink (or copy) it to each `${STAGE_DIR}/${final_name}`.
- Change the MCP launcher file name to exactly `${final_name}.py`: name-derived dispatch
  requires the invoked filename to equal the main module name (verified on Nuitka 4.2.2, see
  Verification Findings), so a launcher named `${final_name}_launcher.py` would make the
  installed name `${final_name}` fail dispatch. None of the ten `mcp_<server>` names collides
  with a `scripts/` top-level package; keep the guard from the `build_one` comment (lines
  358-361) as a runtime check: abort if `scripts/<final_name>.py` or `scripts/<final_name>/`
  exists. The agent keeps `agent_launcher.py` (a single-main onefile does not dispatch by name,
  so the installed `agent` name works unchanged). Launcher bodies are unchanged: each MCP
  launcher still runs `ConfigLoader.restrict_to("${cfg}")` before `from ${module} import
  ${cls}`, and the agent launcher still calls `main()`.
- Do not mask Nuitka's dispatch error for a name that is not an entry; a start under such a
  name must fail with Nuitka's filename-derived-name error (`REQ-005`).

### Details

- The single onefile binary dispatches by the invoked filename; copies/hardlinks named after
  different servers each start the matching server (prototype-observed, re-verified on
  Nuitka 4.2.2 on 2026-11-17 — see Verification Findings).
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

## Verification Findings (2026-11-17, adversarial verification)

Verification Status: Verified — findings applied to Procedure/Method above.

- Live experiment on the pinned Nuitka 4.2.2 (dev host, minimal two-main prototype,
  `/tmp/opencode/mmtest`): multiple positional mains are rejected ("specify only one positional
  argument"); repeated `--main=PATH` is accepted and produces a single onefile artifact named
  `<first-main>.bin`.
- Name-derived dispatch confirmed: copies named after a main module's name run that main; a
  copy named `mcp_a` against main `mcp_a_launcher` fails with `Error, failed to detect what to
  do for filename derived name 'mcp_a'.` This is exactly the `REQ-005` failure mode and proves
  the MCP launcher file must be named `${final_name}.py` (Method updated).
- `ENTRIES` (lines 144-156) confirmed: agent row `agent.repl:agent::` (empty cls) plus ten MCP
  rows. Keep the array named `ENTRIES=(`, one quoted row per line, and split the agent into its
  own `AGENT_ENTRY` variable: `tests/mcp_servers/test_config_isolation_import.py` `_entries()`
  (lines 286-295) locates `ENTRIES(`, drops empty-`cls` rows, and must keep yielding exactly
  ten MCP rows after the split.
- Current shape confirmed: `gen_launcher` 322-349, `build_one` 356-415 (candidate search 389-395,
  `mv` to `STAGE_DIR` 402-403, per-name `write-info` 404-406), `parse_entry` 418-425, main loop
  446-462, result collection 472-488, all-or-nothing abort 489-492, swap 496-502. The MCP phase
  must keep: per-name `write-info`, per-name `RESULT_DIR/<name>.ok` (the collection loop at
  472-488 expects one result file per selected name), `BUILT_NAMES` carrying all ten names to
  the swap, and the 358-361 collision guard as a runtime check.
- Install method decided: hardlinks with copy fallback (Design decisions updated). Symlink
  rejection now has a dispatch-specific reason: realpath resolution changes the invoked name.
- Companion baseline: `tests/tools/test_build_binaries_script.py` 17 cases pass on 2026-11-17;
  its stub asserts one `.py` launcher per build (line 216) and no `--module` flag (line 199).
  The stub and its assertions must be rewritten for the two-phase multi-main build.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261117-095134 | 20261117-101306 | two-phase build (agent build_one + build_mcp_group multi-main), hardlink staging, launcher naming mcp_<server>.py, collision guard |
| 2 | Add or update tests per Validation plan | Completed | — | 20261117-101306 | companion `test_build_binaries_script.py` companion test_build_binaries_script.py rewritten for multi-main stub; 20 pass |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261117-101306 | bash -n; targeted 78 pass; full suite 12478 pass; diff-cover N/A (no source lines); pre-commit passed |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20261117-101306 | N/A: docs scope handled by procedures 08-11 |

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