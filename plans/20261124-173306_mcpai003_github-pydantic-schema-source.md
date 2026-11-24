## Goal
- Make strict Pydantic request models the single source of truth for every GitHub MCP tool `inputSchema` and for request/configuration validation, so discovery-time and runtime validation enforce one contract and can no longer drift.

## Priority
High

## Scope
- **In-Scope**: a shared strict-request base model and a deterministic schema generator under `scripts/mcp_servers/`; regeneration of all 21 GitHub tool `inputSchema` entries from request models; `dry_run` publication on every GitHub write tool; stricter request-model bounds; strict GitHub configuration parsing and allowlist entry validation; runtime dispatch alignment (`model_validate`); model-to-schema CI consistency tests; HTTP rejection tests; documentation updates.
- **Out-of-Scope**: File, Git, CI/CD, Web Search, and MDQ servers' own schema migration (their own Issues: mcpai009, mcpci001, mcpws002, mdqmcp008 reuse this Plan's shared module but change their own files); allowlist enforcement and search scoping (delivered by mcpai002); response models (`IssueInfo`, `PullRequestInfo`, etc.); the pre-existing unrelated failures in `tests/tools/test_append_plan_work_items.py` (see Validation plan notes).
- **Dependencies**: mcpai002 (completed: shared strict-config helpers in `scripts/shared/config_utils.py` and the `owner/repo` identity helpers in `scripts/shared/repo_identity.py` already exist in source; case-normalization policy is canonical lowercase `owner/repo` via `normalize_repo_key`). mcpai001: independent. This Plan blocks mcpai005, mcpai009, mcpai010, mcpci001, mcpws002, mdqmcp008.

## Background
Source: consolidated review backlog (Issue 2). Published tool schemas under `scripts/mcp_servers/github/tools_*.py` are hand-maintained dictionaries placed next to the runtime models in `scripts/mcp_servers/github/github_models_*.py`, with no test tying the two together. Related archived work: mcpget001 (config-loader coercion) already replaced bare `int()`/`list()` coercions in `GitHubConfig.from_dict` for most fields; mcpai002 (completed) added `shared.config_utils` strict accessors and `shared.repo_identity`. Re-verified against both: the remaining `bool(d.get(...))` truthiness calls in `github_models_config.py` are exactly the residue of that policy, and the `owner/repo` helper this Plan must reuse already exists.

## Problem
Published schemas and runtime models have drifted. Verified against current source (Step 2):
- Write models declare `dry_run` (`github_models_file.py:55,81,112`, `github_models_repository.py:157`, `github_models_pull_requests.py:54,76,104`, `github_models_issues.py:61,79`), but none of the published `inputSchema` dicts in `tools_*.py` include it (only the metadata field `preview_capability: "dry_run"`). Runtime accepts it (`github_service_dispatch_writes.py` `args.get("dry_run", False)`), while the agent-side extra-field gate (`scripts/agent/tool_arg_validator.py` `_check_extra_fields`) rejects it because it is absent from `properties` — dry-run is currently unreachable through the validated agent path.
- Runtime request models use Pydantic default `extra` behavior (no `model_config` set), so unknown arguments are silently dropped; the agent-side validator rejects the same fields only when they are absent from `properties`. The two layers enforce different contracts.
- `allow_force_push` and `require_pr_review` are parsed with bare `bool(d.get(...))` (`github_models_config.py:66-67`), so the TOML string `"false"` evaluates to `True`. Correction to the Issue's claim: the field names `write_requires_dry_run`, `require_signed_commits`, and `write_enabled` named by the review do not exist anywhere in `scripts/` or `config/` (checked Step 2); the truthiness residue in `GitHubConfig` is exactly these two fields.
- Pagination bounds drift: models declare `ge=1` with no upper bound (`github_models_*.py`), while the service silently clamps to `cfg.max_per_page` (`github_service_security.py:66-69`) and some published schemas advertise a maximum (for example `search_file` `max_bytes`/`per_page` bounds live only in the hand-written dict).
- Unknown-field and empty-value drift: no required-text lower bounds (`min_length`), no number lower bounds (`>= 1` for issue/PR numbers), no minimum item count for `push_files`, no rejection of a no-op pull request update.
- Allowlist startup validation only checks non-emptiness (`github_service_security.py:391-404`); malformed `allowed_repos` entries reach runtime and only fail at call time.
- No model-to-schema consistency test exists: `tests/mcp_servers/github/test_github_tool_registry.py` pins TOOL_LIST count/names against `ToolRegistry`; `tests/mcp_servers/test_tool_schema_contract.py` validates schema-2.1 metadata fields; `tests/mcp_servers/test_mcp_tool_schema_exports.py` validates exports. None compares `inputSchema` content with the request models (checked Step 2). The review's `tests/test_github_tool_registry.py` path does not exist; the correct location is `tests/mcp_servers/github/test_github_tool_registry.py` (confirmed Step 2).

## Reason for Change
The contract is foundational for dry-run (mcpai005) and the HTTP integration gate (mcpai010); patching individual fields would keep the structural cause of drift (two hand-maintained definitions per tool with no test between them).

## Implementation Intent
Use strict Pydantic models (`extra="forbid"`) as the authoritative contract for runtime validation and `/v1/tools` discovery through one reusable, deterministic schema-generation helper shared by all GitHub domains and placed in a shared MCP module. Preserve `$defs`/`$ref` unless flattening is proven necessary. Reject invalid input and configuration before any GitHub API access.

