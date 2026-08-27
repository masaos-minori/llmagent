## Goal

Make `/reload` re-run the same field validators that `LLMConfig.__post_init__`,
`RAGConfig.__post_init__`, and `ToolConfig.__post_init__` run at startup, by replacing
direct `setattr()` mutation of `ctx.cfg.llm` / `ctx.cfg.rag` / `ctx.cfg.tool` with a
diff-dict-then-`dataclasses.replace()` pattern, so an out-of-range value rejected at
startup is also rejected on reload (REQ-001, REQ-002, REQ-003, REQ-004).

## Scope

- In scope: `scripts/agent/services/config_reload.py` — the 6 `_apply_*` helper
  methods that currently call `setattr(cfg.llm/.rag/.tool, "<field>", v)`
  (`_apply_llm_context_params`, `_apply_llm_retry_params`, `_apply_tool_params`,
  `_apply_rag_params`, `_apply_llm_prompt_params`, `_apply_sse_reload_params`), plus
  `apply_config_dict()` itself (the call site that must own dict creation and the
  single `dataclasses.replace()` point).
- Out of scope (do not touch in this document):
  - `scripts/agent/services/config_validators.py` — no `validate_*` function body
    changes. **Cross-reference**: `plans/20260825-142749_plan.md` (not yet processed
    as of this writing) proposes consolidating 23 of the 27 `validate_*` functions
    into 3 shared helpers, explicitly as a pure refactor with unchanged public
    signatures/names/error messages, and its own Out-of-Scope explicitly excludes
    `/reload` re-validation (this plan's concern) as independently progressable. This
    document calls `validate_*` functions only indirectly, through
    `LLMConfig.__post_init__` / `RAGConfig.__post_init__` / `ToolConfig.__post_init__`
    (via `dataclasses.replace()`), never by name — so it has no direct call-site
    dependency on 142749's consolidation. If 142749 lands first, no re-verification is
    needed here because this document never names an individual `validate_*` function.
  - `ApprovalConfig`/`MemoryConfig`/`MCPConfig` re-validation on reload — plan's own
    Out-of-Scope.
  - `_reload_approval_settings()`, `_classify_mcp_server_changes()`,
    `_detect_startup_only()`, `masked_fields` direct assignment (line 124 as currently
    numbered), and the `getattr(lifecycle, "_cleanup_server_resources")` cleanup call
    (lines ~126-133) — unrelated to llm/rag/tool field validation. **Hot-spot note**:
    `plans/20260825-141919_plan.md` (not yet processed) targets exactly this
    `getattr()` call inside `apply_config_dict()`'s body; both that plan and this one
    edit the body of `apply_config_dict()`, so implement in whichever order the two
    plans are approved and re-read the current file content before editing if the
    other has already landed — do not assume the line numbers in this document remain
    exact after either change. **Additional hot-spot note**:
    `plans/20260825-142436_plan.md` (not yet processed, contingent on a separate
    `ToolExecutor` TTL-cache removal that has not happened yet) would delete the
    `tool_cache_ttl` diff-apply line inside `_apply_tool_params()` (the same line this
    document converts to a dict write). If that removal lands, `tool_cache_ttl` simply
    drops out of `tool_changes` with one less field to convert; no action needed here
    unless that plan is implemented before this one, in which case skip converting the
    already-removed line.
  - Adding a `web_search_url` field to `RAGConfig`, or any other dataclass field
    change — see Design decisions. **Cross-reference**: the underlying ghost-attribute
    problem is independently tracked as
    `issues/done/20260825_cfgreload_web_search_url_ghost_attribute_issue.md`, with its
    own not-yet-processed sibling plan `plans/20260825-142600_plan.md` (Goal: delete
    the `web_search_url` diff-apply line from `_apply_llm_prompt_params()` entirely,
    having confirmed no consumer exists). This document does not depend on 142600 in
    either direction: if 142600 lands first, the line this document says to "leave
    untouched" (Procedure step 4) will simply no longer exist, and there is nothing to
    convert for that field; if this document lands first, 142600 only has to delete
    one direct `setattr` line, unaffected by the dict-aggregation refactor around it.

## Assumptions

- **CORRECTED**: The dict-aggregation + `dataclasses.replace()` pattern is already implemented in code. Verified at `config_reload.py:153-189` and `config_reload.py:309-367`: `llm_changes`/`tool_changes`/`rag_changes` dicts are created, threaded through all 6 `_apply_*` helpers, and applied via `dataclasses.replace()` with `try/except ValueError` gating. No further action needed on this implementation procedure.

## Design decisions

- **Dict ownership moved to `apply_config_dict()`, not `_apply_rag_tool_params()`.**
  The plan's original design assumed `_apply_rag_tool_params()` was the parent of all
  6 helpers; it is not. `apply_config_dict()` (lines 114-140) calls
  `_apply_rag_tool_params(ctx, new_cfg)` (line 121, which internally calls
  `_apply_llm_context_params`, `_apply_tool_params`, `_apply_rag_params`,
  `_apply_llm_retry_params`), then `_reload_approval_settings` / the `masked_fields`
  direct assignment / `_classify_mcp_server_changes` (lines 122-133), then separately
  calls `_apply_llm_prompt_params(ctx, new_cfg)` (line 134) and
  `_apply_sse_reload_params(ctx, new_cfg)` (line 135), then `_sync_services(new_cfg)`
  (line 136). Because the last two helpers run **after** `_apply_rag_tool_params()`
  has already returned, the three diff dicts (`llm_changes`, `tool_changes`,
  `rag_changes`) must be created in `apply_config_dict()` before line 121 and threaded
  as explicit parameters into all 6 helpers (including through
  `_apply_rag_tool_params()` to its 4 sub-helpers), so every helper writes into the
  same dict instances.
- **Single `dataclasses.replace()` point, placed between line 135 and line 136.** All
  3 `dataclasses.replace()` calls (one per subconfig) happen once, in
  `apply_config_dict()`, immediately after the `_apply_sse_reload_params()` call
  returns and before `_sync_services(new_cfg)` is called (that method reads
  `ctx.cfg.llm/.tool.*` directly and must see the fully-applied values). This preserves
  AC-01's single-transaction guarantee (a rejected field leaves all 3 subconfigs
  unchanged) — splitting the replace() into two passes (one after
  `_apply_rag_tool_params()`, one after the later two helpers) would let the first
  pass's changes land even if the second pass is rejected, which is a correctness
  regression the plan's Design section did not originally guard against.
