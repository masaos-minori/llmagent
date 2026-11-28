# Align MDQ request validation, store scope identity, and read consistency

## Goal
- Make the MDQ request contract one source, so the schema a client discovers and the validation the server performs cannot drift and Agent and direct calls accept and reject the same arguments; give the two MDQ write tools one stable store scope identity instead of a path-derived key; and make read consistency during refresh machine-readable in structured metadata instead of a warning string.

## Priority
Medium

## Scope
- **In-Scope**:
  - MDQ request models inherit the shared strict request base, and the advertised `inputSchema` is generated from the model by the shared schema generator.
  - Bounds, the `bm25` enum, and `minItems` move from the hand-written schema blocks to model field constraints so the generated schema carries the same advertised values.
  - Handlers validate the whole argument mapping through the model instead of extracting keys, and a validation failure maps to `MdqValidationError`; unknown and removed fields are errors.
  - The two MDQ write tools declare `resource_scope_kind: "mdq_store"` with no path-derived keys, and the resolver resolves a store-kind write to one stable store identity.
  - Read paths report the consistency state as structured metadata (`refresh_in_progress`, `index_generation`) for `search_docs`, `outline`, `get_chunk`, `grep_docs`, and `stats`; warning text stays display-only.
  - `get_chunk` returns structured metadata, and the audit detail reads the truncation state from metadata instead of from the output marker.
  - The `with_neighbors` decision, applied as the plan default (removed from the model, the generated schema, and the tool description).
  - Pins that record the current parity gap, store scope string, and warning-string behavior before the change, and the tests that replace them.
  - Documentation alignment for validation parity, store identity, and read consistency.
- **Out-of-Scope**:
  - The shared strict request base and schema generator themselves: consumed, not redefined.
  - The shared execution-mode and result-metadata contract: already implemented, consumed unchanged.
  - `scripts/agent/tool_scheduler.py` and `scripts/shared/runtime_tool_registry.py`: they consume the resolver predicate unchanged and are not modified.
  - The closed `ResourceKeyKind` value set and the schema-2.1 required-field contract: unchanged; a new value or a new required field needs the contract owner.
  - The per-file DTO statuses and reason codes owned by the mdqmcp003 plan, and the persisted truncation fields owned by the mdqmcp004 plan: consumed, never extended.
  - Atomic generation switching and per-chunk generation attribution; transaction atomicity (mdqmcp005).
  - Other servers' scope declarations and schemas.
  - Any ADR decision change (an ADR change needs a maintainer approval record; this Plan does not write or simulate one).
- **Dependencies**: depends on the mdqmcp001, mdqmcp003, mdqmcp004, mdqmcp005, mdqmcp006, and mdqmcp007 plans for the contracts this Plan consumes, and on the mcpai002, mcpai003, and mcpai013 plans for the shared strict-parsing posture, the schema generator, and the scope-key convention; blocks the mdqmcp010 issue.
  - **Depends on**: `plans/20261127-160114_mdqmcp001_mdq-server-boundary.md` | all | the availability and error contract the read-consistency fields are reported through
  - **Depends on**: `plans/20261127-163030_mdqmcp003_mdq-file-processing-outcomes.md` | all | the closed per-file status and reason vocabulary that the read metadata must not extend
  - **Depends on**: `plans/20261127-170412_mdqmcp004_mdq-file-identity-stale.md` | all | the persisted truncation flag and character-count columns that `get_chunk` metadata reports
  - **Depends on**: `plans/20261127-171503_mdqmcp005_mdq-transaction-atomicity.md` | all | the transaction boundary that defines when a refresh is considered complete, which the generation state reports
  - **Depends on**: `plans/20261127-172305_mdqmcp006_mdq-fts5-schema-identity.md` | all | the readiness vocabulary that the health-facing consistency state maps onto
  - **Depends on**: `plans/20261127-173835_mdqmcp007_mdq-approval-dry-run.md` | all | the structured result metadata that the audit detail reads instead of output text
  - **Depends on**: `plans/done/20261124-095007_mcpai002_github-read-security-boundary.md` | all | the strict validation posture this Plan aligns the MDQ path with
  - **Depends on**: `plans/done/20261124-173306_mcpai003_github-pydantic-schema-source.md` | all | the strict request base and schema generator this Plan consumes rather than redefines
  - **Depends on**: `plans/done/20261126-073010_mcpai013_github-resource-scope-refine.md` | all | the `<kind>:<identity>` scope-key convention this Plan reuses

## Background
Source issue: `issues/20261119-142130_mdqmcp008_mdq-schema-scope-consistency.md` (consolidated MDQ MCP backlog, Issue 8).

The MDQ server publishes a hand-written `inputSchema` per tool and builds its request models by extracting individual keys from the argument mapping. The Agent validates LLM arguments against the published schema and rejects extra fields, while the direct MCP path accepts them and drops them, so the two paths enforce different contracts. The two MDQ write tools declare the `mdq_store` scope kind with a path-derived key, so the resolved scope string depends on the call's path list. Read consistency during refresh is expressed only as a warning string appended to output text, and `get_chunk` truncation is reported only as a text marker that the audit layer parses.

