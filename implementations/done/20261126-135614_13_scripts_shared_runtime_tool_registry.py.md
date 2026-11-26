## Goal
- Add the `capability` exclusion reason, make `diagnostics()` read the explicit `config_dependent` field, and document the immutability and restart-required rule in `scripts/shared/runtime_tool_registry.py` (REQ-006, REQ-007, REQ-008).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: construction-time exclusion, `diagnostics()`, the immutability note, and the test companion.
- Out of scope: the map hand-off (seq 11); the `/mcp status` rendering (seq 14).

## Assumptions
- Verified in Step 3a: `diagnostics()` derives `config_dep = tool.status != "active"` at `runtime_tool_registry.py:281`; the only post-construction mutation is `apply_policy`, which rebinds `self._tools` to a new mapping (`:248`); the registry is published once at startup (`startup_validation.py:232-234`, reference only).
- D-2 (owner decision): no live swap; atomicity comes from the existing single rebinding, so a reader sees either the complete old or the complete new mapping.
- Corrected in Step 3b: `degraded_capabilities` is keyword-only (placed after `allowed_servers`) so the existing positional call sites are unaffected. It is typed `Mapping[str, Sequence[str]] | None`
  and defaults to an empty mapping, matching the map `mcp_tool_discovery.py` produces (`server_key` to capability names).
- Corrected in Step 3b: the capability dependency is decided as "the tool's declared `capabilities` intersect the degraded set", and a tool that declares no capability is read as depending on the
  owning server's catalog capabilities, which reach this module only as the degraded subset of the map. Server-level reasons (`unavailable`, `disabled`, `posture`) are checked first, so a tool from an
  already-excluded server keeps that reason.
- Corrected in Step 3b: the pinned row at `:314` keeps its value (`False`, the field default); what changes is its source, so the assertion is annotated as the declared field and a new case pins the
  divergence (`status="active"` with `config_dependent=True` shows `True`, `status="inactive"` with `config_dependent=False` shows `False`).
- Corrected in Step 3b: T-08's concurrent reader loop already exists (`test_apply_policy_swap_never_exposes_mixed_state_to_concurrent_reader`) and needed no change; the added case asserts the single
  rebinding does not re-register a capability-excluded tool.
- Corrected in Step 3b: `tools/check_docstrings.py` allows exactly one em-dash in a module docstring, so the immutability note is written without one (the existing "sole routing authority —" is the
  separator the checker splits on).
- Blast radius measured before the change (rule of toolchain.md): 41 test files reference `RuntimeToolRegistry`, 19 constructions in the companion test. The change is additive, so all stay valid; the
  impact-selected run (`test_runtime_tool_registry.py`, `test_tool_routing_validation.py`, `test_route_resolver.py`, `test_tool_executor.py`, `test_cmd_mcp.py`, `test_runtime_tool_routing_integration.py`)
  passed 139 tests.

## Design decisions
- Exclusion by capability happens at construction (D-8), in the same step as the existing `unavailable` and `posture` exclusions, with reason string `capability`.
- `diagnostics()` uses `tool.config_dependent` (seq 12) instead of the status-derived value; the capability dependency is reported as the tool's excluded-or-registered state, so no new row key is
  added: a capability-excluded tool has no row and its state is read through `exclusion_reason()`.

## Alternatives considered
- Rebuild and atomically swap a candidate registry across holders (rejected by D-2: several reference holders, wide change).

## Implementation
### Target file
`scripts/shared/runtime_tool_registry.py`

### Procedure
1. Accept the degraded-capability map (from seq 11) at construction and exclude tools whose capability dependency is `degraded` or `unavailable`, recording exclusion reason `capability`.
2. In `diagnostics()`, read `config_dependent` from the explicit field; keep the `disabled_reason` fallback behavior unchanged.
3. Document in the module docstring: the registry is immutable after construction apart from the single-rebinding policy application, and an availability change requires a restart.

