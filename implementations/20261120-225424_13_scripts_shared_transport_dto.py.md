## Goal

Define the immutable `ToolExecutionContext` in the shared leaf layer and carry it on `ToolCallResult` for downstream consumers (`REQ-002` execution context, AC-2).

## Scope
**Release unit**: contract-chain

## Assumptions
- `shared` is a leaf under the `.importlinter` contracts, so the context must be plain str/dict/hash data with no agent imports (Plan Assumption).
- Row 1 constructs the context; this document defines it.

## Design decisions
- Add `ToolExecutionContext` (new) as a frozen dataclass: `call_id: str` (uuid7 logical id), `tool: str`, `args_hash: str`, `operation: str`.
- Add a `context: ToolExecutionContext | None = None` field to `ToolCallResult` (:26-42) so the transport/executor chain returns the identity it executed with; default `None` keeps existing constructions valid.

## Alternatives considered
- Placing the context in `scripts/agent/`: rejected — the shared transport chain (:16 forwarders) must carry it without importing agent (import-linter contract).

## Implementation
### Target file
`scripts/shared/transport_dto.py`

### Procedure
Insert the new dataclass above `ToolCallResult` (:26) and add the optional field to `ToolCallResult`.

### Method
Stdlib-only dataclass; frozen; no methods beyond dataclass defaults.

### Details
- `args_hash` is hex sha256 over canonical-JSON args — same computation the grant uses (rows 2-3), enabling comparison at the gateway.

## Compatibility considerations
All existing `ToolCallResult` constructions keep working via the `None` default; rows 14-16 populate it.

## Security considerations
Context carries no raw arguments — only a hash.

## Rollback considerations
N/A: revert the commit.

## Validation plan
`uv run pytest tests/shared/test_http_transport.py && uv run lint-imports` — leaf contract intact, result carries the context.

## Completion criteria
`ToolExecutionContext` is importable from `shared.transport_dto`; every executed call's `ToolCallResult` exposes the same `call_id` that preparation generated.

## Out of Scope
Context construction (row 1); forwarding plumbing (rows 14-16).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | Docs sweep owned by mcpai012 |

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
- **Requirement ID**: `REQ-002`
- **Source issue**: `issues/20261120-115840_mcpdl001_approval-grant-intent.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261120-222144_mcpdl001_approval-grant-intent.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261120-225424
- **Related target files**: `scripts/shared/transport_dto.py`