Adversarial verification against current source (evidence revision in Traceability):
- Confirmed: `mdq_tools.py` declares `resource_scope_kind: "mdq_store"` with `resource_scope_keys: {"paths": "path"}` for `index_paths` (lines 178-179) and `refresh_index` (lines 211-212); the issue's citation `148,174` is off by about 30 lines, the claim holds. The issue's `Needs confirmation` scope-key claim is now confirmed: the key value is the stringified `paths` array (`scripts/shared/resource_scope.py:129`), so the resolved scope string is order- and duplicate-sensitive.
- Corrected: `mdq_store` is already a known kind (`scripts/shared/resource_scope.py:52`), so the defect is not an unknown kind. It is `str(value)` applied to a list value, plus the no-declared-key write branch that returns `_FALLBACK_WRITE_SCOPE` (lines 132-134).
- Confirmed: the direct-call unknown-field discard. MDQ request models are plain `BaseModel` (`scripts/mcp_servers/mdq/mdq_models.py:199`) and the handlers build them from `args[...]` or `args.get(...)` (`scripts/mcp_servers/mdq/mdq_server.py:231-235`), so an argument the model does not declare is dropped; `tests/mcp_servers/mdq/test_mdq_get_chunk_behavior.py:81` pins this as intended behavior. `scripts/agent/tool_arg_validator.py::validate_tool_arguments()` (lines 69-73) checks required fields, rejects extra fields unless `allow_extra_fields` is set, and type-checks against the schema, and `RuntimeTool.allow_extra_fields` defaults to `False` (`scripts/shared/runtime_tool.py:102`) with no MDQ tool overriding it, so the Agent path rejects an extra field while the direct path drops it — the two paths enforce different contracts.
- Corrected: the schema and the models do not disagree on fields. A field-by-field comparison of all 7 MDQ tools shows the property names and required sets match exactly; only the representation differs (optional fields generate `anyOf` against hand-written `type`). The defect is enforcement, not field drift.
- Confirmed: read consistency during refresh is a warning string appended to output text (`scripts/mcp_servers/mdq/mdq_service.py:145-146`, gated by `self._is_indexing`), pinned by `tests/mcp_servers/mdq/test_mdq_index_serialization.py:199`; `outline()` carries `stale_warning` (`scripts/mcp_servers/mdq/mdq_models.py:292`, `scripts/mcp_servers/mdq/mdq_service.py:219,234-235`). No read metadata shape carries a consistency field.
- Confirmed: `get_chunk` returns `str` only (`scripts/mcp_servers/mdq/mdq_service.py:149`), and the audit detail for it is built by testing `"[Truncated" in r.output` (`scripts/mcp_servers/mdq/mdq_server.py:378`).
- Confirmed: `with_neighbors` is declared in the model (`scripts/mcp_servers/mdq/mdq_models.py:203`), the schema (`mdq_tools.py:89`), and the handler (`scripts/mcp_servers/mdq/mdq_server.py:233`), and is never used by `MdqService.get_chunk()`.
- Corrected: no index-generation concept exists. `index_state` is a key/value table keyed `mtime:<path>` (`scripts/mcp_servers/mdq/indexer.py:516`; `index_delete.py` deletes `mtime:{path}%`), and `IndexMetadata` is an empty placeholder model. Generation metadata has to be defined, not read from existing state.
- Corrected: MDQ is a single store (`config/mdq_mcp_server.toml:16`); at the evidence revision `scripts/mcp_servers/mdq/health_check.py:145` applied `DEFAULT_DB_PATH` as a fallback, and at current HEAD the health probe connects to the startup-configured path with no default (`scripts/mcp_servers/mdq/startup_config.py:92`, `scripts/mcp_servers/mdq/health_check.py:190`). The issue's "distinguish multiple stores if supported" is not applicable, so one store identity per server is sufficient.
- Corrected: the shared strict request base, the schema generator, and the execution-mode and result-metadata contract already exist (`scripts/mcp_servers/request_contract.py`, `scripts/mcp_servers/execution_context.py`, `scripts/mcp_servers/dispatch.py`) and are consumed unchanged, not redefined.
- Confirmed (Step 3a re-verification, 2026-11-28): parity on wrong-type inputs needs strict typing, not only the strict base. `StrictRequestModel` sets `extra="forbid"` only (`scripts/mcp_servers/request_contract.py:34-41`), and pydantic coerces a string-encoded number to `int` by default — `SearchDocsRequest.model_validate({"limit": "5"})` yields `5` at current HEAD — while `validate_tool_arguments()`'s jsonschema type check rejects the same argument (`scripts/agent/tool_arg_validator.py:62-66`). So `AC-1` for wrong-type inputs requires strict typing on each MDQ request model; the shared base is out of scope, so strictness is declared per MDQ model.

## Problem
Agent and direct calls accept different inputs for the same MDQ tool; scheduler conflicts for the two MDQ write tools do not match the single database they write; and a read that runs during a refresh has no machine-readable consistency state, only formatter wording that a wording change can silently alter.

## Reason for Change
Contract consistency after the core integrity work. The integrity defects themselves carry no data-loss risk, but the drift between the advertised contract and the enforced one, and between the declared scope and the actual store, makes the scheduler and the audit record unreliable to reason about.

## Implementation Intent
One source for the request contract: the model, from which the published schema is generated. One stable identity for the store a write occupies, independent of the call's argument order or duplication. One machine-readable consistency state on every MDQ read result, with display wording kept separate from it.

## Requirements
- `REQ-001`: MDQ request models inherit the shared strict request base, and each tool's `inputSchema` is generated from its request model. Bounds, the `bm25` enum, and `minItems` are declared as model field constraints so the generated schema publishes the same values the current hand-written blocks publish. Handlers validate the whole argument mapping through the model, and a validation failure is reported as `MdqValidationError`; unknown and removed fields are errors.
- `REQ-002`: The two MDQ write tools keep `resource_scope_kind: "mdq_store"` and declare no path-derived scope keys. `resolve_resource_scopes()` resolves a store-kind write to one stable store identity, `<kind>:<server_key>`, instead of the fail-closed global fallback; path order and duplication cannot affect the scope. Reads remain unscoped (plan default).
- `REQ-003`: Every MDQ read result declares its consistency state in structured metadata: `refresh_in_progress` and `index_generation` for `search_docs`, `outline`, `get_chunk`, `grep_docs`, and `stats`. Formatter wording cannot change the state; the existing warning text remains display-only.
- `REQ-004`: `get_chunk` returns text plus structured metadata that carries the truncation state using the fields defined by the mdqmcp004 plan plus the read-time character cap that was applied, and the audit detail for `get_chunk` reads the truncation state from that metadata instead of from the output marker. The shared result-metadata fields are consumed unchanged.
- `REQ-005`: The `with_neighbors` field is removed from the request model, the generated schema, and the tool description, because `MdqService.get_chunk()` does not implement it (plan default; the alternative is recorded as an Unknown).
- `REQ-006`: Documentation records request-validation parity, the store scope identity, and the read consistency state in the documents named by `docs/00_index.md`'s task mapping.

