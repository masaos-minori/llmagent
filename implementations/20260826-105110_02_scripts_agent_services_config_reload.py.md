## Goal

Delete the dead `web_search_url` diff-apply line inside `_apply_llm_prompt_params()` so
`/reload` stops writing an undeclared `web_search_url` attribute onto the `RAGConfig`
instance at `ctx.cfg.rag` (REQ-001).

## Scope

- In scope: the single `_apply_str(new_cfg, "web_search_url", lambda v: setattr(cfg.rag,
  "web_search_url", v))` statement inside `_apply_llm_prompt_params()`
  (`scripts/agent/services/config_reload.py`, currently lines 353-355).
- Out of scope:
  - Declaring `web_search_url` as a formal `RAGConfig` field — verified there is no
    reader anywhere in `scripts/` for this attribute (see Assumptions), and the
    Plan's own Out-of-Scope explicitly rejects formalizing it.
  - Any other field in `_apply_llm_prompt_params()` (`llm_temperature`, `llm_max_tokens`,
    `llm_url`, `embed_url`, `http_timeout`, `max_tool_turns`,
    `tool_result_max_llm_chars`, `tool_definitions`, `system_prompt_tool`,
    `system_prompts`) — none of these are touched by this change.
  - `scripts/shared/config_loader.py` `_FORBIDDEN_KEYS` — confirmed this mechanism does
    not currently exist in the codebase (`rg -n "_FORBIDDEN_KEYS" scripts/` returns zero
    matches); re-introducing it is not part of this Plan's Requirements and is not
    added here.
  - Web search functionality itself (`mcp_servers.web_search` in `config/agent.toml`,
    `scripts/mcp_servers/web_search/`) — unaffected.

## Assumptions

- Verified by `rg -n "web_search_url" scripts/ config/ docs/`: the only match in this
  scope is `scripts/agent/services/config_reload.py:354` (the write side, inside
  `_apply_str(...)`). `RAGConfig` (`scripts/agent/config_dataclasses.py:153-169`) has no
  `web_search_url` field, and `_build_rag_config()`
  (`scripts/agent/config_builders.py:249-271`) never constructs one — so the attribute
  set by this line exists only as a dynamically-added instance attribute with no reader
  anywhere in production code.
- Two incidental string matches exist under `tests/` (outside this Plan's grep scope,
  checked here as an extra safety net): `tests/shared/test_mcp_config.py:110` uses
  `"web_search_url"` as an unrelated flat dict key fed to `_build_mcp_servers()` (a
  different code path, not `RAGConfig`); `tests/agent/commands/test_agent_cmd_config.py:183`
  sets `ctx.cfg.rag.web_search_url = "http://ws"` directly on a `MagicMock`-based test
  context to exercise `_print_config_values()`'s generic attribute printing — it does not
  call `_apply_llm_prompt_params()` and is unaffected by this deletion.
