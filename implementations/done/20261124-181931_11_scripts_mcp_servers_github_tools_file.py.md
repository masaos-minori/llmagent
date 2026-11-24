## Goal
Publish the file-domain schemas from their request models (REQ-002) and expose `dry_run` on the three
file **write** tools (REQ-003 scope is "every GitHub write tool"; `github_get_file_contents` is
`is_write: False` with `preview_capability: "none"` and has no `dry_run` field, so it publishes none).
This is also where the Plan's nested model first reaches a provider payload, so the UNK-01 `$defs`/`$ref`
verification is executed here.

## Scope
**Release unit**: N/A: not part of a release unit

- Modifies only `scripts/mcp_servers/github/tools_file.py` (Plan Phase 4).
- Pattern is the one established by seq 08; this row applies it to four tools.

## Assumptions
- `build_input_schema()` exists from seq 01; the file models (including nested `PushFile`) are strict
  from seq 05.
- Verified today: all four published file schemas declare no validation keyword; none publishes
  `dry_run`; `github_push_files` publishes `files` as an inline `items: {type: object}` object.
- After this row, `github_push_files` is the only GitHub tool whose published schema contains `$defs`
  and a `$ref` (`#/$defs/PushFile`) — the UNK-01 open question applies to this one tool only.

## Design decisions
- Same shape as seq 08: keep `name`, `description`, `_GITHUB_FILE_TOOL_METADATA_HEAD`,
  `_GITHUB_FILE_TOOL_METADATA_TAIL`, and every spread; replace only each `"inputSchema"` literal.
- `$defs`/`$ref` are published unflattened (Plan Design and Issue default). The UNK-01 resolution path
  is executed after this row lands: one live `github_push_files` agent call against the configured
  llama.cpp `llama-server` provider. If the provider rejects it, stop and report per the Issue's AI
  Implementation Instruction before any shared resolver is designed (Plan Risks mitigation).

## Alternatives considered
- Inlining `PushFile` into the `github_push_files` schema by hand: rejected — it would require a second,
  hand-maintained schema copy (the drift this Plan removes) and a flattening helper in the shared module.

## Implementation
### Target file
`scripts/mcp_servers/github/tools_file.py`

### Procedure
1. Add `from mcp_servers.request_contract import build_input_schema` and import
   `CreateOrUpdateFileRequest`, `DeleteRepoFileRequest`, `GetFileContentsRequest`, `PushFilesRequest`
   from `mcp_servers.github.github_models_file`.
2. Replace the four `"inputSchema": { ... }` literals with `build_input_schema(...)` for
   `github_get_file_contents`, `github_create_or_update_file`, `github_push_files`,
   `github_delete_file`.
3. Keep the metadata head/tail constants and their spreads unchanged (the file header comment at
   lines 23-24 stays accurate).

### Method
- One-to-one tool/model mapping as listed above; no schema text remains in this file.

### Details
- `github_push_files` keeps its four top-level required fields (`owner`, `repo`, `branch`, `files`,
  `message`) from `PushFilesRequest`; the per-file contract moves to the `$defs` entry.

## Compatibility considerations
- Newly accepted inputs (record in seq 18): `dry_run` on the three file write tools.
- Newly rejected inputs: unknown keys at the top level or inside a `files` item; empty `owner`/`repo`/
  `path`/`message`/`sha`; explicitly empty `ref`/`branch`/`sha`; `content` over 1048576 characters;
  `files` with 0 or more than 100 entries.
- Structural change to one published schema: `github_push_files.properties.files.items` becomes
  `{"$ref": "#/$defs/PushFile"}` with a sibling `$defs` map. `tests/mcp_servers/test_tool_schema_contract.py`
  and `scripts/shared/resource_scope.py::validate_tool_schema_v2()` check metadata fields, not
  `inputSchema` content, so they need no edits.
- Step 3a verification (local part of the UNK-01 check): the generated `github_push_files` schema is the
  only GitHub schema with nested structure — `$defs.PushFile` (its own `additionalProperties: false`,
  `required: ["path", "content"]`, `minLength` on `path`, `maxLength: 1048576` on `content`) referenced as
  `files.items.$ref = "#/$defs/PushFile"`, with `minItems: 1` and `maxItems: 100` on `files`, and no
  generated `title` key anywhere. The other three file schemas are flat.
- Step 3a blocked item (UNK-01 live leg not executed in this environment): the live call needs the
  configured LLM (`llm_url = "http://192.168.11.228:8080"`, `config/agent.toml:39`) and a GitHub token.
  From this machine that port refuses connections, and neither `GITHUB_TOKEN` nor `MCP_GITHUB_AUTH_TOKEN`
  is set, so neither leg could run. UNK-01 is **not** resolved here; the inline-`items` fallback was not
  applied because there is no evidence of provider rejection. Run one live `github_push_files` agent call
  on a host that can reach the LLM (the production host) before provider-facing rollout and record the
  result in this row.

