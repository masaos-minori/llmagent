# Update the data-layer fail-closed bullet to the shared detector

## Goal

Reword the fail-closed bullet in `docs/23_agent/agent_09_01_data-layer-session-db.md` so it
describes the shared-detector guard instead of the deleted `_SENSITIVE_PATTERNS` (Plan REQ-006
docs row / AC-6).

## Scope

- One bullet at line 73 ("Fail-closed detection: ... `_SENSITIVE_PATTERNS` matching raises
  `RuntimeError` ...") in the accepted-storage-posture section. Nothing else in the file.

## Assumptions

- Verified 20261102: line 73 is the only occurrence of `_SENSITIVE_PATTERNS` in the file; the
  carve-out sentence (filter failure → unencrypted persist + log) stays accurate after the change.
- The wording must land with rows 01-02 (the bullet names `detects_secrets` (new) only once the code
  does).

## Design decisions

- Name the shared function and its module (`agent/secrets_masker.py`) so the doc points at the
  single implementation the Plan creates.

## Alternatives considered

- N/A: docs-only, single bullet.

## Implementation
### Target file
`docs/23_agent/agent_09_01_data-layer-session-db.md`

### Procedure
Replace the bullet's phrase "`_SENSITIVE_PATTERNS` matching" with "shared
`agent/secrets_masker.py` detection (`detects_secrets` (new)) matching"; keep the rest of the bullet —
the `RuntimeError` refusal and the `_filter_sensitive_fields()` carve-out — unchanged.

### Details
- The "Residual risk: pattern detection is best-effort" paragraph needs no edit (still true).

## Compatibility considerations

- N/A: documentation only.

## Security considerations

- N/A: describes the guard; no new claims beyond rows 01-04's tested behavior.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run python tools/check_docs_quality.py`, `tools/check_docs_structure.py`,
  `tools/check_docs_content_policy.py`, `tools/check_docs_consistency.py --domain agent`
  per `routing.md` Tools "When to run which tool".

## Completion criteria

- `rg "_SENSITIVE_PATTERNS" docs/23_agent/agent_09_01_data-layer-session-db.md` returns nothing;
  the bullet matches the shipped guard; docs checkers pass.

## Out of Scope

- Any other section; the operations-doc masker shapes paragraph (row 06).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Reword the fail-closed bullet | Completed | — | — | Land with rows 01-02 line 73 bullet rewritten to reference shared detects_secrets(); docs checkers pass |
| 2 | Run the docs checkers (`routing.md`) | Completed | — | — | ruff format/check, mypy, bandit -ll -r scripts/, lint-imports (6 kept), check_module_size, full suite 11276 passed/8 skipped, diff-cover 100%, docs checkers exit 0 |

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
- **Requirement ID**: REQ-006 (data-layer doc names the shared detector)
- **Source issue**: issues/20261003-180341_diagmask001_diagnostic-guard-is-incomplete-secret-allowlist.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261101-140448_diagmask001_diagnostic-guard-is-incomplete-secret-allowlist.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261102-132614
- **Related target files**: docs/23_agent/agent_09_01_data-layer-session-db.md