- **`web_search_url` is excluded from `rag_changes` and stays a direct `setattr`.**
  `_apply_llm_prompt_params()` (line 354, current numbering) sets
  `cfg.rag.web_search_url` via plain `setattr()`, but `web_search_url` is not a
  declared field of `RAGConfig` (`config_dataclasses.py:153-169`; confirmed by
  grepping the whole file and by reading `_build_rag_config()` in
  `scripts/agent/config_builders.py:249-271`, which never passes it to the
  `RAGConfig(...)` constructor). It exists only as a dynamically-set instance
  attribute on whatever `RAGConfig` instance is currently live. If it were included in
  `rag_changes` and passed to `dataclasses.replace(cfg.rag, **rag_changes)`, that call
  raises `TypeError: __init__() got an unexpected keyword argument 'web_search_url'`
  — not a `ValueError`, so it would not be caught by the `except ValueError` handler
  this document adds, and `/reload` would crash instead of the current
  silently-accepted behavior. `web_search_url` has no corresponding `validate_*` call
  in `RAGConfig.__post_init__` (confirmed: the `__post_init__` body only calls the
  refiner-related validators), so it is also outside this plan's actual goal
  (re-running validators). Resolution: keep `setattr(ctx.cfg.rag, "web_search_url", v)`
  as a direct, immediate assignment, not routed through `rag_changes` — same treatment
  as the existing direct `masked_fields` assignment at line 124, which is likewise
  unvalidated and applied outside the replace() transaction.
- Concrete dict-write idiom: since a `lambda v: changes["field"] = v` is not valid
  Python, use `lambda v: changes.update({"field": v})` (or an equivalent
  `dict.__setitem__` call) as the setter passed to the existing generic
  `_apply_int`/`_apply_float`/`_apply_bool`/`_apply_str`/`_apply_list`/
  `_apply_list_nonempty`/`_apply_str_nonempty`/`_apply_dict_nonempty` helpers
  (`scripts/agent/services/typed_validators.py:163-220`, all typed as
  `setter: Callable[[T], None]` — a dict-writing lambda satisfies this).

## Alternatives considered

- Call `dataclasses.replace()` once per helper (6 times total) instead of once per
  subconfig after all helpers finish: rejected — it does not batch changes from
  different helpers touching the same subconfig (e.g. `_apply_llm_context_params` and
  `_apply_llm_retry_params` both touch `cfg.llm`) into one atomic reconstruction, and
  reintroduces the same non-atomic-update problem this plan exists to fix.
- Give `_apply_rag_tool_params()` its own local replace() for its 4 sub-helpers, and a
  second replace() after `_apply_llm_prompt_params`/`_apply_sse_reload_params`:
  rejected — breaks the single-transaction guarantee (AC-01) as explained in Design
  decisions.
- Add `web_search_url` as a declared `RAGConfig` field so it can be included in
  `rag_changes` uniformly: rejected — out of scope (a dataclass field addition is not
  in this plan's Requirements, and `web_search_url` has no validator to re-run, so
  there is no goal-relevant reason to add it as a field here).

## Implementation

### Target file
`scripts/agent/services/config_reload.py`

