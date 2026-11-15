## Goal

Remove the static-config fallback in `_stream_llm()` so the runtime tool registry is the sole source of the LLM-facing tool definitions. (`REQ-001`)

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- `ctx.services_required.runtime_tools` is always populated in production; an absent registry is now an invalid, unreachable state rather than a valid "use static list" state.
- Removing the fallback does not reduce tool availability: tools are still served by `RuntimeToolRegistry.llm_tool_definitions()` in the normal path.
- The static `tool_definitions` field is still read elsewhere (startup drift validation, `/mcp status` + `/help` counts, test fixtures); this row changes only the LLM-facing read.

## Design decisions
- Fail loudly instead of silently falling back: replace the ternary with a guard that raises when the registry is absent, so a misconfigured turn aborts clearly rather than serving a stale tool surface.
- Do not introduce a replacement authority; the plan makes `RuntimeToolRegistry` the single source.

## Alternatives considered
- Keeping the fallback but marking it deprecated: rejected — `REQ-001` requires no fallback to remain in the LLM-facing path.
- Returning an empty tool list when the registry is absent: weaker than a hard error and could confuse the LLM; a raised error is clearer.

## Implementation
### Target file
`scripts/agent/llm_turn_runner.py`

### Procedure
1. In `_stream_llm()` (around lines 362-367), remove the `else ctx.cfg.tool.tool_definitions` branch of the `tool_defs` ternary.
2. Replace it with a guard that requires the registry: fetch `registry = ctx.services_required.runtime_tools`, assert/raise if `registry is None`, then call `registry.llm_tool_definitions()`.
3. Confirm nothing else in `llm_turn_runner.py` reads `ctx.cfg.tool.tool_definitions` for the LLM-facing surface.

### Method
Locate the block at lines 362-367 with `grep -n "tool_definitions\|runtime_tools" scripts/agent/llm_turn_runner.py`; rewrite the ternary as an explicit guard; run the LLM-turn tests.

### Details
- Current code (lines 362-367):
  ```python
  registry = ctx.services_required.runtime_tools
  tool_defs = (
      registry.llm_tool_definitions()
      if registry is not None
      else ctx.cfg.tool.tool_definitions
  )
  ```
- After the change the static list is never injected here, satisfying the "sole authority" contract. Any test that stubs `runtime_tools` as `None` and expects the static list must be updated (see `test_cmd_mcp.py` / `test_command_registry_consistency.py`).

## Compatibility considerations
Behavior change: a turn whose runtime registry is absent now errors instead of serving the static config. No backward-compat path for the removed fallback (no-shim policy).

## Security considerations
Serving a stale/static tool list could expose tools that the runtime registry would have gated; removing the fallback closes that gap.

## Rollback considerations
Revert the commit.

## Validation plan
- Unit tests for `_stream_llm` / the turn path pass with a populated registry.
- A test asserting that an absent registry raises (rather than falling back) is added or confirmed present.
- `rg` confirms no other LLM-facing read of `cfg.tool.tool_definitions` remains in `llm_turn_runner.py`.

## Completion criteria
- `_stream_llm()` no longer references `ctx.cfg.tool.tool_definitions`.
- The runtime registry is the only source of `tool_defs`.

## Out of Scope
- Changes to `config_dataclasses.py` (that field's documentation is a separate row).
- Changes to the `/mcp status` and `/help` tool-count displays (separate rows).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
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
- **Requirement ID**: `REQ-001` — make the runtime tool registry the sole authority for the LLM-facing tool list
- **Source issue**: `issues/20261111-163741_rtregistry001_runtime-registry-sole-authority.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261115-050235_rtregistry001_runtime-registry-sole-authority.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261115-090843
- **Related target files**: `scripts/agent/llm_turn_runner.py`
