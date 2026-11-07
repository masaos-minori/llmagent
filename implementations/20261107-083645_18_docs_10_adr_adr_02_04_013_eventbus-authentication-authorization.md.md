## Goal

- Update `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md` to describe only the `AuthzGeneration` seam: remove the `_TOKEN_PRINCIPAL_MAP` alias parenthetical (line 65) and rename the publication step `_populate_token_maps()` to `build_and_publish_generation()` (new) at line 109 (REQ-006).

## Scope
**Release unit**: N/A: single atomic Phase 1 (Plan Phase Boundary)

- Documentation-only edit of the sole `docs/` file naming any removed symbol (Plan Validation Step 2 audit: the checker scans `scripts/ docs/ tests/ tools/` and this file is the only document match). Lands in the same commit as document 01 so the scan never sees the old names after Phase 1.

## Assumptions

- Anchors verified 2026-11-07 at HEAD `1a13653e8`: line 65 "The generated map is published atomically into `AuthzGeneration.principals`. `_TOKEN_PRINCIPAL_MAP` is only an alias for that published map."; line 109 (component-contract table, `mcp_agent/api/auth.py` row) "validates it, calls `_populate_token_maps()`, exposes `issue_token_for_employee()`". Re-verify both lines before editing.
- The file's "Superseded Architecture:" section (ADR-012 history, line 1 area) already covers historical naming and needs no change.

## Design decisions

- Two-line minimal diff: delete the alias sentence at line 65; replace `` `_populate_token_maps()` `` with `` `build_and_publish_generation()` `` (new) at line 109 — the name introduced by document 04 (`tests/eventbus/eventbus_helpers.py` row 4 procedure renames the function).
- No new sections, no renumbering; other ADR files untouched (this is the only docs match in the Step 2 audit).

## Alternatives considered

- Rewriting the whole authentication section: rejected — the Plan's documentation row names two specific line edits; a broader rewrite would exceed the narrowest-diff rule (AGENTS.md Policy 5).

## Implementation
### Target file

`docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`

### Procedure

1. Line 65: remove the sentence "`_TOKEN_PRINCIPAL_MAP` is only an alias for that published
   map."; keep the first sentence and its links (`[auth.py](../../mcp_agent/api/auth.py)`).
2. Line 109: replace `_populate_token_maps()` with `build_and_publish_generation()` (new) in the
   component-contract table row for `mcp_agent/api/auth.py`.

### Method

Direct text edits; no code changes.

### Details

Post-edit check:

```bash
rg -n '_TOKEN_PRINCIPAL_MAP|_populate_token_maps|_TOKEN_HASH_CACHE|_verify_token|_CONSUMER_TOKEN_HASH_CACHE' \
  docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md
```

Expect no matches — this is exactly what unlocks the checker flip in document 17 after Phase 1.

## Compatibility considerations

- Sequence with document 01 (auth.py rename `_populate_token_maps` → `build_and_publish_generation()` (new)) in the same atomic Phase 1 commit; the docs checker (`check_compat_shims.py` scan over `docs/`) only stays clean once both land.
- No overlap with plan001/plan003 docs scopes (Plan Assumptions).

## Security considerations

- N/A: documentation edit.

## Rollback considerations

- Revert of the single atomic commit restores both lines (Plan Design "Atomicity").

## Validation plan

- `uv run python tools/check_docs_quality.py docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`
- `uv run python tools/check_docs_structure.py`
- `uv run python tools/check_docs_content_policy.py`
- `uv run python tools/check_docs_consistency.py --domain eventbus`
- The rg command above returns no matches (run after Phase 1 lands).

## Completion criteria

- ADR-013 names no removed symbol and describes `build_and_publish_generation()` (new) as the
  publication step (AC-008).

## Out of Scope

- Other `docs/` files — the Step 2 audit found no other document naming removed symbols (Plan
  Validation).
- ADR-012 "Superseded Architecture" history — unchanged.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Apply the two line edits — Plan Phase 1 (same commit as document 01) | Pending | — | — | re-verify line anchors first |
| 2 | Run the docs checkers listed in Validation plan | Pending | — | — | |

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
- **Requirement ID**: REQ-006
- **Source issue**: issues/20261106-125143_compatrm002_remove-eventbus-auth-compat-state-authzgeneration-only.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261107-063003_compatrm002_remove-eventbus-auth-compat-state-authzgeneration-only.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261107-083645
- **Related target files**: `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`
