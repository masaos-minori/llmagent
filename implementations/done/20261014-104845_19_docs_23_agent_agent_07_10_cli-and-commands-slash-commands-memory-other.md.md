## Goal

Remove MDQ content from the memory/other commands chapter (REQ-004: update documentation).

## Scope

- Retitle, edit Purpose, delete one section, one bullet, one keyword, and one related entry. Title (line 2), `related:` entry (line 20), Purpose (line 29), MDQ Category section (lines 37-39), Responsibility Boundary bullet (line 48), keyword (line 54).

## Assumptions

- Plan `plans/20261014-100930_plan.md` is `Frozen`; this file is one of its `Implementation Target Files` rows.
- Source line numbers were verified in this cycle against the current tree and may shift; locate edits by symbol or test name.

## Design decisions

- Title becomes `Agent CLI and Commands - Slash Commands: Memory and Other`; Purpose reads "... slash commands in the Memory and Other categories."
- Delete the `### MDQ Category` section, the `- **MDQ**: Document indexing and search` bullet, the `- mdq category` keyword, and the `mcp_05_04_mdq-rag-boundary.md` entry under `related:` (nothing in the body references it afterwards; `check_docs_structure.py` does not require it).

## Alternatives considered

N/A: the docs follow the code removal

## Implementation

### Target file

`docs/23_agent/agent_07_10_cli-and-commands-slash-commands-memory-other.md`

### Procedure

Apply the edits in Design decisions; the file name stays unchanged.

### Method

Edit with the Edit tool, top to bottom, re-reading line numbers after each edit.

### Details

Do not edit the other `related:` entries; the chapter-index description is procedure 17.

## Compatibility considerations

N/A: docs-only change

## Security considerations

N/A: docs-only change

## Rollback considerations

N/A: revert the commit

## Validation plan

- `check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py`, `check_docs_consistency.py --domain agent`, and `uv run pytest tests/docs -q` pass.
- `rg -n -i 'mdq' <this file>` has no match.

## Completion criteria

- No MDQ reference remains; headings, bullets, keywords, and front matter are consistent.

## Out of scope

- Memory and Other sections.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Apply the six edits | Completed | 20261014-110318 | 20261014-110318 |  |
| 2 | Run the documentation checkers named in `routing.md` Tools | Completed | 20261014-110318 | 20261014-110318 |  |

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
- **Source issue**: issues/20261014-095505_mdq001_remove-the-mdq-slash-command.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261014-100930_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261014-104845
- **Related target files**: docs/23_agent/agent_07_10_cli-and-commands-slash-commands-memory-other.md