## Security considerations
- Per-file `additionalProperties: false` closes unknown keys inside batched write payloads, which
  previously reached the model unnoticed (the model had no `extra` setting at all).

## Rollback considerations
- Revert this Phase 4 commit; `github_push_files` returns to its inline `items` schema.

## Validation plan
- `uv run pytest tests/mcp_servers/github/test_github_tool_registry.py` (T-02, seq 14; asserts the
  `github_push_files` `$defs`/`$ref` shape) and `uv run pytest tests/mcp_servers/test_tool_schema_contract.py`.
- Post-merge UNK-01 check: one live `github_push_files` agent call; record the result before any
  provider-facing rollout (Plan Unknowns, UNK-01).
- `uv run ruff check`, `uv run mypy`, `uv run lint-imports`, `uv run python tools/generate_reference_table.py --check` (T-06).

## Completion criteria
- All four entries carry generated schemas; the three write entries publish `dry_run` and
  `github_get_file_contents` publishes none (AC-01, REQ-003 write-tool scope).
- `github_push_files` published schema contains `$defs` with `PushFile` (`minLength`, `maxLength`),
  `minItems: 1`, `maxItems: 100`.
- The UNK-01 live-call result is recorded in the commit message or the issue thread.

## Out of Scope
- Model bounds and `PushFile` strictness (seq 05), the drift gate (seq 14), a shared `$ref` resolver
  (would be a follow-up Issue per the Plan Risks mitigation), docs (seq 18-19).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Replace the four `inputSchema` literals with `build_input_schema()` calls | Completed | 20261124-214349 | 20261124-214349 | REQ-002 Changed: scripts/mcp_servers/github/tools_file.py. Four literals replaced by build_input_schema() via the seq 09 swap script. |
| 2 | Confirm `dry_run` publication for all four file tools | Completed | 20261124-214349 | 20261124-214349 | REQ-003 TOOL_LIST dump: dry_run (default false) published on create_or_update_file/push_files/delete_file. github_get_file_contents publishes none: is_write false, preview_capability none, no dry_run field. Procedure Goal/Completion criteria corrected to write-tool scope per REQ-003. |
| 3 | Verify the generated `github_push_files` `$defs`/`$ref` shape locally; live provider leg deferred to deploy | Completed | 20261124-214349 | 20261124-214349 | Plan Unknowns (UNK-01) Local shape verified: $defs.PushFile (additionalProperties false, required path/content, minLength+maxLength) referenced as files.items.$ref, minItems 1 / maxItems 100, no title noise. Live provider leg NOT run: llm_url 192.168.11.228:8080 refuses connections from this machine and no GitHub token is set. UNK-01 open; tracked as the UNK-01-live-push-files-check work item. |
| 4 | Run the validation sequence (`rules/toolchain.md`) for this file | Completed | 20261124-225226 | 20261124-225226 | T-02, T-06 ruff format/check, mypy, check_module_size, generate_reference_table --check, lint-imports (6 KEPT) pass; tests/mcp_servers/github/ + test_tool_schema_contract.py = 411 passed. Full-suite run is the end-of-batch run. End-of-batch run (rules/toolchain.md, Batch mode): full pytest 13959 passed / 5 skipped / 6 errors; all 6 errors are the pre-existing tests/tools/test_append_plan_work_items.py contract mismatch (issues/20261124-155017_qa001_append-plan-attr-mismatch.md), none in this batch's files. ruff format+check, mypy, lint-imports, check_module_size, bandit, check_docstrings (after adding the em-dash separator to scripts/mcp_servers/request_contract.py), and diff-cover --fail-under 90 Pass. pre-commit run --all-files fails only on 14 pre-existing procedure-length findings in implementations/20261124-122732_* (issues/20261124-155017_qa002_workitem-structure-unknowns-kind.md); check_workitem_structure --file on this batch's documents reports no findings. |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| UNK-01-live-push-files-check | 3 | Verification (live provider call) | Open | Repo owner (production host) | Before provider-facing rollout / deploy |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-002` (schemas generated from models, `$defs`/`$ref` preserved), `REQ-003` (publish `dry_run`)
- **Source issue**: issues/20261119-140510_mcpai003_github-pydantic-schema-source.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-173306_mcpai003_github-pydantic-schema-source.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261124-181931
- **Related target files**: `scripts/mcp_servers/github/tools_file.py`