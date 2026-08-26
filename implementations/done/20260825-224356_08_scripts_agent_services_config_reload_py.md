## Goal

Remove the ghost attribute write to `cfg.rag.web_search_url` from `_apply_llm_prompt_params()` so that `/reload` does not create an undeclared attribute on `RAGConfig`.

## Scope

**In-Scope**:
- `scripts/agent/services/config_reload.py:_apply_llm_prompt_params()`: remove the `_apply_str(new_cfg, "web_search_url", ...)` line.

**Out-of-Scope**:
- Formalizing `web_search_url` as a field (consumers are zero; past design decision was to deprecate it per `plans/done/20260714-150003_plan.md`).
- Web search functionality itself.

## Assumptions

- `web_search_url` was designed to be deprecated in favor of `mcp_servers.web_search.url` (confirmed via `plans/done/20260714-150003_plan.md`).
- No consumer exists anywhere in the repo — verified by `grep -rn "web_search_url" scripts/ config/ docs/` returning only the writer side at `config_reload.py:354`.

## Design decisions

- Single-line deletion only. Other fields in `_apply_llm_prompt_params()` (`llm_temperature`, `llm_url`, `embed_url`, etc.) remain untouched.

## Alternatives considered

- Keep the line and accept silent ghost attribute creation: rejected because operators can see `web_search_url` as settable in reload payload but it has no effect.
- Add `_FORBIDDEN_KEYS` guard: rejected because the old plan's `_FORBIDDEN_KEYS` mechanism was lost during later refactoring and re-introducing it is out of scope.

## Implementation

### Target file

`scripts/agent/services/config_reload.py`

### Procedure

#### Phase 1: Preparation

```bash
# Verify: grep -rn "web_search_url" scripts/ config/ docs/
# Expected: only 1 match at config_reload.py:354
```

#### Phase 2: Core Logic

**Step A: Remove `web_search_url` line from `_apply_llm_prompt_params()`**

Current code (lines 339–382):
```python
def _apply_llm_prompt_params(
    self,
    ctx: AgentContext,
    new_cfg: dict[str, Any],
) -> None:
    """Apply hot-reloadable URL, HTTP, LLM generation, tool definition, and prompt settings (diff-apply)."""
    cfg = ctx.cfg
    _apply_float(
        new_cfg, "llm_temperature", lambda v: setattr(cfg.llm, "llm_temperature", v)
    )
    _apply_int(
        new_cfg, "llm_max_tokens", lambda v: setattr(cfg.llm, "llm_max_tokens", v)
    )
    _apply_str(new_cfg, "llm_url", lambda v: setattr(cfg.llm, "llm_url", v))
    _apply_str(
        new_cfg, "web_search_url", lambda v: setattr(cfg.rag, "web_search_url", v)
    )
    _apply_str(new_cfg, "embed_url", lambda v: setattr(cfg.rag, "embed_url", v))
    _apply_float(
        new_cfg, "http_timeout", lambda v: setattr(cfg.llm, "http_timeout", v)
    )
    # ... rest unchanged
```

After change:
```python
def _apply_llm_prompt_params(
    self,
    ctx: AgentContext,
    new_cfg: dict[str, Any],
) -> None:
    """Apply hot-reloadable URL, HTTP, LLM generation, tool definition, and prompt settings (diff-apply)."""
    cfg = ctx.cfg
    _apply_float(
        new_cfg, "llm_temperature", lambda v: setattr(cfg.llm, "llm_temperature", v)
    )
    _apply_int(
        new_cfg, "llm_max_tokens", lambda v: setattr(cfg.llm, "llm_max_tokens", v)
    )
    _apply_str(new_cfg, "llm_url", lambda v: setattr(cfg.llm, "llm_url", v))
    # web_search_url removed — deprecated in favor of mcp_servers.web_search.url
    _apply_str(new_cfg, "embed_url", lambda v: setattr(cfg.rag, "embed_url", v))
    _apply_float(
        new_cfg, "http_timeout", lambda v: setattr(cfg.llm, "http_timeout", v)
    )
    # ... rest unchanged
```

#### Phase 3: Deployment & Verification

- Run: `grep -rn "web_search_url" scripts/`
- Expected: 0 matches (confirming complete removal).
- Run: `uv run pytest tests/agent/services/test_config_reload*.py -v`
- Expected: all existing tests pass (no regression).

### Details

- **REQ-001**: Delete `_apply_str(new_cfg, "web_search_url", lambda v: setattr(cfg.rag, "web_search_url", v))` from `_apply_llm_prompt_params()`.
- **AC-01**: `/reload` no longer creates undeclared attribute on `cfg.rag`.
- **AC-02**: `grep -rn "web_search_url" scripts/` returns 0 results.

## Compatibility considerations

- No API changes — removal of dead code path.
- No config schema changes required.
- Operators sending `web_search_url` in reload payload will have no effect (was already ineffective before this change).

## Security considerations

- None — removal of dead code path.

## Rollback considerations

- Revert: restore original file.
- Git ref-safe rollback: `git checkout HEAD -- scripts/agent/services/config_reload.py`.
- No database migration or config file changes.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `scripts/agent/services/config_reload.py` | Unit | `uv run pytest tests/agent/services/test_config_reload*.py -v` | No regression |
| Repository | Static check | `grep -rn "web_search_url" scripts/` | 0 matches |

## Completion criteria

- [ ] `web_search_url` line removed from `_apply_llm_prompt_params()`.
- [ ] `grep -rn "web_search_url" scripts/` returns 0 matches.
- [ ] `/reload` no longer writes undeclared attribute to `cfg.rag`.
- [ ] Existing reload tests pass without modification.

## Out of scope

- Changes to `validate_*` function contents.
- Applying validation re-execution to `ApprovalConfig`, `MemoryConfig`, `MCPConfig` etc.
- Adding new validation rules.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Preparation | Pending | — | — | Awaiting implementation |
| 2 | Core Logic Implementation | Pending | — | — | Awaiting implementation |
| 3 | Deployment & Verification | Pending | — | — | Awaiting implementation |

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
- **Requirement ID**: REQ-001
- **Source issue**: issues/20260825_cfgreload_web_search_url_ghost_attribute_issue.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260825-142600_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 2026-08-25 22:43:56
- **Related target files**: scripts/agent/services/config_reload.py
