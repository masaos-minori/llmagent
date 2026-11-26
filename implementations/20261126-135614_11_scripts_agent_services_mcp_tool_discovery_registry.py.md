## Goal
- Pass the explicit `config_dependent` value and the catalog-derived capability dependency into `build_runtime_tool`, and pass the degraded-capability map to the registry in `mcp_tool_discovery_registry.py` (REQ-006, REQ-007).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: `_build_runtime_tools()` and `_dedupe_and_build()` in this file only.
- Out of scope: the fetch-layer validation (seq 10); the registry exclusion mechanics (seq 13); the test file is covered by seq 26.

## Assumptions
- Verified in Step 3a: `_build_runtime_tools()` (`:59-103`) passes every schema-2.1 field unchanged but drops `config_dependent`; `build_runtime_tool` gains the field via seq 12 (optional keyword, default `False`, D-7).
- The degraded-capability map arrives from seq 09 (`discover_all`); this module transports it, it does not decide it (same pattern as `allowed_servers`).

## Design decisions
- D-8: exclusion happens at construction in the same step as the existing `unavailable` and `posture` exclusions, keeping one publication.

## Alternatives considered
- Post-construction exclusion (rejected by D-8: breaks the immutability rule, REQ-008).

## Implementation
### Target file
`scripts/agent/services/mcp_tool_discovery_registry.py`

### Procedure
1. Add `config_dependent=entry["config_dependent"]` to the `build_runtime_tool` call (the fetch layer has already verified the bool, same suppression style as the neighboring fields).
2. Add a `degraded_capabilities` (new) parameter (per-server map of capability name to state) to `_build_runtime_tools()` and `_dedupe_and_build()`, and pass it to `RuntimeToolRegistry` so dependent tools are excluded with reason `capability` (mechanics in seq 13).
3. Record each tool's capability dependency (entry `capabilities` if present, else the owning server's catalog capabilities via the map) for the registry's exclusion decision.

### Method
- This module transports the map unchanged; the exclusion decision itself lives in `RuntimeToolRegistry` (seq 13).

### Details
- Excluded tools must still produce the exclusion reason `capability` readable through `get_exclusion_reason()` (seq 13).

## Compatibility considerations
- New keyword arguments with existing call sites updated only here; the 14 test files that call `build_runtime_tool` directly keep working through the default (D-7).

## Security considerations
- N/A: no credential handling; the builder carries tool metadata only.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/agent/services/test_mcp_tool_discovery.py` (exclusion cases added by seq 26); `uv run ruff format` and `uv run ruff check`; `uv run mypy`; then the sequence in `rules/toolchain.md`.

## Completion criteria
- `config_dependent` reaches `RuntimeTool` from the entry; the degraded map reaches the registry; only dependent tools are excluded; tests pass.

## Out of Scope
- The fetch validation, the registry exclusion implementation, and the test file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the field pass-through and map hand-off | Pending | — | — | |
| 2 | Tests are covered by the test-file procedure (seq 26) | Pending | — | — | |
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
- **Requirement ID**: `REQ-006` (capability dependency reaches the registry), `REQ-007` (explicit `config_dependent` pass-through)
- **Source issue**: issues/20261119-145306_cliplc008_mcp-health-capability.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261126-111451_cliplc008_mcp-health-capability.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-135614
- **Related target files**: `scripts/agent/services/mcp_tool_discovery_registry.py`