## Requirements
- `REQ-001`: Add a shared strict request base model (`model_config = ConfigDict(extra="forbid")`) and a deterministic `inputSchema` generator to a shared MCP module (`scripts/mcp_servers/`), not a GitHub-private one, reusable later by File, CI/CD, Web Search, and MDQ.
- `REQ-002`: Generate every GitHub tool `inputSchema` from its request model via `model_json_schema()`, preserving `default`, `enum`, `pattern`, `minimum`, `maximum`, `minLength`, `minItems`, `$defs`, `$ref`, and `additionalProperties`; strip only presentation-only fields (for example `$defs` root title noise that carries no validation meaning).
- `REQ-003`: Publish `dry_run` in the `inputSchema` of every GitHub write tool.
- `REQ-004`: Require non-empty `owner`, `repo`, `branch`/`ref`, `path`, `title`, `message`, and other mandatory text (`min_length=1`); require issue and pull request numbers `>= 1`; require at least one file in `push_files` (`minItems=1`); reject pull request updates with no actual update (model-level validator).
- `REQ-005`: Add justified upper bounds for content, body, labels, assignees, and files per request (proposed values in Assumptions, owner-confirmed per UNK-02).
- `REQ-006`: Apply the shared strict configuration helpers to GitHub configuration: strict booleans for `allow_force_push` and `require_pr_review` (`get_typed(..., bool, ...)`), positive pagination values, rejection of NaN and infinity (`get_non_negative_number`); keep the GitHub-specific rule `default_per_page <= max_per_page` (already enforced by `github_service_security.py:502`).
- `REQ-007`: Validate every `allowed_repos` entry with the shared `owner/repo` helper (`scripts/shared/repo_identity.py`) and the canonical lowercase `owner/repo` normalization policy; deduplicate deterministically (sorted, canonical keys).
- `REQ-008`: Align runtime validation with the published schema: dispatch builds request models with `Model.model_validate(args)` (instead of picking `args[...]` keys) so unknown fields and type errors are rejected at runtime and converted to `GitHubValidationError` (existing 422 handler contract); discovery-time and runtime reject the same invalid arguments.
- `REQ-009`: Make CI fail when a request model and the published schema drift: model-to-schema consistency tests cover every GitHub tool, including `dry_run` presence in every write schema.

