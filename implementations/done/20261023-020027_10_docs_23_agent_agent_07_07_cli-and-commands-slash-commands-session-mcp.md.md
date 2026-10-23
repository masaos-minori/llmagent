## Goal

Document the accepted argument range and grammar for `/history [n]`, `/session list [n]`, and
`/session purge [--max-sessions/--max-age-days]` in the session chapter, so the docs match the
shared-parser behavior this Plan introduces (REQ-008; AC-7).

## Scope

In scope: `docs/23_agent/agent_07_07_cli-and-commands-slash-commands-session-mcp.md`. Out of scope:
the `/memory list` chapter (`agent_07_10`, its own row) and any source-code change.

## Assumptions

- `/history [n]` table row at `:40` (prose at `:43`) documents only "default 5".
- `/session list [n]` table row at `:51` documents only "default 20".
- `/session purge` table row at `:59` lists the flags with no accepted values.
- Ranges must be written in prose, never inside a `` `/command … `` usage code span, because
  `tools/check_docs_consistency.py:285-430` compares those spans against the registered usage lines.

## Design decisions

- In the `/history` prose (`:43`), add that `n` accepts `1..200`; `0`, negatives, and values above
  `200` are usage errors and print nothing; omitting `n` keeps the default of 5.
- In the `/session list` row/prose (`:51`), add that `n` accepts `1..200`; a non-integer, `0`, a
  negative, or a value above `200` is a usage error.
- In the `/session purge` row/prose (`:59`), add that `--max-sessions` accepts an integer `>= 1`
  (bare flag, `0`, negative, non-integer are errors), that `--max-age-days` accepts an integer
  `>= 0` (`0` keeps its documented "disabled" meaning; negative/non-integer are errors), and that
  an absent flag uses the retention default.

## Alternatives considered

- Writing the ranges inside usage code spans: rejected by the Plan (UNK-03 / AC-7) — the
  consistency checker compares those spans to the `ArgSpec`-derived usage lines, which carry no
  range.

## Implementation

### Target file

`docs/23_agent/agent_07_07_cli-and-commands-slash-commands-session-mcp.md`

### Procedure

- In the `/history` prose paragraph (`:43`), add that `n` accepts `1..200`; `0`, negatives, and
  values above `200` are usage errors that print nothing; omitting `n` keeps the default of 5.
- In the `/session list` row/prose (`:51`), add that `n` accepts `1..200`; a non-integer, `0`, a
  negative, or a value above `200` is a usage error.
- In the `/session purge` row/prose (`:59`), add that `--max-sessions` accepts an integer `>= 1`
  (bare flag, `0`, negative, non-integer are errors), that `--max-age-days` accepts an integer
  `>= 0` (`0` keeps its documented "disabled" meaning; negative/non-integer are errors), and that
  an absent flag uses the retention default.

### Method

Prose only — never inside a `` `/command … `` usage code span, because
`tools/check_docs_consistency.py:285-430` compares those spans against the registered usage lines.

### Details

The table rows at `:40`, `:51`, `:59` currently document only defaults; the ranges go in the
surrounding prose. `docs/00_index.md:144` maps this chapter via `agent_07_03:42`.

## Compatibility considerations

- Prose-only additions do not change any registered usage line, so `test_command_def_sync.py`
  (`:207`, `:219`) and the consistency checker stay green.

## Security considerations

- Documenting that `--max-sessions 0`/negatives are rejected makes the destructive-command guard
  visible to operators.

## Rollback considerations

- Revert the doc commit for this row.

## Validation plan

- `uv run python tools/check_docs_quality.py`; `check_docs_structure.py`; `check_docs_content_policy.py`;
  `check_docs_consistency.py --domain agent`; `check_docs_refs.py`; `check_docs_index_completeness.py`;
  `check_docs_japanese.py` — all pass; no GV-023 argument-contract drift for this chapter.

## Completion criteria

- The chapter states the accepted range and grammar for each argument in prose outside usage code
  spans, including `--max-age-days 0` means "disabled" and invalid arguments are always errors
  (AC-7).

## Out of Scope

The `/memory list` chapter (`agent_07_10`) and all source-code rows — each is its own row.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Document accepted ranges/grammars for `/history [n]`, `/session list [n]`, `/session purge` in prose | Completed | 2026-10-23 | 2026-10-23 | REQ-008, AC-7 |
| 2 | Run the documentation checkers (`rules/toolchain.md`) | Completed | 2026-10-23 | 2026-10-23 | — |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | N/A: no blocking unknown remains | N/A: none | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-008`, `REQ-005`
- **Source issue**: `issues/20261021-093421_cmd002-invalid-command-args-silently-reinterpreted.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261022-013404_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261023-020027
- **Related target files**: `docs/23_agent/agent_07_07_cli-and-commands-slash-commands-session-mcp.md`
