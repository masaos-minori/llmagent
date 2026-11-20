## Goal

Regenerate `registry/manifests/config_ownership.yaml` via the reference-table generator so it picks up the new `tool_policy_mode` field ownership (`REQ-008`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- `tools/generate_reference_table.py --manifests` derives ownership from source and writes `registry/manifests/config_ownership.yaml`; it currently includes `allowed_tools` but not `tool_policy_mode`, which the regeneration adds.
- No hand-editing between the generator's guard comments.

## Design decisions
- Run the generator rather than editing the YAML by hand, matching the plan's "regenerate" instruction and keeping the file deterministic.

## Alternatives considered
- Hand-adding a `tool_policy_mode` row to the YAML: rejected because the file is generated and must stay in sync with the generator.

## Implementation
### Target file
`registry/manifests/config_ownership.yaml`

### Procedure
Run `python tools/generate_reference_table.py --manifests` to rewrite the ownership manifests.

### Method
Deterministic generation from source; verify `tool_policy_mode` now appears alongside `allowed_tools`.

### Details
- Confirm the regenerated file lists `tool_policy_mode` under the `[tool]` section ownership table.

## Compatibility considerations
Purely a regenerated reference; no runtime impact.

## Security considerations
No security impact: the manifest documents ownership, not enforcement.

## Rollback considerations
N/A: revert the commit.

## Validation plan
Run the doc/reference checker named in `routing.md` after regeneration; confirm `tool_policy_mode` is present.

## Completion criteria
`config_ownership.yaml` is regenerated and includes `tool_policy_mode`; the reference-table check passes.

## Out of Scope
The `tool_policy_mode` field definition (`config_dataclasses.py`) that the manifest describes.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261120-184830 | 20261120-184830 | Regeneration already reflected upstream: `registry/manifests/config_ownership.yaml` already lists `tool_policy_mode` under `[tool]` ownership (line 142), alongside `allowed_tools`/`disabled_tools`. No hand-edit needed. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261120-184830 | 20261120-184830 | `tools/generate_reference_table.py --check` -> "No drift found" (exit 0): committed manifest and all doc-backed blocks are in sync with live sources, including `tool_policy_mode`. |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-008`
- **Source issue**: `issues/20261120-114209_agentcfg001_tool-policy-mode.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261120-123941_agentcfg001_tool-policy-mode.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261120-132256
- **Related target files**: `registry/manifests/config_ownership.yaml`
