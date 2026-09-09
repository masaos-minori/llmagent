# Implementation Procedure: Add auto-generated-block exemption to literal-port-number check

## Goal

Add an auto-generated-guard-comment exemption to `check_docs_content_policy.py`'s literal-port-number check so that content between `<!-- AUTO-GENERATED -->` / `<!-- END AUTO-GENERATED -->` guard comments is not flagged.

## Scope

- **In-Scope**: Modify `check_literal_port_number()` function in `tools/check_docs_content_policy.py` to skip content within auto-generated guard comments
- **Out-of-Scope**: Changes to other checks in the same file; documentation updates

## Assumptions

- The exemption applies only to content between `<!-- AUTO-GENERATED -->` / `<!-- END AUTO-GENERATED -->` guard comments
- Hand-written port mentions outside those guard comments should still be flagged
- The exemption is narrowly scoped — not a general "tables are exempt" rule

## Design decisions

- Check for guard comment boundaries before flagging each literal port number finding
- Only skip findings where the entire line or context falls between the two guard comments
- Preserve existing behavior for all other cases

## Alternatives considered

- Adding a separate whitelist of files to exclude — rejected because it doesn't address the structural pattern (guard comments) that makes the content safe
- Making the exemption configurable via CLI flag — rejected because the exemption is deterministic based on document structure, not user preference

## Implementation

### Target file

`tools/check_docs_content_policy.py`

### Procedure

Modify `check_literal_port_number()` to skip content within auto-generated guard comments.

### Method

Edit the `check_literal_port_number()` function at line 153 to add guard-comment boundary checking.

### Details

1. Read `tools/check_docs_content_policy.py` around line 153 to locate `check_literal_port_number()`.
2. Identify where the function iterates over lines and checks for literal port numbers.
3. Add logic to track whether we are inside an auto-generated block:
   - When encountering `<!-- AUTO-GENERATED -->`, set a flag `in_auto_generated = True`
   - When encountering `<!-- END AUTO-GENERATED -->`, set `in_auto_generated = False`
   - Skip any literal port number findings when `in_auto_generated` is True
4. Ensure the flag resets properly across multiple auto-generated blocks in the same file.
5. Verify that hand-written port mentions outside guard comments are still flagged.

## Compatibility considerations

- Existing lint findings for hand-written port numbers are unaffected
- Auto-generated sections will no longer produce false positives from this check

## Security considerations

N/A: Tool behavior change only — no security impact

## Rollback considerations

- Revert the guard-comment tracking logic if it causes missed findings
- Ensure the flag reset logic is correct before deploying

## Validation plan

Run `uv run python tools/check_docs_content_policy.py` against the current corpus and confirm:
- Auto-generated sections no longer produce literal-port-number findings
- Hand-written port mentions in other files are still flagged

## Completion criteria

- `check_literal_port_number()` skips content between `<!-- AUTO-GENERATED -->` / `<!-- END AUTO-GENERATED -->` guard comments
- Hand-written port mentions outside those guard comments are still flagged
- Corpus run confirms no regression

## Out of scope

- Unit test creation (separate target file: `tests/tools/test_check_docs_content_policy.py`)
- Changes to other checks in the same file
- Documentation updates (separate target file: `docs/00_governance_04_documentation-checks.md`)

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Locate check_literal_port_number() function | Completed | 2026-09-09 | 2026-09-09 | Found at line 153 |
| 2 | Add guard-comment boundary tracking | Completed | 2026-09-09 | 2026-09-09 | Added in_auto_generated flag with guard comment detection |
| 3 | Verify hand-written ports still flagged | Completed | 2026-09-09 | 2026-09-09 | Flag only applies within auto-generated blocks; outside blocks behavior unchanged |

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
- **Requirement ID**: REQ-002
- **Source issue**: issues/20260905-153715_dcp001_port_number_exemption_policy_decision.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260908-210115_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260909-125541
- **Related target files**: tools/check_docs_content_policy.py