### Method
- Keep `apply_policy` as the single rebinding; do not add any other mutation path.

### Details
- `get_exclusion_reason()` already returns the stored reason string; `capability` joins the existing reason vocabulary.

### Companion test files
- `tests/shared/test_runtime_tool_registry.py`
  - Procedure: capability exclusion (only dependent tools excluded, reason `capability`), explicit diagnostics (`status != "active"` with `config_dependent=False` shows `False`; the pinned row at `:314` changes), and atomic policy application under a concurrent reader loop (T-06, T-07, T-08).
  - Validation: `uv run pytest tests/shared/test_runtime_tool_registry.py` (59 passed; 6 cases added: dependent tool only, no-declared-capability tool inherits the server's degraded set, server-level reason precedence, exclusion survives `apply_policy()`, explicit diagnostics divergence, and no diagnostics row for an excluded tool). T-08's concurrent reader loop was already present and unchanged.

## Compatibility considerations
- The pinned status-derived row in the companion test changes; consumers read `diagnostics()` rows by key, unchanged shape.

## Security considerations
- N/A: no credential handling; diagnostics expose tool metadata only.

## Rollback considerations
- N/A: revert the commit (high blast radius file — keep this change independently revertable, Plan Risk).

## Validation plan
- `uv run pytest tests/shared/test_runtime_tool_registry.py`; `uv run ruff format` and `uv run ruff check`; `uv run mypy`; `wc -c scripts/shared/runtime_tool_registry.py` below 24576 (current size 12964 B); then the sequence in `rules/toolchain.md`.
- Ran: 59 tests passed; ruff format/check clean; mypy clean; lint-imports 6 contracts kept; bandit clean; `wc -c` 15936 B (below 24576); check_docstrings, check_mock_patch_targets, check_module_size clean; reference table no drift; 75 cited ADR tests pass. Full suite pending at end of batch.

## Completion criteria
- Capability exclusion works with reason `capability`; diagnostics show the explicit value; the immutability/restart rule is documented; the concurrent-read test passes.

## Out of Scope
- The `/mcp status` restart notice rendering (seq 14).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the exclusion, diagnostics, and immutability note | Completed | 20261126-184144 | 20261126-184144 | Changed files: scripts/shared/runtime_tool_registry.py, tests/shared/test_runtime_tool_registry.py. Keyword-only degraded_capabilities (Mapping of server key to capability-name sequence, optional) applied at construction with reason 'capability' after the server-level reasons; diagnostics() reads tool.config_dependent; the module docstring carries the immutability and restart-required note. File size 15936 B, below 24576. Blast radius: 41 test files reference the registry, all unaffected (additive keyword-only parameter). |
| 2 | Update the companion tests | Completed | 20261126-184144 | 20261126-184144 | 6 cases added in tests/shared/test_runtime_tool_registry.py (dependent tool only, no-declared-capability tool inherits the server's degraded set, server-level reason precedence, exclusion survives apply_policy, explicit diagnostics divergence, no row for an excluded tool). 59 tests passed; T-08's existing concurrent reader loop unchanged. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261126-184144 | 20261126-184144 | ruff format/check pass; mypy clean; lint-imports 6 contracts kept; bandit pass; check_docstrings, check_mock_patch_targets, check_module_size pass; reference table no drift; 75 cited ADR tests pass; impact-selected run 139 tests passed. Full suite pending at end of batch. Docs: N/A, the docs rows for this module are seq 33-38. |

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
- **Requirement ID**: `REQ-006` (capability exclusion), `REQ-007` (explicit diagnostics), `REQ-008` (immutable, restart-required registry)
- **Source issue**: issues/20261119-145306_cliplc008_mcp-health-capability.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261126-111451_cliplc008_mcp-health-capability.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-135614
- **Related target files**: `scripts/shared/runtime_tool_registry.py`, `tests/shared/test_runtime_tool_registry.py`