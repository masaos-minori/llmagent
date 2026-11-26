## Goal
- Make `_probe_mcp_health_detail` in `mcp_health.py` use the per-server effective timeout, carry the parsed health report on `PostureGate`, and classify capability loss (REQ-001, REQ-004, REQ-005).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the probe function, `PostureGate`, and capability classification in this file, plus the two test companions.
- Out of scope: the contract module (seq 01); the discovery-side use of the classification (seq 09).

## Assumptions
- Verified in Step 3a: `_probe_mcp_health_detail` passes `timeout=5.0` per request (`mcp_health.py:52,54`), overriding the client-level per-server timeout built by `/mcp status`; `PostureGate` (`:95`) has no report field; the Security Posture gate is `ready=validated` (`scripts/shared/security/startup_flow.py:229`, reference only), independent of dependency failures.
- Capability required-versus-optional decision stays in the Agent from the catalog (D-6); this file only classifies the parsed state.

## Design decisions
- `PostureGate` gains the parsed `HealthReport` from seq 01 as an additive field; existing gate consumers keep reading the posture fields unchanged.
- Classification helper (new): given a gate and the server's catalog `required_capability`, returns whether the required capability is proven `ok` and which optional capabilities are degraded/unavailable.
- The classification result is a value (`CapabilityFinding`), not a side effect, so seq 09 can read the same shape from the gate.
- The readiness half of the classification delegates to `HealthChecker.is_ready()` (seq 03); this file does not re-implement the predicate.
- `required_capability` is resolved through the shared leaf reader `scripts/shared/tool_catalog.py` (`load_tool_catalog()` + `required_capability_for()`), the same reader seq 04 and seq 09 use. The catalog is loaded once for the gate loop; an unreadable catalog resolves to `None` with a warning, which keeps the legacy `ready` fallback (D-6); the fail-closed FATAL stays at discovery.

## Alternatives considered
- Keep the per-request 5.0 override (rejected by REQ-001: it defeats the per-server timeout).

## Implementation
### Target file
`scripts/agent/services/mcp_health.py`

### Procedure
1. Change `_probe_mcp_health_detail` to take the effective per-server timeout (`get_effective_health_timeout(cfg)`) instead of the hard-coded 5.0.
2. Add the parsed report to `PostureGate` (populated when the probe body parses; legacy bodies parse through the contract's legacy branch).
3. Add the capability classification helper and use it in the FATAL/warning decision so a required server whose required capability is not proven `ok` produces a FATAL finding (REQ-005).

### Method
- The probe already builds headers through `cfg.auth_headers()` (`:52`); keep that single path (REQ-003).
- Corrected in Step 3b: the probe takes the effective timeout as an optional keyword (`timeout_sec`) rather than a required argument, so the out-of-table consumer `scripts/agent/services/mcp_status.py` keeps its client-level per-server timeout and is not touched here. Omitting the keyword passes no per-request timeout, which is httpx's client-default path; passing `http.timeout` explicitly would break the fake-client fixtures in `tests/agent/services/test_agent_mcp_status.py`.

### Details
- The classification result feeds seq 09 (discovery passes degraded optional capabilities to the registry); expose it as a function, not a side effect.
- Corrected in Step 3b: the classification is a frozen dataclass (`CapabilityFinding`) plus `classify_capabilities()`, and the readiness half delegates to `HealthChecker.is_ready()` instead of re-implementing the predicate.
- Corrected in Step 3b: the new public symbols are recorded by the reference-table gate, so `registry/manifests/agent_api.yaml` and the generated index `docs/23_agent/agent_14_reference-api-subpackages-generated.md` were regenerated; the generated index grew past its recorded size ceiling (37198 -> 37507) and `tools/check_docs_structure.py`'s baseline was re-accepted at the new size.

### Companion test files
- `tests/agent/test_repl_health.py`
  - Procedure: update `_probe_mcp_health_detail` tests to the new signature and assert the per-server timeout is passed per request (T-01).
  - Validation: `uv run pytest tests/agent/test_repl_health.py`.
- `tests/agent/test_mcp_health_posture.py`
  - Procedure: cover the gate carrying the parsed report and the capability classification (required not-ok → FATAL, optional degraded → warning only) (T-04, T-05).
  - Validation: `uv run pytest tests/agent/test_mcp_health_posture.py`.

## Compatibility considerations
- `PostureGate` gains fields additively; consumers in `startup_validation.py` and discovery read existing fields unchanged (reference files).

## Security considerations
- No token in log lines or exception messages (REQ-003).

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/agent/test_repl_health.py tests/agent/test_mcp_health_posture.py`; `uv run ruff format` and `uv run ruff check`; `uv run mypy`; `wc -c scripts/agent/services/mcp_health.py` below 24576 (current size 15157 B); then the sequence in `rules/toolchain.md`.

## Completion criteria
- The probe uses the effective timeout; the gate carries the parsed report; required-capability loss yields FATAL and optional loss yields warning; tests pass.

## Out of Scope
- Registry exclusion mechanics (seq 13) and the contract module (seq 01).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the probe, gate, and classification changes | Completed | 20261126-173555 | 20261126-173555 | Changed: _probe_mcp_health_detail takes the effective timeout as an optional keyword (timeout_sec) so the out-of-table consumer mcp_status.py keeps its client-level timeout; PostureGate gained the parsed report field; CapabilityFinding + classify_capabilities() added, delegating the readiness half to HealthChecker.is_ready(); check_service_health() routes required-capability loss to FATAL and optional loss to a warning. File size 21423 B < 24576. |
| 2 | Update the companion tests | Completed | 20261126-173555 | 20261126-173555 | tests/agent/test_repl_health.py: the hard-coded 5.0 assertion replaced by the per-server timeout (T-01) plus the omitted-timeout case. tests/agent/test_mcp_health_posture.py: gate carries the parsed report (legacy branch, contract-violating body), classification cases (T-04), and the FATAL/warning routing incl. the unreadable-catalog fallback (T-05). 115 tests passed. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261126-173555 | 20261126-173555 | ruff format/check, mypy (no issues), lint-imports (6 contracts kept), bandit pass, check_docstrings, check_mock_patch_targets, check_module_size pass. Reference gate: registry/manifests/agent_api.yaml + docs/23_agent/agent_14 regenerated for the two new public symbols; tools/check_docs_structure.py baseline re-accepted at 37507. Full suite pending at end of batch. Docs: only the generated index changed. |

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
- **Requirement ID**: `REQ-001` (per-server probe timeout), `REQ-004` (parsed report on the gate), `REQ-005` (capability-based FATAL classification)
- **Source issue**: issues/20261119-145306_cliplc008_mcp-health-capability.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261126-111451_cliplc008_mcp-health-capability.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-135614
- **Related target files**: `scripts/agent/services/mcp_health.py`, `tests/agent/test_repl_health.py`, `tests/agent/test_mcp_health_posture.py`