### Procedure
1. In `apply_config_dict()` (currently lines 114-140), before the
   `self._apply_rag_tool_params(ctx, new_cfg)` call, create
   `llm_changes: dict[str, Any] = {}`, `tool_changes: dict[str, Any] = {}`,
   `rag_changes: dict[str, Any] = {}`.
2. Change `_apply_rag_tool_params(self, ctx, new_cfg)` to
   `_apply_rag_tool_params(self, ctx, new_cfg, llm_changes, tool_changes, rag_changes)`
   and pass the 3 dicts through to its 4 calls
   (`_apply_llm_context_params`/`_apply_llm_retry_params` get `llm_changes`;
   `_apply_tool_params` gets `tool_changes`; `_apply_rag_params` gets `rag_changes`).
3. In each of the 4 sub-helpers, replace every
   `lambda v: setattr(cfg.llm/.tool/.rag, "<field>", v)` with
   `lambda v: <changes_dict>.update({"<field>": v})` — 15 call sites across
   `_apply_llm_context_params` (2), `_apply_tool_params` (4), `_apply_rag_params` (7),
   `_apply_llm_retry_params` (2), i.e. everything currently matched by
   `grep -n "setattr(cfg\." scripts/agent/services/config_reload.py` at lines 232,
   237, 243, 248, 253, 258, 266, 271, 276, 279, 284, 287, 292, 300, 305 (15 lines).
4. Pass `llm_changes`, `tool_changes`, `rag_changes` (rag excluding
   `web_search_url`) into `_apply_llm_prompt_params(self, ctx, new_cfg, llm_changes,
   tool_changes, rag_changes)` (line 134 call site) and convert its `cfg.llm`/`cfg.tool`
   `setattr` calls (lines 347, 350, 352, 358, 361, 366, 371, 376, 381) and its
   `cfg.rag` `embed_url` `setattr` (line 356) to dict writes the same way; leave line
   354's `web_search_url` `setattr` untouched (direct, immediate).
5. Pass `llm_changes` into `_apply_sse_reload_params(self, ctx, new_cfg, llm_changes)`
   (line 135 call site) and convert its 5 direct `ctx.cfg.llm.<field> = v` assignments
   (lines 391-403) to `llm_changes["<field>"] = v` (these already use plain assignment,
   not `setattr()`, so the earlier `grep "setattr(cfg\."`-based verification alone
   would not catch a missed conversion here — also grep
   `ctx\.cfg\.llm\.\w+ = ` before/after).
6. After the `_apply_sse_reload_params(ctx, new_cfg)` call (line 135) and before
   `service_result = self._sync_services(new_cfg)` (line 136), add:
   ```python
   if llm_changes:
       try:
           ctx.cfg.llm = dataclasses.replace(ctx.cfg.llm, **llm_changes)
       except ValueError as e:
           raise ConfigReloadValidationError(str(e)) from e
   if tool_changes:
       try:
           ctx.cfg.tool = dataclasses.replace(ctx.cfg.tool, **tool_changes)
       except ValueError as e:
           raise ConfigReloadValidationError(str(e)) from e
   if rag_changes:
       try:
           ctx.cfg.rag = dataclasses.replace(ctx.cfg.rag, **rag_changes)
       except ValueError as e:
           raise ConfigReloadValidationError(str(e)) from e
   ```
   in that order (llm context → tool → rag → llm retry → llm prompt → sse is the
   existing helper call order; the 3 replace() calls themselves run llm → tool → rag,
   an arbitrary but stable order since all 3 dicts are already fully collected by this
   point).
7. Add `import dataclasses` to the module's imports if not already present (currently
   only `from dataclasses import dataclass, field` is imported — `dataclasses.replace`
   needs either `import dataclasses` or `from dataclasses import replace`; prefer
   `from dataclasses import dataclass, field, replace` for consistency with the
   existing import style, and call `replace(...)` unqualified).
8. Run `uv run mypy scripts/agent/services/config_reload.py` and confirm no new errors
   (Plan Phase 3 item).
9. Confirm no `deploy/deploy.sh` change is needed (no file added/removed/moved; Plan
   Phase 3 item) — `scripts/` is rsynced wholesale per `rules/toolchain.md`.

### Method
Diff-collect-then-replace: every `_apply_*` helper writes into one of 3 dicts owned by
`apply_config_dict()` instead of mutating `ctx.cfg.llm/.tool/.rag` in place; a single
`dataclasses.replace()` per subconfig, gated by `try/except ValueError`, applies the
collected diff atomically once all 6 helpers have run.

### Details
- `_apply_rag_tool_params` signature and its 4 internal calls
  (`config_reload.py:213-223`) gain 3 new parameters, threaded straight through.
