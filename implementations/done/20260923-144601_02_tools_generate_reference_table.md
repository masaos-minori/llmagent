## Goal

Correct the stale `tools/gen_deployment_reference.py` reference in the `GUARD_START_DEPLOYMENT` constant of `tools/generate_reference_table.py` to use the consolidated `tools/generate_reference_table.py`, ensuring guard comment alignment with `docs/02_deployment.md`.

## Scope

- Update line 55: Change `gen_deployment_reference.py` → `generate_reference_table.py` in `GUARD_START_DEPLOYMENT` constant
- Verify REQ-001 acceptance criterion

## Assumptions

- The consolidation of `gen_deployment_reference.py` into `tools/generate_reference_table.py` was intentional and complete
- The guard comment format (`<!-- AUTO-GENERATED: ... -->`) must match the actual guard comment used in `docs/02_deployment.md` to prevent regeneration failures
- Other guard constants (e.g., `GUARD_START_MCP`, `GUARD_START_AGENT`) do not require changes — they reference their respective legacy generators that may still exist

## Design decisions

- Minimal changes approach: only modify the one stale reference identified in the plan
- Guard comment alignment: the `GUARD_START_DEPLOYMENT` constant must match the guard comment in `docs/02_deployment.md` to allow future regeneration via `python tools/generate_reference_table.py --type deployment`

## Alternatives considered

- Updating all guard constants to reflect consolidation: rejected because each guard constant corresponds to a specific domain (MCP, agent, eventbus, memory) and only the deployment domain has been consolidated
- Adding a note about Python-level defaults in the table: rejected because line 183 of `tools/generate_reference_table.py` already handles this correctly

## Implementation

### Target file

`tools/generate_reference_table.py`

### Procedure

1. Update line 55: Change `<!-- AUTO-GENERATED: gen_deployment_reference.py db-path-reference -->` to `<!-- AUTO-GENERATED: generate_reference_table.py db-path-reference -->`

### Method

Use Edit tool to perform exact string replacement at the identified line number.

### Details

**Line 55 — GUARD_START_DEPLOYMENT constant:**
- Current: `"<\!-- AUTO-GENERATED: gen_deployment_reference.py db-path-reference -->"`
- Replace with: `"<\!-- AUTO-GENERATED: generate_reference_table.py db-path-reference -->"`
- Rationale: Must match the guard comment in `docs/02_deployment.md` line 269 to prevent regeneration failures
- Note: This constant is used by `generate_deployment_reference_table()` function to identify the guard block boundaries in the target document

## Compatibility considerations

- Future regeneration via `python tools/generate_reference_table.py --type deployment` requires both the guard comment in `docs/02_deployment.md` and the `GUARD_START_DEPLOYMENT` constant to reference the same tool name
- If either value is changed independently, the other must be updated simultaneously to maintain consistency

## Security considerations

N/A: Only internal constant update, no external-facing behavior change.

## Rollback considerations

- Revert the edit to restore original value if regeneration fails after changes
- Document the rollback path in case of unexpected side effects

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| tools/generate_reference_table.py | Dry-run execution to verify guard compatibility | `uv run python tools/generate_reference_table.py --type deployment --dry-run` | Table output with Python-level default source file references |
| docs/02_deployment.md | Verify guard comment alignment | `grep 'AUTO-GENERATED' docs/02_deployment.md` | Both guard comments reference `generate_reference_table.py` |

## Completion criteria

- [ ] Line 55 `GUARD_START_DEPLOYMENT` constant references `generate_reference_table.py` (not `gen_deployment_reference.py`)
- [ ] `uv run python tools/generate_reference_table.py --type deployment --dry-run` produces expected output
- [ ] Guard comment in `docs/02_deployment.md` line 269 also updated (see separate procedure document)

## Out of scope

- Modifying `GUARD_START_MCP`, `GUARD_START_AGENT`, `GUARD_START_EVENTBUS`, `GUARD_START_MEMORY` constants — each corresponds to its own domain
- Modifying docstring historical notes ("Consolidated from: ...") — informational provenance, not functional reference
- Updating archived issue document (`issues/done/20260923-100000_p001_workflow_db_path_config_mismatch.md`)

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | — | GUARD_START_DEPLOYMENT constant updated |
| 2 | Add or update tests per Validation plan | N/A | — | — | Documentation-only task, no tests needed |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | — | Dry-run confirmed working |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — | Out of scope |

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
- **Requirement ID**: REQ-001
- **Source issue**: issues/20260923-100000_p001_workflow_db_path_config_mismatch.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260923-142236_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260923-144601
- **Related target files**: tools/generate_reference_table.py
