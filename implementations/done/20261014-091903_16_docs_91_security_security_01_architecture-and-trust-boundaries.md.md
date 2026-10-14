## Goal

Rewrite the Agent to LLM trust-boundary row without `/skill` (REQ-004: update documentation).

## Scope

- Rewrite one table row. The Agent to LLM row on line 167 only.

## Assumptions

- Plan `plans/20261014-091322_plan.md` is `Frozen`; this file is one of its `Implementation Target Files` rows.
- Source line numbers were verified in this cycle against the current tree and may shift; locate edits by symbol or test name.

## Design decisions

- Target text: "Two kinds of content enter system-role messages: memory snippets (a `--- USER MEMORY ---` block, PII-redacted and length-limited by `snippet_filter.py`) and fixed MDQ/RAG routing hints. Ephemeral markers are accepted only from trusted sources."
- Drop `scripts/agent/commands/cmd_skill.py` from the evidence list (the file is deleted); keep `conversation_state_manager.py` and `snippet_filter.py`.

## Alternatives considered

N/A: the docs follow the code removal

## Implementation

### Target file

`docs/91_security/security_01_architecture-and-trust-boundaries.md`

### Procedure

Replace the row text with the target text and update its `Explicit in code` file list.

### Method

Edit with the Edit tool; keep the table column count.

### Details

`check_docs_consistency.py` verifies referenced file paths exist, so the stale path must go.

## Compatibility considerations

Docs-only change.

## Security considerations

The text must not claim any content that bypasses filtering.

## Rollback considerations

N/A: revert the commit

## Validation plan

- `check_docs_quality.py`, `check_docs_structure.py`, `check_docs_consistency.py --domain overview` and `--domain agent` pass.
- `rg -n 'skill' <this file>` has no match.

## Completion criteria

- The row lists two content kinds and no deleted path.

## Out of scope

- Other trust-boundary rows.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Rewrite the row | Completed | 20261014-094631 | 20261014-094631 |  |
| 2 | Run the documentation checkers named in `routing.md` Tools | Completed | 20261014-094631 | 20261014-094631 |  |

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
- **Requirement ID**: REQ-004
- **Source issue**: issues/20261014-090429_skill001_remove-the-skill-slash-command-and-its-ephemeral-plumbing.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261014-091322_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261014-091903
- **Related target files**: docs/91_security/security_01_architecture-and-trust-boundaries.md