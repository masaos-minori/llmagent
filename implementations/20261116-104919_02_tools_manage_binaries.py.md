## Goal

Treat the ten `mcp_<server>` names as one rebuild unit in `tools/manage_binaries.py`: a change
under any server's embedded paths marks all ten stale, and a swap or rollback replaces all ten
together, while an agent-only change marks none of them stale. Implements `REQ-003` (one
rebuild unit: combined staleness, build info, swap, rollback).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- The ten MCP names are produced from a single built artifact (see `deploy/build_binaries.sh`),
  so they share one checksum and one freshness verdict; the per-name `.build-info.json` files
  therefore stay identical across the set.
- `deploy/deploy.sh` passes all ten names to `manage_binaries.py` swap/check, so the tool sees
  the whole unit, not a subset.

## Design decisions

- **Keep `BINARY_SOURCES` as the per-name file table; add a rebuild-unit layer above it.** The
  ten keys stay in `BINARY_SOURCES` because swap/rollback move each name's file individually,
  each name keeps its own build info, and the tests assert `set(BINARY_SOURCES)` equals the
  script names. The one-unit behavior lives in a small helper that answers "which embedded
  paths make this name stale?" rather than in the table itself.
- **Two rebuild units: `agent` (its own) and the ten MCP names (one).** Staleness is computed
  per unit: `agent` against its own paths, the MCP set against the union of every server's
  embedded paths.

## Alternatives considered

- **Rename the ten names to one logical key in `BINARY_SOURCES`.** Rejected — the installed
  interface is ten distinct files, and swap/rollback must still move each name separately.
- **Compute staleness once per unit and broadcast the verdict.** Equivalent result; the union
  is evaluated per name here because `_check_binary` is already keyed by name, so the change is
  a one-line substitution and stays local.

## Implementation
### Target file
`tools/manage_binaries.py`

### Procedure

1. Immediately after the `BINARY_SOURCES` table, add the one-rebuild-unit definition:
   - `_MCP_NAMES` (new): the ten MCP names, derived as every `BINARY_SOURCES` key except `agent`
     (`tuple(n for n in BINARY_SOURCES if n != "agent")`), so adding or removing a server keeps
     the unit in sync.
   - `_unit_sources(name)` (new): return `BINARY_SOURCES["agent"]` when `name == "agent"`; otherwise
     return the sorted union of `BINARY_SOURCES[mcp]` over every `mcp` in `_MCP_NAMES` (new).
2. In `_check_binary`, replace the staleness lookup `BINARY_SOURCES[name]` with
   `_unit_sources(name)` so a name's freshness is judged against its rebuild unit's embedded
   paths.
3. Leave `swap`, `rollback`, and `record_revision` as-is: they already iterate the passed names
   (or all of `BINARY_SOURCES`), so passing all ten replaces/rolls back the whole set
   all-or-nothing. Confirm this holds after step 1 — do not add a per-name filter that could
   select a subset.

### Method

- The change is confined to staleness: one new module constant (`_MCP_NAMES` (new)), one new
  helper (`_unit_sources` (new)), and one substitution in `_check_binary`. `BINARY_SOURCES`
  keeps its eleven keys unchanged.
- `_unit_sources` (new) returns the union for any MCP name, so all ten evaluate to the same verdict —
  that equality is the one-unit guarantee. The computation is cheap (ten short tuples) and may
  be memoized later if profiling shows cost.
- Do not weaken the all-or-nothing swap: `_replace_files` still requires every requested name to
  pass, and `deploy.sh` requests all ten.

### Details

- A change under any server's embedded paths — a server package such as
  `scripts/mcp_servers/shell/`, or the shared `_MCP_COMMON` (`scripts/mcp_servers/*.py`,
  `scripts/shared/`, `pyproject.toml`, `uv.lock`) — matches the union and marks all ten stale.
- An agent-only change (`scripts/agent/`, `scripts/db/` absent from the union unless a server
  embeds it, `scripts/rag/`) matches none of the union, so all ten MCP names report `ok`; the
  agent itself becomes stale through its own unit. Note `scripts/db/` and `scripts/rag/` are in
  the union via `mcp_rag_pipeline`/`mcp_mdq`, so a change there also rebuilds the whole set —
  that is the intended all-or-nothing coupling.
- Build info and integrity still work per name: each of the ten names keeps a `.build-info.json`
  whose checksum matches its own file, so a corrupted copy among the ten is still caught as
  `mismatch`.

## Compatibility considerations

- `deploy/deploy.sh` passes all ten names to `swap`/`check`, so the deploy flow swaps and checks
  the whole unit; no deploy change is required by this row (that is `deploy/deploy.sh`).
- The `check` output still prints one line per name, so `deploy.sh`'s freshness handling and the
  `--list-stale` consumer see all ten names listed as `stale` together.

## Security considerations

- Freshness drives which rebuilt binaries reach production. Treating the set as one unit means a
  change to any one server forces a rebuild of all ten, so no server can keep serving code that
  predates a sibling's change. The all-or-nothing swap preserves the staged-swap integrity gate:
  a build that fails for one server leaves the previous ten untouched.

## Rollback considerations

`N/A: revert the commit`; the existing `manage_binaries.py rollback` restores the previous set,
and the ten names are restored together because `deploy.sh` rolls back all ten names at once.

## Validation plan

- `uv run pytest tests/tools/test_manage_binaries.py` (companion): combined staleness unit (a
  change under one server's package marks all ten stale; an agent-only change marks none),
  build info, and swap/rollback across the ten names.
- `uv run ruff check tools/manage_binaries.py`; `uv run mypy tools/manage_binaries.py`.
- `uv run python tools/run_validation_gates.py` reports no `Fail`.

## Completion criteria

- A change under any server's embedded paths reports all ten MCP names `stale`; an agent-only
  change reports all ten `ok`.
- A swap or rollback replaces all ten names together, and the agent's own staleness is unchanged.
- `BINARY_SOURCES` still has exactly the eleven script names as keys.

## Out of Scope

- Building the artifact (that is `deploy/build_binaries.sh`).
- The deploy pre-check (that is `deploy/deploy.sh`).
- Changing the staleness rule to per-binary import closures.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | companion `test_manage_binaries.py` |
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
- **Requirement ID**: `REQ-003`
- **Source issue**: `issues/20261115-072739_buildperf001_mcp-multidist-binary.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261115-193516_buildperf001_mcp-multidist-binary.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261116-104919
- **Related target files**: `tools/manage_binaries.py`, `tests/tools/test_manage_binaries.py`

### Companion test files
- `tests/tools/test_manage_binaries.py`
  - Procedure: add tests that a change under one server's embedded package marks all ten MCP
    names stale, that an agent-only change marks none of them stale, and that swap/rollback
    replace all ten together; reuse the existing `_make_binary`/`_init_repo` helpers and write
    build info for each of the ten names.
  - Validation: `uv run pytest tests/tools/test_manage_binaries.py`.
