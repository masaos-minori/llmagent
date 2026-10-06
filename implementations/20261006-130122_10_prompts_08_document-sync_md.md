## Goal

Remove the stale statement in `prompts/08_document-sync.md` that ADR documents keep their
classified body `Related Documents` block (REQ-001 / AC-1): after this plan the ADR `##
Related Documents` body block no longer exists anywhere under `docs/`, so the parenthetical
justification on line 201 is now false.

## Scope

- **In-Scope**: `prompts/08_document-sync.md` — one parenthetical in the "Format" list
  (line 201).
- **Out-of-Scope**: the rest of the prompt; other prompt files; `docs/` targets.

## Assumptions

- Line 201's leading clause "do not add a body Related Documents section" remains a valid
  general formatting rule (REQ-002 forbids a body `Related Documents` heading at any level);
  only the parenthetical `(ADR documents keep their classified block)` is stale.

## Design decisions

- Delete only the parenthetical `(ADR documents keep their classified block)`. Keep the
  leading clause intact. This removes the false ADR exception without altering the general
  rule.

## Alternatives considered

- Rewriting the whole "Format" list — rejected: out of scope; only the one stale clause
  needs correcting (AGENTS.md Global Rule 5).

## Implementation

### Target file

`prompts/08_document-sync.md`

### Procedure

1. Edit line 201. Change
   `- Maintain front matter `related:` with the related documents' filenames; do not add a body Related Documents section (ADR documents keep their classified block).`
   to
   `- Maintain front matter `related:` with the related documents' filenames; do not add a body Related Documents section.`
   (i.e. delete the trailing parenthetical).

### Method

- Read `prompts/08_document-sync.md` lines 199-202.
- Apply the single replacement (step 1).

### Details

- Current line 201 ends with `...do not add a body Related Documents section (ADR documents keep their classified block).`
- No other location in this prompt asserts that ADRs retain a body Related Documents block (verified by grep for `Related Documents` in the file).

## Compatibility considerations

- `prompts/08_document-sync.md` is authoring guidance invoked directly by filename; no
  runtime effect. The general "do not add a body Related Documents section" rule now
  applies uniformly to all `docs/`, including ADRs.

## Security considerations

N/A: documentation-only prompt text.

## Rollback considerations

Revert `prompts/08_document-sync.md` to the pre-this-change commit.

## Validation plan

| Target | Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `prompts/08_document-sync.md` | Manual | Read line 201 | Parenthetical asserting an ADR classified block is gone |
| `prompts/08_document-sync.md` | Grep | `rg "ADR documents keep their classified block"` (this file) | No match |

## Completion criteria

- Line 201 no longer states that ADR documents keep their classified block.
- The general "do not add a body Related Documents section" rule remains.

## Out of scope

- Other prompt files; `docs/` targets; the tool source files.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | REQ-001 / AC-1 |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: prompt text only |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | manual review |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — | |

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
- **Requirement ID**: `REQ-001` — stale ADR classified-block statement removed from prompts/08 (AC-1)
- **Source issue**: `issues/20261005-144150_rel002_remove-the-adr-body-related-documents-block-and-update-adr-rules-and-tools.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261006-084759_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261006-130122
- **Related target files**: `prompts/08_document-sync.md`
