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

### Corrections made in Step 3b
- Corrected in Step 3b: `config_dependent` is read as `entry.get("config_dependent", False)`, not `entry["config_dependent"]`. Seq 10's `_entry_optional_field_error()` verifies the type only when the entry carries the field and does not require it, so a direct index would raise `KeyError` on an entry that omits it. The default matches the `RuntimeTool` field default.
- Corrected in Step 3b: `degraded_capabilities` is a plain positional parameter here (not keyword-only), typed `Mapping[str, Sequence[str]] | None` and optional, matching the signature seq 13 added to `RuntimeToolRegistry` and the map shape `mcp_tool_discovery.py` produces (`server_key` to capability names).
- Corrected in Step 3b: step 3 needs no new record. The capability dependency already reaches `RuntimeTool` as the `capabilities` field from the entry; the "else the owning server's catalog capabilities" fallback is decided in `RuntimeToolRegistry` (seq 13), which is why this module only transports the map.
- Corrected in Step 3b: the call site that hands the map to `_dedupe_and_build()` is in `scripts/agent/services/mcp_tool_discovery.py` (seq 09's target), not in this file, so it is outside the Plan's frozen Implementation Target Files for this row and `tools/amend_plan.py` cannot register it. Recorded here as the deviation.

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
- Excluded tools must still produce the exclusion reason `capability` readable through `RuntimeToolRegistry.exclusion_reason()` (mechanics in seq 13; the procedure previously named it `get_exclusion_reason()`, which is not the method name in the source).

## Compatibility considerations
- New keyword arguments with existing call sites updated only here; the 14 test files that call `build_runtime_tool` directly keep working through the default (D-7).

## Security considerations
- N/A: no credential handling; the builder carries tool metadata only.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/agent/services/test_mcp_tool_discovery.py` (exclusion cases added by seq 26); `uv run ruff format` and `uv run ruff check`; `uv run mypy`; then the sequence in `rules/toolchain.md`.
- Ran: ruff format/check clean; mypy clean on both files; lint-imports 6 contracts kept; bandit clean; `wc -c` 8472 B for the target file (below 24576); check_docstrings, check_mock_patch_targets, check_module_size clean; reference table no drift; 75 cited ADR tests pass.
- Test file: 115 passed, 6 failed. The 6 are the seq 09 fallout list (2 `TestDiscoverAllServerFilter` cases and 4 `TestRequiredCapabilityCheck` cases pinning the inert guard and the tool-declaration proof) and are repaired by seq 26; no new failure comes from this cycle.
- End-to-end pipeline check for the completion criteria (ad-hoc, not committed): entries with `config_dependent=True` and `capabilities=["github.api"]` reach `RuntimeTool` with the declared value, the dependent tool is excluded with reason `capability`, the tool whose capability is not degraded stays registered, and `diagnostics()` shows the declared field.

## Completion criteria
- `config_dependent` reaches `RuntimeTool` from the entry; the degraded map reaches the registry; only dependent tools are excluded; tests pass.

## Out of Scope
- The fetch validation, the registry exclusion implementation, and the test file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the field pass-through and map hand-off | Completed | 20261126-184912 | 20261126-184912 | Changed files: scripts/agent/services/mcp_tool_discovery_registry.py, scripts/agent/services/mcp_tool_discovery.py. config_dependent read with .get(..., False) because seq 10 does not require the field; degraded_capabilities (Mapping of server key to capability-name sequence, optional) added to _build_runtime_tools() and _dedupe_and_build() and handed to RuntimeToolRegistry unchanged. The discover_all() call site is in seq 09's target file, outside the frozen target table for this row, recorded as a Step 3b deviation. File size 8472 B, below 24576. |
| 2 | Tests are covered by the test-file procedure (seq 26) | Completed | 20261126-184912 | 20261126-184912 | No tests added here; the test file is seq 26's target. Ad-hoc pipeline check confirmed the completion criteria: declared config_dependent reaches RuntimeTool, the dependent tool is excluded with reason 'capability', the non-dependent tool stays registered, diagnostics() shows the declared field. Test file currently 115 passed / 6 failed, all 6 the seq 09 fallout list pending seq 26. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261126-184912 | 20261126-184912 | ruff format/check pass; mypy clean on both files; lint-imports 6 contracts kept; bandit pass; check_docstrings, check_mock_patch_targets, check_module_size pass; reference table no drift; 75 cited ADR tests pass. Full suite pending at end of batch. Docs: N/A, the docs rows for this module are seq 33-38. |

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