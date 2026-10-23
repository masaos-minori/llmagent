## Goal

Extend the `/memory list` row in the memory-other chapter with the accepted token grammar after
the shared-parser change, so the documented grammar matches the implementation (REQ-006, REQ-008;
AC-5, AC-7).

## Scope

In scope: `docs/23_agent/agent_07_10_cli-and-commands-slash-commands-memory-other.md`. Out of
scope: the session chapter (`agent_07_07`, its own row) and any source-code change.

## Assumptions

- The `/memory list` row at `:39` already states "default 20, at most 200" but not the accepted
  token grammar.
- `grep -n '`/memory list' docs/23_agent/*.md` returns only `agent_07_10:39`.
- Ranges must be written in prose, never inside a `` `/command … `` usage code span, because
  `tools/check_docs_consistency.py:285-430` compares those spans against the registered usage lines.

## Design decisions

- On the `:39` row, add that the positional `n` accepts the shared `int()` grammar: `'+5'` and
  `'1_0'` are accepted, and the 1..200 bound still applies. Note that non-ASCII decimal digits
  (e.g. `'٣'`) remain accepted, since `int()` accepts them (this matches the implementation; the
  old "rejected" wording was a factual error and has been corrected in the Plan).

## Alternatives considered

- Writing the grammar inside a usage code span: rejected by the Plan (AC-7) — the consistency
  checker compares those spans to the `ArgSpec`-derived usage line, which carries no grammar.

## Implementation

### Target file

`docs/23_agent/agent_07_10_cli-and-commands-slash-commands-memory-other.md`

### Procedure

On the `/memory list` row (`:39`, currently "default 20, at most 200"), add the accepted token
grammar in prose: the positional `n` accepts the shared `int()` grammar — `'+5'` and `'1_0'` are
accepted, the 1..200 bound still applies, and non-ASCII decimal digits (e.g. `'٣'`) remain
accepted because `int()` accepts them.

### Method

Prose only — never inside a `` `/command … `` usage code span, because
`tools/check_docs_consistency.py:285-430` compares those spans against the registered usage lines.

### Details

`grep -n '`/memory list' docs/23_agent/*.md` returns only `agent_07_10:39`. The grammar note
matches the shared parser adopted by this Plan.

## Compatibility considerations

- Prose-only addition; no registered usage line changes, so `test_command_def_sync.py` and the
  consistency checker stay green.

## Security considerations

- N/A: documentation-only row.

## Rollback considerations

- Revert the doc commit for this row.

## Validation plan

- `uv run python tools/check_docs_quality.py`; `check_docs_structure.py`; `check_docs_content_policy.py`;
  `check_docs_consistency.py --domain agent`; `check_docs_refs.py`; `check_docs_index_completeness.py`;
  `check_docs_japanese.py` — all pass; no GV-023 argument-contract drift for this chapter.

## Completion criteria

- The `/memory list` row states the accepted token grammar (`'+5'`/`'1_0'` accepted, 1..200 bound)
  in prose outside usage code spans (AC-5, AC-7).

## Out of Scope

The session chapter (`agent_07_07`) and all source-code rows — each is its own row.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Extend the `/memory list` row with the accepted token grammar in prose | Completed | 2026-10-23 | 2026-10-23 | REQ-006, REQ-008, AC-5, AC-7 |
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
- **Requirement ID**: `REQ-006`, `REQ-008`
- **Source issue**: `issues/20261021-093421_cmd002-invalid-command-args-silently-reinterpreted.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261022-013404_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261023-020027
- **Related target files**: `docs/23_agent/agent_07_10_cli-and-commands-slash-commands-memory-other.md`