- `_apply_llm_context_params`, `_apply_tool_params`, `_apply_rag_params`,
  `_apply_llm_retry_params` (`config_reload.py:225-306`) each gain 1-3 new dict
  parameters (only the ones relevant to what they touch) and lose all `setattr` calls.
- `_apply_llm_prompt_params` (`config_reload.py:339-382`) and
  `_apply_sse_reload_params` (`config_reload.py:384-403`) gain dict parameters at their
  `apply_config_dict()` call sites (lines 134-135) directly — not through
  `_apply_rag_tool_params()`.
- No change to `_apply_rag_tool_params()`'s own docstring beyond what's needed to
  reflect the new parameters; no change to `_reload_approval_settings`,
  `_classify_mcp_server_changes`, `_detect_startup_only`, or the `masked_fields`
  direct-assignment line.

## Compatibility considerations

- Public method signatures of `ConfigReloadService.apply_config()` /
  `apply_config_dict()` (the class's external API, called from the command handler)
  are unchanged — only private `_apply_*` helper signatures gain parameters.
- Behavior change (intended): a value that would be rejected at startup (e.g.
  `llm_temperature = 5.0`) is now also rejected on `/reload`, raising
  `ConfigReloadValidationError` instead of being silently applied. This is the plan's
  explicit goal (REQ-005/AC-01), not a regression.
- `web_search_url` reload behavior is unchanged (still a direct, unvalidated
  `setattr`) — no compatibility impact for that one field.

## Security considerations

- N/A: no new external input path, no new trust boundary — `new_cfg` is already the
  same reload-request-derived dict consumed by the current `setattr`-based code; this
  change only tightens validation (rejects more, not less).

## Rollback considerations

- Single-file change with no data migration and no `config/*.toml` shape change;
  revert via `git revert` of this file's commit. No `deploy.sh` update needed either
  way (no file add/remove/move).

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `scripts/agent/services/config_reload.py` | Unit/Integration | `uv run pytest tests/agent/services/test_config_reload.py -v` | All existing tests green; new tests from the sibling test document (seq 04) green |
| `scripts/agent/services/config_reload.py` | Type check | `uv run mypy scripts/agent/services/config_reload.py` | No new errors |
| Repository-wide | Regression | `uv run pytest` | No new failures |
| Repository-wide | Type check | `uv run mypy scripts/` | No new errors |
| `scripts/agent/services/config_reload.py` | Static verification | `grep -n "setattr(cfg\." scripts/agent/services/config_reload.py; grep -n "ctx\.cfg\.llm\.\w* = " scripts/agent/services/config_reload.py` | Zero matches for both (all 26 `setattr(cfg.*)` sites plus the 5 `_apply_sse_reload_params` direct-assignment sites converted, except the 1 intentionally-untouched `web_search_url` `setattr`) |

## Completion criteria

- All 6 `_apply_*` helpers write to `llm_changes`/`tool_changes`/`rag_changes` instead
  of mutating `ctx.cfg.llm/.tool/.rag` directly, except the intentional
  `web_search_url` exception.
- Exactly one `dataclasses.replace()` call per subconfig exists in
  `apply_config_dict()`, positioned after `_apply_sse_reload_params()` and before
  `_sync_services()`.
- `uv run pytest tests/agent/services/test_config_reload.py -v` and
  `uv run mypy scripts/agent/services/config_reload.py` both pass with no new
  failures/errors.

## Out of scope

- `config_validators.py` validator body/consolidation changes (see Scope
  cross-reference to `plans/20260825-142749_plan.md`).
- `ApprovalConfig`/`MemoryConfig`/`MCPConfig` reload re-validation.
- The `getattr(lifecycle, "_cleanup_server_resources")` fix targeted by
  `plans/20260825-141919_plan.md`.
- Any `RAGConfig` field-set change (e.g. declaring `web_search_url` as a field).
- Test additions — covered by the sibling document
  `implementations/20260826-103846_04_tests_agent_services_test_config_reload.py.md`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Thread `llm_changes`/`tool_changes`/`rag_changes` through `apply_config_dict()` and all 6 `_apply_*` helpers | Obsolete | — | — | Already implemented at config_reload.py:153-189, 309-367 |
| 2 | Add the single `dataclasses.replace()` + `except ValueError` block per subconfig | Obsolete | — | — | Already implemented |
| 3 | Verify `web_search_url` stays a direct `setattr` | Obsolete | — | — | Already handled |
| 4 | Run validation sequence | Obsolete | — | — | N/A |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| All | Document describes work already implemented in source code | Yes | 2026-08-27 |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-001 (llm dict-aggregation), REQ-002 (tool dict-aggregation), REQ-003 (rag dict-aggregation), REQ-004 (single `dataclasses.replace()` + error conversion point)
- **Source issue**: `issues/20260825_cfgreload_missing_validator_reexecution_issue.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260825-142225_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260826-103846
- **Related target files**: `scripts/agent/services/config_reload.py`
