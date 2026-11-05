# Implementation Procedure: docs REPL-IO chapter — hand-off guarantee paragraph

## Goal

State the post-timeout hand-off guarantee in the REPL-IO chapter so the docs match the wired
behavior (REQ-005: the REPL-IO chapter states the hand-off guarantee; AC-5).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: one append-only paragraph in the REPL Input/Output Model section.
- Out of scope: any other chapter. `docs/23_agent/agent_07_02_cli-and-commands-cliview.md` and
  `docs/23_agent/agent_12_reference-api.md` stay unchanged (Plan: no stdin-timeout behavior is
  documented there and the API surface is unchanged).

## Assumptions

- The chapter's existing "Input Reader" bullet is the natural anchor: it already describes the
  daemon reader thread and cancelled-read process-exit guarantee (confirmed in Step 3a).

## Design decisions

- Append one bullet immediately after the Input Reader bullet (chosen): the Plan's risk mitigation
  for this file's high docs churn is an append-only single paragraph, and the guarantee is an I/O
  model property, not a shutdown property.

## Alternatives considered

- Rewriting the Input Reader bullet in place — rejected: higher churn and merge-noise risk for the
  same information.

## Implementation
### Target file
`docs/23_agent/agent_07_05_cli-and-commands-repl-io.md`

### Procedure
Append one bullet to the "REPL Input/Output Model" list, after the Input Reader bullet:

- Hand-off After Timeout: a multiline continuation read is bounded by a timeout in the CLI view; on
  timeout the request is abandoned and the partial text is still returned. A line typed while or
  after that read is abandoned is not lost: every interactive prompt (`> `, `... `, and the
  approval prompts) reads through one process-shared reader instance, and the reader delivers a
  late line to the newest pending request (`TestReadMultilineTimeout`,
  `TestCancelledRequestDelivery`).

### Method
Markdown text only; frontmatter, headings, and all existing bullets are untouched.

### Details
- No line-number citations in the new bullet; reference tests by name only (repository docs rule).
- Match the chapter's existing bullet style (bold lead-in label, inline code for prompts).

### Companion test files
N/A: no companion test files for this target (docs target; checker gate in Validation plan).

### Implementation Checklist
| # | Target File(s) | Action Summary | Acceptance Criteria | Status |
|---|----------------|----------------|---------------------|--------|
| 1 | docs/23_agent/agent_07_05_cli-and-commands-repl-io.md | Append the hand-off guarantee bullet. | Chapter states the guarantee; all docs checkers report no findings. | Completed (20261105) |

## Compatibility considerations

- Append-only edit; no existing statement or test reference is removed (Plan risk mitigation).

## Security considerations

N/A: documentation-only change.

## Rollback considerations

Delete the added bullet; nothing else in the chapter depends on it.

## Validation plan

- Docs gate per the Plan's Validation plan row: `uv run python tools/check_docs_quality.py`,
  `uv run python tools/check_docs_structure.py`, `uv run python tools/check_docs_content_policy.py`,
  `uv run python tools/check_docs_consistency.py --domain agent`, `uv run python
  tools/generate_reference_table.py --check` — no findings; reference-table drift-free.

## Completion criteria

- The REPL-IO chapter states the hand-off guarantee (AC-5) and the docs checkers report no
  findings.

## Out of Scope

- Other documentation chapters (see Scope).
- Any statement about implementation internals beyond the shared-reader guarantee.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Append the hand-off bullet per Implementation > Procedure | Completed | 20261105-105000 | 20261105-105200 | adversarial verification: anchor Input Reader bullet confirmed at L40; bullet style matches (bold lead-in + backticked test names); cited tests TestReadMultilineTimeout and TestCancelledRequestDelivery both exist; one accuracy gap found: the procedure's 'not lost' claim omits the discard case (line discarded when no later read happens) -> landed bullet adds the discard clause; stale_detector clean bullet appended after Input Reader anchor; landed wording adds the discard clause beyond the procedure's draft (see Step 1 verification notes); Input Reader 'owned by its caller' wording left as-is per the frozen append-only decision - residual phrasing noted for the owner |
| 2 | Run the docs checkers (Validation plan) | Completed | — | 20261105-105200 | check_docs_quality/check_docs_structure/check_docs_content_policy/check_docs_consistency --domain agent/generate_reference_table --check: all clean |

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
- **Requirement ID**: REQ-005 (documentation of the hand-off guarantee)
- **Source issue**: issues/20261104-112115_cliview002_stdin-line-lost-after-multiline-timeout.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261104-223334_cliview002_stdin-line-lost-after-multiline-timeout.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261105-090427
- **Related target files**: `docs/23_agent/agent_07_05_cli-and-commands-repl-io.md`