## Implementation Target Files
**Freeze status**: Frozen (passed `issue-to-plan` Step 8 Validation Sequence —
structure check, target path audit, target overlap check; see `rules/workflow-lifecycle.md`
Implementation Target Files Validation (Plan Freeze)).

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| scripts/mcp_servers/request_contract.py | Create (new) | Shared strict request base model + deterministic `inputSchema` generator | REQ-001, REQ-002 / AC-01, AC-02 | Precedent: `extra="forbid"` models already exist in `scripts/mcp_servers/models.py` (lines 107, 169); `mcp_servers` is importable by all server subpackages per `.importlinter` (checked in Step 3) | tests/mcp_servers/test_request_contract.py | Verified |
| tests/mcp_servers/test_request_contract.py | Create (new) | Generator unit tests: determinism, keyword preservation, presentation-field stripping, `$defs`/`$ref` retention | REQ-001, REQ-002 / AC-02, AC-05 | `tests/mcp_servers/` is the shared MCP test directory (checked in Step 2) | this file | Verified |
| scripts/mcp_servers/github/github_models_issues.py | Modify | Inherit strict base; add text/number bounds; keep `dry_run` | REQ-004, REQ-005, REQ-008 / AC-03, AC-04 | Models exist with `dry_run` at lines 61, 79 but no `model_config` and no upper bounds (checked in Step 2) | tests/mcp_servers/github/test_github_request_validation.py | Verified |
| scripts/mcp_servers/github/github_models_pull_requests.py | Modify | Inherit strict base; bounds; reject no-op PR update via model validator | REQ-004, REQ-005, REQ-008 / AC-03, AC-04 | `dry_run` at lines 54, 76, 104; no `model_config`; `UpdatePullRequestRequest` accepts all-default update fields (checked in Step 2) | tests/mcp_servers/github/test_github_request_validation.py | Verified |
| scripts/mcp_servers/github/github_models_file.py | Modify | Inherit strict base; content upper bound; `push_files` `minItems=1` | REQ-004, REQ-005, REQ-008 / AC-03, AC-04 | `dry_run` at lines 55, 81, 112; no `model_config`; no content bound (checked in Step 2) | tests/mcp_servers/github/test_github_request_validation.py | Verified |
| scripts/mcp_servers/github/github_models_repository.py | Modify | Inherit strict base; pagination/query bounds | REQ-004, REQ-005, REQ-008 / AC-03, AC-04 | `per_page` has `ge=1` only, no `le` (checked in Step 2) | tests/mcp_servers/github/test_github_request_validation.py | Verified |
| scripts/mcp_servers/github/github_models_config.py | Modify | Strict bools for `allow_force_push`/`require_pr_review`; allowlist entry validation and deterministic dedup | REQ-006, REQ-007 / AC-04 | `bool(d.get(...))` at lines 66-67; `allowed_repos` validated only as a list, entries unvalidated (checked in Step 2) | tests/mcp_servers/github/test_github_config_strict_parsing.py | Verified |
| scripts/mcp_servers/github/tools_issues.py | Modify | Replace manual `inputSchema` dicts with generated schemas; publish `dry_run` | REQ-002, REQ-003 / AC-01, AC-03 | Manual dict schemas confirmed; `dry_run` absent from all write schemas (checked in Step 2) | tests/mcp_servers/github/test_github_tool_registry.py | Verified |
| scripts/mcp_servers/github/tools_pull_requests.py | Modify | Same as tools_issues.py | REQ-002, REQ-003 / AC-01, AC-03 | Same pattern confirmed (checked in Step 2) | tests/mcp_servers/github/test_github_tool_registry.py | Verified |
| scripts/mcp_servers/github/tools_repository.py | Modify | Same as tools_issues.py | REQ-002, REQ-003 / AC-01, AC-03 | Same pattern confirmed (checked in Step 2) | tests/mcp_servers/github/test_github_tool_registry.py | Verified |
| scripts/mcp_servers/github/tools_file.py | Modify | Same as tools_issues.py | REQ-002, REQ-003 / AC-01, AC-03 | Manual schema advertises `max_bytes`/`per_page` limits the models do not declare (checked in Step 2) | tests/mcp_servers/github/test_github_tool_registry.py | Verified |
| scripts/mcp_servers/github/github_service_dispatch.py | Modify | Build read-domain request models via `model_validate(args)`; convert `pydantic.ValidationError` to `GitHubValidationError` | REQ-008 / AC-04 | Dispatch constructs models with explicit `args[...]` keys, silently dropping unknown fields (checked in Step 3) | tests/mcp_servers/github/test_github_server_endpoints.py | Verified |
| scripts/mcp_servers/github/github_service_dispatch_writes.py | Modify | Same for write-domain `fmt_*` builders | REQ-008 / AC-03, AC-04 | `fmt_create_issue` etc. use `args.get(...)` key picking (checked in Step 3) | tests/mcp_servers/github/test_github_server_endpoints.py | Verified |
| tests/mcp_servers/github/test_github_tool_registry.py | Modify | Add model-to-schema drift gate and per-write-tool `dry_run` presence assertions | REQ-009, REQ-003 / AC-05 | File exists at this path (review's `tests/test_github_tool_registry.py` does not); currently pins only count (21) and registry mapping (checked in Step 2) | this file | Verified |
| tests/mcp_servers/github/test_github_request_validation.py | Create (new) | Model-level validation tests: enums, patterns, numeric ranges, item counts, defaults, unknown-field rejection, no-op PR update rejection | REQ-004, REQ-005, REQ-008 / AC-03, AC-04 | No existing test asserts GitHub request-model validation semantics (checked in Step 2) | this file | Verified |
| tests/mcp_servers/github/test_github_config_strict_parsing.py | Create (new) | Config tests: invalid boolean strings, non-positive limits, NaN/infinity, malformed repo identifiers, duplicate normalization | REQ-006, REQ-007 / AC-04 | Existing `from_dict` tests (`test_github_mcp_service.py:863-881`) pass only well-typed values (checked in Step 3) | this file | Verified |
| tests/mcp_servers/github/test_github_server_endpoints.py | Modify | HTTP tests proving invalid input (unknown fields, bad types, empty identifiers) never reaches a GitHub service method | REQ-008 / AC-04 | File exists and already exercises server endpoints with fake services (checked in Step 3) | this file | Verified |
| docs/22_mcp/mcp_04_01_web-search-file-read-github.md | Modify | Record that request models are the schema source, `dry_run` is published, and the rejection rules (intent and boundaries), including the list of newly rejected inputs | REQ-002, REQ-003, REQ-004 / AC-01, AC-03 | `docs/00_index.md` MCP task table maps "Any MCP server (catalog only)" to this doc; updated by mcpai002 (checked in Step 5) | `docs/00_index.md` mapping | Verified |
| docs/22_mcp/mcp_06_01_configuration-file-inventory.md | Modify | Record the strict parsing semantics for the GitHub config keys this Plan changes | REQ-006, REQ-007 / AC-04 | `docs/00_index.md` MCP task table maps config inventory to this doc; churn 2 commits/30d from mcpai002 (checked in Step 5) | `generate_reference_table.py --check` | Verified |

Rules (see `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan
Freeze) for the full validation procedure):
- One row per file. A directory, glob pattern (`*`, `**`), component/module name, file
  group, or a vague phrase (e.g. "related files", "as necessary", "etc.") MUST NOT
  appear as a row — list each file individually by its exact repository-relative path.
- Record a test, configuration, schema, migration, deployment, or documentation file as
  its own row when it requires modification — do not fold it into the row for the
  source file it accompanies.
- `Validation Status` is `Verified` or `Needs confirmation` per row; every row must be
  `Verified` before this section may be marked `Frozen`.

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same
one-file-per-row discipline as `Implementation Target Files` above — no directories,
glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| scripts/mcp_servers/github/github_models_base.py | Shared response models (`IssueInfo`, `PullRequestInfo`) live here; confirms no GitHub request base exists yet and response models stay untouched | REQ-001 (Issue lists it; no modification needed — verified Step 2) |
| scripts/mcp_servers/github/github_models.py | Re-export aggregation shim consumed by `test_github_mcp_service.py`; confirms re-export list is unaffected (no renames planned) | REQ-002 (checked Step 3) |
| scripts/mcp_servers/models.py | `McpTool` TypedDict entry shape (`inputSchema` required) and existing `extra="forbid"` precedent | REQ-001, REQ-002 (checked Step 2) |
| scripts/shared/resource_scope.py | `validate_tool_schema_v2()` schema-2.1 metadata contract every `tools_*.py` entry must keep carrying explicitly | REQ-002 (checked Step 3) |
| scripts/mcp_servers/github/exception_handlers.py | `GitHubValidationError` HTTP mapping that the dispatch conversion must preserve | REQ-008 (checked Step 3) |
| scripts/shared/config_utils.py | `get_typed` / `get_non_negative_number` strict accessors to reuse | REQ-006 (checked Step 2) |
| scripts/shared/repo_identity.py | `normalize_repo_key` / `is_canonical_repo_key` canonical `owner/repo` helpers to reuse | REQ-007 (checked Step 3) |
| scripts/agent/tool_arg_validator.py | Agent-side consumer of `inputSchema`: required-field, extra-field, and `jsonschema` type gates the generated schema must satisfy | REQ-002, REQ-008 (checked Step 2) |
| scripts/mcp_servers/github/github_service_security.py | `_clamp_per_page`, `default_per_page <= max_per_page` check, and the non-empty allowlist posture check interacting with the new bounds/validation | REQ-006, REQ-007 (checked Step 2) |
| tests/mcp_servers/test_tool_schema_contract.py | Schema-2.1 metadata test that imports all four GitHub `tools_*.py` `TOOL_LIST` exports and must keep passing | REQ-002 (checked Step 3) |

## Acceptance Criteria
- AC-01: All GitHub tool schemas are generated from Pydantic request models and every write schema exposes `dry_run`. (REQ-001, REQ-002, REQ-003)
- AC-02: Schema generation is deterministic: `model_json_schema()` output passes through the generator unchanged except for documented presentation-only stripping, verified by generator unit tests. (REQ-001, REQ-002)
- AC-03: Discovery-time and runtime validation reject the same invalid arguments, including unknown fields. (REQ-008)
- AC-04: Empty identifiers, empty file batches, and no-op pull request updates are rejected; invalid boolean strings, negative limits, NaN, infinity, and malformed repository identifiers are rejected at startup. (REQ-004, REQ-005, REQ-006, REQ-007)
- AC-05: CI fails when a request model and the published schema drift. (REQ-009)

## Tests
- T-01: Generator unit tests in `tests/mcp_servers/test_request_contract.py`: determinism across repeated calls and dict ordering, preservation of `default`, `enum`, `pattern`, `minimum`, `maximum`, `minLength`, `minItems`, `$defs`, `$ref`, `additionalProperties`; stripping of presentation-only fields. (REQ-001, REQ-002)
- T-02: Model-to-schema consistency tests for all 21 GitHub tools plus `dry_run` presence in every write schema, in `tests/mcp_servers/github/test_github_tool_registry.py`. (REQ-003, REQ-009)
- T-03: Model-level tests for enums, patterns, numeric ranges, item counts, defaults, required-text non-emptiness, upper bounds, unknown-field rejection, and no-op PR update rejection in `tests/mcp_servers/github/test_github_request_validation.py`. (REQ-004, REQ-005, REQ-008)
- T-04: Configuration tests for invalid booleans (`"false"`-as-string), non-positive limits, NaN, infinity, malformed repository identifiers, and deterministic duplicate normalization in `tests/mcp_servers/github/test_github_config_strict_parsing.py`. (REQ-006, REQ-007)
- T-05: HTTP tests proving invalid input never reaches a GitHub service method in `tests/mcp_servers/github/test_github_server_endpoints.py`. (REQ-008)
- T-06: Full gates per `rules/toolchain.md`: ruff, mypy, bandit, `lint-imports`, full `uv run pytest`, diff-cover >= 90% on changed lines, `pre-commit`, `generate_reference_table.py --check`. (all REQ)

## Documentation Impact
Yes. Per `docs/00_index.md` "Document References by Task" (MCP table): the GitHub catalog
doc (`22_mcp/mcp_04_01_web-search-file-read-github.md`) must record that request models
are the schema source, `dry_run` is published on write tools, and the rejection rules
(intent and boundaries) including the newly rejected inputs (REQ-002, REQ-003, REQ-004);
the configuration inventory doc (`22_mcp/mcp_06_01_configuration-file-inventory.md`) must
record the strict parsing semantics of the changed GitHub config keys (REQ-006, REQ-007).
Generated contract blocks are re-checked with `tools/generate_reference_table.py --check`
(Step 3 run reported "No drift found"; the port-tool-reference block depends only on
tool names and ports, which do not change).

## Assumptions
- Proposed upper bounds (falsifiable; owner confirmation tracked as UNK-02): `per_page` `le=100` (matches `config/github_mcp_server.toml` `max_per_page = 100` and the GitHub API cap); file `content` `le=1048576` characters (matches the configured `max_file_size_kb = 1024` write guard); `body` `le=65536`; `labels`/`assignees` `maxItems=100`; `push_files` files `minItems=1`, `maxItems=100`; `title` `max_length=256` (GitHub title limit).
- `pydantic` `model_json_schema()` is deterministic for a fixed model definition and installed `pydantic>=2.7`.
- The generated schema keeps `$defs`/`$ref` (see UNK-01): the agent-side validator resolves them through the `jsonschema` library (`tool_arg_validator.py:_check_type_validation`); provider-side tolerance is assumed pending the UNK-01 confirmation path.
- `tools_*.py` entries keep carrying the schema-2.1 metadata fields explicitly (the TypedDict head/tail pattern stays; only `inputSchema` content is replaced).
- No GitHub tool is added or removed, so the pinned counts (`test_github_tool_registry.py:16` and `test_service_dispatch.py:698`, both `== 21`) stay valid.
- The `github_models.py` re-export shim needs no change (no model renames, no new exports from this Plan's GitHub-side rows).

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether the Agent-side / provider-side tool-definition pipeline can consume `$defs` and `$ref` unflattened | Repository evidence covers only the validation side (`jsonschema` resolves embedded `$defs`/`$ref` in `tool_arg_validator.py`); the LLM provider's tool-spec payload tolerance is not verifiable from this repository | Keep `$defs`/`$ref` (Issue-mandated default). During procedure generation, confirm provider tolerance from the agent-side tool-spec builder and provider docs; if flattening is required, stop and report per the Issue's AI Implementation Instruction before implementing a shared resolver | False |
| UNK-02 | Final upper-bound values for content, body, labels, assignees, and files per request | Repository evidence justifies `per_page` (100) and `content` (1 MiB write guard in config) only; the remaining values are proposals | Confirm the proposed values in Assumptions at plan review / procedure generation; rejected inputs must be listed in the change per the Issue's Constraints | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| scripts/mcp_servers/request_contract.py | Create | High (new shared contract for later server reuse) | N/A (new file) | N/A (new file) | not applicable (rsynced) |
| tests/mcp_servers/test_request_contract.py | Create | Low | N/A (new file) | N/A (new file) | not applicable (rsynced) |
| scripts/mcp_servers/github/github_models_issues.py | Modify | Medium | 0 | High (single author) | not applicable (rsynced) |
| scripts/mcp_servers/github/github_models_pull_requests.py | Modify | Medium | 0 | High (single author) | not applicable (rsynced) |
| scripts/mcp_servers/github/github_models_file.py | Modify | Medium | 0 | High (single author) | not applicable (rsynced) |
| scripts/mcp_servers/github/github_models_repository.py | Modify | Medium | 0 | High (single author) | not applicable (rsynced) |
| scripts/mcp_servers/github/github_models_config.py | Modify | High (server startup behavior) | 3 | High (single author) | not applicable (rsynced) |
| scripts/mcp_servers/github/tools_issues.py | Modify | High (published contract consumed by the agent validator) | 1 | High (single author) | not applicable (rsynced) |
| scripts/mcp_servers/github/tools_pull_requests.py | Modify | High | 1 | High (single author) | not applicable (rsynced) |
| scripts/mcp_servers/github/tools_repository.py | Modify | High | 1 | High (single author) | not applicable (rsynced) |
| scripts/mcp_servers/github/tools_file.py | Modify | High | 1 | High (single author) | not applicable (rsynced) |
| scripts/mcp_servers/github/github_service_dispatch.py | Modify | Medium | 0 | High (single author) | not applicable (rsynced) |
| scripts/mcp_servers/github/github_service_dispatch_writes.py | Modify | Medium | 0 | High (single author) | not applicable (rsynced) |
| tests/mcp_servers/github/test_github_tool_registry.py | Modify | Low | 0 | High (single author) | not applicable (rsynced) |
| tests/mcp_servers/github/test_github_request_validation.py | Create | Low | N/A (new file) | N/A (new file) | not applicable (rsynced) |
| tests/mcp_servers/github/test_github_config_strict_parsing.py | Create | Low | N/A (new file) | N/A (new file) | not applicable (rsynced) |
| tests/mcp_servers/github/test_github_server_endpoints.py | Modify | Low | 3 | High (single author) | not applicable (rsynced) |
| docs/22_mcp/mcp_04_01_web-search-file-read-github.md | Modify | Low | 1 | High (single author) | not applicable (rsynced) |
| docs/22_mcp/mcp_06_01_configuration-file-inventory.md | Modify | Low | 2 | High (single author) | not applicable (rsynced) |

## Design
Classification: Path B (Step 3; confirmed). Rationale: >3 files, a new shared module, and a public/runtime-facing schema change.

Module design (python-design Step 4 decision entries):
- **`scripts/mcp_servers/request_contract.py`** (Create)
  - Package path: `scripts/mcp_servers/` (top level of the MCP server package, next to `models.py` and `tool_validators.py`).
  - Responsibility: hold the strict request base model and the deterministic `inputSchema` generator shared by MCP server domains.
  - Public API: `StrictRequestModel` (a `BaseModel` with `model_config = ConfigDict(extra="forbid")`) and `build_input_schema(model: type[BaseModel]) -> dict[str, Any]` (model JSON schema, presentation-only fields stripped, everything else preserved).
  - Dependency direction: imported by `mcp_servers.github.*` (relative import `..request_contract`); imports only `pydantic` (external). Later reused by file/cicd/web_search/mdq per their own Issues.
  - Alternatives considered: `scripts/shared/` — rejected because `shared` is the leaf layer for cross-package utilities (`.importlinter` `shared-is-leaf`) and MCP request-contract semantics belong to `mcp_servers`; extending `scripts/mcp_servers/models.py` — rejected because that module holds the `/v1/*` wire models (`McpTool`, `CallToolRequest`) and mixing schema generation into it would couple wire transport with contract generation. `extra="forbid"` precedent already exists in `models.py` (checked in Step 3).
  - Compatibility impact: `/v1/tools` output changes (schemas gain `dry_run`, `additionalProperties: false`, bounds/patterns/enum); the agent-side extra-field gate starts accepting `dry_run`; malformed/unknown arguments change from "silently dropped" to rejected.
  - Reversibility: per-domain revert (each domain phase is one commit); the shared module itself has no callers until Phase 2 lands.
- **Dispatch alignment** (Modify `github_service_dispatch.py` / `github_service_dispatch_writes.py`): `fmt_*` builders switch from `Model(owner=args["owner"], ...)` key-picking to `Model.model_validate(args)`; a `pydantic.ValidationError` is caught and re-raised as `GitHubValidationError` so the existing `exception_handlers.py` 422 mapping is preserved. Alternative: registering `tool_validators.py` validators per GitHub tool — rejected because it duplicates the model as a second validator definition, the exact drift pattern this Issue removes.
- **Per_page bound**: model `le=100` makes the published schema honest about the current `max_per_page`; `github_service_security._clamp_per_page` stays as defense-in-depth for configs with a lower cap (documented, not removed).
- **Config strictness**: `allow_force_push`/`require_pr_review` switch to `get_typed(..., bool, "a boolean", default=...)`; `allowed_repos` entries are canonicalized/deduplicated via `shared.repo_identity.normalize_repo_key` in `from_dict` and rejected for malformed shape in `load` (startup fail-fast, consistent with the existing `protected_branches` rule).

Consumer scan results (`tools/scan_change_consumers.py`, seeds = the 10 listed GitHub files + `GitHubConfig`, Step 3):
- Target rows already listed: all four `tools_*.py` and `github_models_config.py` (`tests/mcp_servers/test_tool_schema_contract.py`, `tests/agent/_producer_registry.py`, `tools/_agentcfg003_content_producers.py` candidates).
- `tests/mcp_servers/test_tool_schema_contract.py`: not affected — it validates the schema-2.1 per-tool metadata fields (explicit-field assertions and tool-name coverage), not `inputSchema` content; entries keep their metadata (checked in Step 3).
- `tests/agent/_producer_registry.py` + `tests/agent/test_tool_approval_*`: not affected — they import `TOOL_LIST` module paths, which are unchanged (checked in Step 3).
- `tools/_agentcfg003_content_producers.py`: not affected — private content table of the completed agentcfg003 one-off generator; its test (`tests/tools/test_generate_agentcfg003_procedures.py`) exercises assembly with fixtures, not live `tools_*.py` schema text (checked in Step 3).
- `scripts/mcp_servers/github/github_models.py` (re-export shim) and `tests/mcp_servers/github/test_github_mcp_service.py`: recorded as Reference / unaffected — no renames; the `from_dict` tests there pass well-typed values only (checked in Step 3).
- Testmon state: absent (`no .testmondata`); the scan is candidates-only.

Predictable fallout check (Step 3):
- Module size: every target file is far below the 24576 B gate (largest existing: `tools_pull_requests.py` 9978 B; `tools_*.py` shrink as dicts are replaced). No split row needed.
- Pinned counts: `test_github_tool_registry.py:16` and `test_service_dispatch.py:698` pin `== 21`; unchanged (no tools added/removed) — already target/reference rows for other reasons.
- Tool inventory: no `tools/*.py` scripts added or removed — `not affected`.
- Generated blocks: `tools/generate_reference_table.py --check` reported "No drift found" (Step 3); the GitHub-relevant generated block (`mcp_01_tool_ownership_matrix.md` port-tool-reference) is derived from TOOL_LIST names/ports, unchanged. Re-run in the validation plan.

Validation quality baseline (Step 5):
- `radon cc` per Python target (`uv run radon`; CLI not on PATH): all functions A (complexity 1), per-file top entries recorded Step 5.
- `vulture scripts/mcp_servers/github/ --min-confidence 80`: 1 pre-existing finding (`github_server.py:125` unused variable `tool_name`).
- `bandit -r scripts/mcp_servers/github/ -c pyproject.toml`: 1 pre-existing Low-severity finding (B105 `'not_set'`, `github_server.py:179`, confidence Medium).
- diff-cover (`rules/toolchain.md` section 7 sequence): baseline run at clean tree reports "No lines with coverage information in this diff"; full-suite coverage baseline: 13744 passed, 5 skipped, 6 errors (all pre-existing, see Validation plan). The Plan must raise diff-cover to `>= 90%` on changed lines at implementation per `rules/toolchain.md` Completion checklist.
- `lint-imports`: 6 contracts KEPT (including `shared-is-leaf` and "No agent module imports MCP server config models") — the new module must not violate these.
- Architecture analysis used `rg` import scans plus `lint-imports`; `ast-grep` is not installed on this host (Tool availability guard) — the existing-pattern check used `rg "class \w+\(BaseModel\)" scripts/` (15 files with the pattern, no conflicting shared base exists).
- Historical analysis: churn (30d) per file in Affected areas; bus factor is single-author across all sampled GitHub-server files (`git log --format='%an'`, Step 5) — flagged High.
- Operational inspection: production `mcp_github` processes are running (`/opt/llm/bin/mcp_github`, PID 249064/249066) and `127.0.0.1:8006` is listening (`ss`, Step 5) — deployment restart required; no SQLite file is touched by this Plan (no persisted-schema check needed); `pip-audit` not applicable (no dependency change).

Unresolved Question resolved with repository evidence (Issue Q3, test location): the model-to-schema test belongs in `tests/mcp_servers/github/test_github_tool_registry.py` — that file already exists at that location, is titled "Consistency tests for GitHub MCP tools", and is the established location for GitHub TOOL_LIST consistency tests.

## Implementation steps
Each step description MUST cite the exact file path(s) it touches by referencing rows
of `Implementation Target Files` above — do not restate file-level detail
independently of that frozen table. A step is a top-level numbered item (a Phase); its
checklist items are sub-tasks, and the Execution Status table has one row per step.

1. **Phase 1: Shared request contract module**
   - [ ] Create `scripts/mcp_servers/request_contract.py` with `StrictRequestModel` (`extra="forbid"`) and `build_input_schema()` (REQ-001, REQ-002).
   - [ ] Create `tests/mcp_servers/test_request_contract.py` covering determinism, keyword preservation, presentation-field stripping, `$defs`/`$ref` retention (REQ-001, REQ-002).
2. **Phase 2: Issues domain migration**
   - [ ] `scripts/mcp_servers/github/github_models_issues.py`: inherit `StrictRequestModel`, add `min_length=1` text bounds, `ge=1` numbers, upper bounds per Assumptions (REQ-004, REQ-005).
   - [ ] `scripts/mcp_servers/github/tools_issues.py`: generate `inputSchema` via `build_input_schema()`; `dry_run` now published (REQ-002, REQ-003).
   - [ ] `tests/mcp_servers/github/test_github_tool_registry.py`: add the issues-domain model-to-schema drift gate; `tests/mcp_servers/github/test_github_request_validation.py`: create with issues-domain validation cases (REQ-004, REQ-009).
3. **Phase 3: Pull requests domain migration**
   - [ ] `scripts/mcp_servers/github/github_models_pull_requests.py`: strict base, bounds, no-op-update rejection (REQ-004, REQ-005).
   - [ ] `scripts/mcp_servers/github/tools_pull_requests.py`: generated schemas (REQ-002, REQ-003).
   - [ ] Extend `test_github_tool_registry.py` drift gate and `test_github_request_validation.py` with PR cases (REQ-004, REQ-009).
4. **Phase 4: File domain migration**
   - [ ] `scripts/mcp_servers/github/github_models_file.py`: strict base, content bound, `push_files` `minItems=1` (REQ-004, REQ-005).
   - [ ] `scripts/mcp_servers/github/tools_file.py`: generated schemas (REQ-002, REQ-003).
   - [ ] Extend `test_github_tool_registry.py` and `test_github_request_validation.py` with file cases (REQ-004, REQ-009).
5. **Phase 5: Repository domain migration**
   - [ ] `scripts/mcp_servers/github/github_models_repository.py`: strict base, `per_page le=100`, query bounds (REQ-004, REQ-005).
   - [ ] `scripts/mcp_servers/github/tools_repository.py`: generated schemas (REQ-002, REQ-003).
   - [ ] Extend `test_github_tool_registry.py` (all 21 tools now gated) and `test_github_request_validation.py` with repository cases (REQ-002, REQ-009).
6. **Phase 6: Runtime dispatch alignment**
   - [ ] `scripts/mcp_servers/github/github_service_dispatch.py` and `scripts/mcp_servers/github/github_service_dispatch_writes.py`: build every request model with `model_validate(args)`; convert `pydantic.ValidationError` to `GitHubValidationError` (REQ-008).
   - [ ] `tests/mcp_servers/github/test_github_server_endpoints.py`: HTTP tests that unknown fields, bad types, and empty identifiers never reach a GitHub service method (REQ-008).
7. **Phase 7: Configuration strictness**
   - [ ] `scripts/mcp_servers/github/github_models_config.py`: `get_typed` booleans for `allow_force_push`/`require_pr_review`, strict pagination values, allowlist entry canonicalization/validation via `shared.repo_identity`, deterministic dedup (REQ-006, REQ-007).
   - [ ] Create `tests/mcp_servers/github/test_github_config_strict_parsing.py`: `"false"`-string rejection, NaN/infinity, non-positive limits, malformed identifiers, dedup determinism (REQ-006, REQ-007).
8. **Phase 8: Documentation, full validation, deploy hand-off**
   - [ ] `docs/22_mcp/mcp_04_01_web-search-file-read-github.md`: record schema source of truth, `dry_run` publication, and the list of newly rejected inputs (REQ-002, REQ-003, REQ-004).
   - [ ] `docs/22_mcp/mcp_06_01_configuration-file-inventory.md`: record strict parsing semantics (REQ-006, REQ-007).
   - [ ] Run the full `rules/toolchain.md` sequence (ruff, mypy, bandit, lint-imports, full pytest, diff-cover >= 90%, pre-commit, `generate_reference_table.py --check`) (all REQ).
   - [ ] Deployment hand-off to `skills/deploy/SKILL.md`: the change must be committed and pushed first; deploying (rsync + `github-mcp` service restart, production listener `127.0.0.1:8006`) is the user's decision (approval gate).

### Release units
N/A: no release unit (every phase imports only what earlier phases created and is verifiable alone).

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/mcp_servers/request_contract.py | Unit (T-01) | `uv run pytest tests/mcp_servers/test_request_contract.py` | Deterministic schema output; all validation keywords preserved |
| scripts/mcp_servers/github/tools_*.py + github_models_*.py | Integration contract (T-02, T-03) | `uv run pytest tests/mcp_servers/github/test_github_tool_registry.py tests/mcp_servers/github/test_github_request_validation.py` | Every published schema equals its model's generated schema; every write schema has `dry_run`; drift fails CI |
| scripts/mcp_servers/github/github_service_dispatch*.py | HTTP-level (T-05) | `uv run pytest tests/mcp_servers/github/test_github_server_endpoints.py` | Invalid args yield 422 through `GitHubValidationError` without reaching service methods |
| scripts/mcp_servers/github/github_models_config.py | Unit (T-04) | `uv run pytest tests/mcp_servers/github/test_github_config_strict_parsing.py` | Ambiguous booleans, NaN/infinity, malformed repo ids rejected at load |
| All changed files | Full gates | `rules/toolchain.md` sequence + `uv run diff-cover coverage.xml --compare-branch=master` | >= 90% coverage on changed lines (baseline at clean tree: no diff lines yet, Step 5) |
| docs + generated blocks | Doc gates | `uv run pre-commit run --all-files`; `uv run python tools/generate_reference_table.py --check` | No drift (baseline Step 3: "No drift found") |
| Baseline note | — | — | Pre-existing, unrelated: 6 errors in `tests/tools/test_append_plan_work_items.py` at HEAD (`tool.IMPLEMENTATIONS_DIR` missing; reproduced Step 5, baseline run 13744 passed / 6 errors). Compare "no new failures" against this baseline; fixing it is out of this Plan's scope |

## Risks
- **Risk**: Stricter rejection changes currently accepted calls (unknown fields silently dropped today; `dry_run` currently rejected agent-side; empty strings accepted) → **Mitigation**: per the Issue Constraints, list every newly rejected input in the docs row and in T-03/T-05 tests; phases are per-domain and individually revertable.
- **Risk**: An LLM provider rejects `$defs`/`$ref` in the tool-definition payload → **Mitigation**: UNK-01 confirmation path before provider-facing rollout; if flattening is required, stop and report per the Issue's AI Implementation Instruction (one shared, tested resolver would be filed as a follow-up, not improvised).
- **Risk**: The shared module becomes a contract for four later Issues (mcpai009, mcpci001, mcpws002, mdqmcp008); a GitHub-shaped design would force those Issues to fork it → **Mitigation**: module imports only `pydantic`, API limited to base model + generator function, unit-tested independently of any domain.
- **Risk**: Single-author bus factor across all GitHub-server files (High, Step 5 historical analysis) means review depth is limited → **Mitigation**: small per-domain phases, each gated by tests before the next lands.
- **Risk**: Publishing `dry_run` makes preview calls reachable from the agent path and may change agent behavior toward write tools → **Mitigation**: dry-run executes no GitHub call (`_execute_with_dry_run` already short-circuits); mcpai005 owns the execution-context semantics.
- **Risk**: Model `le=100` for `per_page` conflicts with a future config `max_per_page` > 100 → **Mitigation**: 100 is the GitHub API cap; startup check keeps `default_per_page <= max_per_page`; documented in the config inventory doc row.
- **Risk**: Pre-existing baseline noise (6 errors in `tests/tools/test_append_plan_work_items.py`) could mask new regressions in full-suite runs → **Mitigation**: validation plan records the exact baseline counts for comparison.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`.

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Create shared request contract module + its unit tests (`scripts/mcp_servers/request_contract.py`, `tests/mcp_servers/test_request_contract.py`) | Pending | — | — | REQ-001, REQ-002 |
| 2 | Migrate issues domain (`scripts/mcp_servers/github/github_models_issues.py`, `scripts/mcp_servers/github/tools_issues.py`, `tests/mcp_servers/github/test_github_tool_registry.py`, `tests/mcp_servers/github/test_github_request_validation.py`) | Pending | — | — | REQ-002..REQ-005, REQ-009 |
| 3 | Migrate pull requests domain (`scripts/mcp_servers/github/github_models_pull_requests.py`, `scripts/mcp_servers/github/tools_pull_requests.py`, `tests/mcp_servers/github/test_github_tool_registry.py`, `tests/mcp_servers/github/test_github_request_validation.py`) | Pending | — | — | REQ-002..REQ-005, REQ-009 |
| 4 | Migrate file domain (`scripts/mcp_servers/github/github_models_file.py`, `scripts/mcp_servers/github/tools_file.py`, `tests/mcp_servers/github/test_github_tool_registry.py`, `tests/mcp_servers/github/test_github_request_validation.py`) | Pending | — | — | REQ-002..REQ-005, REQ-009 |
| 5 | Migrate repository domain (`scripts/mcp_servers/github/github_models_repository.py`, `scripts/mcp_servers/github/tools_repository.py`, `tests/mcp_servers/github/test_github_tool_registry.py`, `tests/mcp_servers/github/test_github_request_validation.py`) | Pending | — | — | REQ-002..REQ-005, REQ-009 |
| 6 | Runtime dispatch alignment + HTTP rejection tests (`scripts/mcp_servers/github/github_service_dispatch.py`, `scripts/mcp_servers/github/github_service_dispatch_writes.py`, `tests/mcp_servers/github/test_github_server_endpoints.py`) | Pending | — | — | REQ-008 |
| 7 | Configuration strictness + config tests (`scripts/mcp_servers/github/github_models_config.py`, `tests/mcp_servers/github/test_github_config_strict_parsing.py`) | Pending | — | — | REQ-006, REQ-007 |
| 8 | Documentation updates + full validation + deploy hand-off (`docs/22_mcp/mcp_04_01_web-search-file-read-github.md`, `docs/22_mcp/mcp_06_01_configuration-file-inventory.md`) | Pending | — | — | Deploy is the user's decision (approval gate) |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261119-140510_mcpai003_github-pydantic-schema-source.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261124-173306
- **Overlap check disposition (Step 8b)**: `tools/check_plan_target_overlaps.py` reported 5 findings, all between the pre-existing plans `plans/20261124-095950_cliplc004_bounded-shutdown-machine.md` and `plans/20261124-110935_cliplc005_staged-reload-transaction.md` (`docs/23_agent/agent_08_01_configuration-loading-agent-config.md`, `docs/23_agent/agent_14_reference-api-subpackages-generated.md`, `scripts/agent/config_builders.py`, `tests/agent/test_agent_factory.py`, `tests/agent/test_config_builders.py`). None involves any row of this Plan: `not affected: external overlap between other Plans, no shared target path with this Plan`.
- **Related target files**: `scripts/mcp_servers/request_contract.py`, `tests/mcp_servers/test_request_contract.py`, `scripts/mcp_servers/github/github_models_issues.py`, `scripts/mcp_servers/github/github_models_pull_requests.py`, `scripts/mcp_servers/github/github_models_file.py`, `scripts/mcp_servers/github/github_models_repository.py`, `scripts/mcp_servers/github/github_models_config.py`, `scripts/mcp_servers/github/tools_issues.py`, `scripts/mcp_servers/github/tools_pull_requests.py`, `scripts/mcp_servers/github/tools_repository.py`, `scripts/mcp_servers/github/tools_file.py`, `scripts/mcp_servers/github/github_service_dispatch.py`, `scripts/mcp_servers/github/github_service_dispatch_writes.py`, `tests/mcp_servers/github/test_github_tool_registry.py`, `tests/mcp_servers/github/test_github_request_validation.py`, `tests/mcp_servers/github/test_github_config_strict_parsing.py`, `tests/mcp_servers/github/test_github_server_endpoints.py`, `docs/22_mcp/mcp_04_01_web-search-file-read-github.md`, `docs/22_mcp/mcp_06_01_configuration-file-inventory.md`

### Requirement Traceability
See `templates/requirement-traceability.md` for the canonical column format.

| Requirement ID | Source Issue Section or Evidence | Target File | Implementation Step | Acceptance Criterion | Test or Validation Item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes bullets 1-2 | `scripts/mcp_servers/request_contract.py` | Phase 1 | AC-01, AC-02 | T-01 | Explicit in issue |
| REQ-002 | Required Changes bullet 1; Step 2 verification of manual dict schemas | `scripts/mcp_servers/github/tools_issues.py`, `tools_pull_requests.py`, `tools_repository.py`, `tools_file.py` | Phases 2-5 | AC-01, AC-02 | T-01, T-02 | Confirmed by repository evidence |
| REQ-003 | Problem; Step 2 verified `dry_run` drift (models vs schemas, agent extra-field gate) | `scripts/mcp_servers/github/tools_*.py`, `tests/mcp_servers/github/test_github_tool_registry.py` | Phases 2-5 | AC-01 | T-02 | Confirmed by repository evidence |
| REQ-004 | Required Changes bullet 4 | `scripts/mcp_servers/github/github_models_issues.py`, `github_models_pull_requests.py`, `github_models_file.py`, `github_models_repository.py` | Phases 2-5 | AC-04 | T-03 | Confirmed by repository evidence |
| REQ-005 | Required Changes bullet 5; Issue Unresolved Questions (values) | `scripts/mcp_servers/github/github_models_file.py`, `github_models_issues.py`, `github_models_pull_requests.py`, `github_models_repository.py` | Phases 2-5 | AC-04 | T-03 | Needs confirmation (values via UNK-02; existence of the gap confirmed) |
| REQ-006 | Problem (string `"false"` as true); Step 2 verified `bool()` residue at `github_models_config.py:66-67` and absence of the review's named fields | `scripts/mcp_servers/github/github_models_config.py` | Phase 7 | AC-04 | T-04 | Confirmed by repository evidence |
| REQ-007 | Required Changes bullet 7; Step 2 verified allowlist entries are format-unvalidated at startup | `scripts/mcp_servers/github/github_models_config.py` | Phase 7 | AC-04 | T-04 | Confirmed by repository evidence |
| REQ-008 | Constraints (unknown fields rejected); Step 2-3 verified dispatch key-picking and unregistered GitHub validators | `scripts/mcp_servers/github/github_service_dispatch.py`, `github_service_dispatch_writes.py` | Phase 6 | AC-03 | T-03, T-05 | Confirmed by repository evidence |
| REQ-009 | Acceptance Criteria bullet 5; Step 2 verified no model-to-schema test exists | `tests/mcp_servers/github/test_github_tool_registry.py` | Phases 2-5 | AC-05 | T-02 | Confirmed by repository evidence |
