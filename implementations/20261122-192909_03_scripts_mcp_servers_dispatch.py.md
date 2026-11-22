## Goal

Make the dispatcher's dedup context inject-only (`configure_dedup()` (new)) and switch retry decisions from the TOML mirror to `retry_policy` tool metadata (REQ-003, REQ-005, REQ-008).

## Scope
**Release unit**: dedup-config-isolation-core (shared-store config isolation, store-identity gate, and operational reference removal)

## Assumptions
- `DedupStoreConfig`/`load_dedup_section()` from seq 01 and the injected `open_dedup_store()` from seq 02 are in place.
- Unknown/unregistered tools stay non-retryable: `RuntimeToolRegistry.get()` raises `KeyError` (caught at the call site, as today at lines 545-546) and `retry_policy_is_retryable(None)` is False — no new fallback constant (plan correction 2026-11-22).

## Design decisions
- `configure_dedup(store_config)` (new) is an eager setter over the existing replaceable module globals `_dedup_store`/`_dedup_config` (lines 164-168): it calls `open_dedup_store()` once and stores the result, preserving the test-replacement pattern.
- `_dedup_context()` (lines 171-200) keeps its degradation contract but loses the lazy `load_dedup_config()` fallback: an unconfigured process sets `_dedup_disabled` with a `not_configured` (new) start state in the audit log and returns `(None, None)` → existing payload `error_type="dedup_store_error"`, `dedup_state="store_error"`.
- Retry switch (Phase 3): the three `retry_class(...)` call sites (lines 327, 525, 544) become a registry `retry_policy` lookup through `retry_policy_is_retryable()` from `shared.tool_metadata`.

## Alternatives considered
- Keeping a lazy fallback that reads a designated server file: rejected — re-introduces discovery (REQ-001).
- A module-level retry-class dict populated at import: rejected — duplicates the registry (mirror anti-pattern this plan removes).

## Implementation
### Target file
`scripts/mcp_servers/dispatch.py`
### Procedure
1. Phase 1: add `configure_dedup()` (new) and keep a transitional `mcp_dedup.toml`-based bootstrap inside `_dedup_context()` so the suite stays green until Phase 2.
2. Phase 2: delete the transitional bootstrap and the `load_dedup_config` import; unconfigured behavior as in Design.
3. Phase 3: replace `retry_class(name, config)` at lines 327 and 525 and `retry_class(name)` at line 544 with the registry lookup (`try: rt = registry.get(name) except KeyError: non-retryable`); delete the `retry_class` import.
### Method
Registry access goes through the existing runtime tool registry import path already used by the approval path; keep the default-closed `except Exception` shape at line 545 for config-error safety.
### Details
- Size risk (measured 2026-11-22): module is 24,185 B against the 24,576 B gate (391 B headroom). Phase 2-3 removals (bootstrap + retry plumbing) must outweigh the `configure_dedup()` insertion; verify with `uv run python tools/check_module_size.py` after each phase, and split via `tools/module_nodes.py measure`/`extract` if the gate fails.
- Degradation audit keeps naming `_dedup_start_state` (add `not_configured` (new) as a value).

### Companion test files
- `tests/mcp_servers/test_mcp_dispatch.py`
  - Procedure: replace dedup-globals fixtures with `configure_dedup()`-based setup (store + injected config); keep overlay-only degradation assertions on the `dedup_state="store_error"` payload and null `call_id`; add an unconfigured (`not_configured` (new)) case; retarget retry cases from the mirror to registry `retry_policy` declarations.
  - Validation: `uv run pytest tests/mcp_servers/test_mcp_dispatch.py -q` and `uv run pytest tests/mcp_servers/ -q`.

## Compatibility considerations
- Test replacement of `_dedup_store`/`_dedup_config` (seqs 32, 34) must keep working: keep the globals module-level and unrenamed.

## Security considerations
- Unconfigured fail-safe: side-effecting non-retryable tools are refused when the store is unavailable (existing line 547-559 behavior), unchanged.

## Rollback considerations
- Revert the commit; the transitional bootstrap existed only between Phase 1 and Phase 2 in the same delivery unit.

## Validation plan
- `uv run pytest tests/mcp_servers/ -q`; `uv run pytest tests/shared/test_mcp_dedup_identity.py -q` (degradation contract); `uv run mypy scripts/mcp_servers/dispatch.py`; `uv run python tools/check_module_size.py` after every phase.

## Completion criteria
- No `load_dedup_config` or `retry_class` reference remains in the module; an unconfigured process degrades with the `store_error` payload and `not_configured` (new) start state; retry decisions read registry metadata only; module stays under the size gate.

## Out of Scope
- Server bootstrap call sites (seq 04); tool-metadata declarations themselves (unchanged, `shared.tool_metadata` is not a target row); `retry_class()` facade deletion (seq 02).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: add `configure_dedup()` + transitional bootstrap | Pending | — | — | |
| 2 | Phase 2: remove transitional bootstrap and `load_dedup_config` import | Pending | — | — | |
| 3 | Phase 3: retry switch to registry `retry_policy` + delete `retry_class` import | Pending | — | — | |
| 4 | Add or update companion tests per Validation plan | Pending | — | — | |
| 5 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: REQ-003, REQ-005, REQ-008; AC-002, AC-004
- **Source issue**: issues/20261120-115842_mcpdl003_dedup-config-isolation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261121-172154_mcpdl003_dedup-config-isolation.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261122-192909
- **Related target files**: `scripts/mcp_servers/dispatch.py`, `tests/mcp_servers/test_mcp_dispatch.py`
