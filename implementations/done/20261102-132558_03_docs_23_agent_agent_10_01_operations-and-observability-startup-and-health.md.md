# Update the masker shapes in the operator docs

## Goal

Rewrite the "Secret Masking in MCP Subprocess Failure Reports" paragraph in
`docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md` so it lists the
masker's final masked shapes accurately after the colon forms land (Plan REQ-006 operator-facing
description update / AC-7).

## Scope

- One paragraph rewrite in the existing `### Secret Masking in MCP Subprocess Failure Reports`
  section. No other section, no new doc file.

## Assumptions

- Verified 20261102: the section exists and its text says the masker "masks three shapes" while
  the code already has the quoted-JSON shape (`secrets_masker.py` pattern 6) — the docs claim is
  already stale today.
- Final text must match the row-01 pattern set and the recorded UNK-01 decision (unquoted values
  stop at the first whitespace/newline; quoted values mask in full).

## Design decisions

- State the whitespace decision explicitly in one sentence so operators know a multi-word
  unquoted value is only masked up to the first space — this is the tested contract.

## Alternatives considered

- N/A: docs-only, single paragraph.

## Implementation
### Target file
`docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md`

### Procedure
Replace the single paragraph under `### Secret Masking in MCP Subprocess Failure Reports`.

### Method
The new paragraph must enumerate, case-insensitively: `key=value`; `key: value` unquoted and
quoted (`key: "value"`, `key: 'value'`) for the key names `password`, `passwd`, `pwd`,
`api_key`, `apikey`, `secret`, `token` including suffixed keys such as `access_token` and
`X-Api-Key`; quoted-JSON keys (`"password": "hunter2"`); `Authorization:` header lines (scheme
preserved, token masked); and standalone `Bearer <token>`. Add one sentence: unquoted values are
masked up to the first whitespace or newline; whitespace-containing secrets must be quoted to be
masked in full.

### Details
- Drop the now-false "masks three shapes" count — describe shapes without a count.

## Compatibility considerations

- N/A: documentation only.

## Security considerations

- N/A: describes behavior of `secrets_masker.py`; no new claims beyond rows 01-02's tested shapes.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run python tools/check_docs_quality.py`, `tools/check_docs_structure.py`,
  `tools/check_docs_content_policy.py`, `tools/check_docs_consistency.py --domain agent`
  per `routing.md` Tools "When to run which tool".

## Completion criteria

- The section names every shape row 01 implements, contains no count claim that contradicts
  `SECRET_PATTERNS`, and passes the docs checkers.

## Out of Scope

- Any other section of the file; `gateway_01_operations-and-usage.md` (not a target row).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Rewrite the masking-shapes paragraph | Completed | — | 20261102-160517 | Land with rows 01-02 so claims match code paragraph rewritten: shapes enumerated without a count, colon forms (quoted and unquoted), JSON keys, Authorization scheme preserved, standalone Bearer, whitespace rule stated |
| 2 | Run the docs checkers (`routing.md`) | Completed | — | 20261102-160517 | check_docs_quality/structure/content_policy exit 0; check_docs_consistency --domain agent exit 0 |

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
- **Requirement ID**: REQ-006 (operator-facing shape description)
- **Source issue**: issues/20261003-180324_secmask001_secrets-masker-leaks-unmasked-value.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261101-140116_secmask001_secrets-masker-leaks-unmasked-value.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261102-132558
- **Related target files**: docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md