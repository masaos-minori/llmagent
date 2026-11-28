## Goal

Record the store-kind scope identity rule in the dispatch-and-routing document, so the two places that state the global-write fallback do not contradict the resolver's store-kind branch (`REQ-006`, `AC-6`, `REQ-002`, `AC-3`).

## Scope
**Release unit**: N/A: not part of a release unit

- The `is_write` bullet in "### Fields used by the DAG scheduler" (line 122) gains the store-kind exception.
- The `Overlapping resource_scopes` row of the "### Key distinction" table (line 171) gains the same exception, so both statements agree.

## Assumptions

- The rule is defined by kind, not by server, so the document states it for store kinds generally; the RAG store-kind write is included, which is the consequence recorded as Plan UNK-04 and confirmed with the scheduler owner before merging.
- The fail-closed statement for a key-declaring write that resolves nothing stays, since the resolver keeps that behavior (`scripts/shared/resource_scope.py:132-134`).
- Reads stay outside the conflict graph, as the document already states, so the store identity affects only write calls.
- Content policy: the document already names `shared/resource_scope.py` functions; the added sentences state a rule, not an implementation-location mapping, so no new symbol index or file tree is introduced.

## Design decisions

- State the exception in both places where the fallback is stated. A reader who reads only the conflict table would otherwise take the global fallback as the rule for every unkeyed write.
- Keep the wording in the form `<kind>:<identity>`, the convention the document already uses for scope strings.

## Alternatives considered

- State the exception only in the field list: rejected, the table repeats the rule and would then be incomplete.

## Implementation
### Target file
`docs/22_mcp/mcp_03_01_dispatch-and-routing.md`

### Procedure
1. In the `is_write` bullet, add: a store-kind write that declares no keys resolves to the store identity `<kind>:<server_key>` instead of the synthetic `global:write` scope.
2. Add the same exception to the conflict-row wording in the Key distinction table.
3. Keep the existing clauses about composed GitHub identities and reads.

### Method

- Both edits are single sentences inside existing bullets; no new section and no new heading is added.

### Details

- The table row keeps its "unscoped writes use synthetic `global:write`" clause qualified by the store-kind exception, so the two statements read as one rule with one exception.

## Compatibility considerations

- `tools/check_docs_consistency.py --domain mcp` and `tools/generate_reference_table.py --check` run against this document; the added rule must match `scripts/shared/resource_scope.py` after row 05 lands, so the document is updated in the same change as the resolver.

## Security considerations

- `N/A: documentation only.`

## Rollback considerations

- `N/A: revert the commit.`

## Validation plan

- `uv run python tools/check_docs_content_policy.py`
- `uv run python tools/check_docs_structure.py docs/22_mcp/mcp_03_01_dispatch-and-routing.md`
- `uv run python tools/check_docs_quality.py`
- `uv run python tools/check_docs_consistency.py --domain mcp`
- `uv run python tools/generate_reference_table.py --check`

## Completion criteria

- Both places that state the global-write fallback record the store-kind exception, and the document passes the docs content-policy gate (`AC-6`).

## Out of Scope

- The resolver branch itself (`scripts/shared/resource_scope.py`, row 05).
- The MDQ tool declarations (`scripts/mcp_servers/mdq/mdq_tools.py`, row 02).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Plan Phase 5 |
| 2 | Run the documentation checkers named in `rules/tool-gates.md` | Pending | — | — | The "Add or update tests" step does not apply to a docs-only row |

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
- **Requirement ID**: REQ-006, REQ-002, AC-6, AC-3
- **Source issue**: `issues/20261119-142130_mdqmcp008_mdq-schema-scope-consistency.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261127-184702_mdqmcp008_mdq-schema-scope-consistency.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261128-084218
- **Related target files**: `docs/22_mcp/mcp_03_01_dispatch-and-routing.md`
