## Goal
Replace the hard-coded `_SERVERS` list in `tests/mcp_servers/test_require_auth_token.py` with an enumeration of the `[mcp_servers.*]` tables of `config/agent.toml`, so a newly configured server is covered automatically (`REQ-005`, AC-05).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Lands in the same change as, or after, the code rows it exercises (Plan rows 01-16 and 75); a test edit alone leaves the suite red until the code row lands.
- `config/agent.toml` currently defines ten `[mcp_servers.*]` tables (`shell`, `git`, `web_search`, `file_delete`, `file_write`, `file_read`, `github`, `cicd`, `rag_pipeline`, `mdq`), each with `auth_token = "${ENV:MCP_..._AUTH_TOKEN}"` and `cmd = ["/opt/llm/bin/mcp_<key>"]`; these match the current `_SERVERS` entries one-to-one.
- The server module is not named in the config; it is found by globbing `scripts/mcp_servers/*/*_server.py` (the glob the file already uses at line 99): module `mcp_servers.<dir>.<stem>`, key `<stem minus _server>` when it equals `<dir>`, otherwise `<dir>_<stem minus _server>` (`file/delete_server.py` -> `file_delete`). All ten current keys resolve this way.
- `accept_all_for_tests` is removed from `attach_auth_middleware` (row 11); this file does not use it, but it is the test the Plan names for the empty-token coverage.

## Design decisions
- Parse the TOML with `tomllib` directly (`config/agent.toml`, path from `_SCRIPTS.parent / "config" / "agent.toml"`): the test must see the committed file, not the deployed `/opt/llm` copy and not `ConfigLoader` (which resolves the deployed path).
- Fail loudly on an entry that cannot be mapped: a configured server with no matching module, or with an `auth_token` that is not a single `${ENV:NAME}` reference, makes a dedicated test fail rather than being skipped silently.

## Alternatives considered
Keeping `_SERVERS` and adding a consistency assertion against the config: rejected because the Issue asks to enumerate from the config instead of maintaining two lists.

## Implementation
### Target file
`tests/mcp_servers/test_require_auth_token.py`

### Procedure
- Replace `_SERVERS` (lines 20-31) and `_ALL_TOKEN_VARS` (line 32) with a helper `_configured_servers() -> list[tuple[str, str, str]]` (new) returning `(key, module, env_var)` built from `tomllib.loads(...)["mcp_servers"]`, the `${ENV:...}` regex, and the module map from the `_SERVER_SOURCE_GLOB` files; keep the module-level `_SERVERS = [(module, env) ...]` name as the derived list so the parametrized test at line 69 and `_import_in_fresh_interpreter` stay unchanged.
- Add `test_every_configured_server_resolves_to_a_module_and_token_variable` (new): asserts each table has an `${ENV:...}` token and a module, and that the number of derived servers equals the number of `[mcp_servers.*]` tables.
- Add the converse check `test_every_server_module_is_configured` (new): every `*_server.py` found by the glob maps to a configured key, so a server module without a config table is also noticed.
- Dummy non-empty tokens: `_import_in_fresh_interpreter` already sets every derived variable to `"test-token"` (line 49) except the one under test; with the derived `_ALL_TOKEN_VARS` it keeps doing so, so no production token is read and the tests never rely on `accept_all_for_tests`.

### Method
- Use the `tomllib` standard-library module (Python 3.13); open the file in binary mode as `tomllib.load` requires.

### Details
- Non-HTTP or `startup_mode != "subprocess"` entries: all ten current entries are HTTP subprocess servers; the derivation does not filter on transport. If a future entry has a different shape, the dedicated test above fails and the implementer decides whether to exclude it with an explicit, commented allow-list entry (not a silent skip).
- The resolved list is sorted by key so the parametrized ids are stable.

## Compatibility considerations
The parametrized test ids change from module names to the derived list's order; no external consumer references the ids.

## Security considerations
The test strengthens the authentication guarantee: every configured server is checked for empty-token refusal.

## Rollback considerations
N/A: revert the commit

## Validation plan
- `uv run pytest tests/mcp_servers/test_require_auth_token.py -v` (expect 10 parametrized empty-token cases plus the two new consistency tests).
- `uv run ruff check tests/mcp_servers/test_require_auth_token.py`
- `uv run mypy --no-namespace-packages tests/mcp_servers/test_require_auth_token.py` if it is within the mypy `files` scope

## Completion criteria
- `_SERVERS` is derived from `config/agent.toml`; no hard-coded server list remains.
- A server table or module without its counterpart fails a test.
- `rg -n accept_all_for_tests scripts tests` returns nothing after rows 11 and 28 land.

## Out of Scope
- Changing server code or the authentication ADR (`issues/20261109-113023_adrrev011_mcp-audit-auth-adr.md`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `_configured_servers` (new) and derive `_SERVERS`/`_ALL_TOKEN_VARS` | Done | 20261110-203000 | 20261110-203300 | Added `_CONFIG_TOML`, `_server_source_modules()` (dir/stem key rule), `_configured_servers()` (tomllib + `${ENV:NAME}` regex, raises ValueError on unmappable table), `_CONFIGURED_SERVERS` sorted by key; `_SERVERS`/`_ALL_TOKEN_VARS` derived. `_SERVER_SOURCE_GLOB` moved to the top (single definition, reused by the enforcement-point test). |
| 2 | Add the two consistency tests (new) | Done | 20261110-203300 | 20261110-203300 | `test_every_configured_server_resolves_to_a_module_and_token_variable` (count equality + per-table token/module assertions) and `test_every_server_module_is_configured` (converse glob check). |
| 3 | Run `uv run pytest tests/mcp_servers/test_require_auth_token.py -v` | Done | 20261110-203300 | 20261110-203300 | 28 passed (10 derived empty-token cases + 2 new consistency tests + existing cases). Derived `_SERVERS` verified identical (as a sorted set) to the previous hard-coded 10-entry list. |
| 4 | Run the validation sequence (`rules/toolchain.md`) | Done | 20261110-203300 | 20261110-203300 | ruff check + ruff format clean. mypy not run: this path is outside the mypy `files` scope (`scripts/ tests/eventbus tools`). |

### Verification Findings
| Item | Finding | Action taken |
|------|---------|--------------|
| VF-1 | Anchors confirmed: `_SERVERS` lines 20-31, `_ALL_TOKEN_VARS` line 32; the glob the file uses is at line 101 (doc says 99 — pre-reorg offset) | Applied as written |
| VF-2 | Config confirmed: `config/agent.toml` defines exactly ten `[mcp_servers.*]` tables, each `auth_token = "${ENV:MCP_..._AUTH_TOKEN}"`; ten `*_server.py` modules map 1:1 under the dir/stem key rule (`file/delete_server.py` -> `file_delete`) | Derived list equals the old list |
| VF-3 | `rg -n accept_all_for_tests scripts tests` returns nothing — row 11 has landed, so the Assumption's premise holds | No extra change needed |

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
- **Requirement ID**: `REQ-005` (empty-token test derived from `config/agent.toml`)
- **Source issue**: issues/20261109-112640_adrrev004_non-strict-bypass-removal.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261110-094140_adrrev004_non-strict-bypass-removal.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261110-154603
- **Related target files**: `tests/mcp_servers/test_require_auth_token.py`
