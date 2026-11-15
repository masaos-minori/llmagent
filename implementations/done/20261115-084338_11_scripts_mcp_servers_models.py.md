## Goal

Verify that `/v1/call_tool` handlers reuse only the shared models in `models.py`, and confirm direct-route request/response models are NOT in this file (they live in per-domain `*_models.py` and stay). No deletion required. (`REQ-005`)

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- `CallToolRequest`/`CallToolResponse`/`McpTool`/`McpToolProperty` are the only models in `models.py`; they are shared across apps and stay.
- Route-specific models (`ShellRunRequest`, `WriteFileRequest`, `GetFileContentsResponse`, GitHub route models, etc.) live in per-domain `*_models.py` (`shell/shell_models.py`, `file/{read,write}_models.py`, `github/github_models*.py`) and are consumed by the service/dispatch path, so they are correctly retained here.

## Design decisions
- This row is verification-only: confirm the model layout rather than delete anything. Deletion of any model is gated by AC-7 (confirm `/v1/call_tool` handlers do not reuse it) and is out of scope unless the verification discovers an unreused shared model.

## Alternatives considered
- Deleting route-specific models from `models.py`: not applicable — they are not in this file.
- Deleting shared models (`CallToolRequest`/`CallToolResponse`): rejected — `/v1/call_tool` handlers import them.

## Implementation
### Target file
`scripts/mcp_servers/models.py`

### Procedure
1. Confirm `models.py` contains only the shared models: `CallToolRequest` (line 15), `CallToolResponse` (line 40), `McpTool` (line 51), `McpToolProperty` (line 65).
2. Confirm each `/v1/call_tool` handler in every app imports these shared models and builds its own route-specific request models from the per-domain `*_models.py` modules (rather than importing route models into `models.py`).
3. If verification finds a model in `models.py` that no `/v1/call_tool` handler reuses, report it as a Plan Gap (deletion is AC-7-gated and out of scope for this verify row); otherwise record that the model layout is correct and no change is made.

### Method
- `grep -n "class .*(" scripts/mcp_servers/models.py` to enumerate the models present.
- `rg -n "from mcp_servers.models import" scripts/mcp_servers` to confirm which names are consumed app-wide.
- Cross-check that route-specific names resolve to per-domain `*_models.py` modules, not `models.py`.

### Details
- This is a no-op verification when the current layout holds; the generated document records the confirmation for AC-7 rather than editing the file.

## Compatibility considerations
N/A: no code change when the layout is confirmed (this is a verify row).

## Security considerations
N/A: no code change.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- mypy/ruff pass confirms no stray or unused shared-model import.
- The route-inventory and `/v1/call_tool` tests still pass (shared models intact).

## Completion criteria
- Confirmed `models.py` holds only the shared models and that route-specific models live in per-domain `*_models.py`; no deletion required, or a discovered unreused shared model is escalated as a Plan Gap for AC-7.

## Out of Scope
- Deleting shared models used by `/v1/call_tool`.
- Deleting route-specific models (they are not in this file; AC-7 governs any deletion).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261115-122517 | 20261115-122517 |  |
| 2 | Add or update tests per Validation plan | Completed | 20261115-122517 | 20261115-122517 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261115-122517 | 20261115-122517 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261115-122517 | 20261115-122517 | STEP:4:N/A verify-only row; model layout confirmed correct, no deletion (AC-7 governs any future deletion) |

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
- **Requirement ID**: `REQ-005` — confirm vs. remove direct-route request/response models not reused by `/v1/call_tool`
- **Source issue**: `issues/20261111-163724_mcproute001_remove-direct-mcp-routes.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261115-045455_mcproute001_remove-direct-mcp-routes.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261115-084338
- **Related target files**: `scripts/mcp_servers/models.py`