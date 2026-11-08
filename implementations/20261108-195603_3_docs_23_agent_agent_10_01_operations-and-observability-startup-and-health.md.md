## Goal
State in the secret-masking section that bare-password URL userinfo is masked too (REQ-001).

## Scope
**Release unit**: N/A: not part of a release unit
- One clause of the URL-credential sentence in the "Secret Masking in MCP Subprocess Failure Reports" section (line 96).

## Assumptions
- Adversarial finding: the current clause says "only the password between `:` and `@` is masked, the username is preserved"; that remains true only for the colon form, so it must be scoped, not just extended.
- The same sentence is the only doc in `docs/` that enumerates URL masking shapes (`rg` for `user:password` found one hit).

## Design decisions
- Rewrite the clause to cover both forms and mention that a lone userinfo (`scheme://token@host`, also a username-only one such as `ssh://git@host`) is masked entirely.

## Alternatives considered
N/A: docs-only.

## Implementation
### Target file
`docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md`

### Procedure
1. Replace `credentials embedded in URLs (`scheme://user:password@host` — only the password between `:` and `@` is masked, the username is preserved)` with `credentials embedded in URLs (`scheme://user:password@host` — only the password between `:` and `@` is masked and the username is preserved; a userinfo without a colon, such as `scheme://token@host`, is a bare credential and is masked entirely, which also covers a username-only userinfo like `ssh://git@host`)`.

### Method
Edit that clause only; keep the rest of the long sentence.

### Details
- Do not change the surrounding sentences about quoting and whitespace.

## Compatibility considerations
N/A: docs-only.

## Security considerations
N/A: docs-only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- Documentation checkers selected by `tools/run_validation_gates.py` for `docs/` changes (`check_docs_consistency.py`).

## Completion criteria
- The sentence describes both forms and the username-only over-mask.

## Out of Scope
Code, other docs.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Rewrite the URL-credential clause | Pending | — | — |  |
| 2 | Run the documentation checkers (`routing.md` Tools) | Pending | — | — |  |

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
- **Requirement ID**: `REQ-001` (document bare-password masking)
- **Source issue**: `issues/20261107-191650_secmask002_url-userinfo-secret-leak.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261108-190626_secmask002_url-userinfo-secret-leak.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261108-195603
- **Related target files**: `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md`
