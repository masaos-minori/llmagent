## Goal
- Describe `tools/check_evidence_freshness.py` in `tools/TOOL_DESCRIPTIONS.md` so `tools/check_tool_descriptions_sync.py` passes (REQ-006).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: one Index row and one detail row. Out of scope: any other row.

## Assumptions
- Verified in Step 3a: the Index and the Work Items detail table list `scan_change_consumers.py` and `plan_dependency_order.py` (the read-only planning aids) in the Work item category; `tools/check_tool_descriptions_sync.py` requires every `tools/*.py` to be listed.
- Procedure 01 runs first, so the rows describe real behavior.

## Design decisions
- Both rows go directly after the `plan_dependency_order.py` row of their table. The text states: the two subcommands; the revision source (the Plan's `Evidence revision`, a procedure through its `Source plan`); the derived cited-path set and `--also`; the three reported statuses and the summary line; exit 0, 1 (any reported path), 2 (no revision, unknown SHA, unreadable document); that `record` refuses uncommitted cited files; that it writes nothing; and that the skip rule is in `rules/ai-execution.md` Adversarial Verification (Base).

## Alternatives considered
- N/A: documentation only.

## Implementation
### Target file
`tools/TOOL_DESCRIPTIONS.md`

### Procedure
1. Add the Index row (Category `Work item`) and the detail row in the same style as the neighbors.
2. Run the sync check.

### Method
- Two inserted rows; no other line changes. English text.

### Details
- Do not claim a hook, gate, or CI step: none exists (Plan Out of Scope).

## Compatibility considerations
- N/A: documentation only.

## Security considerations
- N/A: documentation only.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run python tools/check_tool_descriptions_sync.py`; the pre-commit hook "Check tools/TOOL_DESCRIPTIONS.md sync" on commit.

## Completion criteria
- The sync check passes and both rows exist.

## Out of Scope
- The tool, template, rule, and workflow changes (procedures 01 to 07).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Run the documentation checkers named in `rules/tool-gates.md` "When to run which tool" | Pending | — | — | |

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
- **Requirement ID**: `REQ-006`
- **Source issue**: issues/20261126-151439_wfeff004_evidence-sha-carryover.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261126-182520_wfeff004_evidence-sha-carryover.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-183845
- **Related target files**: `tools/TOOL_DESCRIPTIONS.md`
