# Extend the masker shapes paragraph for the diagmask shapes

## Goal

Extend the "Secret Masking in MCP Subprocess Failure Reports" paragraph in
`docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md` so it also lists
the shapes diagmask001 adds (Plan REQ-006 / AC-6) — on top of the paragraph secmask001's row 03
already rewrote.

## Scope

- The same single paragraph secmask001 rewrote (batch step 1 before this plan's step 2).
- One added sentence stating that the same shared detection also gates unencrypted diagnostic
  writes, cross-referencing the data-layer doc (agent_09_01).

## Assumptions

- This document executes after secmask001 row 03 landed: the paragraph already enumerates
  `key=value`, unquoted/quoted `key: value`, quoted-JSON keys, `Authorization:` lines and
  standalone `Bearer`; this row only extends it.
- Final key-name list must equal `_KEY_ALT` (new) (row 01): password, passwd, pwd, api_key,
  `apikey`, secret, token, access_token, auth_token, client_secret, bearer, authorization,
  credential, private_key — suffixed forms (`X-Api-Key`) masked too.
- Add the new shapes exactly as row 01 implements them: `=>` separator, bare JWT tokens, and
  `scheme://user:password@host` credentials (only the password masked); no count claim.

## Design decisions

- Keep the paragraph operator-facing: describe shapes, not regex internals; one sentence on the
  guard cross-link so the "one implementation" fact is discoverable from the operations doc.

## Alternatives considered

- N/A: docs-only, single paragraph.

## Implementation
### Target file
`docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md`

### Procedure
Extend the paragraph secmask001 rewrote: append the `key => value` separator, the extended key
names, the bare-JWT shape and the URL-credential shape (with "only the password between `:` and
`@` is masked"), and add the cross-reference sentence that the same `agent/secrets_masker.py`
detection refuses unencrypted `session_diagnostics` writes (see agent_09_01 data-layer doc).

### Details
- The whitespace sentence from secmask001 row 03 stays as-is.

## Compatibility considerations

- N/A: documentation only.

## Security considerations

- N/A: describes behavior tested by rows 03-04.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run python tools/check_docs_quality.py`, `tools/check_docs_structure.py`,
  `tools/check_docs_content_policy.py`, `tools/check_docs_consistency.py --domain agent`
  per `routing.md` Tools "When to run which tool".

## Completion criteria

- The paragraph names every shape the final `SECRET_PATTERNS` masks (neither more nor fewer) and
  the docs checkers pass.

## Out of Scope

- secmask001's base rewrite (owned by that plan's row 03); agent_09_01 (row 05).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Extend the shapes paragraph with the diagmask shapes | Completed | — | — | After secmask001 row 03 and rows 01-03 of this plan masker shapes paragraph extended (14 patterns, => syntax, composite key names, scheme-preserved authorization, URL username preserved); cross-reference to agent_09_01 added |
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
- **Requirement ID**: REQ-006 (operations doc lists the final masked shapes)
- **Source issue**: issues/20261003-180341_diagmask001_diagnostic-guard-is-incomplete-secret-allowlist.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261101-140448_diagmask001_diagnostic-guard-is-incomplete-secret-allowlist.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261102-132614
- **Related target files**: docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md