## Implementation Target Files
**Freeze status**: Frozen — `issue-to-plan` Step 8's Implementation Target Files Validation passes (backtick and structure checks, `tools/audit_plan_target_paths.py`, `tools/check_plan_target_overlaps.py`).
Amended 2026-11-28 (fallout): added tests/mcp_servers/mdq/test_mdq_stale_detection.py — Assert the outline consistency state through metadata instead of the warning text in the returned value, because REQ-003 changes the outline return shape to text plus metadata
Amended 2026-11-28 (fallout): added tests/mcp_servers/mdq/test_mdq_outline_stale_helper.py — Assert the outline consistency state through metadata instead of the warning text in the returned value, because REQ-003 changes the outline return shape to text plus metadata

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/mcp_servers/mdq/mdq_models.py` | Modify | Request models inherit the strict base; bounds, enum, and `minItems` become field constraints; the read metadata shapes gain `refresh_in_progress` and `index_generation`; a `get_chunk` metadata shape is added; `with_neighbors` is removed | REQ-001, REQ-003, REQ-004, REQ-005, AC-1, AC-4, AC-5 | `GetChunkRequest` is a plain `BaseModel` (line 199) with `with_neighbors` at line 203; `SearchDocsMetadata` (lines 482-495) has no consistency field; no `get_chunk` metadata shape exists; request models carry no bounds (checked in Step 3) | `tests/mcp_servers/mdq/test_mdq_tool_schema.py`, `tests/mcp_servers/mdq/test_mdq_get_chunk_behavior.py` | Verified |
| `scripts/mcp_servers/mdq/mdq_tools.py` | Modify | `inputSchema` is generated from the request model; the two write tools declare `mdq_store` with no path-derived keys; the `get_chunk` description no longer advertises `with_neighbors` | REQ-001, REQ-002, REQ-005, AC-1, AC-3 | `resource_scope_keys: {"paths": "path"}` at lines 179 and 212; hand-written `inputSchema` blocks at lines 17, 85, 119, 155, 184, 217, 235; the `with_neighbors` property at line 91 (checked in Step 3) | `tests/mcp_servers/mdq/test_mdq_tool_layer_consistency.py` | Verified |
| `scripts/mcp_servers/mdq/mdq_server.py` | Modify | Handlers validate the whole argument mapping through the model and map a validation failure to `MdqValidationError`; `get_chunk` returns text plus metadata; the audit detail reads the truncation state from metadata | REQ-001, REQ-004, AC-1, AC-4 | `_handle_get_chunk()` builds the model from `args.get("with_neighbors", False)` (line 233) and returns `str` (line 236); `_build_call_tool_audit_detail()` tests `"[Truncated" in r.output` for `get_chunk` (line 378); `MdqValidationError` already has an exception handler (line 124) (checked in Step 3) | `tests/mcp_servers/mdq/test_mdq_exception_handlers.py`, `tests/mcp_servers/mdq/test_mdq_error_taxonomy.py` | Verified |
| `scripts/mcp_servers/mdq/mdq_service.py` | Modify | Read paths report the consistency state as structured metadata; the warning text stays display-only; `get_chunk` returns text plus metadata | REQ-003, REQ-004, AC-4, AC-5 | `search_docs()` appends the warning string when `self._is_indexing` (lines 145-146); `outline()` appends `stale_warning` (lines 219, 233-234); `get_chunk()` returns `str` only (line 149); `stats()` built `index_metadata` from raw `index_state` rows at the evidence revision, and at current HEAD it reads no `index_state` and its docstring (line 355) states that the raw dict is not part of the response (checked in Step 3) | `tests/mcp_servers/mdq/test_mdq_index_serialization.py`, `tests/mcp_servers/mdq/test_mdq_service.py` | Verified |
| `scripts/shared/resource_scope.py` | Modify | A store-kind write with no declared keys resolves to the store identity `<kind>:<server_key>` instead of the fail-closed global fallback; store kinds that declare keys keep the current behavior | REQ-002, AC-3 | `mdq_store` is already in `_KNOWN_SCOPE_KINDS` (line 52) and is not in `_FILESYSTEM_LIKE_KINDS` (line 59), so a list value reaches `str(value)` (line 129) and the scope string is order- and duplicate-sensitive; the no-key write branch returns `_FALLBACK_WRITE_SCOPE` (lines 132-134) (checked in Step 3) | `tests/shared/test_resource_scope.py` | Verified |
| `tests/mcp_servers/mdq/test_mdq_tool_schema.py` | Modify | Assert the generated schema: the same bounds, enum, and `minItems` values now come from model constraints, and the schema is the model's schema rather than a hand-written block | REQ-001, AC-1 | The file asserts bounds and enums read from `TOOL_LIST` blocks (lines 34-104) and cross-checks five maxima against `config/mdq_mcp_server.toml` (lines 100-121) (checked in Step 3) | itself | Verified |
| `tests/mcp_servers/mdq/test_mdq_tool_layer_consistency.py` | Modify | Add guardrails that each entry's `inputSchema` equals the generated schema of its request model and that the two write tools resolve to the same store scope | REQ-001, REQ-002, AC-1, AC-3 | The file pins name, registry, and write-flag agreement only (lines 16-44); nothing compares the schema with the model or the resolved scope (checked in Step 3) | itself | Verified |
| `tests/mcp_servers/mdq/test_mdq_get_chunk_behavior.py` | Modify | Flip the characterization test that pins silent ignoring of extra fields, and assert the structured metadata instead of the text marker | REQ-001, REQ-004, AC-1, AC-4 | `test_use_summary_field_silently_ignored` pins "extra kwargs are silently ignored (not rejected)" (line 81); the truncation assertion reads the output marker (line 72) (checked in Step 3) | itself | Verified |
| `tests/mcp_servers/mdq/test_mdq_service.py` | Modify | Remove the `with_neighbors` assertion and add the read-consistency metadata assertions for the service read paths | REQ-003, REQ-005, AC-4, AC-5 | `assert req.with_neighbors is False` (line 260) (checked in Step 3) | itself | Verified |
| `tests/mcp_servers/mdq/test_mdq_index_serialization.py` | Modify | Re-express the pinned warning-string assertion as an assertion on the machine-readable consistency state, keeping the display wording test separate | REQ-003, AC-5 | Line 197 asserts `"[WARNING: Index is being updated" in text` as the only consistency signal (checked in Step 3) | itself | Verified |
| `tests/shared/test_resource_scope.py` | Modify | Add the store-kind identity case for a write tool that declares no keys; keep the existing store-kind case that declares keys | REQ-002, AC-3 | `test_mdq_store_resolves_fixed_scope` asserts `("mdq_store:default",)` from a declared key (lines 164-171); the no-key write case asserts the global fallback (lines 186-199) (checked in Step 3) | itself | Verified |
| `tests/mcp_servers/mdq/test_mdq_validation_parity.py` | Create | New file: Agent-side schema validation and direct model validation accept and reject the same arguments for unknown, empty, wrong-type, and boundary inputs | REQ-001, AC-1 | Does not exist; `tests/mcp_servers/mdq/` holds 36 entries and none compares the two validation paths (checked in Step 3) | itself | Verified |
| `tests/mcp_servers/mdq/test_mdq_read_consistency_metadata.py` | Create | New file: batch-refresh read metadata for `search_docs`, `outline`, `get_chunk`, `grep_docs`, and `stats` reports the consistency state without depending on formatter wording | REQ-003, REQ-004, AC-4, AC-5 | Does not exist; the only refresh-time read test asserts the warning string (checked in Step 3) | itself | Verified |
| `docs/22_mcp/mcp_04_04_mdq.md` | Modify | State the MDQ input contract as one source (generated schema, strict models, validation error), the read consistency state, and the `get_chunk` metadata | REQ-001, REQ-003, REQ-004, REQ-006, AC-1, AC-4, AC-5 | Line 66 describes the stale check as a reporting guard that returns `stale_warning`; no input-contract or read-consistency statement exists for mdq (checked in Step 3) | `uv run python tools/check_docs_content_policy.py` | Verified |
| `docs/22_mcp/mcp_03_01_dispatch-and-routing.md` | Modify | Record the store-kind scope identity rule: a store-kind write with no declared keys resolves to the store identity rather than the synthetic global write scope | REQ-002, REQ-006, AC-3 | Line 122 states that a write tool with no resolved scope is treated as the synthetic `"global:write"` scope, and line 171 repeats it in the conflict table (checked in Step 3) | `uv run python tools/check_docs_content_policy.py` | Verified |
| `tests/mcp_servers/mdq/test_mdq_stale_detection.py` | Modify | Assert the outline consistency state through metadata instead of the warning text in the returned value, because REQ-003 changes the outline return shape to text plus metadata | REQ-003 / N/A: none cites REQ-003 | Lines 89 and 118 apply `in result` to the value outline() returns (line 91 asserts the absence of "modified since last indexing", line 120 its presence); after the REQ-003 return-shape change that value is a text-plus-metadata pair, so the assertion must read the metadata | itself | Verified |
| `tests/mcp_servers/mdq/test_mdq_outline_stale_helper.py` | Modify | Assert the outline consistency state through metadata instead of the warning text in the returned value, because REQ-003 changes the outline return shape to text plus metadata | REQ-003 / N/A: none cites REQ-003 | Lines 61-63 apply `in result` to the value outline() returns (asserting the absence of "modified since last indexing" and the presence of "Title"); after the REQ-003 return-shape change that value is a text-plus-metadata pair, so the assertion must read the returned text element and the metadata separately | itself | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/mcp_servers/request_contract.py` | The strict request base and the schema generator this Plan consumes; it must not be redefined | REQ-001 |
| `scripts/shared/tool_metadata.py` | The closed `ResourceKeyKind` set and `TOOL_FIELD_SET_VERSION` stay unchanged; the plan default must not add a value | REQ-002 |
| `scripts/shared/runtime_tool.py` | `RuntimeTool.server_key` is the store identity source the resolver reads | REQ-002 |
| `scripts/shared/runtime_tool_registry.py` | Builds the per-call `ToolSpec` through `resolve_resource_scopes()`; consumes the change unchanged | REQ-002 |
| `scripts/agent/tool_scheduler.py` | Consumes `_scopes_conflict()` and the read/read non-conflict rule unchanged; reads stay out of the conflict graph | REQ-002 |
| `scripts/agent/tool_arg_validator.py` | The Agent-side contract that defines the parity the Plan must reach (extra fields rejected, type checks against the schema) | REQ-001, AC-1 |
| `tests/shared/test_tool_metadata.py` | Pins the closed value set (line 53); must not change | REQ-002 |
| `config/mdq_mcp_server.toml` | Source of the five bounds the generated schema must still publish | REQ-001 |
| `scripts/mcp_servers/rag_pipeline/rag_pipeline_tools.py` | The other store-kind write (`rag_store`, no declared keys, line 131) whose resolved scope string changes under the rule; not a modification target | REQ-002, Risk |
| `docs/22_mcp/mcp_03_02_tool-registry.md` | The schema-2.1 required-field contract that this Plan does not change | REQ-001, REQ-002 |

