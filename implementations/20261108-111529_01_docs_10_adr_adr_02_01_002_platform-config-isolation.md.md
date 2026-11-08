## Goal
Make ADR-002 state exactly what the loader enforces and what depends on deployment: rule and EventBus exception together, file isolation separate from key validation, verified EventBus controls, no physical-isolation claim, and an explicit deployment-control assumption (REQ-001 to REQ-005).

## Scope
**Release unit**: N/A: not part of a release unit
Edits ADR-002 only: Decision Details items 6 and 9 and the EventBus note, the Per-Process Required Files and Keys lead-in and table, Rationale, Assumptions, Security Consequences, Exceptions, and Implementation Notes. No invariant text, decision, or ownership changes.

## Assumptions
- `load_config()` in the EventBus config module does not restrict the path; the default path can be overridden by the documented `EVENTBUS_CONFIG_PATH` operator override; call sites passing `get_config_path()` are locked by a regression test (verified in the Plan against the loader and EventBus config module).
- The repository establishes no operating-system control over configuration files; the ADR must say so rather than imply it.
- The adrver001 Plan later reads the revised wording for its verification mapping; this procedure has no other overlap on ADR-002.

## Design decisions
- State the guarantee per mechanism: the loader rejects non-permitted files for a process that called `restrict_to()`; EventBus relies on its local path handling; neither prevents reading other files by other means.
- Keep invariants untouched; qualify prose (items 6, 9, Rationale, Security Consequences) instead.

## Alternatives considered
N/A: Plan decisions already fix the approach (wording only, no loader change).

## Implementation
### Target file
`docs/10_adr/adr_02_01_002_platform-config-isolation.md`

### Procedure
1. Phase 1: Reconcile Decision item 9, the Per-Process lead-in and Exceptions so the general rule and the EventBus exception appear together; limit "otherwise unconditional" to what the loader enforces; qualify Decision item 6.
2. Phase 2: Restructure the Per-Process lead-in and table so file isolation (mechanism) and key validation (required keys) are separate, including the EventBus row naming its different mechanism.
3. Phase 3: Correct the Implementation Notes EventBus sentence (the loader does not "accept only" that path; describe the default path, the operator override, the regression test, and the absent `ConfigLoader` permission check); replace "physically blocked" in Rationale and Security Consequences with the mechanism-specific guarantee; add the deployment-control assumption (file permissions and service-user separation are outside the loader and not established by the repository).
4. Phase 4: Read the whole ADR for universal claims such as "unconditional" or "physically" and fix any remaining one.

### Method
Documentation edit of one file; verify every claim about the loader against the source before writing it.

### Details
- Do not change `load_config()` or `get_config_path()` (out of scope).
- Keep the H2 sequence, invariant identifiers and anchors; do not touch Approval.

## Compatibility considerations
Documentation only; no behavior change.

## Security considerations
The edit removes an overstated security claim and states the deployment dependency; no secret or permission behavior changes.

## Rollback considerations
N/A: revert the commit

## Validation plan
- `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py`, `check_docs_japanese.py`: no findings
- `uv run python tools/check_adr_preservation.py`, `check_adr_structure.py`, `check_adr_invariant_matrix.py`: no ERROR
- `uv run pytest tests/shared/test_config_loader.py tests/eventbus/test_eventbus_config.py tests/agent/test_config_permission_cross_server.py`: pass (unchanged)

## Completion criteria
- No sentence claims physical isolation or an unconditional rule beyond what the loader enforces.
- EventBus controls are described as verified, including the operator override.
- The deployment-control assumption is stated explicitly.

## Out of Scope
- Loader refactoring; secret-management redesign; EventBus authentication changes.
- Invariant, decision or ownership changes.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Apply Phases 1 to 3 of Implementation > Procedure | Pending | — | — |  |
| 2 | Read the whole ADR for remaining universal claims and run the documentation checkers (Phase 4) | Pending | — | — |  |

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
- **Requirement ID**: `REQ-001` to `REQ-005` (rule and exception, file isolation versus key validation, EventBus controls, security claims, deployment assumption)
- **Source issue**: issues/20261107-050704_adrcfg001_clarify-adr-002-isolation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261108-092140_adrcfg001_clarify-adr-002-isolation.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261108-111529
- **Related target files**: `docs/10_adr/adr_02_01_002_platform-config-isolation.md`
