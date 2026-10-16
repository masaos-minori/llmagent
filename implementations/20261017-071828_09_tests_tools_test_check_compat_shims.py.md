## Goal

Add GV-017 pattern tests for the four new removed-name patterns to
`tests/tools/test_check_compat_shims.py` (`REQ-005`, command-surface reduction).

## Scope

In scope: add tests covering the four new `_REMOVED_NAME_PATTERNS` entries to
`tests/tools/test_check_compat_shims.py`. Out of scope: adding the patterns themselves
(`tools/check_compat_shims.py`, `REQ-005`, separate document), the command/handler/mixin
deletions (`REQ-001`–`REQ-004`), and the `GV-017` documentation update
(`governance_04_documentation-checks.md`, `REQ-007`, separate document).

## Assumptions

- The patterns are gated behind `--check-removed-names` (off by default); tests exercise
  the checker directly against controlled inputs.
- Existing tests provide the fixture/pattern to mirror.

## Design decisions

- **Cover the three required cases.** For each of the four names assert: (a) a hit on
  slash-command usage, (b) no hit on the ordinary word, (c) the historical-context
  exemption suppresses a flagged-but-exempt mention.
- **Parametrize over the four names** to avoid four near-duplicate tests.

## Alternatives considered

`N/A`: the goal requires detecting reintroduction of each name; tests must lock in that
behavior.

## Implementation

### Target file

`tests/tools/test_check_compat_shims.py`

### Procedure

1. Locate the existing GV-017 / `_REMOVED_NAME_PATTERNS` tests and mirror their style.
2. Add, per removed name (`/diff`, `/system`, `/audit`, `/workflow`): a hit-on-command-use
   assertion, a no-hit-on-ordinary-word assertion, and a historical-context-exemption
   assertion.
3. Keep the existing tests unchanged.

### Method

Mirror the existing fixture/setup style; parametrize the removed-name list.

### Details

- The no-hit case uses the bare word (`diff`, `audit`, `system`, `workflow`) in a plausible
  sentence to confirm the leading-`/` anchoring prevents false positives.
- The exemption case uses a historical-context marker string that the exempted corpus
  permits.

## Compatibility considerations

Test-only change; production behavior is unaffected.

## Security considerations

`N/A`: test addition; no secret, permission, or data path is introduced.

## Rollback considerations

Revert the commit.

## Validation plan

- `pytest tests/tools/test_check_compat_shims.py` — all four names pass the three cases.
- `python tools/check_compat_shims.py --check-removed-names` — passes on the current
  corpus.
- `ruff` / `mypy --no-namespace-packages tests/` — clean.

## Completion criteria

`test_check_compat_shims.py` has, for each of `/diff`, `/system`, `/audit`, `/workflow`, a
hit, a no-hit, and an exemption assertion, and all pass.

## Out of scope

`tools/check_compat_shims.py` (`REQ-005`), `command_defs_list.py` (`REQ-001`),
`cmd_context.py` (`REQ-002`), `cmd_audit.py`/`registry.py` (`REQ-003`),
`conversation_service.py` (`REQ-004`), documentation (`REQ-007`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add GV-017 pattern tests to `tests/tools/test_check_compat_shims.py` (`REQ-005`) | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: `REQ-005`
- **Source issue**: `issues/20261016-162117_cli001_remove-diff-system-audit-slash-commands.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261016-233542_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261017-071828
- **Related target files**: `tests/tools/test_check_compat_shims.py`