## Acceptance Criteria
- `AC-1` (REQ-001): Agent-side argument validation and direct model validation accept and reject the same arguments for the MDQ tools, including unknown and removed fields, which are errors on both paths.
- `AC-2` (REQ-001): The published `inputSchema` is the request model's schema; the bounds, enum, and `minItems` values asserted by the existing schema tests are unchanged.
- `AC-3` (REQ-002): `index_paths` and `refresh_index` resolve to the same store scope string for any argument order or duplication, and the conflict is observable from the discovery entry through the `ToolSpec` the scheduler receives.
- `AC-4` (REQ-003, REQ-004): Every read result during a refresh carries `refresh_in_progress` and `index_generation`; `get_chunk` reports its truncation state in metadata, and the audit detail is built from that metadata.
- `AC-5` (REQ-003): A change to the display wording cannot change the reported consistency state or truncation state; the tests assert the metadata, not the string.
- `AC-6` (REQ-006): The documents named by the task mapping state the validation contract, the store identity rule, and the read consistency state, and pass the docs content-policy gate.

## Tests
- `REQ-001`: parity tests for unknown, empty, wrong-type, and boundary inputs comparing `validate_tool_arguments()` with model validation; the flipped silent-ignore characterization test.
- `REQ-002`: discovery-to-`ToolSpec` scope integration test; same-store tests for `index_paths` and `refresh_index`; a store-kind case that declares a key keeps the current behavior; the RAG store-kind case is asserted as the documented consequence of the rule.
- `REQ-003`: batch-refresh tests for `search_docs`, `outline`, `get_chunk`, `grep_docs`, and `stats` asserting the metadata fields while a refresh is in progress.
- `REQ-004`: `get_chunk` metadata assertions for the truncated and non-truncated cases, and an audit-detail test that builds the detail from metadata.
- `REQ-005`: removal test asserting the field is absent from the model, the generated schema, and the description.
- Full sequence: `ruff`, `mypy`, the full test suite, and the diff-scoped coverage gate at the `rules/toolchain.md` threshold.

## Documentation Impact
Yes. `REQ-001`, `REQ-003`, `REQ-004`, and `REQ-006` drive it. Per `docs/00_index.md`'s "Document References by Task" table, the MCP server spec mapping names the MCP document guide and system overview, and the mdq per-server section is the target for the MDQ input contract and read consistency; the dispatch-and-routing document is the target for the store-kind scope identity rule. Both are rows in `Implementation Target Files`.

