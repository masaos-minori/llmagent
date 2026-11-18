## Goal

Add load-time validation of `config/mcp_dedup.toml`'s `[retry_class]` section to
`load_dedup_config` in `scripts/shared/mcp_dedup.py`: reject unknown tool names,
values outside `{retryable, non_retryable}`, and keys contradicting `RETRYABLE_TOOLS`
membership. (`REQ-001` single source of truth, `REQ-002` unknown keys rejected)

## Scope
**Release unit**: retry-class-load-gate

## Assumptions

- The gate validates per key (name known, value allowed, membership consistent);
  full two-way set equality against the repository config is enforced by the test in
  `tests/shared/test_tool_constants.py`, not the loader (plan Assumptions: strict
  equality would force every synthetic fixture to replicate the 22-tool constant).
- The lookup-time default (`retry_class()` for unlisted tools -> `non_retryable`,
  `:175-179`) stays unchanged: unlisted known tools remain fail-safe.
- A malformed config now fails service startup — intended fail-closed policy (plan
  Risks); repository-config consistency is proven by the sibling test procedure.

## Design decisions

- Import `RETRYABLE_TOOLS` and `get_all_mcp_tool_names` from `shared.tool_constants`
  (same-layer import; `lint-imports` re-checked at plan time: 6 contracts kept).
- Reuse the existing error idiom: wrap a `ValueError` naming the offending key in
  `ConfigParseError(filename, ...)` (pattern already at `:129-155`).

## Alternatives considered

- **Validate set equality in the loader.** Rejected: breaks every synthetic test
  fixture that supplies a partial `[retry_class]` map (e.g. `test_partial_config_gets_defaults`).
- **Owner = toml, constant as mirror.** Rejected at plan time: the Agent path already
  depends only on `RETRYABLE_TOOLS` (config isolation).

## Implementation
### Target file
`scripts/shared/mcp_dedup.py`

### Procedure
1. Add `from shared.tool_constants import RETRYABLE_TOOLS, get_all_mcp_tool_names` to
   the module imports (`:25` area already imports from `shared.config_errors`).
2. In the `[retry_class]` loop (`:149-155`), after the existing string-type check,
   add three per-key checks raising `ConfigParseError(filename, ValueError(...))`
   naming the key:
   - `tool_name not in get_all_mcp_tool_names()` -> not a known MCP tool name;
   - `cls not in ("retryable", "non_retryable")` -> disallowed value;
   - `(tool_name in RETRYABLE_TOOLS) != (cls == "retryable")` -> contradicts the
     owner constant.

### Method
Keep the loop's existing structure; the new checks run before inserting into the
`retry_class` dict so a violating config never reaches `DedupConfig` or the cache
(`_DEDUP_CONFIG_CACHE` write at `:163` stays after validation).

### Details
Error text must name the key (e.g. `f"retry_class.{tool_name} is not a known MCP tool name"`)
so operators can locate the offending line; the section-shape check (`:127-131`) and
the dedup-field checks (`:133-147`) are unchanged.

### Companion test files
- `tests/shared/test_mcp_dedup.py`
  - Procedure: update `test_bad_section_types_raise_parse_error`'s `bad3` fixture (`:301`) to a valid tool name with a disallowed value shape; update `test_retry_class_lookup`'s fixture (`:316`) to valid, consistent names (e.g. `write_file = "retryable"`, `shell_run = "non_retryable"`) keeping the `some_new_tool -> non_retryable` default assertion; add three new `TestConfigValidation` tests — unknown tool name, value outside `{retryable, non_retryable}`, and a membership contradiction (e.g. `search_web = "retryable"`) — each expecting `ConfigParseError`.
  - Validation: `uv run pytest tests/shared/test_mcp_dedup.py -q` passes with the three new rejection tests green.

## Compatibility considerations

- `dispatch.py` and Agent dedup wiring use lookup-only paths (`retry_class()`),
  unchanged; `tests/mcp_servers/test_mcp_dispatch.py` builds `DedupConfig` directly
  and bypasses the loader (plan consumer scan: unaffected).
- Deployment: `scripts/` is rsynced by `deploy.sh`; repository config is copied
  verbatim, so shipped configs load (plan Risks mitigation).

## Security considerations

- Fail-closed on malformed classification config: a typo can no longer silently make
  a tool fall through to a wrong class (config integrity).

## Rollback considerations

- Reverting this file alone re-opens the silent-acceptance gap; revert together with
  the Phase 1 rows (release unit `retry-class-load-gate`).

## Validation plan

- `uv run pytest tests/shared/test_mcp_dedup.py -q` — existing + 3 new tests pass (AC-1).
- `uv run mypy scripts/shared/mcp_dedup.py`, `uv run bandit -q -r scripts/shared/tool_constants.py scripts/shared/mcp_dedup.py -c pyproject.toml`.
- `PYTHONPATH=scripts uv run lint-imports` — 6 contracts kept, 0 broken.
- Mutation spot-check: locally mutate `RETRYABLE_TOOLS`, confirm
  `tests/shared/test_tool_constants.py` fails, revert (proves the tests detect drift).

## Completion criteria

- A test-proven `ConfigParseError` for each of the three violation classes (AC-1);
  repository `config/mcp_dedup.toml` loads under the gate; lookup default unchanged.

## Out of Scope

- Loader-side full set-equality enforcement (test-enforced instead).
- `scripts/agent/tool_runner.py` (reference only; its comment defect is plan UNK-03).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the import and the three per-key validation checks | Completed | 2026-11-18 | — |  |
| 2 | Update `tests/shared/test_mcp_dedup.py` fixtures and add the 3 rejection tests | Completed | 2026-11-18 | 2026-11-18 | full suite + diff-cover run at release-unit end 2026-11-18 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 2026-11-18 |  |

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
- **Requirement ID**: `REQ-001` (owner/mirror enforcement), `REQ-002` (unknown keys rejected)
- **Source issue**: issues/20261117-123018_adrchk018_mcp-retry-classes.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261118-153543_adrchk018_mcp-retry-classes.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-162033
- **Related target files**: `scripts/shared/mcp_dedup.py`, `tests/shared/test_mcp_dedup.py`