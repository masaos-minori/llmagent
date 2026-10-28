# Procedure: enforce the four-field presence contract and reject the legacy singular `resource_scope` in the validator

## Goal

Make `validate_tool_schema_v2()` in `scripts/shared/resource_scope.py` the single owner of the
schema-2.0 entry contract: enforce presence of all four mandatory fields, reject an entry carrying
the legacy singular `resource_scope` key (owner-approved policy, Plan Decision record 2026-10-28),
and make the docstring match the behavior (Plan REQ-002, REQ-004; AC-2, AC-4).

## Scope

- Modify only `scripts/shared/resource_scope.py`.
- In scope: the presence checks for `resource_scope_kind` and `resource_scope_keys`, the legacy
  `resource_scope` rejection, the docstring, and a small helper to keep cyclomatic complexity
  bounded (validator is currently rated C (17) by `radon cc`).
- Out of scope: known scope-kind vocabulary (`_KNOWN_SCOPE_KINDS`), scope-conflict logic
  (`_scopes_conflict`, `resolve_resource_scopes`), the fetch layer (procedure 02), tests
  (procedures 03, 04), the document (procedure 05).

## Assumptions

- The owner-approved policy is explicit rejection of the legacy singular `resource_scope`
  (Plan `Decision record`; UNK-01/UNK-02 resolved 2026-10-28).
- All in-tree tool lists carry the four fields and no legacy key (Plan Background: runtime check
  of 56 entries; contract test covers the two environment-dependent modules).
- Empty values (`""`, `[]`) stay valid; only presence of the keys is enforced.

## Design decisions