## Assumptions
- MDQ is a single store: `db_path` comes from `config/mdq_mcp_server.toml` (line 16) and `scripts/mcp_servers/mdq/health_check.py` connects to the startup-configured path with no implicit default (`scripts/mcp_servers/mdq/startup_config.py` line 92, `health_check.py` line 190); no multi-store support was found, so one store identity per server is sufficient.
- The store identity is taken from `RuntimeTool.server_key`, because the Agent-side contract has no access to the server's configured database path; the alternative is recorded as an Unknown.
- Reads remain outside the conflict graph, as the dispatch-and-routing document states, so the plan default for "whether reads share the store scope" is that they do not.
- The plan default for read semantics during refresh is the current behavior: non-blocking reads against the index state as it stands, reported through machine-readable metadata. A blocking or snapshot decision is an owner decision recorded as an Unknown.
- MDQ declares the only list-valued scope key in the repository (`paths`); after the declaration change no tool resolves a list-valued scope key, so the order- and duplicate-sensitivity is removed by the declaration rather than by new normalization code.
- Target-file overlap with the open plans is a compatible ordering overlap, not a conflict: `scripts/mcp_servers/mdq/mdq_models.py` with mdqmcp001, 002, 003, 004, 007; `mdq_service.py` with 001, 003, 004, 007; `mdq_server.py` with 001, 007; `mdq_tools.py` with 001, 005, 007; `tests/mcp_servers/mdq/test_mdq_service.py` with 001, 003; `test_mdq_tool_layer_consistency.py` and `test_mdq_tool_schema.py` with 007; `test_mdq_index_serialization.py` with 005; `docs/22_mcp/mcp_04_04_mdq.md` with 001-007. `tools/check_plan_target_overlaps.py --plan` reports these as cross-plan overlaps to verify, not as conflicts; this Plan executes after them per the dependency bullets and consumes their vocabularies without extending them.
- `scripts/shared/resource_scope.py` is not a target of any other open plan (only of the archived mcpai013 plan), so the resolver change has no ordering conflict.
- Bus factor is 1 for the mdq module set (single author across all commits).

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Read semantics during refresh: old generation, snapshot, blocking, or mixed | No owner decision recorded | Plan default: keep the current non-blocking old-generation behavior and make it machine-readable; a blocking or snapshot decision would add a scheduler-facing change and must come from the owner before the procedure is generated | False |
| UNK-02 | Whether `with_neighbors` is wanted | No owner decision recorded | Plan default: remove it, since `MdqService.get_chunk()` never uses it; if the owner wants it, the requirement becomes an implementation instead of a removal and the Plan is amended | False |
| UNK-03 | Whether the store identity should be the configured database path instead of the server key | No contract field carries a server-owned identity; `validate_tool_schema_v2()` requires every `resource_scope_keys` entry to be an argument property, so a store identity cannot come from args without a client-controlled field | Ask the contract owner; the plan default uses `RuntimeTool.server_key` because it needs no contract change. A new contract field or a new `ResourceKeyKind` value needs the contract owner and is not invented here | False |
| UNK-04 | Whether the store-kind identity rule should apply to every store kind or only to MDQ | No owner decision recorded; the rule is defined by kind, so the RAG store-kind write (`rag_pipeline_tools.py:131`) also changes its resolved scope string from the global fallback to `rag_store:<server_key>` | Confirm with the scheduler owner. Both store-kind writes are `requires_serial: True`, so serialization is unchanged; only the conflict-graph name changes | False |
| UNK-05 | Whether `index_generation` must survive a server restart | No persisted generation record exists; `index_state` holds per-file `mtime:<path>` keys only (`scripts/mcp_servers/mdq/indexer.py:516`) | Plan default: the generation is a service-level value incremented at each completed refresh; persistence needs a reserved `index_state` key and the owner's decision about mixing it with the per-file namespace | False |
| UNK-06 | Whether the open dependency plans must complete before this Plan is implemented | The mdqmcp001, mdqmcp003, mdqmcp004, mdqmcp005, mdqmcp006, and mdqmcp007 plans are all open with `Pending` rows | Ordering recorded in the `Depends on` bullets; this Plan's rows are written against current source and consume their vocabularies, so implementation before them would rewrite the same lines twice | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/mcp_servers/mdq/mdq_models.py` | Modify | Medium: mdq request and read-metadata shapes, so the published schema and the schema tests change with it | 0 | High (75% single author) | not applicable (rsynced) |
| `scripts/mcp_servers/mdq/mdq_tools.py` | Modify | Medium: the discovery entries the agent reads for LLM visibility and registry metadata | 1 | High (88% single author) | not applicable (rsynced) |
| `scripts/mcp_servers/mdq/mdq_server.py` | Modify | Medium: the mdq handler validation path and the audit detail; mdq-mcp service restart | 6 | High (94% single author) | not applicable (rsynced) |
| `scripts/mcp_servers/mdq/mdq_service.py` | Modify | Medium: the mdq read path return shape (text plus metadata); mdq-mcp service restart | 1 | High (88% single author) | not applicable (rsynced) |
| `scripts/shared/resource_scope.py` | Modify | High: shared resolver used by every MCP server and the agent conflict graph; agent and every MCP server restart | 2 | High (100% single author) | not applicable (rsynced) |
| `tests/mcp_servers/mdq/test_mdq_tool_schema.py` | Modify | Low: test only | 0 | High (100% single author) | not applicable (rsynced) |
| `tests/mcp_servers/mdq/test_mdq_tool_layer_consistency.py` | Modify | Low: test only | 0 | High (100% single author) | not applicable (rsynced) |
| `tests/mcp_servers/mdq/test_mdq_get_chunk_behavior.py` | Modify | Low: test only | 0 | High (100% single author) | not applicable (rsynced) |
| `tests/mcp_servers/mdq/test_mdq_service.py` | Modify | Low: test only | 0 | High (100% single author) | not applicable (rsynced) |
| `tests/mcp_servers/mdq/test_mdq_index_serialization.py` | Modify | Low: test only | 0 | High (100% single author) | not applicable (rsynced) |
| `tests/shared/test_resource_scope.py` | Modify | Low: test only | 3 | High (100% single author) | not applicable (rsynced) |
| `tests/mcp_servers/mdq/test_mdq_validation_parity.py` | Create | Low: test only | N/A (new) | N/A (new) | not applicable (rsynced) |
| `tests/mcp_servers/mdq/test_mdq_read_consistency_metadata.py` | Create | Low: test only | N/A (new) | N/A (new) | not applicable (rsynced) |
| `docs/22_mcp/mcp_04_04_mdq.md` | Modify | Low: documentation only | 2 | High (100% single author) | not applicable (rsynced) |
| `docs/22_mcp/mcp_03_01_dispatch-and-routing.md` | Modify | Low: documentation only | 8 | High (100% single author) | not applicable (rsynced) |
| `tests/mcp_servers/mdq/test_mdq_stale_detection.py` | Modify | Not assessed (amendment 2026-11-28) | N/A | N/A | Not assessed (amendment 2026-11-28) |
| `tests/mcp_servers/mdq/test_mdq_outline_stale_helper.py` | Modify | Not assessed (amendment 2026-11-28) | N/A | N/A | Not assessed (amendment 2026-11-28) |

