## Goal

Create `config/tool_catalog.toml`, a machine-readable static ownership/capability registry (`REQ-004`, `REQ-005`, `UNK-01`). It maps each MCP server key to its owned tools/capabilities and declares each required server's required capability, replacing the `[[tool_definitions]]` / `tool_names` data that lived in `config/agent.toml`. The drift check (`tool_validation.py`, row 6) and discovery (`mcp_tool_discovery.py`, row 7) read it; `agent.toml` reduction stays intact.

## Scope
**Release unit**: static-catalog removal

## Assumptions
- `config/tool_catalog.toml` does not yet exist (verified: no such file in `config/`); ownership currently lives only in `agent.toml`'s removed `[[tool_definitions]]`/`tool_names`.
- The manifest is **data, not code**: it crosses no import boundary (`shared` is a leaf per `.importlinter`), so it is loaded by `tool_validation.py` and `mcp_tool_discovery.py` at runtime rather than imported as a module.
- `cliplc008`'s required-capability schema is canonical; this manifest reuses it unchanged (design decision 2). A required server's requirement is a required-capability declaration; a missing capability is fatal (`AC-3`).
- The manifest is shipped via a new `deploy.sh` cp line (Plan step 8 / `REQ-004` target); confirm the deploy path matches the existing `agent.toml` cp line.
- Exact filename/schema are finalized at implementation (design decision 1); the structure below is the minimum the two consumers require.

## Design decisions
- Structure the manifest as one table per server key, each declaring owned tools/capabilities plus, for required servers, the required capability. This mirrors the old `[[tool_definitions]]`/`tool_names` server-keyed layout so ownership facts move with minimal reshaping.
- Keep the manifest pure TOML data (no Python): load it with the stdlib TOML reader at startup and hand the parsed structure to `tool_validation.py` (drift/ownership input) and `mcp_tool_discovery.py` (required-capability input). This avoids a new import chain into `shared`.
- Reuse `cliplc008`'s required-capability field names verbatim so the health/capability schema stays single-version across `agentcfg002`, `cliplc008`, and `agentcfg003` (per clipc008's related-issues note).

## Alternatives considered
- A Python module under `scripts/shared/`: rejected (design decision 1) because ownership data belongs with configuration, not code, and a Python module would add an import chain into the `shared` leaf.
- Keeping ownership in `agent.toml`: rejected by `REQ-002`/`REQ-003`, which remove `[[tool_definitions]]`/`tool_names` from `agent.toml`.

## Implementation
### Target file
`config/tool_catalog.toml` (new)

### Procedure
Author the manifest with per-server ownership and required-capability declarations, structured for the two runtime consumers.

### Method
- Add one TOML table per server key declaring owned tools and capabilities.
- For each server marked `required` elsewhere (ADR-004), declare its required capability using `cliplc008`'s field names.
- Keep the file valid TOML; validate by loading it with the stdlib TOML reader.

### Details
- Include every server that previously had `[[tool_definitions]]`/`tool_names` entries, carrying over its owned tool set so the drift check (`tool_validation.py`) has a complete expected set.
- Declare the required capability for each required server so `mcp_tool_discovery.py` can confirm a surfaced tool provides it (missing capability → FATAL, `AC-3`).
- Do not introduce new capability semantics beyond `cliplc008`; reuse its schema unchanged.
- Coordinate the loader with rows 6 (`tool_validation.py`) and 7 (`mcp_tool_discovery.py`): they consume this parsed structure; the manifest itself carries no loader code.
- The `deploy.sh` cp line for this file is added in Plan step 8 (not in this file's creation), but confirm the target deploy path now.

## Compatibility considerations
Backward incompatible by design (`REQ-004`, `REQ-005`): the drift check now fails on static-vs-live ownership mismatches that the old config-based check never saw. The manifest must exist and be populated for every required server, or those servers report an ownership/capability mismatch. Existing `agent.toml` is cleaned by row 1, so no config migration is needed.

## Security considerations
Fail-closed: a server whose live tools do not match its declared ownership is fatal (`REQ-006`), and a required server that cannot prove its declared capability blocks startup (`AC-3`). An empty or missing manifest makes every required server fail, so the manifest must be shipped alongside `agent.toml`.

## Rollback considerations
N/A: revert the commit. Ensure the previous `agent.toml`-based ownership data is restored if reverting (row 1 restores `agent.toml`).

## Validation plan
Load `config/tool_catalog.toml` with the stdlib TOML reader and assert: (a) it parses; (b) every required server declares a required capability; (c) the parsed ownership set matches the live `/v1/tools` for a representative server (drift pass) and diverges for a synthetic mismatch (drift fail). Run the affected discovery and drift tests (rows 6/7).

## Completion criteria
`config/tool_catalog.toml` exists, parses as valid TOML, declares owned tools/capabilities per server and a required capability per required server, and is loadable by both `tool_validation.py` and `mcp_tool_discovery.py`.

## Out of Scope
The drift-check rewrite reading this manifest (`tool_validation.py`, row 6), the required-capability check consuming it (`mcp_tool_discovery.py`, row 7), the `deploy.sh` cp line (Plan step 8), and documentation of `[[tool_definitions]]` (`REQ-011`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261120 | 20261120 | `config/tool_catalog.toml` created; owned_tools verified byte-equal to the ToolRegistry singleton seed for all 10 servers. |
| 2 | Add or update tests per Validation plan | Completed | 20261120 | 20261120 | `tests/shared/test_tool_catalog_manifest.py`: parse, completeness, and owned-tools-match-singleton assertions. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261120 | 20261120 | ruff format/check + mypy clean; 4 manifest tests pass; no new failures vs baseline. |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — | Deploy cp line is Plan step 8 (out of scope). |

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
- **Requirement ID**: `REQ-004`, `REQ-005`, `UNK-01`
- **Source issue**: `issues/20261120-114210_agentcfg002_tool-catalog-registry.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261120-151418_agentcfg002_tool-catalog-registry.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261120-154254
- **Related target files**: `config/tool_catalog.toml`
