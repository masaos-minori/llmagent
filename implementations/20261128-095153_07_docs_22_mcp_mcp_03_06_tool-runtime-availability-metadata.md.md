## Goal

Define the production-status criteria and the process for changing a tool's status in `docs/22_mcp/mcp_03_06_tool-runtime-availability-metadata.md`, and record the `disabled_reason` fallback semantics, so the production claim for mdq-mcp has a documented basis (`REQ-002`, `REQ-005`; `AC-2`, `AC-5`).

## Scope
**Release unit**: N/A: not part of a release unit

- Documentation-only change in one document: two new sections and one paragraph recording the fallback, plus one entry in the front matter `related:` list.
- No runtime code, no schema, and no status value changes.

## Assumptions

- `status` has no closed vocabulary: `McpTool.status` is `Required[str]` (`scripts/mcp_servers/models.py:244`) and `validate_tool_schema_v2()` validates the tier, side-effect, retry, reconciliation, and preview vocabularies only (`scripts/shared/resource_scope.py:248`). The document records this gap; adding a required value is the contract owner's decision (`UNK-04`) and is not this row.
- The fallback is existing behavior, not a claim to change: `diagnostics()` falls back to the status string when no policy reason exists (`scripts/shared/runtime_tool_registry.py:342-353`), which is why the 7 MDQ entries report `enabled=False` with `disabled_reason="production"`. Two pinned tests hold that behavior (`tests/shared/test_runtime_tool_registry.py:294`, `tests/shared/test_tool_routing_validation.py:203`), so the plan documents the semantics rather than changing them (`UNK-06`).
- The per-area evidence for the criteria is named in `docs/22_mcp/mcp_04_04_mdq.md`; this document states the criteria and points there, so the same file list is not written twice.
- The status-change process is the plan default (`UNK-03`): the owner must confirm the process before any tool's status changes, so the section states a process, not an approval of any change.

## Design decisions

- State criteria as measurable conditions with a satisfied-or-unmeasured outcome, so a criterion that cannot be measured today, such as recovery, is recorded as unmeasured with the reason instead of reading as satisfied.
- Add unnumbered headings rather than renumbering sections 1-5, because the existing numbering is referenced by the body text ("section 3 above").
- Keep the criteria dimension list closed to the five the plan names (integrity, security, observability, performance, recovery), so the criteria section and the per-server section cannot drift into different sets.

## Alternatives considered

- Add a `status` vocabulary to `validate_tool_schema_v2()`: rejected here, it changes the schema-2.1 contract and needs the contract owner (`UNK-04`).
- Change the fallback so `disabled_reason` stops reporting the status string: rejected here, it is a runtime behavior change that would flip two pinned tests (`UNK-06`).

## Implementation
### Target file
`docs/22_mcp/mcp_03_06_tool-runtime-availability-metadata.md`

### Procedure
1. Add a `## Production status criteria` section after `## Standard disabled_reason values`, with one bullet per dimension stating the measurable condition, the evidence kind, and whether it is satisfied or unmeasured with the reason.
2. Add a `## Status change process` section after the criteria section, stating who decides a change, what evidence a change requires, and that a status value does not change until the performance thresholds are agreed.
3. Record the fallback in the section that defines `disabled_reason`: when no policy reason exists, the reason is the status string, so a `production` tool can appear as `enabled=False` with `disabled_reason="production"`; name the two tests that pin it.
4. Add `mcp_04_04_mdq.md` to the front matter `related:` list, since the criteria section cross-references the per-server section.

### Method

- Write the criteria so each one is verifiable by an existing contract module or is explicitly recorded as unmeasured with the reason, which is what `AC-2` checks and `AC-5` requires for the fallback paragraph.
- Do not restate the fence statement or the measured scale here; those belong to `docs/22_mcp/mcp_04_04_mdq.md`, so the cross-reference is a link, not a copy of the claim.

### Details

- Criteria shape to record: integrity, security, and observability are satisfied by the contract modules named in the per-server section; performance is unmeasured because no p50/p95/p99 threshold is agreed (`UNK-02`); recovery is unmeasured because the mdq store is not a recovery-drill domain (`scripts/db/recovery_drill.py` `DOMAINS`, `UNK-05`).
- Process wording: a status change requires a satisfied criterion plus the measurement that justifies it, is recorded in the per-server catalog section, and is reported as a documentation change rather than as a runtime flag.

## Compatibility considerations

- Existing per-server documents that already state `status` values are unaffected; the criteria section adds a basis for the claim without changing any declared value.
- The pinned tests named in the fallback paragraph keep passing, which is what confirms the paragraph describes current behavior rather than a planned change.
- `tools/check_docs_content_policy.py` must stay clean, so the criteria are prose conditions with cross-references, not a per-file mapping table.

## Security considerations

- `N/A: documentation text only.` The security dimension is recorded as satisfied by an existing contract module; no new security mandate is introduced.

## Rollback considerations

- `N/A: revert the commit.`

## Validation plan

- `uv run python tools/check_docs_content_policy.py` (`--strict` in CI)
- `uv run python tools/check_docs_structure.py`
- `uv run python tools/generate_reference_table.py --check`
- `uv run python tools/check_docs_quality.py`
- `uv run python tools/check_docs_consistency.py --domain mcp` — the recorded fallback must match `scripts/shared/runtime_tool_registry.py` (`AC-5`)

## Completion criteria

- The document defines the criteria and the status-change process, and each criterion is satisfied by named evidence or recorded as unmeasured with the reason (`AC-2`).
- The `enabled`/`disabled_reason` divergence for the MDQ tools is explained by the documented fallback (`AC-5`).
- No tool's `status` value is changed by this row, and no status value is justified by an unmeasured criterion.
- The documentation checkers above report no finding.

## Out of Scope

- The fence decision and the measured scale (`docs/22_mcp/mcp_04_04_mdq.md`, row 06).
- Any change to `validate_tool_schema_v2()` or to `diagnostics()`, and any change of a declared `status` value.
- `docs/00_governance/governance_03_issue-and-uncertainty-management.md`, which is not a target of this row.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Plan Phase 7 |
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
- **Requirement ID**: REQ-002 (measurable production criteria and the status-change process), REQ-005 (documentation records the fallback semantics), AC-2, AC-5
- **Source issue**: `issues/20261119-142132_mdqmcp010_mdq-release-readiness.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261127-203046_mdqmcp010_mdq-release-readiness.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261128-095153
- **Related target files**: `docs/22_mcp/mcp_03_06_tool-runtime-availability-metadata.md`
