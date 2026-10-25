# Implementation Procedure — docs/41_db/db_06_api_and_operations-maintenance-and-rotation.md

## Goal

State the active-session retention exemption as policy in the DB maintenance doc
(REQ-007, AC-006): policy wording only, no code detail (issue Documentation Impact).

## Scope

- Modify only `docs/41_db/db_06_api_and_operations-maintenance-and-rotation.md`:
  the `purge_old_sessions` bullet and the `RetentionConfig` paragraph (Section:
  maintenance API list, lines ~23 and ~32).
- English (repo docs rule); no code samples, signatures, or SQL added.

## Assumptions

- This page is the canonical retention-policy location for `scripts/db` maintenance
  (its §Maintenance API lists `purge_old_sessions` and `RetentionConfig`).
- The current wording quoted below is verbatim from HEAD 529c2fe3e; re-confirm before
  editing in case doc churn landed first.

## Design decisions

- Two touch-points: the function bullet (what the guard does) and the
  `RetentionConfig` paragraph (operator-visible count effect), so a reader of either
  paragraph learns the exemption.
- Wording avoids implementation terms (no parameter names, no SQL) per the issue's
  "policy statement, no code detail" constraint.

## Alternatives considered

- A new standalone section for the exemption: rejected — retention text already lives
  in these two spots; a new section would fragment the page (docs style favors
  in-place edits).

## Implementation
### Target file
`docs/41_db/db_06_api_and_operations-maintenance-and-rotation.md`

### Procedure

1. Function bullet — replace:

   > `purge_old_sessions` performs age-based and count-based session purging and
   > commits internally.

   with:

   > `purge_old_sessions` performs age-based and count-based session purging and
   > commits internally. When an active-session guard is supplied, the guarded
   > session is exempt from both retention rules and the exemption is reported in
   > the result data.

2. `RetentionConfig` paragraph — append one sentence after the existing paragraph
   ("`RetentionConfig` defines the session retention limits ... defaults are in the
   dataclass."):

   > When the purge comes from the agent command path, the session currently active
   > in the agent is guarded and therefore exempt from both rules; when the exemption
   > fires, the kept session count may exceed `max_sessions` by one.

### Method
Two in-place text edits (one bullet extension, one appended sentence); no new
sections, headings, or cross-links.

### Details
- Do not state the config defaults numerically (they are documented elsewhere); the
  existing paragraph keeps its current factual claims.

## Compatibility considerations

- `docs/00_index.md` mapping for `docs/41_db/` is unchanged; no index edit needed.
- Adjacent claims (mode semantics, corrupt-archive retention) are untouched.

## Security considerations

N/A: documentation-only.

## Rollback considerations

Restore the two sentences to their quoted originals.

## Validation plan

- Docs checkers per `routing.md` Tools after the edit:
  `uv run python tools/check_docs_quality.py`,
  `uv run python tools/check_docs_structure.py`,
  `uv run python tools/check_docs_content_policy.py`, and
  `uv run python tools/check_docs_consistency.py --domain db`.
- Confirm quoted "before" text still matches HEAD before editing.

## Completion criteria

- AC-006: both statements present; docs checker passes.

## Out of Scope

- The CLI-side operational note (procedure 08).
- Any statement of the guard's parameter names or SQL shape.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Apply the two sentence edits | Completed | — | — | two policy sentences applied; before-wording verified against current file first |
| 2 | Run docs checkers | Completed | — | — | quality/structure/content-policy/consistency(db) green; pre-existing content-policy warning in db_07 copy2() unrelated |

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
- **Requirement ID**: REQ-007 (AC-006)
- **Source issue**: `issues/20261025-115826_sess005_purge-deletes-current-session.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261025-124106_sess005_purge-deletes-current-session.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261025-141651
- **Related target files**: docs/23_agent/agent_07_07_cli-and-commands-slash-commands-session-mcp.md (procedure 08)