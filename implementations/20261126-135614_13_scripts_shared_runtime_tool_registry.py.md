## Goal
- Add the `capability` exclusion reason, make `diagnostics()` read the explicit `config_dependent` field, and document the immutability and restart-required rule in `scripts/shared/runtime_tool_registry.py` (REQ-006, REQ-007, REQ-008).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: construction-time exclusion, `diagnostics()`, the immutability note, and the test companion.
- Out of scope: the map hand-off (seq 11); the `/mcp status` rendering (seq 14).

## Assumptions
- Verified in Step 3a: `diagnostics()` derives `config_dep = tool.status != "active"` at `runtime_tool_registry.py:281`; the only post-construction mutation is `apply_policy`, which rebinds `self._tools` to a new mapping (`:248`); the registry is published once at startup (`startup_validation.py:232-234`, reference only).
- D-2 (owner decision): no live swap; atomicity comes from the existing single rebinding, so a reader sees either the complete old or the complete new mapping.

## Design decisions
- Exclusion by capability happens at construction (D-8), in the same step as the existing `unavailable` and `posture` exclusions, with reason string `capability`.
- `diagnostics()` uses `tool.config_dependent` (seq 12) instead of the status-derived value; the capability dependency is reported as the tool's excluded-or-registered state.

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
  - Validation: `uv run pytest tests/shared/test_runtime_tool_registry.py`.

## Compatibility considerations
- The pinned status-derived row in the companion test changes; consumers read `diagnostics()` rows by key, unchanged shape.

## Security considerations
- N/A.

## Rollback considerations
- N/A: revert the commit (high blast radius file — keep this change independently revertable, Plan Risk).

## Validation plan
- `uv run pytest tests/shared/test_runtime_tool_registry.py`; `uv run ruff format` and `uv run ruff check`; `uv run mypy`; `wc -c scripts/shared/runtime_tool_registry.py` below 24576 (current size 12964 B); then the sequence in `rules/toolchain.md`.

## Completion criteria
- Capability exclusion works with reason `capability`; diagnostics show the explicit value; the immutability/restart rule is documented; the concurrent-read test passes.

## Out of Scope
- The `/mcp status` restart notice rendering (seq 14).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the exclusion, diagnostics, and immutability note | Pending | — | — | |
| 2 | Update the companion tests | Pending | — | — | |
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
- **Requirement ID**: `REQ-006` (capability exclusion), `REQ-007` (explicit diagnostics), `REQ-008` (immutable, restart-required registry)
- **Source issue**: issues/20261119-145306_cliplc008_mcp-health-capability.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261126-111451_cliplc008_mcp-health-capability.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-135614
- **Related target files**: `scripts/shared/runtime_tool_registry.py`, `tests/shared/test_runtime_tool_registry.py`
