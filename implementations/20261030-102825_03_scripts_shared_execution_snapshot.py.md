# Implementation Procedure: scripts/shared/execution_snapshot.py

## Goal

Create the execution-snapshot builder/comparator: a component-keyed fingerprint of the
running deployment captured at call start, used to decide replay of completed dedup rows
(REQ-004 snapshot builder; feeds REQ-005 equality decision).

## Scope

**In scope:**
- `scripts/shared/execution_snapshot.py` (new): snapshot build, canonical JSON encoding,
  per-component equality.

**Out of scope:**
- Recording sites (rows 04, 05), `DEPLOYED_REV` producer itself (`tools/manage_binaries.py`,
  unchanged by this plan).

## Assumptions

- Evidence correction (Needs Confirmation closed against HEAD): the plan's Reference Files
  cite "`deploy.sh` writes `/opt/llm/DEPLOYED_REV`"; the actual producer is
  `tools/manage_binaries.py` (`record-revision` subcommand, `REVISION_FILE` at `:14`,
  `:53`, `:354`) invoked by the deploy flow. The builder only reads the file.
- `scripts/shared/web_search.py` cited in the plan does not exist; it is irrelevant to
  this module (the `web_search` tool ships as an MCP binary).
- Snapshot components fixed to four keys: `deployed_rev` (new), `git_sha` (new), `config_hash` (new),
  `schema_versions` (new) — the REQ-004 component list; equality is per component.

## Design decisions

- API (all new): `build_execution_snapshot() -> dict[str, str]`,
  `snapshot_json(snapshot) -> str` (canonical sorted JSON for storage),
  `snapshots_equal(a, b) -> bool` (component-wise: any differing component → False; a
  missing component on either side → False).
- `deployed_rev` (new): read `/opt/llm/DEPLOYED_REV` tolerantly — JSON parse failure or missing
  file → `"unknown"` (REQ-004). `git_sha` (new): the `commit` field of the same file when
  present; otherwise `"unknown"` (do not shell out to git — deployed runs must not depend
  on a repo).
- `config_hash` (new): SHA-256 over `sorted(glob config/*.toml)` contents, path-delimited, in
  the repo-relative order so the same tree hashes identically from any cwd; path root
  resolved from an env-tunable base with the deployed default `/opt/llm/config` and repo
  fallback for tests (config-boundary rule: base path comes from config/env, not
  hardcoded absolute reads beyond the documented DEPLOYED_REV path).
- `schema_versions` (new): for each known DB path (config-provided), `PRAGMA user_version`
  integer, joined; missing DB → `"absent"`. Read-only connections only.

## Alternatives considered

- Single concatenated hash — rejected: REQ-004 defines equality per component so a
  config-only change can be distinguished from a code-revision change in audit.
- Capturing the snapshot in the transport (shared/http layer) — rejected: the plan's
  recording sites are the dispatcher and the agent audit (rows 04, 05); the builder is a
  pure shared-layer helper.

## Implementation
### Target file
`scripts/shared/execution_snapshot.py` (new)

### Procedure
1. Module docstring binding REQ-004 and the component contract.
2. Implement the four component readers, each independently tolerant (never raises).
3. Implement `build_execution_snapshot` (new), `snapshot_json` (new), `snapshots_equal` (new).

### Method
Stdlib only (`hashlib`, `json`, `tomllib`, `sqlite3`, `pathlib`); all file reads
read-only and best-effort; no caching (fresh read per call keeps `config_hash` (new) live —
Needs Confirmation whether a per-process TTL cache is worth it once recording volume is
measured).

### Details
- Cost: four small file reads + N `PRAGMA` probes per call; row 04 records it once per
  dispatch (not per retry attempt).

## Compatibility considerations

- New module only; no existing consumer changes here. Row 05/04/18 add consumers/tests.

## Security considerations

- Snapshot stores hashes, never config contents or result bodies; safe for the audit log.

## Rollback considerations

- N/A: revert the commit; rows 04/05 record `"unknown"` snapshots if the module is gone
  (their fallbacks are specified there).

## Validation plan

- Row 18 (`tests/shared/test_execution_snapshot.py`, new, test-first): build shape,
  per-component mismatch → `snapshots_equal` (new) False, missing `DEPLOYED_REV` → `unknown`,
  malformed `DEPLOYED_REV` JSON → `unknown` without raising, config-tree sensitivity.
- `uv run pytest tests/shared/test_execution_snapshot.py`; `uv run mypy
  --no-namespace-packages scripts/ tests/shared`; `lint-imports`.

## Completion criteria

- Identical deployment trees hash identically across processes; any single component
  change (one `config/*.toml` byte, one DB version) flips equality to False; missing
  inputs never raise (REQ-004 tolerance).

## Out of Scope

- Where snapshots are stored (`mcp_dedup.snapshot_id`, `tool_audit` payload — rows 02, 05).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the snapshot builder module | Pending | — | — | |
| 2 | Land row 18 tests (test-first) before or with this row | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-004` (snapshot builder/comparator), `REQ-005` (replay equality input)
- **Source issue**: `issues/20261029-104503_toolexec001_idempotent-tool-call-snapshot.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261029-233524_toolexec001_idempotent-tool-call-snapshot.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-102825
- **Related target files**: scripts/shared/execution_snapshot.py