## Design
- Single source for the request contract. `scripts/mcp_servers/request_contract.py` already provides `StrictRequestModel` and `build_input_schema()`, and the GitHub tools use them (`scripts/mcp_servers/github/github_tools.py`, `github_models_file.py`); the documented contract in `docs/22_mcp/mcp_04_01_web-search-file-read-github.md:94` states that the discovered schema and the enforced validation are one source. MDQ is the exception: hand-written schema blocks plus plain `BaseModel` request models and per-key extraction in the handlers. The Plan moves MDQ to the shared contract rather than defining a new one. Bounds move to model constraints (`Field(ge=…, le=…)`, `min_length`, `Literal`, `list[str]`) so the generated schema keeps the values the existing tests assert; the config cross-check test continues to compare the generated maxima with `config/mdq_mcp_server.toml`.
- Strict typing is part of the parity requirement, not the strict base. `StrictRequestModel` carries `extra="forbid"` only, so a string-encoded number is coerced by the model and rejected by the Agent-side jsonschema type check; each MDQ request model declares `model_config = ConfigDict(extra="forbid", strict=True)` so both paths make the same decision, and the shared base stays unchanged.
- Store identity. The scope-key convention `f"{kind}:{normalized_value}"` is already defined by `resolve_resource_scopes()` (docstring lines 90-91) and reused here. Alternatives considered: (a) a new `ResourceKeyKind` value — rejected, the identity would still come from args and the closed set is pinned by `tests/shared/test_tool_metadata.py:53`; (b) a server-owned identity field in the schema-2.1 contract — rejected as the plan default, it changes `validate_tool_schema_v2()` and the `RuntimeTool` required-field contract and needs the contract owner (UNK-03); (c) plan default — keep `resource_scope_kind: "mdq_store"`, declare no keys, and resolve a store-kind write to `<kind>:<server_key>`. Path order and duplication cannot affect a single store identity, and store-level serialization for the two MDQ write tools already comes from `requires_serial: True` (`mdq_tools.py:177,210`).
- Reads stay unscoped (`resource_scope_kind: ""`, `mdq_tools.py:79,113,149,229,280`), because the conflict graph only groups overlapping scopes when at least one call is `is_write=True` (`docs/22_mcp/mcp_03_01_dispatch-and-routing.md:171`, and the mcpai013 plan recorded the same boundary). The consistency state is reported in metadata, not enforced through the conflict graph.
- Consumer scan candidates (`tools/scan_change_consumers.py --seed resolve_resource_scopes`): `scripts/shared/runtime_tool_registry.py`, `scripts/agent/tool_scheduler.py`, and `scripts/agent/services/mcp_tool_discovery_fetch.py` are reference rows (consume the predicate unchanged); `tests/shared/test_resource_scope.py` is a target row; `tests/shared/test_runtime_tool_registry.py`, `tests/shared/test_tool_routing_validation.py`, `tests/agent/test_tool_scheduler*.py`, `tests/agent/test_tool_runner.py`, and `tests/agent/test_tool_run_recorder.py` are not affected: they pin the global fallback for `filesystem` and `github_branch` kinds only (`test_resource_scope.py:186-199`, `test_runtime_tool_registry.py:102,143`, `test_tool_routing_validation.py:100,144`, `test_tool_scheduler_serialization.py:178`), never a store kind. `scripts/mcp_servers/rag_pipeline/rag_pipeline_tools.py` is a reference row whose resolved scope string changes as a consequence of the rule (UNK-04, Risk). ADR basis for the seed (`docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md:72`) names `resource_scope_kind` and `resource_scope_keys` as producer-declared fields on `RuntimeTool`; the plan default changes how a declared kind resolves, not the ownership of the declaration, so no ADR decision changes here.
- `GetChunkRequest` candidates: `scripts/mcp_servers/mdq/mdq_server.py:37,231`, `scripts/mcp_servers/mdq/mdq_service.py:31,149`, and 15 test files; the handler and service rows are targets, the remaining test files are not affected because they construct the model with declared fields only. `with_neighbors` candidates: `scripts/mcp_servers/mdq/mdq_models.py:203`, `scripts/mcp_servers/mdq/mdq_server.py:233`, `mdq_tools.py:89`, `tests/mcp_servers/mdq/test_mdq_service.py:260` — all target rows. `stale_warning` candidates: `scripts/mcp_servers/mdq/mdq_models.py:292`, `scripts/mcp_servers/mdq/mdq_service.py:219,234-235`, `docs/22_mcp/mcp_04_04_mdq.md:129` — target rows; the display wording is kept, the state moves to metadata.
- Predictable fallout check: module sizes are below the 24576 B gate (`mdq_models.py` 12071 B, `mdq_tools.py` 10884 B, `mdq_server.py` 20547 B, `mdq_service.py` 15897 B, `scripts/shared/resource_scope.py` 12573 B), so no split is required. Pinned counts: `tests/mcp_servers/mdq/test_mdq_routing.py:209` compares the tool count with `MDQ_TOOLS` and is unaffected because no tool is added or removed; `tests/shared/test_tool_metadata.py:53` pins the closed value set and must not change; `tests/mcp_servers/mdq/test_mdq_search_limits.py` and `test_audit_target.py` pin lengths that the plan does not touch. Tool inventory (`docs/22_mcp/mcp_01_tool_ownership_matrix.md:95`) lists 7 mdq tools and is unchanged.
- Validation quality baseline (Step 5): `radon cc -s` reports rank A for every Python target, including `scripts/shared/resource_scope.py::_scope_problems` at A(4); `vulture --min-confidence 80` reports no findings for the mdq package and `resource_scope.py`; `bandit -c pyproject.toml` reports no Medium or High finding for the target files. Diff-scoped coverage at HEAD has no diff to measure; the Plan must raise the changed-line coverage to the `rules/toolchain.md` threshold of 90 percent through the new parity and read-consistency tests.

## Implementation steps
1. **Phase 1: Characterization pins**
   - [ ] Pin the current parity gap: Agent-side `validate_tool_arguments()` rejects an extra field while the MDQ model drops it (REQ-001; `tests/mcp_servers/mdq/test_mdq_validation_parity.py`)
   - [ ] Pin the current store scope string for `index_paths` and `refresh_index` as the stringified path list, order- and duplicate-sensitive (REQ-002; `tests/shared/test_resource_scope.py`)
   - [ ] Pin the current consistency signal as the warning string and the `get_chunk` truncation marker (REQ-003, REQ-004; `tests/mcp_servers/mdq/test_mdq_index_serialization.py`, `tests/mcp_servers/mdq/test_mdq_get_chunk_behavior.py`)
2. **Phase 2: Single-source request contract**
   - [ ] MDQ request models inherit the shared strict base and carry the bounds, enum, and `minItems` as field constraints (REQ-001; `scripts/mcp_servers/mdq/mdq_models.py`)
   - [ ] `inputSchema` is generated from the request model, and the `get_chunk` description no longer advertises `with_neighbors` (REQ-001, REQ-005; `scripts/mcp_servers/mdq/mdq_tools.py`)
   - [ ] Handlers validate the whole argument mapping through the model and map a validation failure to `MdqValidationError` (REQ-001; `scripts/mcp_servers/mdq/mdq_server.py`)
   - [ ] Flip the silent-ignore characterization test and update the schema tests to read the generated schema (REQ-001, REQ-005; `tests/mcp_servers/mdq/test_mdq_get_chunk_behavior.py`, `tests/mcp_servers/mdq/test_mdq_tool_schema.py`, `tests/mcp_servers/mdq/test_mdq_service.py`, `tests/mcp_servers/mdq/test_mdq_error_taxonomy.py`)
3. **Phase 3: Store scope identity**
   - [ ] The two MDQ write tools declare `mdq_store` with no path-derived keys (REQ-002; `scripts/mcp_servers/mdq/mdq_tools.py`)
   - [ ] A store-kind write with no declared keys resolves to `<kind>:<server_key>`; store kinds that declare keys keep the current behavior (REQ-002; `scripts/shared/resource_scope.py`)
   - [ ] Add the store-identity cases and the discovery-to-`ToolSpec` integration assertion; record the RAG store-kind consequence (REQ-002; `tests/shared/test_resource_scope.py`, `tests/mcp_servers/mdq/test_mdq_tool_layer_consistency.py`)
4. **Phase 4: Read consistency and `get_chunk` metadata**
   - [ ] Add `refresh_in_progress` and `index_generation` to the read metadata shapes and the `get_chunk` metadata shape using the truncation fields defined by the mdqmcp004 plan (REQ-003, REQ-004; `scripts/mcp_servers/mdq/mdq_models.py`)
   - [ ] Read paths report the state in metadata and keep the warning text display-only; `get_chunk` returns text plus metadata (REQ-003, REQ-004; `scripts/mcp_servers/mdq/mdq_service.py`)
   - [ ] The audit detail for `get_chunk` reads the truncation state from metadata instead of the output marker (REQ-004; `scripts/mcp_servers/mdq/mdq_server.py`)
   - [ ] Batch-refresh read tests and the re-expressed warning-string test (REQ-003, REQ-004; `tests/mcp_servers/mdq/test_mdq_read_consistency_metadata.py`, `tests/mcp_servers/mdq/test_mdq_index_serialization.py`, `tests/mcp_servers/mdq/test_mdq_service.py`)
   - [ ] Modify (REQ-003; `tests/mcp_servers/mdq/test_mdq_stale_detection.py`) — amendment 2026-11-28
   - [ ] Modify (REQ-003; `tests/mcp_servers/mdq/test_mdq_outline_stale_helper.py`) — amendment 2026-11-28
