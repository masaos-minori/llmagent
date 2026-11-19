## Goal

Correct `registry/component_mandatoriness.yaml`: state the derivation in one direction (the
registry is the machine-readable source; the `agent_08_04` table is generated from it —
ADR-004 Decision Group 3 item 13), replace the stale `adrauth001 (U-1)` pending note with
citations of the new governance_03 ledger IDs, and fix the factually wrong `rag_pipeline`
`safety_role` (REQ-001, REQ-002).

## Scope
**Release unit**: mandatoriness-registry-refresh

## Assumptions

- The header rewrite states the current contract only (Plan Design decision 5,
  Current-Specification-Only): no "formerly derived from" history wording.
- `safety_role` text is derived only from the server's published tool set
  (`scripts/mcp_servers/rag_pipeline/rag_pipeline_tools.py` TOOL_LIST: `rag_run_pipeline`,
  `rag_debug_pipeline`, `rag_list_documents`, `rag_delete_document` — no ingestion tool), not
  from an invented rationale (Plan Assumption A-2).

## Design decisions

- The header cites governance_03 ledger IDs instead of carrying an untracked "pending" note
  (Plan Design decision 1); the cited entries are created by sibling procedure
  `implementations/20261120-043919_01_docs_00_governance_governance_03_issue-and-uncertainty-management.md.md`
  (Plan Phase 1 precedes this phase, so the IDs exist when this edit lands).
- Only the header comment block and one `safety_role` line change; all `classification`,
  `failure_category`, `rationale`, and the other 9 entries stay byte-identical (Plan AC-02).

## Alternatives considered

- N/A: the Plan fixed the direction fix as header-text-only; restructuring the registry file
  would touch loader-consumed structure (`scripts/shared/component_mandatoriness.py`) for no
  benefit.

## Implementation
### Target file
`registry/component_mandatoriness.yaml`

### Procedure
1. Rewrite the header comment block (lines 1–7): keep the registry identity sentences and the
   `config/agent.toml` validation sentence; state that `agent_08_04`'s table is generated from
   this registry (ADR-004 Decision Group 3 item 13); delete the "Derived from the table in
   docs/23_agent/..." sentence (line 3) and the whole "Authority/placement reconciliation
   pending adrauth001 (U-1); loader reads one path constant, so relocation is a one-file
   change" note (lines 6–7); add one sentence citing Known Issues MCP-003 and MCP-004 in
   `docs/00_governance/governance_03_issue-and-uncertainty-management.md` as the tracked
   pending items.
2. Replace the `rag_pipeline` `safety_role` value at line 97.

### Method
- New `safety_role` value (single line, same style as sibling entries):
  `RAG retrieval pipeline execution, debug, and document listing/deletion; fail-closed prevents retrieval work on posture failure.`
- Do not touch the `version: 1` key, `entries:` structure, or any entry field other than the
  one `safety_role`.

### Details
- `docs/23_agent/agent_08_04_configuration-mcp-approval-obs.md:57` and the canonical-source row
  `config/documentation_canonical_sources.toml:66-71` already state the registry-as-source
  direction; the header must agree with them (ADR-004 line 81).
- `tools/check_component_mandatoriness.py` compares classification and rationale across
  registry/table/config only — a header-comment or `safety_role` edit cannot break its
  three-way comparison, and `docs/23_agent/agent_08_04_configuration-mcp-approval-obs.md`'s
  table renders only Server/Classification/Rationale, so it stays byte-identical (Plan Design
  decision 4).

## Compatibility considerations

- The manifest `registry/manifests/component_mandatoriness.yaml` mirrors `safety_role`
  (`tools/generate_reference_table.py:955-956`): it must be regenerated in the same commit — sibling procedure
  `implementations/20261120-043919_03_registry_manifests_component_mandatoriness.yaml.md`
  (release unit mandatoriness-registry-refresh).
- The startup loader (`scripts/shared/component_mandatoriness.py`) reads entries only; comments
  are not parsed.

## Security considerations

- No classification value changes: fail-fast/fail-closed behavior of every server is unchanged
  (Plan Out-of-Scope; ADR-004 item 13 reserves classification changes to approved changes).

## Rollback considerations

- Revert the commit together with the manifest regeneration (same release unit); a header-only
  revert has no runtime effect.

## Validation plan

- `uv run python tools/check_component_mandatoriness.py` exit 0 (AC-01).
- `rg "Derived from" registry/component_mandatoriness.yaml` returns nothing; `rg "adrauth001"
  registry/component_mandatoriness.yaml` returns nothing (AC-01).
- Diff review: only the header comment lines and the one `safety_role` line changed;
  `classification`/`failure_category`/`rationale` untouched for all 10 entries (AC-02).
- `uv run python tools/generate_reference_table.py --manifests --type mandatoriness` then
  `--check` exit 0 (shared with the manifest sibling; unit gate).

## Completion criteria

- The header states the single source direction citing ADR-004 Group 3 item 13 and cites
  MCP-003/MCP-004; `rag_pipeline` `safety_role` names retrieval/list/delete functions with no
  "ingestion" or "index corruption" wording; every other field byte-identical; the consistency
  checker and drift gate exit 0 (Plan AC-01, AC-02).

## Out of Scope

- Any `classification`, `failure_category`, or `rationale` change (proposal tracked as MCP-003).
- `docs/23_agent/agent_08_04_configuration-mcp-approval-obs.md` (Reference File; regenerated
  content only, must stay byte-identical).
- `config/agent.toml` `required` values (already consistent with the registry).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Rewrite header comment block and `rag_pipeline` safety_role per Procedure | Pending | — | — | Land with the manifest regeneration (release unit) |
| 2 | Run check_component_mandatoriness + regeneration/drift gate (with sibling 03) | Pending | — | — | |

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
- **Requirement ID**: `REQ-001` (single-direction derivation header), `REQ-002` (rag_pipeline safety_role correction)
- **Source issue**: issues/20261117-123020_adrchk020_mandatoriness-registry-posture.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261120-001311_adrchk020_mandatoriness-registry-posture.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261120-043919
- **Related target files**: `registry/component_mandatoriness.yaml`
