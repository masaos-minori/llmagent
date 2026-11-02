# Document the content scrub alongside `masked_fields`

## Goal

Extend the `masked_fields` bullet in `docs/23_agent/agent_08_03_configuration-tools-memory.md` so
it states that string values are additionally scrubbed for content-pattern secrets under any key,
with the approval-preview exception kept intact (Plan REQ-006 / AC-7).

## Scope

- The `masked_fields` bullet (line 32) and its sub-bullets in the tool-configuration section.
- Nothing else in the file; no new doc file.

## Assumptions

- Verified 20261102: the bullet already documents key-based `"***"` masking at any depth, the
  sinks list (audit events, logger writes, REPL tool-call line, plan-mode blocked notice), and the
  approval-preview exception — the exception text stays as-is (UNK-02 recorded decision: preview
  stays raw).
- The doc must land with row 01 so claims match code.

## Design decisions

- Add one sentence to the existing bullet naming the shared masker
  (`agent/secrets_masker.py`) as the content-pattern source — keeps "no second pattern set"
  discoverable (REQ-001) without a new section.

## Alternatives considered

- N/A: docs-only, single bullet.

## Implementation
### Target file
`docs/23_agent/agent_08_03_configuration-tools-memory.md`

### Procedure
Extend the end of the `masked_fields` bullet's first paragraph with: in addition to key-based
replacement, string values under any key are scrubbed for secret content patterns (the
`key=value`, `key: value`, `key => value`, quoted-JSON, `Bearer`/`Authorization`, JWT-shaped and
URL-credential shapes listed in the operations doc), applied at every depth and idempotently.
Keep the two existing sub-bullets (preview rationale, shipped-default note) unchanged.

### Details
- Shape list must match what the masker implements after the batch's masking plans land; phrase
  shapes without regex internals.

## Compatibility considerations

- N/A: documentation only.

## Security considerations

- N/A: describes tested behavior; no new claims beyond rows 01-04.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run python tools/check_docs_quality.py`, `tools/check_docs_structure.py`,
  `tools/check_docs_content_policy.py`, `tools/check_docs_consistency.py --domain agent`
  per `routing.md` Tools "When to run which tool".

## Completion criteria

- The bullet states both masking mechanisms (key-based `"***"` and content scrub), keeps the
  approval-preview exception sentence, and passes the docs checkers.

## Out of Scope

- Changing the approval-preview behavior (out of the Plan).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Extend the `masked_fields` bullet | Completed | 20261102-180240 | 20261102-180004 | Land with rows 01-04 landed in batch 20261102-132615; red-first verified, all targets green |
| 2 | Run the docs checkers (`routing.md`) | Completed | — | 20261102-180004 | full suite 11348 passed/8 skipped; diff-cover 100%; ruff/mypy/bandit/lint-imports/check_module_size green; docs checkers green |

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
- **Requirement ID**: REQ-006 (documented masking coverage incl. content scrub)
- **Source issue**: issues/20261003-180335_maskargs001_audit-masking-misses-free-form-secrets.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261101-140856_maskargs001_audit-masking-misses-free-form-secrets.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261102-132615
- **Related target files**: docs/23_agent/agent_08_03_configuration-tools-memory.md