5. **Phase 5: Documentation**
   - [ ] MDQ input contract, read consistency state, and `get_chunk` metadata in the mdq per-server section (REQ-006; `docs/22_mcp/mcp_04_04_mdq.md`)
   - [ ] Store-kind scope identity rule in the dispatch-and-routing document (REQ-006; `docs/22_mcp/mcp_03_01_dispatch-and-routing.md`)
6. **Phase 6: Deployment and verification**
   - [ ] Hand-off to `skills/deploy/SKILL.md`: the change is committed and pushed first, and deploying is the user's decision (approval gate); `scripts/` and `docs/` are synced and the mdq-mcp service and the agent are restarted (REQ-001, REQ-002, REQ-003; `scripts/mcp_servers/mdq/mdq_server.py`, `scripts/shared/resource_scope.py`)
   - [ ] Verify the deployed files are current and that a direct call with an unknown field, a store-scope conflict, and a read during refresh behave as documented (REQ-001, REQ-002, REQ-003; `tests/mcp_servers/mdq/test_mdq_validation_parity.py`, `tests/mcp_servers/mdq/test_mdq_read_consistency_metadata.py`)

### Release units
N/A: no release unit — every phase changes its own pins and passes validation alone.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/mcp_servers/mdq/mdq_models.py` | Unit: strict model, bounds, metadata shapes | `uv run pytest tests/mcp_servers/mdq/test_mdq_tool_schema.py tests/mcp_servers/mdq/test_mdq_get_chunk_behavior.py` | Unknown field rejected; generated schema publishes the same bounds, enum, and `minItems` |
| `scripts/mcp_servers/mdq/mdq_tools.py` | Guardrail: schema equals the generated model schema | `uv run pytest tests/mcp_servers/mdq/test_mdq_tool_layer_consistency.py` | No drift between the published schema and the model |
| `scripts/mcp_servers/mdq/mdq_server.py` | Integration: handler validation path and audit detail | `uv run pytest tests/mcp_servers/mdq/test_mdq_error_taxonomy.py tests/mcp_servers/mdq/test_mdq_exception_handlers.py` | Validation failure reported as `MdqValidationError`; truncation reported from metadata |
| `scripts/mcp_servers/mdq/mdq_service.py` | Integration: read during refresh | `uv run pytest tests/mcp_servers/mdq/test_mdq_read_consistency_metadata.py tests/mcp_servers/mdq/test_mdq_index_serialization.py` | `refresh_in_progress` and `index_generation` reported; display wording separate |
| `scripts/shared/resource_scope.py` | Unit: store-kind identity; integration: discovery to `ToolSpec` | `uv run pytest tests/shared/test_resource_scope.py tests/shared/test_runtime_tool_registry.py tests/agent/test_tool_scheduler_serialization.py` | Both MDQ write tools resolve to the same store identity for any path order |
| Agent-side parity | Integration: schema validation against model validation | `uv run pytest tests/mcp_servers/mdq/test_mdq_validation_parity.py` | Same accept and reject decisions on both paths |
| Docs rows | Content policy and reference-table drift | `uv run python tools/check_docs_content_policy.py`, `uv run python tools/generate_reference_table.py --check` | Pass |
| Changed lines | Diff-scoped coverage | `uv run pytest tests/ -n logical --cov=scripts --cov-report= -m "not integration and not production_paths_allowed and not repo_scan"`, then `uv run coverage xml` and `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90` | Changed-line coverage raised from the current baseline (no diff at HEAD) to at least 90 percent |
| Whole module | Lint, types, security | `uv run python tools/run_validation_gates.py` | Pass |

## Risks
- **Risk**: making the request models strict changes the error behavior for callers that pass fields the schema never advertised, and the existing characterization test pins the opposite behavior → **Mitigation**: the Agent path already rejects extra fields, so the change aligns the direct path with the documented contract; the flipped test is recorded as a deliberate characterization change in Phase 2.
- **Risk**: moving bounds from the hand-written schema to model constraints can silently drop an advertised bound, because `minimum`/`maximum` and `minItems` come from `Field` constraints rather than from the schema block → **Mitigation**: the existing schema tests continue to assert the same values against the generated schema, and the config cross-check test compares the generated maxima with `config/mdq_mcp_server.toml`.
- **Risk**: the store-kind identity rule changes the resolved scope string for the other store-kind write, narrowing its conflict graph from the global write scope to its own store → **Mitigation**: both store-kind writes declare `requires_serial: True`, so serialization is unchanged; the change is recorded in the dispatch-and-routing document and confirmed with the scheduler owner before merging (UNK-04).
- **Risk**: the plan default takes the store identity from `RuntimeTool.server_key`, which names the server rather than the configured database path → **Mitigation**: MDQ is a single store, so the server key identifies it; the alternative is recorded as an Unknown and no contract field is invented here (UNK-03).
- **Risk**: reporting the generation as a service-level value means it does not survive a restart, so a read after a restart reports a generation that is not the one the stored rows were written under → **Mitigation**: the plan reports the state as "generation unknown after restart" rather than inventing a persisted value; persistence is recorded as an Unknown (UNK-05).
- **Risk**: this Plan consumes vocabularies owned by open plans, and implementing before them would rewrite the same lines twice → **Mitigation**: ordering recorded in the `Depends on` bullets; the Plan consumes the closed vocabularies and does not extend them (UNK-06).
- **Risk**: `StrictRequestModel` does not enable strict typing, so a string-encoded number is accepted by the model and rejected by the Agent-side check, leaving `AC-1` unsatisfied for wrong-type inputs → **Mitigation**: declare `model_config = ConfigDict(extra="forbid", strict=True)` on each MDQ request model, asserted by `tests/mcp_servers/mdq/test_mdq_validation_parity.py`; the shared base is not modified.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: characterization pins for parity, store scope, and read consistency | In Progress | — | — | Pins the current behavior before any production change |
| 2 | Phase 2: single-source request contract | In Progress | — | — | Strict models, generated schema, handler validation path, `with_neighbors` removal |
| 3 | Phase 3: store scope identity | In Progress | — | — | Declaration change plus the store-kind identity rule in the resolver |
| 4 | Phase 4: read consistency and `get_chunk` metadata | In Progress | — | — | Machine-readable state in metadata; audit detail reads metadata |
| 5 | Phase 5: documentation | In Progress | — | — | mdq per-server section and dispatch-and-routing rule |
| 6 | Phase 6: deployment and verification | Pending | — | — | Hand-off to `skills/deploy/SKILL.md` after commit and push |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| `implementations/20261128-084218_01_scripts_mcp_servers_mdq_mdq_models.py.md` | 2, 4 | Procedure | Pending | — | — |
| `implementations/20261128-084218_02_scripts_mcp_servers_mdq_mdq_tools.py.md` | 2, 3 | Procedure | Pending | — | — |
| `implementations/20261128-084218_03_scripts_mcp_servers_mdq_mdq_server.py.md` | 2, 4 | Procedure | Pending | — | — |
| `implementations/20261128-084218_04_scripts_mcp_servers_mdq_mdq_service.py.md` | 4 | Procedure | Pending | — | — |
| `implementations/20261128-084218_05_scripts_shared_resource_scope.py.md` | 3 | Procedure | Pending | — | — |
| `implementations/20261128-084218_06_tests_mcp_servers_mdq_test_mdq_tool_schema.py.md` | 2 | Procedure | Pending | — | — |
| `implementations/20261128-084218_07_tests_mcp_servers_mdq_test_mdq_tool_layer_consistency.py.md` | 3 | Procedure | Pending | — | — |
| `implementations/20261128-084218_08_tests_mcp_servers_mdq_test_mdq_get_chunk_behavior.py.md` | 1, 2 | Procedure | Pending | — | — |
| `implementations/20261128-084218_09_tests_mcp_servers_mdq_test_mdq_service.py.md` | 2, 4 | Procedure | Pending | — | — |
| `implementations/20261128-084218_10_tests_mcp_servers_mdq_test_mdq_index_serialization.py.md` | 1, 4 | Procedure | Pending | — | — |
| `implementations/20261128-084218_11_tests_shared_test_resource_scope.py.md` | 1, 3 | Procedure | Pending | — | — |
| `implementations/20261128-084218_12_tests_mcp_servers_mdq_test_mdq_validation_parity.py.md` | 1, 2 | Procedure | Pending | — | — |
| `implementations/20261128-084218_13_tests_mcp_servers_mdq_test_mdq_read_consistency_metadata.py.md` | 1, 4 | Procedure | Pending | — | — |
| `implementations/20261128-084218_14_docs_22_mcp_mcp_04_04_mdq.md.md` | 5 | Procedure | Pending | — | — |
| `implementations/20261128-084218_15_docs_22_mcp_mcp_03_01_dispatch-and-routing.md.md` | 5 | Procedure | Pending | — | — |
| `implementations/20261128-084218_16_tests_mcp_servers_mdq_test_mdq_stale_detection.py.md` | 4 | Procedure | Pending | — | — |
| `implementations/20261128-084218_17_tests_mcp_servers_mdq_test_mdq_outline_stale_helper.py.md` | 4 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: `issues/20261119-142130_mdqmcp008_mdq-schema-scope-consistency.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261127-184702
- **Evidence revision**: 4504b4fd6b2a7ec7ccc08109911a975387b7a8b5
- **Related target files**: `scripts/mcp_servers/mdq/mdq_models.py`, `scripts/mcp_servers/mdq/mdq_tools.py`, `scripts/mcp_servers/mdq/mdq_server.py`, `scripts/mcp_servers/mdq/mdq_service.py`, `scripts/shared/resource_scope.py`, `tests/mcp_servers/mdq/test_mdq_tool_schema.py`, `tests/mcp_servers/mdq/test_mdq_tool_layer_consistency.py`, `tests/mcp_servers/mdq/test_mdq_get_chunk_behavior.py`, `tests/mcp_servers/mdq/test_mdq_service.py`, `tests/mcp_servers/mdq/test_mdq_index_serialization.py`, `tests/shared/test_resource_scope.py`, `tests/mcp_servers/mdq/test_mdq_validation_parity.py`, `tests/mcp_servers/mdq/test_mdq_read_consistency_metadata.py`, `docs/22_mcp/mcp_04_04_mdq.md`, `docs/22_mcp/mcp_03_01_dispatch-and-routing.md`, `tests/mcp_servers/mdq/test_mdq_stale_detection.py`, `tests/mcp_servers/mdq/test_mdq_outline_stale_helper.py`

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes item 1; `scripts/mcp_servers/mdq/mdq_models.py:199`, `mdq_tools.py:17,85`, `tests/mcp_servers/mdq/test_mdq_get_chunk_behavior.py:81` | `scripts/mcp_servers/mdq/mdq_models.py`, `scripts/mcp_servers/mdq/mdq_tools.py`, `scripts/mcp_servers/mdq/mdq_server.py` | Phase 2 | AC-1, AC-2 | `tests/mcp_servers/mdq/test_mdq_validation_parity.py`, `tests/mcp_servers/mdq/test_mdq_tool_schema.py` | Confirmed |
| REQ-002 | Required Changes item 2; `scripts/mcp_servers/mdq/mdq_tools.py:178-179,211-212`, `scripts/shared/resource_scope.py:52,59,129,132-134` | `scripts/mcp_servers/mdq/mdq_tools.py`, `scripts/shared/resource_scope.py` | Phase 3 | AC-3 | `tests/shared/test_resource_scope.py`, `tests/mcp_servers/mdq/test_mdq_tool_layer_consistency.py` | Confirmed |
| REQ-003 | Required Changes item 3; `scripts/mcp_servers/mdq/mdq_service.py:145-146,219,234-235,367`, `tests/mcp_servers/mdq/test_mdq_index_serialization.py:199` | `scripts/mcp_servers/mdq/mdq_models.py`, `scripts/mcp_servers/mdq/mdq_service.py` | Phase 4 | AC-4, AC-5 | `tests/mcp_servers/mdq/test_mdq_read_consistency_metadata.py`, `tests/mcp_servers/mdq/test_mdq_index_serialization.py` | Confirmed |
| REQ-004 | Required Changes item 1; `scripts/mcp_servers/mdq/mdq_server.py:236,378`, `scripts/mcp_servers/mdq/mdq_models.py:482-495` | `scripts/mcp_servers/mdq/mdq_models.py`, `scripts/mcp_servers/mdq/mdq_server.py` | Phase 4 | AC-4 | `tests/mcp_servers/mdq/test_mdq_get_chunk_behavior.py` | Confirmed |
| REQ-005 | Required Changes item 1; `scripts/mcp_servers/mdq/mdq_models.py:203`, `mdq_tools.py:89`, `scripts/mcp_servers/mdq/mdq_server.py:233`, `tests/mcp_servers/mdq/test_mdq_service.py:260` | `scripts/mcp_servers/mdq/mdq_models.py`, `scripts/mcp_servers/mdq/mdq_tools.py`, `scripts/mcp_servers/mdq/mdq_server.py` | Phase 2 | AC-1 | `tests/mcp_servers/mdq/test_mdq_service.py` | Confirmed |
| REQ-006 | Documentation Impact; `docs/22_mcp/mcp_04_04_mdq.md:129`, `docs/22_mcp/mcp_03_01_dispatch-and-routing.md:122,171` | `docs/22_mcp/mcp_04_04_mdq.md`, `docs/22_mcp/mcp_03_01_dispatch-and-routing.md` | Phase 5 | AC-6 | `uv run python tools/check_docs_content_policy.py` | Confirmed |
| REQ-003 | Amendment 2026-11-28: Assert the outline consistency state through metadata instead of the warning text in the returned value, because REQ-003 changes the outline return shape to text plus metadata | tests/mcp_servers/mdq/test_mdq_stale_detection.py | Phase 4 | N/A: none cites REQ-003 | itself | Confirmed by repository evidence |
| REQ-003 | Amendment 2026-11-28: Assert the outline consistency state through metadata instead of the warning text in the returned value, because REQ-003 changes the outline return shape to text plus metadata | tests/mcp_servers/mdq/test_mdq_outline_stale_helper.py | Phase 4 | N/A: none cites REQ-003 | itself | Confirmed by repository evidence |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261128-084218 -->
