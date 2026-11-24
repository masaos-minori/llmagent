## Goal
Create the single shared strict request contract for MCP server domains: `StrictRequestModel` (new)
(REQ-001, shared strict request base model) and `build_input_schema()` (REQ-002, deterministic
`inputSchema` generator that preserves validation keywords). Every GitHub model row (seq 03-06)
inherits the base; every GitHub tools row (seq 08-11) calls the generator.

## Scope
**Release unit**: N/A: not part of a release unit

- Creates `scripts/mcp_servers/request_contract.py` and nothing else.
- Holds no bound values: the numeric/text bounds live in the domain model rows.

## Assumptions
- Installed `pydantic` is 2.13.4. Verified output shape of `model_json_schema()` for a
  `extra="forbid"` model with a nested model: `$defs` + `$ref` (`#/$defs/PushFile`),
  `additionalProperties: false`, `min_length` -> `minLength`, `ge`/`le` -> `minimum`/`maximum`,
  list min_length/max_length -> minItems/maxItems, pattern and default carried, and a
  generated `title` key at the schema root, in every `$defs` entry, and in every property.
- Presentation-only noise in this pydantic version is exactly that generated `title` noise
  (REQ-002's "for example `$defs` root title noise"); `description` comes from
  `Field(description=...)` and is meaningful, so it is never stripped.
- UNK-01 (non-blocking, Plan Unknowns): `$defs`/`$ref` are kept unflattened per the Issue
  default; the agent forwards `inputSchema` unchanged and the configured llama.cpp
  `llama-server` provider resolves same-document `$ref`. A live `github_push_files` call remains
  the final provider-facing check (seq 11).

## Design decisions
- Public API is exactly two names: `StrictRequestModel` (new), a `BaseModel` subclass with
  `model_config = ConfigDict(extra="forbid")`, and `build_input_schema(model: type[BaseModel]) -> dict[str, Any]` (new).
- Dependency direction: the module imports only `pydantic` (plus `from __future__ import
  annotations` and `collections.abc` typing), so `.importlinter` `shared-is-leaf` and "No agent
  module imports MCP server config models" stay KEPT. GitHub code reaches it as
  `from mcp_servers.request_contract import ...`.
- Stripping rule is a single recursive pass that deletes the `title` key at the schema root, in
  every `$defs` entry, and in every nested sub-schema dict. No renaming,
  no sorting, no flattening, no injection of keywords the model did not declare.
- `properties`, `$defs`, and `patternProperties` are name-to-sub-schema maps, not schema nodes: the
  pass recurses into their values and never deletes one of their keys. A request model field named
  `title` (`CreateIssueRequest.title`, `CreatePullRequestRequest.title`) is a key of `properties`, so a
  pass that deleted `title` from every dict it descended into would remove that field from the
  published schema (Step 3a finding, verified against pydantic 2.13.4 output).
- The generator is a pure function: no module-level cache, no config access, no I/O, so two calls
  on the same model class return an equal dict (AC-02).

## Alternatives considered
- `scripts/shared/request_contract.py`: rejected in the Plan Design — `shared` is the leaf layer
  for cross-package utilities and MCP request-contract semantics belong to `mcp_servers`.
- Extending `scripts/mcp_servers/models.py`: rejected — that module holds the `/v1/*` wire models
  (`McpTool`, `CallToolRequest`); mixing contract generation into it couples wire transport with
  contract generation.
- Flattening `$defs`/`$ref` in the generator: rejected — the Issue mandates keeping them unless
  provider rejection is proven (UNK-01 resolution path).

## Implementation
### Target file
`scripts/mcp_servers/request_contract.py` (new)

### Procedure
1. Module header docstring stating the responsibility (shared strict request base model +
   deterministic `inputSchema` generator) and the dependency line "(external: pydantic only)".
2. Define `StrictRequestModel` (new) with `model_config = ConfigDict(extra="forbid")` and a docstring
   that points to `scripts/mcp_servers/models.py` lines 107 and 169 as the existing
   `extra="forbid"` precedent.
3. Define `build_input_schema` (new) as a function calling `model.model_json_schema()` once, then a private
   `_strip_presentation_fields(node)` helper that removes the `title` key from each schema node and
   recurses into its sub-schemas: dict values, the values of name-to-sub-schema maps, and dict items
   of lists.
4. Export both names in `__all__`.

### Method
- Recursion handles the container shapes pydantic emits: `properties`, `$defs`, and
  `patternProperties` maps, `items`/`additionalProperties` sub-schemas, and `anyOf`/`allOf`/`oneOf`
  lists of sub-schemas. Deleting `title` from every schema node, while treating the name-to-sub-schema
  maps as containers whose keys are field and definition names, keeps the rule version-independent
  instead of enumerating pydantic internals.
- Nothing else in the returned dict is touched, so a future pydantic that adds a validation keyword
  passes through without a code change (REQ-002 "preserving ... everything else").

### Details
- Signature: `def build_input_schema(model: type[BaseModel]) -> dict[str, Any]:`.
- `build_input_schema()` accepts any `BaseModel` (not only `StrictRequestModel` (new)) so response models
  and later domains can use it; strictness is the caller's choice of base class.
- Do not call model_json_schema(mode="validation"), do not pass ref_template, and do not set
  sort_dicts: the default output is declaration-ordered and byte-stable.

### Companion test files
- `tests/mcp_servers/test_request_contract.py` (new)
  - Procedure: unit tests per Plan T-01 — determinism across repeated calls and dict ordering, preservation of default, enum, pattern, minimum, maximum, minLength, maxLength, minItems, maxItems, `$defs`, `$ref`, additionalProperties, required, items, and stripping of every generated title key. Include a model whose field is named `title` and assert the field remains in `properties` with its bounds after stripping.
  - Validation: `uv run pytest tests/mcp_servers/test_request_contract.py` (T-01).

## Compatibility considerations
- No runtime behavior changes in this row: nothing imports the new module until seq 03-06 land
  (Plan Design reversibility note).
- `/v1/tools` payload changes begin at seq 08-11, not here.

## Security considerations
- No I/O, no config reads, no subprocesses; the module only shapes a dict.
- `extra="forbid"` is the mechanism that closes the Plan's "unknown arguments silently dropped"
  problem for every domain that inherits the base.

## Rollback considerations
- Revert the commit: the module has no callers until Phase 2 lands, so a revert is self-contained.

## Validation plan
- `uv run pytest tests/mcp_servers/test_request_contract.py` (T-01): deterministic output, all
  validation keywords preserved, `title` noise stripped.
- `uv run ruff check scripts/mcp_servers/request_contract.py`; `uv run mypy scripts/mcp_servers/request_contract.py`;
  `uv run lint-imports` (6 contracts KEPT baseline); `uv run python tools/check_module_size.py`.

## Completion criteria
- `StrictRequestModel` (new) and `build_input_schema()` exist with the documented signatures and are the
  module's only public API.
- T-01 passes, including a `$defs`/`$ref` case (a model with a nested model).
- `lint-imports` reports all contracts KEPT and the module imports no repository-local module.

## Out of Scope
- Bound values and model inheritance (seq 03-06), publishing generated schemas (seq 08-11),
  dispatch alignment (seq 12-13), configuration strictness (seq 07), documentation rows (seq 18-19).
- Reuse by File, CI/CD, Web Search, MDQ: owned by their own Issues (mcpai009, mcpci001, mcpws002,
  mdqmcp008).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement `scripts/mcp_servers/request_contract.py` per Procedure/Method/Details | Completed | 20261124-210654 | 20261124-210654 | REQ-001, REQ-002 Changed: scripts/mcp_servers/request_contract.py, tests/mcp_servers/test_request_contract.py. Step 3b correction: title-stripping pass must treat properties/$defs as name-to-sub-schema maps (a model field named title is a properties key). |
| 2 | Add companion tests `tests/mcp_servers/test_request_contract.py` (T-01) | Completed | 20261124-210654 | 20261124-210654 | 11 tests in tests/mcp_servers/test_request_contract.py pass (T-01). |
| 3 | Run the validation sequence (`rules/toolchain.md`) for this file | Completed | 20261124-225226 | 20261124-225226 | ruff, mypy, lint-imports, module size ruff format/check, mypy, lint-imports (6 KEPT), check_module_size, bandit pass; full-suite run is the end-of-batch run. End-of-batch run (rules/toolchain.md, Batch mode): full pytest 13959 passed / 5 skipped / 6 errors; all 6 errors are the pre-existing tests/tools/test_append_plan_work_items.py contract mismatch (issues/20261124-155017_qa001_append-plan-attr-mismatch.md), none in this batch's files. ruff format+check, mypy, lint-imports, check_module_size, bandit, check_docstrings (after adding the em-dash separator to scripts/mcp_servers/request_contract.py), and diff-cover --fail-under 90 Pass. pre-commit run --all-files fails only on 14 pre-existing procedure-length findings in implementations/20261124-122732_* (issues/20261124-155017_qa002_workitem-structure-unknowns-kind.md); check_workitem_structure --file on this batch's documents reports no findings. |
| 4 | Update documentation | Completed | 20261124-210654 | 20261124-210654 | N/A: documentation rows are seq 18-19 N/A: no docs/00_index.md task-scope row for this file; documentation is owned by seq 18-19. |

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
- **Requirement ID**: `REQ-001` (shared strict request base model), `REQ-002` (deterministic schema generator)
- **Source issue**: issues/20261119-140510_mcpai003_github-pydantic-schema-source.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-173306_mcpai003_github-pydantic-schema-source.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261124-181931
- **Related target files**: `scripts/mcp_servers/request_contract.py`, `tests/mcp_servers/test_request_contract.py`