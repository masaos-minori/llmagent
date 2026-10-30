# Implementation Procedure: `registry/component_mandatoriness.yaml`

## Goal

Create the machine-readable component-mandatoriness registry (REQ-002: new registry file with the issue-enumerated per-component fields) recording the currently approved classification — all 10 MCP servers `required` (plan A-1: records, not re-decides).

## Scope

- New YAML file at `registry/component_mandatoriness.yaml` (the plan's row path; `registry/` already exists as a directory created for adrcov001's `registry/manifests/`).
- One entry per approved server key from the `agent_08_04` classification table (`docs/23_agent/agent_08_04_configuration-mcp-approval-obs.md` :56-66): `shell`, `git`, `web_search`, `file_delete`, `file_write`, `file_read`, `github`, `cicd`, `rag_pipeline`, `mdq`.
- Content is static data authored in this procedure; drift against `agent_08_04` and `config/agent.toml` is enforced later by `tools/check_component_mandatoriness.py` (target row 8).

## Assumptions

- A-1 (plan): initial content equals the approved classification; no re-decision.
- The file layout below is this procedure's design; the plan fixes only the field list (REQ-002).
- Needs Confirmation (U-1, plan): final authority home once adrauth001 lands (`config/adr_authority.toml` vs `registry/`). Default: keep the file here; the loader reads one path constant, so relocation is a one-file change.

## Design decisions

- Top level: `version: 1` and `entries:` list; each entry carries exactly the REQ-002 fields plus a `rationale` string so the `agent_08_04` table (Server | Classification | Rationale) can later be rendered losslessly from the registry (target row 26).
- Field vocabulary (entry keys): `component_id` (new), `classification` (`required` | `non_required` (new)), `failure_category` (new) (`safety-integrity` | `availability`), `safety_role` (new) (free text), `safely_disableable_functions` (new) (list, empty while unassessed), `startup_consequence` (new) (`abort_startup` (new)), `observability` (list), `owner`, `authority_adr` (new), `rationale`.
- `owner` value: the classification table records no owner today; use `agent-architecture-owner` as the placeholder. Needs Confirmation: the human/role name the owner field should carry (plan A-2 leaves authority unsettled until adrauth001).

## Alternatives considered

- TOML instead of YAML — rejected: the plan's row names a `.yaml` file and PyYAML `>=6.0` is already a dependency (plan A-3).
- Encoding the classification inside `config/agent.toml` — rejected: config must stay the effective-value side of the contract (ADR-004 Group 3 item 13); the registry must be independent of the thing it validates.

## Implementation

### Target file

`registry/component_mandatoriness.yaml` (new)

### Procedure

1. Author the header (`version`, a one-line purpose comment naming ADR-004 Group 3 item 13 as the criteria source and `agent_08_04` as the derived table).
2. Write 10 entries, one per approved server key, each carrying the REQ-002 fields.
3. Per-entry values derived from `agent_08_04` and ADR-004: `classification: required`; `failure_category: safety-integrity` for posture-failure handling as decided by `scripts/agent/services/mcp_health.py` `_is_fatal_gate` (:139-147); `startup_consequence: abort_startup`; `safely_disableable_functions: []` (unassessed today — the table says "Not assessed as satisfying Decision Group 3 item 10"); `observability: ["ServiceWarning", "pipeline fatal outcome"]` mirroring REQ-008; `authority_adr: ADR-004`; `rationale` exactly the table's rationale text.

### Method

Hand-authored static YAML (no generator in this row; generation/drift checking are rows 9 and 8). Keep the file parseable by PyYAML `safe_load`.

### Details

- Entry order: alphabetical by `component_id` (new) so generated tables are diff-stable.
- Do not copy ADR-004's mandatory/non-mandatory criteria text into the file (plan Constraint: no competing copy); reference it via `authority_adr` (new) only.
- `failure_category` (new) per entry: all 10 share the same value under current behavior (safety/integrity posture failures are fatal regardless of `required`); record `safety-integrity` and leave room for future per-component values. Needs Confirmation: whether `failure_category` (new) should instead record the failure class the component's own failure produces (posture `FAILED` is safety/integrity per ADR-004 Group 3 item 9's context, `:82` note).

## Compatibility considerations

- New file; no consumer exists until target row 2 (loader) lands. Existing startup behavior is unchanged by this row alone.
- Cross-plan note: adrcov001's `registry/manifests/` manifests (U-2 of that plan) may reference this file; placement coexistence is recorded in the plan Dependencies (this plan blocks adrcov001's component-mandatoriness manifest).

## Security considerations

- The registry is a fail-closed contract input: consumers must treat a missing or malformed file as fatal (loader row 2), never as "no classifications".

## Rollback considerations

- Revert the commit; nothing else consumes the file yet.

## Validation plan

- `uv run python -c "import yaml,pathlib; yaml.safe_load(pathlib.Path('registry/component_mandatoriness.yaml').read_text())"` parses.
- After rows 2 and 8 land: `uv run pytest tests/shared/test_component_mandatoriness.py` and `uv run python tools/check_component_mandatoriness.py` exit 0.

## Completion criteria

- The file parses, lists exactly the 10 approved servers, every entry has all REQ-002 fields populated, and all 10 carry `classification: required` (plan AC-2 precondition).

## Out of Scope

- Validation code, loader, drift checker, generated docs (rows 2, 8, 9, 26).
- Any change to which components are mandatory (plan Out-of-Scope).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Author the 10-entry registry file per Procedure/Details | Pending | — | — | |
| 2 | No new tests in this row; validation is the parse check (tests arrive with rows 2/8/10) | Pending | — | — | |
| 3 | Run YAML parse check; later `tools/check_component_mandatoriness.py` | Pending | — | — | |
| 4 | N/A: no separate documentation change in this row | — | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

#### Marker edit record
- `(new)` マーカー編集（この doc が導入する新規コンポーネント）は `tools/mark_new_115752.py`（冪等）に記録済み。

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-002 (machine-readable component-mandatoriness registry with issue-enumerated fields)
- **Source issue**: `issues/20261029-104502_mcpgate001_mcp-mandatory-construction-contracts.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261030-001153_mcpgate001_mcp-mandatory-construction-contracts.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-115752
- **Related target files**: `registry/component_mandatoriness.yaml` (new)
