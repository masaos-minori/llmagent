# Procedure: add the structured ADR-014 marker comment

## Goal

Add a one-line `# ADR-014` marker comment so `tools/check_adr_reference.py` recognizes the file named by the ADR-014 INV-01 matrix row (Plan REQ-006).

## Scope

- Modify only `scripts/agent/orchestrator.py`.
- Comment-only change; no runtime effect.
- Out of scope: any code, docstring or behavior change.

## Assumptions

- Apply this row before the reference-checker repair (seq 03) so the live run of the repaired checker is clean (ordering note).
- The marker is a comment token matching `#\s*ADR-014\b`, found with `tokenize`; a docstring or string mention does not count.
- Overlap (compatible): `plans/20261028-094441_ebdlqunique007_enforce-dlq-redelivery-uniqueness.md` edits only the ADR-006 Implementation Notes, while this Plan edits ADR-006's Verification table. Any citation added by that Plan must resolve to an existing test node once the node validation of this Plan is in force.

## Design decisions

- Place the marker directly below the module docstring so it is easy to find and does not move code.

## Alternatives considered

N/A: the Plan fixes the approach (see its Design section).

## Implementation

### Target file

`scripts/agent/orchestrator.py`

### Procedure

- Add the line `# ADR-014: Orchestrator arbitrates processing within a turn and does not decide persistent state` after the module docstring and before the first import.
- Do not reformat or reorder anything else.

### Method

Insert one comment line.

### Details

- `ruff format` must leave the file unchanged; keep the line under 88 characters.
- Verify with `uv run python tools/check_adr_reference.py` after the checker repair row has landed.

## Compatibility considerations

- No runtime effect; byte-code identical.

## Security considerations

- No security impact.

## Rollback considerations

- Revert the commit.

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| 1 | `uv run ruff format scripts/agent/orchestrator.py`; `uv run ruff check scripts/agent/orchestrator.py`; `uv run mypy --no-namespace-packages scripts/` | No finding |
| 2 | `uv run python tools/check_adr_reference.py` | The file is accepted once the repaired checker has landed |
| 3 | `uv run python tools/check_module_size.py` | No new violation |

## Completion criteria

- The file contains a comment line starting with `# ADR-014`.

## Out of Scope

- Code and docstring edits.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261028-162007 | 20261028-162007 |  |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261028-162007 | 20261028-162007 |  |

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
- **Requirement ID**: REQ-006 (marker comment on matrix-named sources)
- **Source issue**: issues/20261027-155848_adrgate005_enforce-adr-evidence-checks.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261028-093931_adrgate005_enforce-adr-evidence-checks.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261028-115901
- **Related target files**: scripts/agent/orchestrator.py