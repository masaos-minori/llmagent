## Goal

Stop the slash-command regex from reading a log path as a command (REQ-005: keep docs checks warning-free).

## Scope

- Change one character class in one regex. The negative lookbehind of `_DOC_SLASH_COMMAND_RE` at lines 213-217 only.

## Assumptions

- Plan `plans/20261014-100930_plan.md` is `Frozen`; this file is one of its `Implementation Target Files` rows.
- Source line numbers were verified in this cycle against the current tree and may shift; locate edits by symbol or test name.

## Design decisions

- Add `>` to the lookbehind: `(?<![`/a-zA-Z0-9>])`, so `<log_dir>/mdq-mcp.log` no longer matches while `` `/mdq status` `` style text still behaves as before.
- Keep `mdq` in the alternation by design: it guards against a `/mdq` reference returning to a doc.

## Alternatives considered

N/A: deletion is the decided direction (Plan Design)

## Implementation

### Target file

`tools/_docs_consistency_lib.py`

### Procedure

Edit the regex lookbehind.

### Method

Confirm with a one-line `python -c` that `<log_dir>/mdq-mcp.log` and `/opt/llm/db/mdq.sqlite` do not match and `run /db rag stats` still does; then run `check_docs_consistency.py --domain mcp`.

### Details

After the `/mdq` removal this regex produced 2 new warnings (`mcp_04_04_mdq.md:41`, `mcp_06_05_reading-audit-logs.md:61`) in a trial removal; the docs themselves stay unchanged.

## Compatibility considerations

A check-only change; severity stays WARNING.

## Security considerations

N/A: removal only; no new input path

## Rollback considerations

N/A: revert the commit

## Validation plan

- `uv run python tools/check_docs_consistency.py --domain mcp` reports no WARNING for the two docs.
- `--domain agent`, `rag`, `deployment`, `overview` stay at "No issues found".

## Completion criteria

- The regex excludes a slash preceded by `>`.
- The mcp domain check is warning-free for the two docs.

## Out of scope

- The two MDQ docs and other checker logic.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit the regex | Pending | — | — | |
| 2 | Run the tests that cover this file | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: REQ-005
- **Source issue**: issues/20261014-095505_mdq001_remove-the-mdq-slash-command.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261014-100930_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261014-104845
- **Related target files**: tools/_docs_consistency_lib.py
