## Goal
- Reorder discovery in `mcp_tool_discovery.py` so the catalog is loaded before registry construction, prove the required capability from the health report, and pass degraded optional capabilities to the registry (REQ-005, REQ-006).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: `discover_all()`, `_check_required_tools()`, and the capability hand-off in this file, plus the test companion.
- Out of scope: the registry builder internals (seq 11); the classification helper (seq 06); the catalog content itself (seq 17).

## Assumptions
- Verified in Step 3a: `discover_all()` builds the registry at `:107` before loading the catalog at `:112`; `_check_required_tools()` (`:260`) is inert because no tool declares `capabilities` (`:280` guard, `docs/22_mcp/mcp_08...md:86`); the missing-catalog path is already FATAL (`:113-123`).
- Required-versus-optional rule (D-6): required only when the capability equals the catalog `required_capability` of a `required=true` server; the GitHub server is always `required=true` (`mcp_config.py:208-212`).
- UNK-02 (Plan Risk mitigation): check the production health samples under `/opt/llm` for a required server with no capability block before the required-capability gate is relied on in production; start every server in staging before deploy.
- Corrected in Step 3b (owner decision, 2026-11-26): the hand-off call is deferred to seq 11. `_dedupe_and_build()` has no capability-map parameter yet, so this procedure provides the producer
  (`_degraded_capability_map()`) and seq 11 adds the call site. The map is inert until seq 13 implements the exclusion.
- Corrected in Step 3b: `_load_tool_catalog()` stays as a thin wrapper delegating to `shared.tool_catalog.load_tool_catalog()` (the shared reader recorded as the seq 03 design decision), so the
  existing monkeypatch points in `test_mcp_tool_discovery.py` keep working. `tomllib` and `resolve_config_dir` are no longer imported here.
- Corrected in Step 3b: the per-server `absent from tool_catalog.toml` and `does not declare a required_capability` FATAL branches are dropped. Under D-6 a required server with no catalog entry is
  read through the legacy `ready` flag, so absence is no longer a finding by itself; only the missing/unreadable-file FATAL stays.
- Corrected in Step 3b: a required server with no gate, or a gate carrying no parsed report, proves nothing and is FATAL. This makes six existing cases in `test_mcp_tool_discovery.py` (seq 26's
  target file) fail until seq 26 updates them: `TestDiscoverAllServerFilter::test_empty_url_server_is_skipped`, `::test_disabled_server_is_skipped_no_http_call`, and four
  `TestRequiredCapabilityCheck` cases that pin the inert guard or the tool-declaration proof. Recorded as seq 26's fallout, not fixed here.

## Design decisions
- D-9: load the catalog first, then build the registry with the degraded-capability map so dependent tools are excluded at construction (one publication, no post-construction mutation).
- The health report (from the gate, seq 06) is the proof of the required capability; the catalog supplies the identifier.

## Alternatives considered
- Keep the check inert until servers declare capabilities (rejected by REQ-005: required loss must block startup).

## Implementation
### Target file
`scripts/agent/services/mcp_tool_discovery.py`

### Procedure
1. Read the catalog through `shared.tool_catalog` before `_dedupe_and_build()`; keep the missing-file FATAL message. The fail-closed path now returns an empty registry, since no tool row is built
   before the catalog is read.
2. Replace the inert `capabilities` guard in `_check_required_tools()` with the report-based proof: for each `required=true` server, the parsed health report must prove its catalog
   `required_capability` `ok` (legacy bodies fall back to `ready`, D-6); otherwise FATAL. The method no longer takes the registry — the proof reads the gate map.
3. Collect the degraded/unavailable optional capabilities per server from the report into `_degraded_capability_map()`; the call site that hands the map to `_dedupe_and_build()` is added in seq 11.

### Method
- The gate map (`self._posture_gates`) already carries the parsed report (seq 06); read the capability states from it through `classify_capabilities()` rather than re-parsing.

### Details
- A tool's capability dependency is the catalog `capabilities` of its owning server unless the discovery entry declares `capabilities` (Plan Assumption); the exclusion itself happens in the registry (seq 13).

### Companion test files
- `tests/agent/services/test_mcp_tool_discovery_posture_gate.py`
  - Procedure: `TestRequiredCapabilityProofFromTheGateReport` — required capability `degraded` and `unavailable` produce FATAL, a proven `ok` reports nothing, a legacy body falls back to `ready`
    (and a legacy body with `ready=false` produces FATAL), and an optional `degraded` capability produces the map (T-05). Gates carry the parsed report through `parse_health_body()`; the catalog
    fixture is patched through `_load_tool_catalog()` so the test does not read `config/tool_catalog.toml`.
  - Validation: `uv run pytest tests/agent/services/test_mcp_tool_discovery_posture_gate.py` (15 passed).

## Compatibility considerations
- The reorder changes the FATAL path order only; the existing missing-catalog message and status stay (Plan Risk mitigation).

## Security considerations
- N/A: no credential handling in this file.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/agent/services/test_mcp_tool_discovery.py tests/agent/services/test_mcp_tool_discovery_posture_gate.py`; `uv run ruff format` and `uv run ruff check`; `uv run mypy`; `wc -c scripts/agent/services/mcp_tool_discovery.py` below 24576 (current size 14858 B); then the sequence in `rules/toolchain.md`.

## Completion criteria
- Catalog loads before registry construction; required capability loss produces FATAL; the degraded optional capability map is produced (its registry call site lands in seq 11); the companion
  tests pass. The six `test_mcp_tool_discovery.py` cases listed in Assumptions stay red until seq 26.

## Out of Scope
- The registry builder, the catalog content, and the standalone discovery test file (seq 26).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the reorder, capability proof, and map hand-off | Completed | 20261126-181832 | 20261126-181832 | Catalog read through shared.tool_catalog (thin _load_tool_catalog wrapper kept for the existing monkeypatch points) before _dedupe_and_build(); the fail-closed path returns an empty registry. _check_required_tools() no longer takes the registry and proves the required capability from the gate report via classify_capabilities(); the inert guard and the per-server absent/undeclared FATAL branches are dropped (D-6 legacy ready fallback). _degraded_capability_map() is the producer; its call site lands in seq 11 (owner decision). File size 16126 B < 24576. |
| 2 | Update the companion tests | Completed | 20261126-181832 | 20261126-181832 | tests/agent/services/test_mcp_tool_discovery_posture_gate.py: TestRequiredCapabilityProofFromTheGateReport added (degraded, unavailable, proven ok, legacy ready true/false, optional degraded map). 15 tests passed. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261126-181832 | 20261126-181832 | ruff format/check pass; mypy clean; lint-imports 6 contracts kept; bandit pass; check_docstrings, check_mock_patch_targets, check_module_size pass; reference table no drift; 75 cited ADR tests pass. Six cases in tests/agent/services/test_mcp_tool_discovery.py are red by design until seq 26 updates them. |

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
- **Requirement ID**: `REQ-005` (required capability proof blocks startup), `REQ-006` (degraded optional capabilities reach the registry)
- **Source issue**: issues/20261119-145306_cliplc008_mcp-health-capability.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261126-111451_cliplc008_mcp-health-capability.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-135614
- **Related target files**: `scripts/agent/services/mcp_tool_discovery.py`, `tests/agent/services/test_mcp_tool_discovery_posture_gate.py`