- `tests/agent/services/test_config_reload.py` and
  `tests/agent/services/test_config_reload_classification.py` (the files matched by the
  Plan's `test_config_reload*.py` glob) contain zero references to `web_search_url`
  (`rg -n "web_search_url" tests/agent/services/` — zero matches), so no test edits are
  required alongside this deletion.

## Design decisions

- Delete the whole `_apply_str(...)` statement (all 3 physical lines, 353-355) rather
  than only the string literal — a partial edit would leave a syntactically invalid or
  dead call. This is a pure deletion, not a refactor of the surrounding helper calls.
- Do not add `web_search_url` to `RAGConfig` as a compatibility shim: doing so would
  reintroduce exactly the "written but never read" ghost field the Plan's Reason for
  change identifies as the maintenance hazard, just moved from "undeclared instance
  attribute" to "declared but pointless field."

## Alternatives considered

- Add `web_search_url` to `RAGConfig` and keep the diff-apply line: rejected per the
  Plan's Out-of-Scope — no consumer exists anywhere in `scripts/`, so formalizing the
  field would only legitimize dead configuration.
- Reintroduce `_FORBIDDEN_KEYS` in `scripts/shared/config_loader.py` and add
  `web_search_url` to it: rejected — out of scope for this Plan (REQ-001 only calls for
  deleting the write line); `_FORBIDDEN_KEYS` does not exist in the current codebase and
  reintroducing it is a separate, larger design decision not requested here.

## Implementation

### Target file
`scripts/agent/services/config_reload.py`

### Procedure
1. In `_apply_llm_prompt_params()` (`scripts/agent/services/config_reload.py:339-382`),
   remove the following statement in full (currently lines 353-355):
   ```python
   _apply_str(
       new_cfg, "web_search_url", lambda v: setattr(cfg.rag, "web_search_url", v)
   )
   ```
2. Do not modify the `_apply_str(new_cfg, "llm_url", ...)` line immediately above it
   (line 352) or the `_apply_str(new_cfg, "embed_url", ...)` line immediately below it
   (line 356) — `_apply_str` remains used by both and its import
   (`from agent.services.typed_validators import ... _apply_str, ...`, line 36) must
   stay in place.
3. Run `uv run ruff format scripts/agent/services/config_reload.py` to confirm no
   formatting fallout from the deletion (the surrounding lines are independent
   statements, so none is expected).
4. Run `grep -rn "web_search_url" scripts/` and confirm zero matches (AC-02).
5. Confirm no `deploy/deploy.sh` change is needed — no file added, removed, or moved;
   `scripts/` is rsynced wholesale per `rules/toolchain.md`.

### Method
Straight statement deletion: remove the 3-line `_apply_str(...)` call for
`web_search_url` from `_apply_llm_prompt_params()`; no replacement logic, no signature
change, no other call sites touched.

### Details
- `_apply_llm_prompt_params()`'s signature and docstring are unchanged by this Plan.
  **Cross-plan note**: sibling plan `plans/20260825-142225_plan.md` (already processed
  into `implementations/20260826-103846_01_scripts_agent_services_config_reload.py.md`
  and `implementations/20260826-103846_04_tests_agent_services_test_config_reload.py.md`)
  independently investigated this same function and its own Design decisions explicitly
  excludes `web_search_url` from the `rag_changes` dict it threads through
  `_apply_llm_prompt_params()`, specifically so its `dataclasses.replace()`-based
  refactor does not collide with this deletion. That document already states: "if
  142600 lands first, the line this document says to 'leave untouched' ... will simply
  no longer exist, and there is nothing to convert for that field; if this document
  lands first, 142600 only has to delete one direct `setattr` line, unaffected by the
  dict-aggregation refactor around it." Confirmed no functional conflict either order —
  implementers should apply whichever of the two changes lands first, then re-read the
  current body of `_apply_llm_prompt_params()` before applying the second, since line
  numbers inside the function will have shifted once 142225's document is implemented.
- No other `implementations/` document references `web_search_url` as a target of
  change (checked `implementations/` and `implementations/done/` for a document whose
  `Source plan` is `plans/20260825-142600_plan.md` — none exists), so this is genuinely
  new, unstarted work.

## Compatibility considerations

- Public behavior change (intended): after this change, sending `web_search_url` in a
  `/reload` payload has no effect at all (previously it silently set an unused instance
  attribute with no effect either — so the externally observable behavior for any
  consumer of the reload result is unchanged; only the internal side effect of the
  ghost `setattr` is removed).
- No effect on `_print_config_values()` (`scripts/agent/commands/cmd_config.py`) or its
  test (`tests/agent/commands/test_agent_cmd_config.py:183`) — that test sets the
  attribute directly on a mock, independent of `_apply_llm_prompt_params()`.

## Security considerations

- N/A: no new external input path, no new trust boundary. This removes a write, it does
  not add one; the deleted line had no reader, so no confidentiality/integrity surface
  is affected either way.

## Rollback considerations

- Single-statement deletion, no data migration, no `config/*.toml` shape change; revert
  via `git revert` of this file's commit if needed.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `scripts/agent/services/config_reload.py` | Unit | `uv run pytest tests/agent/services/test_config_reload.py tests/agent/services/test_config_reload_classification.py -v` | All existing tests remain green (no test references `web_search_url`) |
| `scripts/agent/services/config_reload.py` | Static verification | `grep -rn "web_search_url" scripts/` | 0 matches (AC-02) |
| `scripts/agent/services/config_reload.py` | Format/lint | `uv run ruff format scripts/agent/services/config_reload.py && uv run ruff check scripts/agent/services/config_reload.py` | No diff beyond the deletion; no new lint errors |
| `scripts/agent/services/config_reload.py` | Type check | `uv run mypy scripts/agent/services/config_reload.py` | No new errors |
| Repository-wide | Regression | `uv run pytest` | No new failures |

## Completion criteria

- The `_apply_str(new_cfg, "web_search_url", lambda v: setattr(cfg.rag,
  "web_search_url", v))` statement no longer exists in
  `scripts/agent/services/config_reload.py`.
- `grep -rn "web_search_url" scripts/` returns 0 matches.
- `uv run pytest tests/agent/services/test_config_reload*.py -v` passes with no new
  failures.

## Out of scope

- Declaring `web_search_url` as a `RAGConfig` field (see Alternatives considered).
- Reintroducing `_FORBIDDEN_KEYS` in `scripts/shared/config_loader.py`.
- `deploy/deploy.sh` — no update needed (Plan Phase 3 item; confirmed no file
  added/removed/moved).
- `plans/20260825-142225_plan.md`'s `dataclasses.replace()`-based diff-apply refactor of
  the other fields in `_apply_llm_prompt_params()` — tracked by its own implementation
  documents (see Implementation > Details cross-plan note).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Delete the `web_search_url` `_apply_str(...)` statement from `_apply_llm_prompt_params()` (REQ-001) | Pending | — | — | |
| 2 | Run `grep -rn "web_search_url" scripts/` and confirm 0 matches (AC-02) | Pending | — | — | |
| 3 | Run validation sequence (`uv run pytest tests/agent/services/test_config_reload*.py -v`, `ruff`, `mypy`) | Pending | — | — | |

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
- **Requirement ID**: REQ-001 (delete the dead `web_search_url` diff-apply line)
- **Source issue**: `issues/20260825_cfgreload_web_search_url_ghost_attribute_issue.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260825-142600_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260826-105110
- **Related target files**: `scripts/agent/services/config_reload.py`