- Presence enforcement replaces the `.get(key, default)` reads: a missing key produces a
  "is required" problem string, mirroring the existing `is_write` / `requires_serial` wording
  ("X is required") so one wording style covers all four fields (Plan Design: finding wording
  follows the validator's wording).
- The kind/keys/legacy checks move into one small helper `_scope_problems()` (new) so
  `validate_tool_schema_v2` complexity does not grow beyond C (17) (Plan Implementation Intent).
- Legacy rejection lives in the validator, not the fetch layer (Plan Design decision: one module
  owns the entry contract; validator-only callers such as the contract test must be protected).

## Alternatives considered

- Reject the legacy key in the fetch layer only — rejected by the Plan (leaves validator-only
  callers unprotected).
- Keep `.get` defaults and document presence as the caller's responsibility — rejected by the
  Plan (validator docstring says it never coerces or defaults).
- Ignore-and-document policy — rejected by the owner on 2026-10-28.

## Implementation

### Target file

`scripts/shared/resource_scope.py`

### Procedure

1. Add module-level helper `_scope_problems()` (new) next to the validator: takes the raw entry
   and the resolved `inputSchema.properties` dict (or `None`) and returns a `list[str]`:
   - `if "resource_scope" in entry:` report `legacy singular resource_scope is not supported;
     use resource_scope_kind and resource_scope_keys` (exact finding wording is free; it must
     contain the literal `resource_scope` so the discovery test assertions match).
   - `if "resource_scope_kind" not in entry:` report `resource_scope_kind is required`;
     otherwise keep today's unknown-kind check (`unknown resource_scope_kind: <repr>`).
   - `if "resource_scope_keys" not in entry:` report `resource_scope_keys is required`;
     otherwise keep today's `list[str]` type check and the
     `inputSchema.properties` membership check.
2. In `validate_tool_schema_v2()`, replace the current kind block (lines 161-163) and keys block
   (lines 165-175) with `problems.extend(_scope_problems(entry, properties))`.
3. Update the docstring: state that all four fields (`is_write`, `requires_serial`,
   `resource_scope_kind`, `resource_scope_keys`) must be present, that empty values are valid,
   and that an entry carrying the legacy singular `resource_scope` key is rejected.
4. Do not touch `_KNOWN_SCOPE_KINDS`, `resolve_resource_scopes()`, `scopes_conflict()`, or the
   fail-closed fallback constant.

### Method

Direct edit of the existing validator body; the helper is a pure function returning strings, no
new imports, no public API change (`validate_tool_schema_v2` signature and return shape
unchanged).

### Details

- Current behavior to change: `entry.get("resource_scope_kind", "")` makes a missing key valid
  because `""` is a known kind, and `entry.get("resource_scope_keys", [])` makes a missing key
  valid — both contradict the "never coerces or defaults" docstring (lines 130-132).
- `mcp_tool_discovery_registry.py` reads `entry["resource_scope_kind"]` etc. directly after
  validation (lines 86-89) and stays correct because the validator now guarantees presence; no
  change there (reference file only).
- `_entry_optional_field_error()` in the fetch layer (which validates `status`/`enabled`/
  `capabilities`) is not affected: the legacy key is now rejected earlier, in the schema step.

## Compatibility considerations

- Callers of `validate_tool_schema_v2()`: `scripts/agent/services/mcp_tool_discovery_fetch.py`
  (its own presence pre-check is removed by procedure 02) and tests. No other production caller
  exists (verified by grep on 2026-10-28).
- Sequencing: apply this procedure together with procedures 02-04 in one commit; between this
  change and procedure 02 the fetch layer still pre-rejects missing fields, so partial
  application does not corrupt findings, but procedure 04's rewritten legacy test only passes
  after step 1 of this procedure.
- External MCP servers that emit a legacy `resource_scope` key will have the affected tool
  excluded with a per-entry finding; the owner accepted this risk in the Plan Decision record.

## Security considerations

No new attack surface: this is a stricter validation (fail-closed) of tool declarations. The
legacy rejection prevents a server from sneaking an ambiguous scope declaration that the registry
would ignore.

## Rollback considerations

Single-file change; revert the commit. The helper has no state and no callers outside this file,
so no migration or data rollback is needed.

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| Unit | `uv run pytest tests/shared/test_resource_scope.py tests/mcp_servers/test_tool_schema_contract.py -v` | Pass; missing fields rejected; empty values accepted |
| Static | `uv run mypy --no-namespace-packages scripts/`; `PYTHONPATH=scripts uv run lint-imports`; `uv run ruff check scripts/shared/resource_scope.py`; `uv run bandit -r scripts/shared/resource_scope.py -c pyproject.toml -ll` | No new finding; six import contracts kept |
| Complexity | `uv run radon cc scripts/shared/resource_scope.py -s` | `validate_tool_schema_v2` rating not worse than C (17); `_scope_problems` (new) small (B or lower) |

## Completion criteria

- AC-2: entry lacking `resource_scope_kind` or `resource_scope_keys` reports that field as
  required; `""`/`[]` entry still valid; docstring and implementation agree.
- AC-4: entry carrying a singular `resource_scope` is reported as invalid.
- AC-5: validator and contract tests pass (tests added by procedure 03).
- AC-7: static checks and complexity constraint pass.

## Out of Scope

- The fetch-layer pre-check removal (procedure 02).
- Test additions and rewrites (procedures 03, 04).
- The tool-registry document sentence (procedure 05).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261028-110758 | 20261028-110758 | Changed: scripts/shared/resource_scope.py (helpers _scope_keys_problems, _scope_problems (new)); stale check clean; ruff/mypy/lint-imports/bandit pass; radon: validator B(10), _scope_problems A(4) |
| 2 | Add or update tests per Validation plan | Completed | 20261028-110758 | 20261028-111618 | Tests owned by procedures 03/04; targeted 40 passed; full suite: 1 failure owned by procedure 04 (legacy test), re-run after 04 full suite 10265 passed |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261028-110758 | 20261028-111618 | Static validators passed; full-suite run pending joint application with 04 joint full-suite run after procedures 01-05 applied: 10265 passed, 8 skipped; diff-cover 95% |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261028-111618 | 20261028-111618 | N/A: no docs/00_index.md mapping needed; docs handled by procedure 05 |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-002, REQ-004 (AC-2, AC-4)
- **Source issue**: issues/20261027-104324_mcpcompat003_align-legacy-resource-scope.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261027-111522_mcpcompat003_align-legacy-resource-scope.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261028-065435
- **Related target files**: scripts/shared/resource_scope.py